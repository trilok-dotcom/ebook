import logging
from fastapi import Header, HTTPException, Depends
from typing import Dict
from firebase_admin import auth as admin_auth

logger = logging.getLogger(__name__)


async def verify_bearer(authorization: str | None = Header(default=None)) -> Dict:
    """
    Verify Firebase ID token from Authorization header
    Returns decoded token with user info
    """
    if not authorization:
        raise HTTPException(
            status_code=401,
            detail="Missing Authorization header"
        )
    
    if not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=401,
            detail="Invalid Authorization header format. Expected 'Bearer <token>'"
        )
    
    token = authorization.split(" ", 1)[1]
    
    if not token:
        raise HTTPException(status_code=401, detail="Empty token")
    
    try:
        decoded = admin_auth.verify_id_token(token, check_revoked=True)
        logger.info(f"User authenticated: {decoded.get('uid')}")
        return decoded
        
    except admin_auth.InvalidIdTokenError:
        logger.warning("Invalid Firebase token received")
        raise HTTPException(status_code=401, detail="Invalid token")
        
    except admin_auth.ExpiredIdTokenError:
        logger.warning("Expired Firebase token received")
        raise HTTPException(status_code=401, detail="Token expired. Please sign in again")
        
    except admin_auth.RevokedIdTokenError:
        logger.warning("Revoked Firebase token received")
        raise HTTPException(status_code=401, detail="Token has been revoked")
        
    except admin_auth.CertificateFetchError:
        logger.error("Failed to fetch Firebase certificates")
        raise HTTPException(status_code=500, detail="Authentication service error")
        
    except Exception as e:
        logger.error(f"Token verification error: {str(e)}")
        raise HTTPException(status_code=401, detail="Authentication failed")


async def require_doctor(user: Dict = Depends(verify_bearer)) -> Dict:
    """Require user to be a doctor"""
    # You need to fetch user role from Firestore
    # This is a simplified version
    if user.get("role") != "doctor":
        raise HTTPException(
            status_code=403,
            detail="This action requires doctor privileges"
        )
    return user