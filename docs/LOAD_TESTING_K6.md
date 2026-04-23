# Load Testing with k6

This guide provides a practical and laptop-friendly benchmark setup for the Foodie Hub API.

## Scope

The benchmark script covers:

- Public endpoints (`/health`, `/docs`)
- Authenticated consumer endpoints (`/api/v1/consumer/profile`, `/api/v1/consumer/hotels`)

Script path:

- `tests/load/k6_foodie_hub_benchmark.js`

The script sends per-VU `X-Real-IP` and `X-Forwarded-For` headers to simulate distinct clients.
This avoids artificial throttling from local per-IP rate limiting during laptop benchmarks.

## Prerequisites

1. Run the API locally (default expected at `http://127.0.0.1:8000`).
2. Install `k6`.

Linux install example:

```bash
sudo gpg -k
sudo gpg --no-default-keyring --keyring /usr/share/keyrings/k6-archive-keyring.gpg --keyserver hkp://keyserver.ubuntu.com:80 --recv-keys C5AD17C747E3415A3642D57D77C6C491D6AC1D69
echo "deb [signed-by=/usr/share/keyrings/k6-archive-keyring.gpg] https://dl.k6.io/deb stable main" | sudo tee /etc/apt/sources.list.d/k6.list
sudo apt-get update
sudo apt-get install k6
```

## Environment Variables

Optional variables:

- `BASE_URL` (default: `http://127.0.0.1:8000`)
- `API_PREFIX` (default: `/api/v1`)
- `K6_PROFILE` (`smoke`, `baseline`, `stress`; default: `baseline`)
- `K6_PUBLIC_PEAK_VUS` (optional override for peak VUs in public scenario)
- `K6_AUTH_PEAK_VUS` (optional override for peak VUs in authenticated scenario)
- `THINK_TIME_SEC` (default: `0.5`)
- `ENABLE_AUTH_SCENARIO` (`true`/`false`; default: `true`)

For authenticated scenario, provide either:

- `ACCESS_TOKEN` (preferred for stable benchmarking), or
- `USERNAME` and `PASSWORD` (script logs in during setup)

## Recommended Runs (Laptop)

### 1) Quick smoke check

```bash
K6_PROFILE=smoke ENABLE_AUTH_SCENARIO=false k6 run tests/load/k6_foodie_hub_benchmark.js
```

### 2) Baseline benchmark (public + authenticated)

```bash
BASE_URL=http://127.0.0.1:8000 \
K6_PROFILE=baseline \
USERNAME=<your_username> \
PASSWORD=<your_password> \
k6 run tests/load/k6_foodie_hub_benchmark.js
```

### 3) Higher stress pass (still laptop-conscious)

```bash
BASE_URL=http://127.0.0.1:8000 \
K6_PROFILE=stress \
USERNAME=<your_username> \
PASSWORD=<your_password> \
k6 run tests/load/k6_foodie_hub_benchmark.js
```

### 4) Authenticated high-concurrency run with VU overrides

```bash
BASE_URL=http://127.0.0.1:8000 \
K6_PROFILE=stress \
ENABLE_AUTH_SCENARIO=true \
K6_PUBLIC_PEAK_VUS=40 \
K6_AUTH_PEAK_VUS=30 \
USERNAME=<your_test_username> \
PASSWORD=<your_test_password> \
k6 run tests/load/k6_foodie_hub_benchmark.js
```

## Result Interpretation

Default thresholds in the script:

- `http_req_failed < 2%`
- `checks > 98%`
- `http_req_duration p(90) < 500ms`
- `http_req_duration p(95) < 900ms`
- `auth_failures < 1%`

If a threshold fails:

1. Re-run with `K6_PROFILE=smoke` to check consistency.
2. Inspect API logs for database/Redis bottlenecks.
3. Compare `public` vs `auth` scenario behavior to isolate bottlenecks.

## Notes

- Keep browser tabs and heavy apps closed while running stress profile on a laptop.
- For CI or dedicated performance hosts, increase stages/targets in the script.
