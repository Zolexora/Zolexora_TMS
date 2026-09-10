from typing import List, Optional
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class AdminSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(".env", "../../.env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    PROJECT_NAME: str = "Zolexora Admin Panel API"
    ENVIRONMENT: str = Field(default="development", validation_alias="NODE_ENV")
    PORT: int = 8001
    API_V1_PREFIX: str = "/api/v1"

    CORS_ORIGINS: List[str] = [
        "https://admin.tms.zolexora.worker.dev",
        "http://localhost:5174",
        "http://localhost:3001",
    ]

    DATABASE_URL: str = Field(
        default="postgresql://postgres:postgres@localhost:5432/postgres",
        validation_alias="DATABASE_URL",
    )
    SUPABASE_URL: str = Field(
        default="https://culeiqroofltvizgfzim.supabase.co",
        validation_alias="SUPABASE_URL",
    )
    SUPABASE_SERVICE_ROLE_KEY: str = Field(
        default="", validation_alias="SUPABASE_SERVICE_ROLE_KEY"
    )


settings = AdminSettings()
