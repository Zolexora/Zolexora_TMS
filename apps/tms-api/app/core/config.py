from typing import List, Optional
from pydantic import Field, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(".env", "../../.env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Core Application
    PROJECT_NAME: str = "Zolexora TMS API"
    ENVIRONMENT: str = Field(default="development", validation_alias="NODE_ENV")
    PORT: int = 8000
    API_V1_PREFIX: str = "/api/v1"
    DEBUG: bool = False

    # CORS
    CORS_ORIGINS: List[str] = [
        "https://tms.zolexora.worker.dev",
        "http://localhost:5173",
        "http://localhost:3000",
    ]

    # Database
    DATABASE_URL: str = Field(
        default="postgresql://postgres:postgres@localhost:5432/postgres",
        validation_alias="DATABASE_URL",
    )

    @computed_field
    @property
    def ASYNC_DATABASE_URL(self) -> str:
        url = self.DATABASE_URL
        if url.startswith("postgresql://"):
            return url.replace("postgresql://", "postgresql+asyncpg://", 1)
        elif url.startswith("postgres://"):
            return url.replace("postgres://", "postgresql+asyncpg://", 1)
        return url

    # Supabase Auth
    SUPABASE_URL: str = Field(
        default="https://culeiqroofltvizgfzim.supabase.co",
        validation_alias="SUPABASE_URL",
    )
    SUPABASE_PROJECT_REF: str = Field(
        default="culeiqroofltvizgfzim",
        validation_alias="SUPABASE_PROJECT_REF",
    )
    SUPABASE_ANON_KEY: str = Field(default="", validation_alias="SUPABASE_ANON_KEY")
    SUPABASE_SERVICE_ROLE_KEY: str = Field(
        default="", validation_alias="SUPABASE_SERVICE_ROLE_KEY"
    )
    JWT_SECRET: Optional[str] = Field(default=None, validation_alias="JWT_SECRET")

    # Payment Gateway (Cashfree)
    CASHFREE_APP_ID: Optional[str] = Field(default=None, validation_alias="CASHFREE_APP_ID")
    CASHFREE_SECRET_KEY: Optional[str] = Field(default=None, validation_alias="CASHFREE_SECRET_KEY")
    CASHFREE_ENV: str = Field(default="TEST", validation_alias="CASHFREE_ENV")  # TEST or PROD

    # Storage (Cloudflare R2 & Cloudinary)
    CLOUDFLARE_ACCOUNT_ID: Optional[str] = Field(
        default=None, validation_alias="CLOUDFLARE_ACCOUNT_ID"
    )
    R2_ACCESS_KEY_ID: Optional[str] = Field(default=None, validation_alias="CLOUDFLARE_R2_ACCESS_KEY")
    R2_SECRET_ACCESS_KEY: Optional[str] = Field(default=None, validation_alias="CLOUDFLARE_R2_SECRET_KEY")
    R2_BUCKET_NAME: str = Field(default="zolexora-assets", validation_alias="CLOUDFLARE_R2_BUCKET")
    R2_ENDPOINT_URL: Optional[str] = None

    CLOUDINARY_CLOUD_NAME: Optional[str] = Field(default=None, validation_alias="CLOUDINARY_CLOUD_NAME")
    CLOUDINARY_URL: Optional[str] = Field(default=None, validation_alias="CLOUDINARY_URL")

    # Email (Resend)
    RESEND_API_KEY: Optional[str] = Field(default=None, validation_alias="RESEND_API_KEY")

    # Background Tasks (Redis & Dramatiq)
    REDIS_URL: str = Field(default="redis://localhost:6379/0", validation_alias="REDIS_URL")

    # Observability (Sentry)
    SENTRY_DSN: Optional[str] = Field(default=None, validation_alias="SENTRY_DSN")


settings = Settings()
