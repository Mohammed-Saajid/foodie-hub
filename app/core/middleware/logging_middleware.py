import logging
import time
from contextvars import Token

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import Response

from app.core.logger import correlation_id_var


logger = logging.getLogger(__name__)


class CorrelationIDMiddleware(BaseHTTPMiddleware):
    """Sets correlation_id on request.state and logs request lifecycle."""

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        import re
        import uuid

        _SAFE = re.compile(r"^[a-zA-Z0-9\-]{1,64}$")

        incoming = (
            request.headers.get("X-Correlation-ID") or request.headers.get("X-Request-ID") or ""
        )
        correlation_id = incoming if _SAFE.match(incoming) else str(uuid.uuid4())

        token: Token[str] = correlation_id_var.set(correlation_id)  # Set for current context

        request.state.correlation_id = correlation_id

        start = time.perf_counter()
        logger.info(
            "request_start",
            extra={
                "method": request.method,
                "path": request.url.path,
                "client_ip": request.client.host if request.client else "unknown",
            },
        )

        response = await call_next(request)

        duration_ms = round((time.perf_counter() - start) * 1000, 2)
        log_fn = (
            logger.error
            if response.status_code >= 500
            else logger.warning
            if response.status_code >= 400
            else logger.info
        )
        log_fn(
            "request_end",
            extra={
                "status_code": response.status_code,
                "duration_ms": duration_ms,
            },
        )

        response.headers["X-Correlation-ID"] = correlation_id

        correlation_id_var.reset(
            token
        )  # Clean up contextvar to prevent leaks in long-running processes
        return response
