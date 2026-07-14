"""Thin asyncio Postgres helper over asyncpg for Supabase-hosted masters data.

Deliberately raw SQL (no ORM) to mirror the original repository-layer style
of the Cloudflare Worker backend (routes/services stay free of SQL; only
*.repository.py files touch this module). Render web services are
long-running processes, so a single pool created at startup is appropriate
here (use the Session Pooler connection string from Supabase; the
Transaction Pooler is intended for true serverless/short-lived connections).
"""
from __future__ import annotations

import logging
from typing import Any, Optional

import asyncpg

logger = logging.getLogger("zolexora.db.supabase_pg")


class SupabasePostgres:
    def __init__(self, dsn: str, min_size: int = 1, max_size: int = 10):
        self._dsn = dsn
        self._min_size = min_size
        self._max_size = max_size
        self._pool: Optional[asyncpg.Pool] = None

    async def connect(self) -> None:
        if self._pool is not None:
            return
        if not self._dsn:
            raise RuntimeError(
                "SUPABASE_DB_URL is not configured. Set it to your Supabase project's "
                "Postgres connection string (Settings -> Database -> Connection string)."
            )
        self._pool = await asyncpg.create_pool(
            dsn=self._dsn,
            min_size=self._min_size,
            max_size=self._max_size,
            # Supabase pooled connections (pgbouncer) don't support prepared
            # statement caching across the pool; disable it to stay compatible
            # whether the caller is using the Session or Transaction pooler.
            statement_cache_size=0,
        )
        logger.info("Supabase Postgres pool ready (max_size=%s)", self._max_size)

    async def close(self) -> None:
        if self._pool is not None:
            await self._pool.close()
            self._pool = None

    @property
    def pool(self) -> asyncpg.Pool:
        if self._pool is None:
            raise RuntimeError("Postgres pool used before connect() was called.")
        return self._pool

    @staticmethod
    def _row_to_dict(row: Optional[asyncpg.Record]) -> Optional[dict[str, Any]]:
        return dict(row) if row is not None else None

    async def fetch_all(self, query: str, *args: Any) -> list[dict[str, Any]]:
        rows = await self.pool.fetch(query, *args)
        return [dict(r) for r in rows]

    async def fetch_one(self, query: str, *args: Any) -> Optional[dict[str, Any]]:
        row = await self.pool.fetchrow(query, *args)
        return self._row_to_dict(row)

    async def fetch_val(self, query: str, *args: Any) -> Any:
        return await self.pool.fetchval(query, *args)

    async def execute(self, query: str, *args: Any) -> str:
        """Returns the command status tag, e.g. 'UPDATE 1'."""
        return await self.pool.execute(query, *args)

    def transaction(self):
        """Usage: `async with pg.transaction() as conn: await conn.execute(...)`."""
        return _TransactionContext(self.pool)


class _TransactionContext:
    def __init__(self, pool: asyncpg.Pool):
        self._pool = pool
        self._conn: Optional[asyncpg.Connection] = None
        self._tx = None

    async def __aenter__(self) -> asyncpg.Connection:
        self._conn = await self._pool.acquire()
        self._tx = self._conn.transaction()
        await self._tx.start()
        return self._conn

    async def __aexit__(self, exc_type, exc, tb) -> None:
        assert self._conn is not None and self._tx is not None
        try:
            if exc_type is not None:
                await self._tx.rollback()
            else:
                await self._tx.commit()
        finally:
            await self._pool.release(self._conn)
