import logging
import asyncpg

logger = logging.getLogger(__name__)

class BasePostgreSQLClient:
    """Base client — manages asyncpg connection pool lifecycle."""
    def __init__(self):
        self._pool: asyncpg.Pool | None = None
        
    async def connect(
        self,
        connection_string: str,
        min_size: int = 1,
        max_size: int = 10,
    ) -> None:
        """Create connection pool."""
        if self._pool is not None:
            return
        
        logger.info("[client] Creating connection pool.")
        self._pool = await asyncpg.create_pool(
            dsn=connection_string,
            min_size=min_size,
            max_size=max_size,
        )
        logger.info("[client] Connection pool created (min=%d, max=%d)", min_size, max_size)
        
    async def close(self) -> None:
        """Close connection pool."""
        if self._pool is not None:
            await self._pool.close()
            self._pool = None
            logger.info("[client] Connection pool closed")
            
    async def ping(self) -> bool:
        """Health check - run a simple query."""
        if self._pool is None:
            return False
        
        try:
            async with self._pool.acquire() as conn:
                await conn.fetchval("SELECT 1")
            return True
        except Exception as e:
            logger.error(f"Error in health check function: {e}")
            return False
        
    @property
    def pool(self) -> asyncpg.Pool:
        if self._pool is None:
            raise RuntimeError("Not connected. Call connect() first.")
        return self._pool

    