"""Dependencias de FastAPI para inyección de conexiones y autenticación.

Este módulo define las dependencias reutilizables que se inyectan en los endpoints:
- ConnectionDep: conexión asíncrona a PostgreSQL desde el pool global.
- CurrentUserDep: correo electrónico del usuario autenticado extraído del JWT cookie.
"""

import asyncpg
from fastapi import Depends, HTTPException, Request, status
from typing import Annotated

from app.database import get_db
from app.seguridad import verify_token

ConnectionDep = Annotated[asyncpg.Connection, Depends(get_db)]
"""Dependencia para obtener una conexión asíncrona a PostgreSQL desde el pool.

Se inyecta en los endpoints que necesitan ejecutar consultas SQL.
"""


async def get_current_user(request: Request) -> str:
    """Extrae y verifica el JWT del cookie `token`, devolviendo el email del usuario.

    Si el cookie no existe o el token es inválido, lanza HTTPException con
    código 303 y redirige a `/`.

    Returns:
        El email del usuario extraído del payload del JWT.

    Raises:
        HTTPException: Si el usuario no está autenticado (303 See Other).
    """
    token = request.cookies.get("token")
    email = verify_token(token) if token else None
    if not email:
        raise HTTPException(
            status_code=status.HTTP_303_SEE_OTHER,
            headers={"location":"/"},
            detail="Usuario no autenticado",
        )
    return email


CurrentUserDep = Annotated[str, Depends(get_current_user)]
"""Dependencia para obtener el email del usuario autenticado.

Se usa como argumento de los endpoints que requieren autenticación.
Devuelve un string (email) o lanza HTTPException si no hay token válido.
"""
