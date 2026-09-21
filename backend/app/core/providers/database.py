import os
import httpx
from abc import ABC, abstractmethod
from typing import Any

class TenantDatabaseProvider(ABC):
    @abstractmethod
    async def get_connection(self) -> Any:
        pass
        
    @abstractmethod
    async def health_check(self) -> bool:
        pass
        
    @abstractmethod
    async def get_schema_version(self) -> int:
        pass
        
    @abstractmethod
    async def run_migrations(self, target_version: int = None) -> bool:
        pass
        
    @abstractmethod
    async def close(self) -> None:
        pass

class PostgresTenantProvider(TenantDatabaseProvider):
    def __init__(self, database_identifier: str):
        self.database_identifier = database_identifier
        
    async def get_connection(self) -> Any:
        return None
        
    async def health_check(self) -> bool:
        return True
        
    async def get_schema_version(self) -> int:
        return 1
        
    async def run_migrations(self, target_version: int = None) -> bool:
        return True
        
    async def close(self) -> None:
        pass


class RemoteD1Cursor:
    def __init__(self, rows: list):
        self.rows = rows
        self._index = 0

    async def fetchall(self):
        return self.rows

    async def fetchone(self):
        if self._index < len(self.rows):
            row = self.rows[self._index]
            self._index += 1
            return row
        return None

class RemoteD1ContextManager:
    def __init__(self, conn, sql, params):
        self.conn = conn
        self.sql = sql
        self.params = params

    async def __aenter__(self):
        return await self.conn._execute_internal(self.sql, self.params)

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass

    def __await__(self):
        return self.conn._execute_internal(self.sql, self.params).__await__()

class RemoteD1Connection:
    def __init__(self, database_uuid: str):
        self.database_uuid = database_uuid
        self.account_id = os.environ.get("CLOUDFLARE_ACCOUNT_ID")
        self.api_token = os.environ.get("CLOUDFLARE_API_TOKEN")
        
        if not self.account_id or not self.api_token:
            raise ValueError("CLOUDFLARE_ACCOUNT_ID and CLOUDFLARE_API_TOKEN must be set in environment")
            
        self.client = httpx.AsyncClient(
            base_url=f"https://api.cloudflare.com/client/v4/accounts/{self.account_id}/d1/database/{self.database_uuid}",
            headers={
                "Authorization": f"Bearer {self.api_token}",
                "Content-Type": "application/json",
            },
            timeout=10.0
        )

    def execute(self, sql: str, params: tuple | list = ()):
        return RemoteD1ContextManager(self, sql, params)

    async def _execute_internal(self, sql: str, params: tuple | list):
        payload = {
            "sql": sql,
            "params": list(params)
        }
        response = await self.client.post("/query", json=payload)
        
        if response.status_code != 200:
            raise Exception(f"D1 HTTP Error {response.status_code}: {response.text}")
            
        data = response.json()
        if not data.get("success"):
            raise Exception(f"D1 Query Error: {data.get('errors')}")

        # Extract results array
        results = data["result"][0].get("results", [])
        return RemoteD1Cursor(results)

    async def commit(self):
        # D1 HTTP endpoint is auto-commit.
        pass

    async def close(self):
        await self.client.aclose()


class D1TenantProvider(TenantDatabaseProvider):
    # Adapter for D1. Queries Cloudflare HTTP REST API directly.
    def __init__(self, database_identifier: str):
        # database_identifier must be the UUID of the D1 database.
        self.database_identifier = database_identifier
        self.conn = None
        
    async def get_connection(self) -> Any:
        if not self.conn:
            self.conn = RemoteD1Connection(self.database_identifier)
        return self.conn
        
    async def health_check(self) -> bool:
        try:
            conn = await self.get_connection()
            async with conn.execute("SELECT 1") as cursor:
                await cursor.fetchone()
            return True
        except Exception:
            return False
        
    async def get_schema_version(self) -> int:
        return 1
        
    async def run_migrations(self, target_version: int = None) -> bool:
        return True
        
    async def close(self) -> None:
        if self.conn:
            await self.conn.close()
            self.conn = None

