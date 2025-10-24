from fastapi import Header, HTTPException
from typing import Dict
from firebase_admin import auth as admin_auth

async def verify_bearer(authorization: str | None = Header(default=None)) -> Dict:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing Bearer token")
    token = authorization.split(" ", 1)[1]
    try:
        decoded = admin_auth.verify_id_token(token)
        return decoded
    except Exception as e:
        raise HTTPException(status_code=401, detail="Invalid or expired token") from e
