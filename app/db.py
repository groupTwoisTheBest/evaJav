import os
from pathlib import Path
import asyncpg
from dotenv import load_dotenv
from typing import AsyncGenerator
from loguru import logger



DATABASE_URL = os.getenv("DATABASE_URL") 


_pool: asyncpg.Pool | None = None



async def init_db_pool():
    """Inicializa el pool de conexiones."""
    global _pool
    if _pool is None:
        try:
            _pool = await asyncpg.create_pool(
                DATABASE_URL,
                min_size=10,      # conexiones mínimas abiertas
                max_size=20,      # máx. conexiones simultáneas
                max_queries=50000,  # reinicia tras X consultas
                max_inactive_connection_lifetime=300.0,
            )
            logger.info("Connection pool con PostgreSQL creado exitosamente.")
        except Exception as e:
            logger.error(f"Error al crear el connection pool: {e}")
            raise e


async def close_db_pool():
    """Cierra el pool de conexiones limpiamente."""
    global _pool
    if _pool is not None:
        await _pool.close()
        logger.info("Connection pool con PostgreSQL cerrado.")


async def get_db() -> AsyncGenerator[asyncpg.Connection, None]:
    """
    Dependencia para FastAPI.
    Adquiere una conexión del pool y la devuelve.
    Garantiza que la conexión se libere al terminar el request.
    """
    if _pool is None:
        raise RuntimeError("El pool de conexiones no ha sido inicializado.")

    async with _pool.acquire() as connection:
        yield connection