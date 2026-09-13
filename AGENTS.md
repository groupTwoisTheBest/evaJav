# AGENTS.md

## What this is
FastAPI + Jinja2 teacher evaluation app. Deployed on Vercel. PostgreSQL via asyncpg. Password hashing con pwdlib[argon2]. Autenticación via JWT (PyJWT).

## Run
    uvicorn main:app --reload

## Tests
    pytest

Requires live PostgreSQL. Set `DATABASE_URL` (or `POSTGRES_URL`) in `.env`.

## Dependencies

- `fastapi` + `jinja2` — web framework + templates
- `asyncpg` — driver async de PostgreSQL
- `pwdlib[argon2]` — hashing de contraseñas (Argon2id)
- `PyJWT` — creación y verificación de tokens JWT
- `loguru` — logging
- `python-dotenv` — carga de `.env`

## Gotchas

- **Contraseñas en texto plano (PENDIENTE):** Actualmente `app/repositorio.py` almacena y compara contraseñas sin hashear. Se debe implementar hashing con `pwdlib` (ya instalado como dependencia en `pyproject.toml`).
- **No lint/format/typecheck** está configurado para este repo.
- **No hay tests** configurados aún.
- **Schema SQL menciona bcrypt** (`schema.sql:30`) pero se usa `pwdlib` con Argon2id.

## Password Hashing

Usar `pwdlib` con hasher Argon2id. API principal:

```python
from pwdlib import PasswordHash

# Crear instancia (recomendada: usa Argon2id con params por defecto)
password_hasher = PasswordHash.recommended()

# Hashear contraseña
hashed = password_hasher.hash("mi_contraseña")

# Verificar contraseña (orden: password, hash)
is_valid = password_hasher.verify("correcta", hashed)  # True
is_valid = password_hasher.verify("incorrecta", hashed)  # False

# Verificar + rehashear si los parámetros cambiaron
valid, updated_hash = password_hasher.verify_and_update("correcta", hashed)
if updated_hash:
    # Actualizar en DB con updated_hash
```

### Integración en el código

**`app/repositorio.py`** — cambios necesarios:
- `registrar_estudiante()`: hashear antes de INSERT
- `inicio_sesion()`: buscar por email, luego `verify()` con el hash de la DB
- `inicio_sesion_admin()`: mismo patrón

**Patrón recomendado para login:**
```python
async def inicio_sesion(conn, email: str, contrasenna: str) -> dict | None:
    row = await conn.fetchrow(
        "SELECT email, contrasenna FROM estudiantes WHERE email = $1",
        email
    )
    if row is None:
        return None
    if not password_hasher.verify(contrasenna, row["contrasenna"]):
        return None
    return dict(row)
```

**Patrón recomendado para registro:**
```python
async def registrar_estudiante(conn, nombre, email, contrasenna, grado):
    hashed = password_hasher.hash(contrasenna)
    async with conn.transaction():
        estudiante_id = await conn.fetchval(
            "INSERT INTO estudiantes (nombre, contrasenna, email, id_grado) VALUES ($1, $2, $3, $4) RETURNING id",
            nombre, hashed, email, grado
        )
        # ... inscripciones
```

## Rules

- **Pedir permiso antes de modificar archivos**: Cada vez que se modifique un archivo, se debe solicitar permiso al usuario antes de aplicar los cambios.
- **Testear al finalizar procesos**: Cada vez que termine algún proceso o tarea, se debe ejecutar un testeo para verificar que todo funciona correctamente.
