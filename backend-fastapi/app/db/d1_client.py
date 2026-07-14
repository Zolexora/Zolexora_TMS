"""Client for Cloudflare D1 (transactional data: entries, imports, audit).

Two backends behind one interface, selected by settings.d1_access_mode:

- "gateway" (recommended, default): calls the small authenticated Worker in
  cloudflare-d1-gateway/, which holds the real D1 binding. This matches
  Cloudflare's own documented pattern for reaching D1 from a non-Worker app
  (https://developers.cloudflare.com/d1/tutorials/build-an-api-to-access-d1/).
  Supports true atomic multi-statement batches via D1's native db.batch().

- "direct_admin_api": calls Cloudflare's account-level Admin API
  (`/accounts/{id}/d1/database/{id}/query`) directly. Simpler (one fewer
  service to deploy) but Cloudflare's docs mark this API as rate-limited and
  intended for administrative/ad-hoc use, not hot-path application traffic.
  Batches in this mode are executed as sequential statements, NOT as a
  single atomic transaction -- avoid this mode for anything that must be
  all-or-nothing (e.g. posting a ledger batch) unless you accept that risk.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional

import httpx

from app.config import Settings


@dataclass
class D1Result:
    rows: list[dict[str, Any]] = field(default_factory=list)
    meta: dict[str, Any] = field(default_factory=dict)


class D1Error(RuntimeError):
    pass


class D1Client:
    def __init__(self, settings: Settings):
        self._settings = settings
        self._http = httpx.AsyncClient(timeout=settings.request_timeout_seconds)

    async def aclose(self) -> None:
        await self._http.aclose()

    async def query(self, sql: str, params: Optional[list[Any]] = None) -> D1Result:
        params = params or []
        if self._settings.d1_access_mode == "gateway":
            return await self._gateway_query(sql, params)
        return await self._admin_api_query(sql, params)

    async def batch(self, statements: list[tuple[str, list[Any]]]) -> list[D1Result]:
        """Executes multiple statements. In gateway mode this is one atomic
        D1 transaction (db.batch()); in direct_admin_api mode these run as
        sequential, non-atomic requests."""
        if self._settings.d1_access_mode == "gateway":
            return await self._gateway_batch(statements)
        return [await self._admin_api_query(sql, params) for sql, params in statements]

    # -- gateway mode --------------------------------------------------
    async def _gateway_query(self, sql: str, params: list[Any]) -> D1Result:
        if not self._settings.d1_gateway_url:
            raise D1Error("D1_GATEWAY_URL is not configured.")
        resp = await self._http.post(
            f"{self._settings.d1_gateway_url.rstrip('/')}/gateway/query",
            json={"sql": sql, "params": params},
            headers=self._gateway_headers(),
        )
        return self._unwrap_gateway(resp)

    async def _gateway_batch(self, statements: list[tuple[str, list[Any]]]) -> list[D1Result]:
        if not self._settings.d1_gateway_url:
            raise D1Error("D1_GATEWAY_URL is not configured.")
        resp = await self._http.post(
            f"{self._settings.d1_gateway_url.rstrip('/')}/gateway/batch",
            json={"statements": [{"sql": sql, "params": params} for sql, params in statements]},
            headers=self._gateway_headers(),
        )
        if resp.status_code >= 400:
            raise D1Error(f"D1 gateway batch failed ({resp.status_code}): {resp.text}")
        body = resp.json()
        return [D1Result(rows=item.get("results", []), meta=item.get("meta", {})) for item in body.get("results", [])]

    def _gateway_headers(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self._settings.d1_gateway_token}"}

    def _unwrap_gateway(self, resp: httpx.Response) -> D1Result:
        if resp.status_code >= 400:
            raise D1Error(f"D1 gateway query failed ({resp.status_code}): {resp.text}")
        body = resp.json()
        return D1Result(rows=body.get("results", []), meta=body.get("meta", {}))

    # -- direct admin API mode -------------------------------------------
    async def _admin_api_query(self, sql: str, params: list[Any]) -> D1Result:
        s = self._settings
        if not (s.cf_account_id and s.cf_d1_database_id and s.cf_api_token):
            raise D1Error("CF_ACCOUNT_ID / CF_D1_DATABASE_ID / CF_API_TOKEN are not fully configured.")
        url = (
            f"https://api.cloudflare.com/client/v4/accounts/{s.cf_account_id}"
            f"/d1/database/{s.cf_d1_database_id}/query"
        )
        resp = await self._http.post(
            url,
            json={"sql": sql, "params": params},
            headers={"Authorization": f"Bearer {s.cf_api_token}"},
        )
        if resp.status_code >= 400:
            raise D1Error(f"Cloudflare D1 admin API failed ({resp.status_code}): {resp.text}")
        body = resp.json()
        if not body.get("success"):
            raise D1Error(f"Cloudflare D1 admin API returned failure: {body}")
        result = body.get("result") or [{}]
        first = result[0] if result else {}
        return D1Result(rows=first.get("results", []), meta=first.get("meta", {}))
