import logging
from collections.abc import Mapping

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import ValidationError
from sqlalchemy.exc import SQLAlchemyError
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.status import HTTP_500_INTERNAL_SERVER_ERROR

from app.core.exceptions import BaseAppException
from app.schemas.error.error import ErrorDetail, ErrorResponse


logger = logging.getLogger(__name__)


def setup_exception_handlers(app: FastAPI) -> None:

    @app.exception_handler(SQLAlchemyError)
    async def sqlalchemy_exception_handler(request: Request, exc: SQLAlchemyError) -> JSONResponse:
        logger.error(
            "sqlalchemy_exception",
            extra={"error": str(exc), "path": request.url.path},
            exc_info=True,
        )

        response = ErrorResponse(
            status_code=HTTP_500_INTERNAL_SERVER_ERROR,
            message="Database error occurred.",
        )

        return JSONResponse(
            status_code=HTTP_500_INTERNAL_SERVER_ERROR,
            content=response.model_dump(exclude_none=True),
        )

    @app.exception_handler(RuntimeError)
    async def runtime_error_handler(request: Request, exc: RuntimeError) -> JSONResponse:
        logger.error(
            "runtime_error",
            extra={"error": str(exc), "path": request.url.path},
            exc_info=True,
        )

        response = ErrorResponse(
            status_code=HTTP_500_INTERNAL_SERVER_ERROR,
            message="A runtime error occurred.",
            details=[ErrorDetail(loc=[], msg=str(exc), type="runtime_error")],
        )

        return JSONResponse(
            status_code=HTTP_500_INTERNAL_SERVER_ERROR,
            content=response.model_dump(exclude_none=True),
        )

    @app.exception_handler(BaseAppException)
    async def app_exception_handler(request: Request, exc: BaseAppException) -> JSONResponse:
        """Handles expected domain errors."""
        logger.warning(
            "domain_exception",
            extra={
                "error_code": getattr(exc, "code", None),
                "status_code": exc.status_code,
                "details": getattr(exc, "details", None),
                "path": request.url.path,
            },
        )

        # Enforce that custom details match the ErrorDetail schema if provided
        formatted_details = None
        if hasattr(exc, "details") and exc.details:
            try:
                if isinstance(exc.details, dict) and {"loc", "msg", "type"}.issubset(exc.details):
                    formatted_details = [
                        ErrorDetail(
                            loc=[str(loc) for loc in exc.details["loc"]],
                            msg=str(exc.details["msg"]),
                            type=str(exc.details["type"]),
                        )
                    ]
                else:
                    formatted_details = [
                        ErrorDetail(
                            loc=[], msg=str(exc.details), type=str(getattr(exc, "code", "error"))
                        )
                    ]
            except (TypeError, KeyError):
                logger.error("BaseAppException details do not match ErrorDetail schema.")
                formatted_details = []

        response = ErrorResponse(
            status_code=exc.status_code, message=exc.message, details=formatted_details
        )

        return JSONResponse(
            status_code=exc.status_code,
            content=response.model_dump(exclude_none=True),
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        """Overrides the default FastAPI 422 payload to match our schema."""
        logger.warning(
            "validation_exception", extra={"details": exc.errors(), "path": request.url.path}
        )

        # Map FastAPI's internal Pydantic validation errors strictly to ErrorDetail
        details = [
            ErrorDetail(loc=[str(loc) for loc in err["loc"]], msg=err["msg"], type=err["type"])
            for err in exc.errors()
        ]

        response = ErrorResponse(
            status_code=422, message="The request payload is invalid.", details=details
        )

        return JSONResponse(
            status_code=422,
            content=response.model_dump(exclude_none=True),
        )

    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
        """Handles default Starlette/FastAPI HTTP exceptions (e.g., 404 Not Found)."""
        logger.warning(
            "http_exception",
            extra={"status_code": exc.status_code, "detail": exc.detail, "path": request.url.path},
        )

        response = ErrorResponse(status_code=exc.status_code, message=str(exc.detail))

        raw_headers = getattr(exc, "headers", None)
        headers = raw_headers if isinstance(raw_headers, Mapping) else None

        return JSONResponse(
            status_code=exc.status_code,
            content=response.model_dump(exclude_none=True),
            headers=headers,
        )

    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        """
        Catch-all for unhandled exceptions.
        Logs the stack trace but hides it from the client to prevent security leaks.
        """
        logger.error(
            "unhandled_exception",
            extra={"error": str(exc), "path": request.url.path},
            exc_info=True,
        )

        response = ErrorResponse(
            status_code=HTTP_500_INTERNAL_SERVER_ERROR,
            message="An unexpected server error occurred.",
        )

        return JSONResponse(
            status_code=HTTP_500_INTERNAL_SERVER_ERROR,
            content=response.model_dump(exclude_none=True),
        )

    @app.exception_handler(ValidationError)
    async def pydantic_validation_exception_handler(
        request: Request, exc: ValidationError
    ) -> JSONResponse:
        """Handles Pydantic validation errors that occur inside the application."""
        logger.warning(
            "pydantic_validation_exception",
            extra={"details": exc.errors(), "path": request.url.path},
        )

        details = [
            ErrorDetail(loc=[str(loc) for loc in err["loc"]], msg=err["msg"], type=err["type"])
            for err in exc.errors()
        ]

        response = ErrorResponse(
            status_code=422,
            message="An internal validation error occurred.",
            details=details,
        )

        return JSONResponse(
            status_code=422,
            content=response.model_dump(exclude_none=True),
        )
