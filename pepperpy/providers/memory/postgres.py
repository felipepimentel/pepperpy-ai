"""PostgreSQL memory provider implementation."""
from typing import Any, Dict, Optional
import json

import asyncpg

from ..base.provider import BaseProvider, ProviderConfig

class PostgresMemoryProvider(BaseProvider):
    """Provider for PostgreSQL-based memory storage."""
    
    def __init__(self, config: ProviderConfig):
        """Initialize the PostgreSQL memory provider."""
        super().__init__(config)
        self.pool = None
        self.table_name = config.parameters.get("table_name", "pepperpy_memory")
        self.schema = config.parameters.get("schema", "public")
    
    async def initialize(self) -> None:
        """Initialize the PostgreSQL connection pool."""
        if not self._initialized:
            dsn = self.config.parameters.get("dsn")
            if not dsn:
                # Build DSN from individual parameters
                host = self.config.parameters.get("host", "localhost")
                port = self.config.parameters.get("port", 5432)
                database = self.config.parameters.get("database", "pepperpy")
                user = self.config.parameters.get("user", "postgres")
                password = self.config.parameters.get("password")
                
                dsn = f"postgresql://{user}:{password}@{host}:{port}/{database}"
            
            self.pool = await asyncpg.create_pool(dsn)
            
            # Create table if it doesn't exist
            async with self.pool.acquire() as conn:
                await conn.execute(f"""
                    CREATE TABLE IF NOT EXISTS {self.schema}.{self.table_name} (
                        key TEXT PRIMARY KEY,
                        value JSONB,
                        created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
                    )
                """)
            
            self._initialized = True
    
    async def cleanup(self) -> None:
        """Cleanup resources."""
        if self.pool:
            await self.pool.close()
            self._initialized = False
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value from PostgreSQL."""
        if not self._initialized:
            raise RuntimeError("Provider not initialized")
        
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                f"SELECT value FROM {self.schema}.{self.table_name} WHERE key = $1",
                key
            )
            return row["value"] if row else None
    
    async def set(self, key: str, value: Any) -> None:
        """Set value in PostgreSQL."""
        if not self._initialized:
            raise RuntimeError("Provider not initialized")
        
        async with self.pool.acquire() as conn:
            await conn.execute(
                f"""
                INSERT INTO {self.schema}.{self.table_name} (key, value, updated_at)
                VALUES ($1, $2, CURRENT_TIMESTAMP)
                ON CONFLICT (key) DO UPDATE
                SET value = $2, updated_at = CURRENT_TIMESTAMP
                """,
                key,
                json.dumps(value)
            )
    
    async def delete(self, key: str) -> None:
        """Delete value from PostgreSQL."""
        if not self._initialized:
            raise RuntimeError("Provider not initialized")
        
        async with self.pool.acquire() as conn:
            await conn.execute(
                f"DELETE FROM {self.schema}.{self.table_name} WHERE key = $1",
                key
            )
    
    async def exists(self, key: str) -> bool:
        """Check if key exists in PostgreSQL."""
        if not self._initialized:
            raise RuntimeError("Provider not initialized")
        
        async with self.pool.acquire() as conn:
            exists = await conn.fetchval(
                f"SELECT EXISTS(SELECT 1 FROM {self.schema}.{self.table_name} WHERE key = $1)",
                key
            )
            return bool(exists) 