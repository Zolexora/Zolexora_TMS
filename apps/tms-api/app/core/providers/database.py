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
    # This provider represents the current PostgreSQL architecture.
    # Currently it just wraps the existing async_sessionmaker or engine if needed, 
    # but for now we simply define the interface.
    
    def __init__(self, database_identifier: str):
        self.database_identifier = database_identifier
        
    async def get_connection(self) -> Any:
        # For the current architecture, dependencies already use get_db
        return None
        
    async def health_check(self) -> bool:
        return True
        
    async def get_schema_version(self) -> int:
        return 1
        
    async def run_migrations(self, target_version: int = None) -> bool:
        return True
        
    async def close(self) -> None:
        pass


import sqlite3
import aiosqlite

class D1TenantProvider(TenantDatabaseProvider):
    # Adapter for D1. Uses aiosqlite locally for validation purposes
    # since D1 is effectively a remote SQLite compatible environment.
    
    def __init__(self, database_identifier: str):
        self.database_identifier = database_identifier
        self.db_path = f"/tmp/{database_identifier}"
        self.conn = None
        
    async def get_connection(self) -> Any:
        if not self.conn:
            self.conn = await aiosqlite.connect(self.db_path)
            self.conn.row_factory = aiosqlite.Row
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
        # Schema is created via migration service prepare_schema
        return True
        
    async def close(self) -> None:
        if self.conn:
            await self.conn.close()
            self.conn = None
