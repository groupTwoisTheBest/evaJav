import asyncpg
from fastapi import APIRouter, Depends, Request, Form, status
from fastapi.responses import RedirectResponse, PlainTextResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from loguru import logger
from typing import Annotated

from app.database import get_db
ConnectionDep = Annotated[asyncpg.Connection, Depends(get_db)]