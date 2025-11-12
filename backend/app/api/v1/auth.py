"""
Authentication Endpoints
User authentication, OAuth, and JWT token management
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional, Dict
from datetime import datetime, timedelta, timezone

from app.database import get_db
from app.config import settings
from app.models import BrokerSession
from app.utils.crypto import encrypt, decrypt

router = APIRouter()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


def _calculate_zerodha_expiry(now: Optional[datetime] = None) -> datetime:
    """Calculate the expected Zerodha token expiry time (6 AM IST)."""
    ist = timezone(timedelta(hours=5, minutes=30))
    now_ist = (now or datetime.utcnow()).astimezone(ist)
    expiry_ist = now_ist.replace(hour=6, minute=0, second=0, microsecond=0)
    if now_ist >= expiry_ist:
        expiry_ist += timedelta(days=1)
    return expiry_ist.astimezone(timezone.utc)


def _mask_token(token: str) -> str:
    if len(token) <= 8:
        return "*" * len(token)
    return f"{token[:6]}...{token[-4:]}"


async def _store_broker_session(
    db: AsyncSession,
    user_identifier: str,
    broker: str,
    session_data: Dict
) -> BrokerSession:
    """Store or update the broker session with encrypted tokens"""
    encrypted_token = encrypt(session_data["access_token"])
    meta = {k: v for k, v in session_data.items() if k != "access_token"}
    expires_at = _calculate_zerodha_expiry()
    now_utc = datetime.now(timezone.utc)

    result = await db.execute(
        select(BrokerSession).where(
            BrokerSession.user_identifier == user_identifier,
            BrokerSession.broker == broker,
        )
    )
    broker_session = result.scalar_one_or_none()

    if broker_session:
        broker_session.access_token_encrypted = encrypted_token
        broker_session.status = "active"
        broker_session.meta = meta
        broker_session.expires_at = expires_at
        broker_session.updated_at = now_utc
    else:
        broker_session = BrokerSession(
            user_identifier=user_identifier,
            broker=broker,
            access_token_encrypted=encrypted_token,
            status="active",
            meta=meta,
            expires_at=expires_at,
            created_at=now_utc,
            updated_at=now_utc,
        )
        db.add(broker_session)

    await db.commit()
    await db.refresh(broker_session)
    return broker_session


@router.post("/register")
async def register(db: AsyncSession = Depends(get_db)):
    """
    Register new user
    
    TODO: Implement user registration
    - Validate email/username
    - Hash password
    - Create user record
    - Generate 2FA secret
    """
    return {
        "message": "User registration endpoint - TODO",
        "status": "not_implemented"
    }


@router.post("/login")
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db)
):
    """
    User login with username/password
    
    Returns JWT access token and refresh token
    
    TODO: Implement
    - Validate credentials
    - Check 2FA
    - Generate JWT tokens
    - Log audit event
    """
    return {
        "message": "Login endpoint - TODO",
        "status": "not_implemented"
    }


@router.post("/logout")
async def logout(token: str = Depends(oauth2_scheme)):
    """
    User logout
    
    TODO: Implement
    - Invalidate token
    - Log audit event
    """
    return {
        "message": "Logout endpoint - TODO",
        "status": "not_implemented"
    }


@router.post("/refresh")
async def refresh_token():
    """
    Refresh access token using refresh token
    
    TODO: Implement
    - Validate refresh token
    - Generate new access token
    """
    return {
        "message": "Token refresh endpoint - TODO",
        "status": "not_implemented"
    }


@router.get("/me")
async def get_current_user(token: str = Depends(oauth2_scheme)):
    """
    Get current authenticated user
    
    TODO: Implement
    - Decode JWT
    - Fetch user from database
    - Return user profile
    """
    return {
        "message": "Get current user endpoint - TODO",
        "status": "not_implemented"
    }


@router.get("/zerodha/connect")
async def zerodha_oauth_initiate(
    state: Optional[str] = Query(
        default=None,
        description="Optional user identifier to track session (e.g., username, email, or friend name)"
    )
):
    """
    Initiate Zerodha OAuth flow
    
    Returns:
        dict: Login URL for Zerodha Kite Connect
    """
    from app.services.zerodha_service import zerodha_service
    
    login_url = zerodha_service.get_login_url(state)
    
    return {
        "status": "success",
        "login_url": login_url,
        "message": "Redirect user to this URL to login with Zerodha",
        "instructions": [
            "1. Open the login_url in browser",
            "2. Login with Zerodha credentials",
            "3. Authorize the app",
            "4. You'll be redirected to callback URL with request_token"
        ],
        "state": state,
    }


@router.get("/zerodha/callback")
async def zerodha_oauth_callback(
    request_token: Optional[str] = None,
    status: Optional[str] = None,
    action: Optional[str] = None,
    state: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """
    Handle Zerodha OAuth callback
    
    This endpoint receives the redirect from Zerodha after user authorization.
    
    Query Parameters:
        request_token: Token to exchange for access_token
        status: success or error
        action: login
    
    Returns:
        dict: Session data with access_token
    """
    from app.services.zerodha_service import zerodha_service
    
    # Check if authorization was successful
    if status != "success" or not request_token:
        return {
            "status": "error",
            "message": "Authorization failed or was denied",
            "details": {
                "status": status,
                "action": action,
                "request_token_received": request_token is not None
            }
        }
    
    # Exchange request_token for access_token
    session_data = zerodha_service.generate_session(request_token)
 
    if session_data["status"] == "success":
        user_identifier = state or session_data.get("user_id") or "default"
        broker_session = await _store_broker_session(
            db=db,
            user_identifier=user_identifier,
            broker="zerodha",
            session_data=session_data,
        )
        access_token = session_data["access_token"]

        return {
            "status": "success",
            "message": "Successfully connected to Zerodha!",
            "user_id": session_data.get("user_id"),
            "user_name": session_data.get("user_name"),
            "broker": "zerodha",
            "user_identifier": user_identifier,
            "state": state,
            "access_token": access_token,
            "access_token_preview": _mask_token(access_token),
            "expires_at": broker_session.expires_at.isoformat() if broker_session.expires_at else None,
            "note": "Access token stored securely. You can now place orders."
        }
    else:
        return {
            "status": "error",
            "message": session_data.get("message", "Unknown error"),
            "broker": "zerodha"
        }


@router.post("/brokers/groww/connect")
async def groww_totp_connect(db: AsyncSession = Depends(get_db)):
    """
    Connect to Groww using TOTP
    
    TODO: Implement
    - Generate TOTP
    - Authenticate with Groww
    - Store session
    - Log audit event
    """
    return {
        "message": "Groww TOTP connection - TODO",
        "status": "not_implemented"
    }


@router.get("/brokers/status")
async def broker_status(db: AsyncSession = Depends(get_db)):
    """
    Get broker connection status
    
    Returns:
        dict: Status of all broker connections
    """
    # TODO: Check actual connection status from database
    return {
        "status": "success",
        "brokers": {
            "zerodha": {
                "configured": bool(settings.ZERODHA_API_KEY),
                "api_key_set": bool(settings.ZERODHA_API_KEY),
                "redirect_url": settings.ZERODHA_REDIRECT_URL,
                "status": "configured" if settings.ZERODHA_API_KEY else "not_configured",
                "message": "Ready for OAuth authentication" if settings.ZERODHA_API_KEY else "API key not configured"
            },
            "groww": {
                "configured": bool(settings.GROWW_API_KEY),
                "status": "not_configured",
                "message": "Not configured yet"
            }
        }
    }


@router.get("/zerodha/session")
async def get_zerodha_session(
    user_identifier: Optional[str] = Query(
        default=None,
        description="User identifier used during OAuth (defaults to Zerodha user_id)"
    ),
    include_token: bool = Query(
        default=False,
        description="Set to true to include decrypted access token in response"
    ),
    db: AsyncSession = Depends(get_db)
):
    """Fetch stored Zerodha session details"""
    identifier = user_identifier or "default"

    result = await db.execute(
        select(BrokerSession).where(
            BrokerSession.user_identifier == identifier,
            BrokerSession.broker == "zerodha",
        )
    )
    session = result.scalar_one_or_none()

    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No Zerodha session found for user")

    response = {
        "user_identifier": session.user_identifier,
        "broker": session.broker,
        "status": session.status,
        "expires_at": session.expires_at.isoformat() if session.expires_at else None,
        "meta": session.meta,
    }

    try:
        decrypted_token = decrypt(session.access_token_encrypted)
    except ValueError:
        decrypted_token = None

    if include_token and decrypted_token:
        response["access_token"] = decrypted_token
    elif decrypted_token:
        response["access_token_preview"] = _mask_token(decrypted_token)

    return {"status": "success", "session": response}

