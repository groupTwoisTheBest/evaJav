from pathlib import Path
import jwt
import os
from dotenv  import load_dotenv
from datetime import datetime, timedelta, timezone
from pwdlib import PasswordHash

password_hash = PasswordHash.recommended()

load_dotenv(Path(__file__).resolve().parents[1] / ".env")
key = os.getenv("JWT_SECRET")
if not key:
    raise RuntimeError("La variable de entorno JWT_SECRET no está configurada.")
algorithm = "HS256"
exp_minutes=30

def create_token(email: str) -> str:

    payload={
    "email": email,
    "exp": datetime.now(tz=timezone.utc) + timedelta(minutes=exp_minutes)
    }
    return jwt.encode(payload, key, algorithm=algorithm)

def verify_token(token: str) -> str | None:
    try:
        payload = jwt.decode(token,key,algorithms=[algorithm])
        return payload.get("email")
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None


def hash_password(password: str) -> str:
    return password_hash.hash(password)

def verify_password(password: str, hash: str) -> bool:
    return password_hash.verify(password, hash)
