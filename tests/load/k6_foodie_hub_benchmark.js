import http from 'k6/http';
import { check, group, sleep } from 'k6';
import exec from 'k6/execution';
import { Counter, Rate, Trend } from 'k6/metrics';

const BASE_URL = (__ENV.BASE_URL || 'http://127.0.0.1:8000').replace(/\/$/, '');
const API_PREFIX = __ENV.API_PREFIX || '/api/v1';
const PROFILE = (__ENV.K6_PROFILE || 'baseline').toLowerCase();
const PUBLIC_PEAK_VUS = Number(__ENV.K6_PUBLIC_PEAK_VUS || 0);
const AUTH_PEAK_VUS = Number(__ENV.K6_AUTH_PEAK_VUS || 0);

const USERNAME = __ENV.USERNAME;
const PASSWORD = __ENV.PASSWORD;
const STATIC_ACCESS_TOKEN = __ENV.ACCESS_TOKEN;

const ENABLE_AUTH_SCENARIO =
  (__ENV.ENABLE_AUTH_SCENARIO || 'true').toLowerCase() === 'true' &&
  (Boolean(STATIC_ACCESS_TOKEN) || (Boolean(USERNAME) && Boolean(PASSWORD)));

const ITERATION_THINK_TIME_SEC = Number(__ENV.THINK_TIME_SEC || 0.5);

const endpointLatency = new Trend('endpoint_latency', true);
const businessFailures = new Rate('business_failures');
const authFailures = new Rate('auth_failures');
const loginAttempts = new Counter('login_attempts');

const PROFILES = {
  smoke: {
    public: [
      { duration: '15s', target: 1 },
      { duration: '30s', target: 2 },
      { duration: '15s', target: 0 },
    ],
    auth: [
      { duration: '20s', target: 1 },
      { duration: '20s', target: 2 },
      { duration: '10s', target: 0 },
    ],
  },
  baseline: {
    public: [
      { duration: '30s', target: 5 },
      { duration: '1m', target: 10 },
      { duration: '30s', target: 0 },
    ],
    auth: [
      { duration: '30s', target: 3 },
      { duration: '1m', target: 6 },
      { duration: '30s', target: 0 },
    ],
  },
  stress: {
    public: [
      { duration: '45s', target: 10 },
      { duration: '2m', target: 20 },
      { duration: '45s', target: 0 },
    ],
    auth: [
      { duration: '45s', target: 5 },
      { duration: '2m', target: 12 },
      { duration: '45s', target: 0 },
    ],
  },
};

const selectedProfile = PROFILES[PROFILE] || PROFILES.baseline;

function applyPeakVuOverride(stages, peakVus) {
  if (!Number.isFinite(peakVus) || peakVus <= 0) {
    return stages;
  }

  const currentPeak = stages.reduce((max, stage) => Math.max(max, stage.target), 0);
  if (currentPeak <= 0) {
    return stages;
  }

  const scaleFactor = peakVus / currentPeak;
  return stages.map((stage) => {
    if (stage.target === 0) {
      return { ...stage };
    }
    return {
      ...stage,
      target: Math.max(1, Math.round(stage.target * scaleFactor)),
    };
  });
}

const publicStages = applyPeakVuOverride(selectedProfile.public, PUBLIC_PEAK_VUS);
const authStages = applyPeakVuOverride(selectedProfile.auth, AUTH_PEAK_VUS);

const scenarios = {
  public_api: {
    executor: 'ramping-vus',
    exec: 'publicScenario',
    stages: publicStages,
    gracefulRampDown: '15s',
    tags: { scenario: 'public' },
  },
};

if (ENABLE_AUTH_SCENARIO) {
  scenarios.authenticated_api = {
    executor: 'ramping-vus',
    exec: 'authenticatedScenario',
    startTime: '5s',
    stages: authStages,
    gracefulRampDown: '15s',
    tags: { scenario: 'auth' },
  };
}

export const options = {
  discardResponseBodies: true,
  scenarios,
  thresholds: {
    http_req_failed: ['rate<0.02'],
    http_req_duration: ['p(90)<500', 'p(95)<900'],
    checks: ['rate>0.98'],
    auth_failures: ['rate<0.01'],
    business_failures: ['rate<0.02'],
  },
  summaryTrendStats: ['avg', 'min', 'med', 'p(90)', 'p(95)', 'p(99)', 'max'],
};

function apiUrl(path) {
  return `${BASE_URL}${API_PREFIX}${path}`;
}

function simulatedClientIp() {
  let vuId = 1;
  let iterationId = 0;

  try {
    vuId = exec.vu.idInTest || 1;
  } catch (_) {
    vuId = 1;
  }

  try {
    iterationId = exec.scenario.iterationInTest || 0;
  } catch (_) {
    iterationId = 0;
  }

  const seed = vuId * 100000 + iterationId;
  const octet3 = (seed % 250) + 1;
  const octet4 = (Math.floor(seed / 250) % 250) + 1;
  return `10.10.${octet3}.${octet4}`;
}

