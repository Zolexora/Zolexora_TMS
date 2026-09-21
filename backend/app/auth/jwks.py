from datetime import datetime, timezone
import json
import logging
from typing import Any, Dict, Optional
import httpx
from jose import jwt, jwk
from jose.exceptions import JWTError, ExpiredSignatureError
from app.core.config import settings

logger = logging.getLogger(__name__)

# In-memory cache for JWKS keys
_JWKS_CACHE: Dict[str, Any] = {}
_JWKS_CACHE_TIME: Optional[float] = None
_CACHE_TTL_SECONDS = 3600  # 1 hour


async def get_supabase_jwks() -> Dict[str, Any]:
    global _JWKS_CACHE, _JWKS_CACHE_TIME
    now = datetime.now(timezone.utc).timestamp()

    if _JWKS_CACHE and _JWKS_CACHE_TIME and (now - _JWKS_CACHE_TIME < _CACHE_TTL_SECONDS):
        return _JWKS_CACHE

    jwks_url = f"{settings.SUPABASE_URL.rstrip('/')}/auth/v1/.well-known/jwks.json"
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(jwks_url)
            if resp.status_code == 200:
                _JWKS_CACHE = resp.json()
                _JWKS_CACHE_TIME = now
                logger.info("Fetched and cached Supabase JWKS successfully")
                return _JWKS_CACHE
    except Exception as e:
        logger.warning(f"Failed to fetch Supabase JWKS from {jwks_url}: {e}")

    return _JWKS_CACHE


async def verify_supabase_jwt(token: str) -> Dict[str, Any]:
    """
    Independently verifies Supabase JWT:
    1. Inspects token header for kid & alg.
    2. If RS256/ES256, matches with Supabase JWKS.
    3. If HS256 and JWT_SECRET is configured, verifies with JWT_SECRET.
    """
    try:
        headers = jwt.get_unverified_header(token)
    except JWTError as e:
        raise ValueError(f"Invalid token header: {e}")

    alg = headers.get("alg", "HS256")
    kid = headers.get("kid")

    if alg.startswith("RS") or alg.startswith("ES"):
        jwks_data = await get_supabase_jwks()
        keys = jwks_data.get("keys", [])
        matched_key = None
        for k in keys:
            if k.get("kid") == kid:
                matched_key = k
                break

        if not matched_key and keys:
            matched_key = keys[0]

        if matched_key:
            public_key = jwk.construct(matched_key)
            return jwt.decode(
                token,
                public_key.to_pem().decode("utf-8"),
                algorithms=[alg],
                audience="authenticated",
                options={"verify_aud": False},
            )

    # Fallback to HS256 symmetric secret if available
    if settings.JWT_SECRET:
        return jwt.decode(
            token,
            settings.JWT_SECRET,
            algorithms=["HS256"],
            options={"verify_aud": False},
        )

    # If neither JWKS nor secret could verify, attempt decode without signature in test/dev if explicitly allowed
    if settings.ENVIRONMENT == "development" and not settings.JWT_SECRET:
        claims = jwt.get_unverified_claims(token)
        exp = claims.get("exp")
        if exp and exp < datetime.now(timezone.utc).timestamp():
            raise ExpiredSignatureError("Token has expired")
        return claims

    raise ValueError("Unable to cryptographically verify token signature")
