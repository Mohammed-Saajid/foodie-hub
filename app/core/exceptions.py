# core/exceptions.py
from typing import Any


class BaseAppException(Exception):
    """Base class for all domain-specific exceptions."""

    def __init__(
        self, status_code: int, code: str, message: str, details: dict[str, Any] | None = None
    ):
        self.status_code = status_code
        self.code = code
        self.message = message
        self.details = details or {}
        super().__init__(self.message)


class ResourceNotFoundException(BaseAppException):
    def __init__(self, message: str = "Resource not found", details: dict[str, Any] | None = None):
        super().__init__(
            status_code=404, code="RESOURCE_NOT_FOUND", message=message, details=details
        )


class InvalidOperationException(BaseAppException):
    def __init__(self, message: str = "Invalid operation", details: dict[str, Any] | None = None):
        super().__init__(
            status_code=400, code="INVALID_OPERATION", message=message, details=details
        )


class ConflictException(BaseAppException):
    def __init__(self, message: str = "Conflict", details: dict[str, Any] | None = None):
        super().__init__(status_code=409, code="CONFLICT", message=message, details=details)


class UnauthorizedException(BaseAppException):
    def __init__(self, message: str = "Unauthorized", details: dict[str, Any] | None = None):
        super().__init__(status_code=401, code="UNAUTHORIZED", message=message, details=details)


class ForbiddenException(BaseAppException):
    def __init__(self, message: str = "Forbidden", details: dict[str, Any] | None = None):
        super().__init__(status_code=403, code="FORBIDDEN", message=message, details=details)


class BadRequestException(BaseAppException):
    def __init__(self, message: str = "Bad request", details: dict[str, Any] | None = None):
        super().__init__(status_code=400, code="BAD_REQUEST", message=message, details=details)
