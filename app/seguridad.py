import jwt
import os
from datetime import datetime, timedelta, timezone


key = os.getenv("JWT_SECRET")
algorithm = "HS256"
exp_minutes=30

async def create_token(email: str) -> str:

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
