import asyncpg
from fastapi import APIRouter, Depends, HTTPException, Request, Form, status
from fastapi.responses import RedirectResponse, PlainTextResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from loguru import logger
from typing import Annotated

from app.database import get_db
from app.seguridad import verify_token

ConnectionDep = Annotated[asyncpg.Connection, Depends(get_db)]


async def get_current_user(request: Request) -> str:
    token = request.cookies.get("token")
    email = verify_token(token) if token else None
    if not email:
        raise HTTPException(
            status_code=status.HTTP_303_SEE_OTHER,
            headers={"Location": "/inicio-sesion?error=1"}
        )
    return email


CurrentUserDep = Annotated[str, Depends(get_current_user)]