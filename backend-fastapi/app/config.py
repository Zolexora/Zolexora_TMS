"""Central application configuration.

Every external dependency (Supabase, the Cloudflare D1 gateway, CORS) is
driven entirely from environment variables so the same image can be pointed
at local/dev/staging/prod backends without a code change. Copy .env.example
to .env for local development; on Render, set these as service Environment
Variables instead.
"""
from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_env: Literal["development", "staging", "production", "test"] = Field(default="development")

    # --- Supabase (masters + auth) ---------------------------------------
    supabase_url: str = Field(default="", description="https://<project-ref>.supabase.co")
    supabase_db_url: str = Field(
        default="",
        description="Direct Postgres connection string (Session Pooler recommended for Render).",
    )
    # Current recommended verification path: Supabase's JWKS endpoint (asymmetric ES256/RS256).
    # If not set explicitly, it is derived from supabase_url.
    supabase_jwks_url: str = Field(default="")
    # Legacy fallback only: projects that have not migrated off the shared HS256 JWT secret.
    # Safe to leave blank once your Supabase project has rotated to JWT Signing Keys.
    supabase_jwt_secret: str = Field(default="")
    # Server-side key for the Supabase Auth Admin API (user provisioning/lookup only).
    # Accepts either the new "secret key" (sb_secret_...) or legacy service_role key.
    supabase_service_key: str = Field(default="")

    # --- Cloudflare D1 (transactional data) --------------------------------
    # Recommended path: a small authenticated proxy Worker in front of D1 (see
    # cloudflare-d1-gateway/). Cloudflare's own docs mark the raw Admin API as
    # rate-limited/administrative, not meant for hot-path application traffic.
    d1_access_mode: Literal["gateway", "direct_admin_api"] = Field(default="gateway")
    d1_gateway_url: str = Field(default="", description="e.g. https://zolexora-d1-gateway.<subdomain>.workers.dev")
    d1_gateway_token: str = Field(default="")

    # Fallback / simple-deployment mode: call Cloudflare's account-level Admin API directly.
    # Only use this for low-volume deployments; see README for the tradeoffs.
    cf_account_id: str = Field(default="")
    cf_d1_database_id: str = Field(default="")
    cf_api_token: str = Field(default="")

    # --- App-level -----------------------------------------------------------
    cors_allowed_origins: str = Field(default="http://localhost:5173")
    default_currency: str = Field(default="INR")
    request_timeout_seconds: float = Field(default=15.0)

    @property
    def cors_origins(self) -> list[str]:
        return [origin.strip() for origin in self.cors_allowed_origins.split(",") if origin.strip()]

    @property
    def resolved_jwks_url(self) -> str:
        if self.supabase_jwks_url:
            return self.supabase_jwks_url
        if self.supabase_url:
            return f"{self.supabase_url.rstrip('/')}/auth/v1/.well-known/jwks.json"
        return ""


@lru_cache
def get_settings() -> Settings:
    return Settings()
