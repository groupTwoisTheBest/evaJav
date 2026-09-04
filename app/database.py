import os
from pathlib import Path
import asyncpg
from dotenv import load_dotenv
from loguru import logger
from typing import AsyncGenerator

load_dotenv(Path(__file__).resolve().parents[1] / ".env")

DATABASE_URL = os.getenv("DATABASE_URL") 
_pool: asyncpg.Pool | None = None

if not DATABASE_URL:
    logger.error("DATABASE_URL no está configurada en el archivo .env")
else:
    logger.info(f"Conectando a la base de datos en: {DATABASE_URL}")

async def init_db_pool():
    """Inicializa el pool de conexiones."""
    global _pool
    if _pool is None:
        try:
            _pool = await asyncpg.create_pool(
                DATABASE_URL,
                min_size=1,
                max_size=5,
                max_queries=50000,
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

    async with _pool.acquire() as conn:
        yield conn


