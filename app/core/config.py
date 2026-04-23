from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "Foodie Hub API"
    PROJECT_VERSION: str = "1.0.0"
    DATABASE_URL: str = "sqlite+aiosqlite:///:memory:"
    SECRET_KEY: str = "DEFAULT_SECRET_KEY"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    RESET_TOKEN_EXPIRE_MINUTES: int = 15
    OTP_LENGTH: int = 6
    ENVIRONMENT: str = "development"
    LOG_LEVEL: str = "INFO"
    BACKEND_CORS_ORIGINS: list[str] = []
    ENABLE_RATE_LIMITING: bool = True
    AUTO_CREATE_TABLES: bool = False

    # Email configuration (Mailtrap)
    MAILTRAP_API_TOKEN: str = ""
    MAILTRAP_ACCOUNT_ID: str = ""
    EMAIL_FROM: str = "noreply@foodiehub.com"
    EMAIL_FROM_NAME: str = "Foodie Hub"
    FRONTEND_URL: str = "http://localhost:3000"

    # Rate limiting configuration
    REDIS_URL: str = "redis://localhost:6379/0"
    RATE_LIMIT: int = 100  # Max requests per window
    RATE_WINDOW: int = 60  # Window size in seconds

    # SSE notifications configuration
    NOTIFICATION_CHANNEL_PREFIX: str = "notifications"
    SSE_RETRY_MS: int = 15000
    SSE_HEARTBEAT_SECONDS: int = 20
    SSE_POLL_TIMEOUT_SECONDS: float = 1.0
    SSE_MAX_GROUPS_PER_CONNECTION: int = 20

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    @model_validator(mode="after")
    def validate_secret_key_for_production(self) -> "Settings":
        if self.ENVIRONMENT.lower() == "production" and self.SECRET_KEY == "DEFAULT_SECRET_KEY":
            raise ValueError("SECRET_KEY must be explicitly set in production")
        return self


settings = Settings()
