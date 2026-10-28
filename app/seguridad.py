"""Funciones de seguridad: hashing de contraseñas y gestión de tokens JWT.

Este módulo centraliza toda la lógica de seguridad de la aplicación:
- Creación y verificación de tokens JWT para autenticación cookie-based.
- Hashing y verificación de contraseñas con Argon2id mediante pwdlib.

Requisitos:
    - Variable de entorno `JWT_SECRET` obligatoria para firmar/verificar tokens.
"""

from pathlib import Path
import jwt
import os
from dotenv  import load_dotenv
from datetime import datetime, timedelta, timezone
from pwdlib import PasswordHash

password_hash = PasswordHash.recommended()
"""Instancia global de PasswordHash configurada con el algoritmo recomendado (Argon2id).

Se usa para hash_password() y verify_password().
"""

load_dotenv(Path(__file__).resolve().parents[1] / ".env")
key = os.getenv("JWT_SECRET")
if not key:
    raise RuntimeError("La variable de entorno JWT_SECRET no está configurada.")
algorithm = "HS256"
exp_minutes=30


def create_token(email: str) -> str:
    """Crea un token JWT firmado con el email del usuario y una expiración de 30 minutos.

    Args:
        email: Correo electrónico del usuario que se incluye en el payload.

    Returns:
        Token JWT codificado en base64 como string.
    """

    payload={
    "email": email,
    "exp": datetime.now(tz=timezone.utc) + timedelta(minutes=exp_minutes)
    }
    return jwt.encode(payload, key, algorithm=algorithm)


def verify_token(token: str) -> str | None:
    """Verifica y decodifica un token JWT, devolviendo el email si es válido.

    Args:
        token: Token JWT firmado a verificar.

    Returns:
        El email del usuario si el token es válido y no ha expirado,
        o None si el token expiró o es inválido.
    """
    try:
        payload = jwt.decode(token,key,algorithms=[algorithm])
        return payload.get("email")
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None


def hash_password(password: str) -> str:
    """Genera el hash de una contraseña usando Argon2id.

    Args:
        password: Contraseña en texto plano a hashear.

    Returns:
        String con el hash de la contraseña (incluye el salt).
    """
    return password_hash.hash(password)


def verify_password(password: str, hash: str) -> bool:
    """Verifica si una contraseña en texto plano coincide con un hash almacenado.

    Args:
        password: Contraseña en texto plano ingresada por el usuario.
        hash: Hash de contraseña almacenado en la base de datos.

    Returns:
        True si la contraseña coincide con el hash, False en caso contrario.
    """
    return password_hash.verify(password, hash)
