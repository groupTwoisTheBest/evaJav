# AGENTS.md

## What this is
FastAPI + Jinja2 teacher evaluation app. Deployed on Vercel. PostgreSQL via asyncpg (pool: min=1, max=5, max_queries=50000). Password hashing con pwdlib/Argon2id (`app/seguridad.py`). Autenticación via JWT cookie-based (HS256, 30-min expiry, httponly, samesite=lax, secure=True).

## Run
    uvicorn main:app --reload

## Tests
    pytest

Requires live PostgreSQL. Set `DATABASE_URL` and `JWT_SECRET` in `.env`.

## Dependencies

- `fastapi` + `jinja2` — web framework + templates (20 HTML templates en `templates/`)
- `asyncpg` — driver async de PostgreSQL
- `pwdlib[argon2]` — hashing de contraseñas (Argon2id)
- `PyJWT` — tokens JWT
- `pydantic` — validación de requests (`app/esquemas.py`: EmailStr, Field, min_length)
- `loguru` — logging
- `python-dotenv` — carga de `.env`
- `uvicorn` — ASGI server (usado en `uvicorn main:app --reload`)

## Config

- **Env vars required:** `DATABASE_URL`, `JWT_SECRET`
- **DB pool:** asyncpg pool en `app/database.py`, inicializado con FastAPI lifespan
- **Static files:** montados en `/static`
- **`.gitignore`:** excluye `pyproject.toml` y `.python-version`

## Gotchas

- **No lint/format/typecheck** configurado.
- **No hay tests** — `.gitignore` excluye `test/`.
- **Pydantic schemas** en `app/esquemas.py` definen validación: email (EmailStr), password min 8 chars, nombre max 100 chars.

## Auth Pattern

Cookie-based JWT. `CurrentUserDep` en `app/dependencias.py` extrae email de cookie `token` y verifica con `verify_token()`. Redirige a `/` si no autenticado.

## DB Access

`ConnectionDep` en `app/dependencias.py` inyecta `asyncpg.Connection` desde pool. CRUD en `app/repositorio.py` (inserciones, selects, updates, deletes).
