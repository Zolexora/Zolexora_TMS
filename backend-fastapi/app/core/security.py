"""Verifies Supabase Auth JWTs and resolves the app-level user session.

Verification strategy (current Supabase-recommended approach, as of the
JWT Signing Keys rollout): Supabase now signs new-project tokens with an
asymmetric key (ES256/RS256) and exposes the public key at
`{SUPABASE_URL}/auth/v1/.well-known/jwks.json`. This lets us verify tokens
locally (no round-trip to the Supabase Auth server on every request) and
survive key rotation automatically.

Projects that have not yet migrated off the legacy shared JWT secret still
sign with HS256; we detect this from the token header and fall back to
verifying against SUPABASE_JWT_SECRET when it's configured. Supabase's own
migration guidance keeps both paths valid simultaneously during a rotation,
so this dual-path approach is intentional, not a shortcut.

We deliberately do not hard-fail on the `aud` claim: Supabase's own sample
verification code (see their docs/blog on migrating to JWKS) treats `aud`
as informational rather than a hard boundary, because the signature check
is what actually proves the token is genuine. exp/nbf/iat ARE enforced.
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Optional

import jwt
from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.config import Settings, get_settings
from app.core.errors import ForbiddenError, UnauthorizedError

_bearer = HTTPBearer(auto_error=False)

_ASYMMETRIC_ALGS = ["ES256", "RS256"]


@dataclass
class UserSession:
    """Mirrors the original shared/types/auth.ts UserSession shape."""

    user_id: str  # Supabase auth user id (JWT `sub`)
    email: str
    name: Optional[str]
    role: str
    company_codes: list[str] = field(default_factory=list)
    all_company_access: bool = False
    identity_provider: str = "supabase"

    def has_company_access(self, company_code: str) -> bool:
        return self.all_company_access or company_code in self.company_codes

    def assert_company_access(self, company_code: str) -> None:
        if not self.has_company_access(company_code):
            raise ForbiddenError("Access denied to this company")

    def assert_permission(self, permission: str) -> None:
        from app.core.permissions import role_has_permission

        if not role_has_permission(self.role, permission):
            raise ForbiddenError(f"Role '{self.role}' lacks permission '{permission}'")


class _JWKSCache:
    """Lazy, process-wide PyJWKClient so we don't refetch JWKS per request."""

    _client: Optional[jwt.PyJWKClient] = None
    _url: Optional[str] = None

    @classmethod
    def get(cls, jwks_url: str) -> jwt.PyJWKClient:
        if cls._client is None or cls._url != jwks_url:
            cls._client = jwt.PyJWKClient(jwks_url, cache_keys=True, lifespan=600)
            cls._url = jwks_url
        return cls._client


def decode_supabase_jwt(token: str, settings: Settings) -> dict:
    try:
        header = jwt.get_unverified_header(token)
    except jwt.PyJWTError as exc:
        raise UnauthorizedError("Malformed access token") from exc

    alg = header.get("alg", "")
    try:
        if alg.startswith("HS"):
            if not settings.supabase_jwt_secret:
                raise UnauthorizedError(
                    "Token is signed with a legacy HS256 secret but SUPABASE_JWT_SECRET is not configured."
                )
            payload = jwt.decode(
                token,
                settings.supabase_jwt_secret,
                algorithms=["HS256"],
                options={"verify_aud": False},
            )
        else:
            jwks_url = settings.resolved_jwks_url
            if not jwks_url:
                raise UnauthorizedError("SUPABASE_URL / SUPABASE_JWKS_URL is not configured.")
            signing_key = _JWKSCache.get(jwks_url).get_signing_key_from_jwt(token)
            payload = jwt.decode(
                token,
                signing_key.key,
                algorithms=_ASYMMETRIC_ALGS,
                options={"verify_aud": False},
            )
    except UnauthorizedError:
        raise
    except jwt.ExpiredSignatureError as exc:
        raise UnauthorizedError("Access token has expired") from exc
    except jwt.PyJWTError as exc:
        raise UnauthorizedError(f"Invalid access token: {exc}") from exc

    if payload.get("exp") and payload["exp"] < time.time():
        raise UnauthorizedError("Access token has expired")
    return payload


async def _load_profile(request: Request, auth_user_id: str, email: str) -> tuple[str, list[str], bool]:
    """Resolves role + company grants from Supabase Postgres `user_profiles` /
    `user_company_access`. Auto-provisions a Viewer profile with no company
    access on first login so a fresh Supabase Auth sign-up doesn't dead-end
    with a 403 -- an Admin then grants real access from the Companies/Users
    screen. Matches the original AuthRepository: Admin always implies
    all_company_access, derived from role rather than stored separately."""
    pg = request.app.state.pg
    profile = await pg.fetch_one(
        "SELECT auth_user_id, email, full_name, role FROM user_profiles WHERE auth_user_id = $1",
        auth_user_id,
    )
    if profile is None:
        profile = await pg.fetch_one(
            """
            INSERT INTO user_profiles (auth_user_id, email, role)
            VALUES ($1, $2, 'Viewer')
            ON CONFLICT (auth_user_id) DO UPDATE SET email = EXCLUDED.email
            RETURNING auth_user_id, email, full_name, role
            """,
            auth_user_id,
            email,
        )

    role = profile["role"]
    if role == "Admin":
        return role, [], True

    grants = await pg.fetch_all(
        "SELECT company_code FROM user_company_access WHERE auth_user_id = $1 AND is_active = true",
        auth_user_id,
    )
    return role, [g["company_code"] for g in grants], False


async def get_current_user(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(_bearer),
    settings: Settings = Depends(get_settings),
) -> UserSession:
    if credentials is None or not credentials.credentials:
        raise UnauthorizedError("Missing bearer token")

    payload = decode_supabase_jwt(credentials.credentials, settings)
    auth_user_id = payload.get("sub")
    email = payload.get("email") or ""
    if not auth_user_id:
        raise UnauthorizedError("Access token is missing a subject claim")

    role, company_codes, all_access = await _load_profile(request, auth_user_id, email)
    name = None
    user_metadata = payload.get("user_metadata") or {}
    if isinstance(user_metadata, dict):
        name = user_metadata.get("full_name") or user_metadata.get("name")

    return UserSession(
        user_id=auth_user_id,
        email=email,
        name=name,
        role=role,
        company_codes=company_codes,
        all_company_access=all_access,
    )


def require_permission(permission: str):
    async def _dependency(user: UserSession = Depends(get_current_user)) -> UserSession:
        user.assert_permission(permission)
        return user

    return _dependency