function withClientHeaders(headers = {}) {
  const ip = simulatedClientIp();
  return {
    ...headers,
    'X-Real-IP': ip,
    'X-Forwarded-For': ip,
  };
}

function authHeaders(token) {
  return withClientHeaders({
    Authorization: `Bearer ${token}`,
    'Content-Type': 'application/json',
  });
}

function requestJson(method, url, payload = null, params = {}) {
  const body = payload ? JSON.stringify(payload) : null;
  return http.request(method, url, body, params);
}

function checkAndRecord(response, label, expectedStatus) {
  endpointLatency.add(response.timings.duration, { endpoint: label, status: String(response.status) });
  const statusOk = Array.isArray(expectedStatus)
    ? expectedStatus.includes(response.status)
    : response.status === expectedStatus;

  const ok = check(response, {
    [`${label} status is expected`]: () => statusOk,
    [`${label} latency < 1500ms`]: (r) => r.timings.duration < 1500,
  });

  businessFailures.add(!ok);
  return ok;
}

export function setup() {
  if (!ENABLE_AUTH_SCENARIO) {
    console.log('Auth scenario is disabled (no ACCESS_TOKEN or USERNAME/PASSWORD provided).');
    return { token: null };
  }

  if (STATIC_ACCESS_TOKEN) {
    return { token: STATIC_ACCESS_TOKEN };
  }

  loginAttempts.add(1);
  const loginResponse = requestJson('POST', apiUrl('/auth/login'), {
    username: USERNAME,
    password: PASSWORD,
  }, {
    headers: withClientHeaders({ 'Content-Type': 'application/json' }),
    responseType: 'text',
    tags: { endpoint: 'auth_login_setup' },
  });

  let loginPayload = null;
  try {
    loginPayload = loginResponse.json();
  } catch (_) {
    loginPayload = null;
  }

  const loginOk = check(loginResponse, {
    'setup login status is 200': (r) => r.status === 200,
    'setup login has access token': () => Boolean(loginPayload && loginPayload.access_token),
  });

  if (!loginOk) {
    authFailures.add(1);
    exec.test.abort(`Setup login failed: HTTP ${loginResponse.status} ${loginResponse.body || ''}`);
  }

  const accessToken = loginPayload ? loginPayload.access_token : null;
  const firstLoginTermsRequired = Boolean(
    loginPayload ? loginPayload.first_login_terms_required : false,
  );

  if (firstLoginTermsRequired) {
    const acceptTermsResponse = requestJson('POST', apiUrl('/auth/accept-terms'), null, {
      headers: authHeaders(accessToken),
      tags: { endpoint: 'auth_accept_terms_setup' },
    });
    const acceptOk = checkAndRecord(acceptTermsResponse, 'POST /auth/accept-terms (setup)', [200, 201]);
    if (!acceptOk) {
      authFailures.add(1);
      exec.test.abort('Setup terms acceptance failed; this account cannot access terms-protected routes.');
    }
  }

  authFailures.add(0);
  return { token: accessToken };
}

export function publicScenario() {
  group('public_endpoints', () => {
    const healthResponse = requestJson('GET', `${BASE_URL}/health`, null, {
      headers: withClientHeaders(),
      tags: { endpoint: 'health' },
    });
    checkAndRecord(healthResponse, 'GET /health', 200);

    const docsResponse = requestJson('GET', `${BASE_URL}/docs`, null, {
      headers: withClientHeaders(),
      tags: { endpoint: 'docs' },
    });
    checkAndRecord(docsResponse, 'GET /docs', 200);
  });

  sleep(ITERATION_THINK_TIME_SEC);
}

export function authenticatedScenario(data) {
  if (!data || !data.token) {
    exec.test.abort(
      'Authenticated scenario started without a token. Provide ACCESS_TOKEN or USERNAME/PASSWORD.',
    );
  }

  const params = {
    headers: authHeaders(data.token),
  };

  group('authenticated_endpoints', () => {
    const profileResponse = requestJson('GET', apiUrl('/consumer/profile'), null, {
      ...params,
      tags: { endpoint: 'consumer_profile' },
    });
    checkAndRecord(profileResponse, 'GET /api/v1/consumer/profile', 200);

    const offset = Math.floor(Math.random() * 10);
    const hotelsResponse = requestJson('GET', apiUrl(`/consumer/hotels?limit=20&offset=${offset}`), null, {
      ...params,
      tags: { endpoint: 'consumer_hotels' },
    });
    checkAndRecord(hotelsResponse, 'GET /api/v1/consumer/hotels', 200);
  });

  sleep(ITERATION_THINK_TIME_SEC + Math.random() * 0.3);
}
