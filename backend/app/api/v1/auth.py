"""
Authentication Endpoints
User authentication, OAuth, and JWT token management
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional, Dict
from datetime import datetime, timedelta, timezone
from pydantic import BaseModel, Field

from app.database import get_db
from app.config import settings
from app.models import BrokerSession
from app.utils.crypto import encrypt, decrypt
from app.services.audit_service import audit_service
from app.services.zerodha_service import zerodha_service
from fastapi import Request

router = APIRouter()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


class ZerodhaCredentialsUpdate(BaseModel):
    api_key: str = Field(..., min_length=5, description="Zerodha API key")
    api_secret: str = Field(..., min_length=10, description="Zerodha API secret")
    redirect_url: Optional[str] = Field(
        default=None,
        description="Optional override for Zerodha redirect URL",
    )


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
    refresh_token = session_data.get("refresh_token")
    refresh_token_encrypted = encrypt(refresh_token) if refresh_token else None
    public_token = session_data.get("public_token")
    
    # Convert meta data, handling datetime objects
    meta = {}
    for k, v in session_data.items():
        if k not in {"access_token", "refresh_token"}:
            # Convert datetime objects to ISO format strings
            if isinstance(v, datetime):
                meta[k] = v.isoformat()
            else:
                meta[k] = v
    
    expires_at = _calculate_zerodha_expiry()
    now_utc = datetime.now(timezone.utc)
    
    # Convert timezone-aware datetimes to naive UTC for SQLite compatibility
    expires_at_naive = expires_at.replace(tzinfo=None) if expires_at else None
    now_utc_naive = now_utc.replace(tzinfo=None)

    result = await db.execute(
        select(BrokerSession).where(
            BrokerSession.user_identifier == user_identifier,
            BrokerSession.broker == broker,
        )
    )
    broker_session = result.scalar_one_or_none()

    if broker_session:
        broker_session.access_token_encrypted = encrypted_token
        if refresh_token_encrypted:
            broker_session.refresh_token_encrypted = refresh_token_encrypted
        if public_token:
            broker_session.public_token = public_token
        broker_session.status = "active"
        broker_session.meta = meta
        broker_session.expires_at = expires_at_naive
        broker_session.updated_at = now_utc_naive
    else:
        broker_session = BrokerSession(
            user_identifier=user_identifier,
            broker=broker,
            access_token_encrypted=encrypted_token,
            refresh_token_encrypted=refresh_token_encrypted,
            public_token=public_token,
            status="active",
            meta=meta,
            expires_at=expires_at_naive,
            created_at=now_utc_naive,
            updated_at=now_utc_naive,
        )
        db.add(broker_session)

    await db.commit()
    await db.refresh(broker_session)
    return broker_session


from pydantic import BaseModel, EmailStr, Field

class UserRegister(BaseModel):
    """User registration request"""
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(..., min_length=8)
    full_name: Optional[str] = None

class UserLogin(BaseModel):
    """User login request"""
    username: str
    password: str

@router.post("/register")
async def register(user_data: UserRegister, request: Request, db: AsyncSession = Depends(get_db)):
    """
    Register new user
    
    Creates a new user account with hashed password
    """
    from app.services.auth_service import auth_service
    from app.models.user import User, UserRole
    
    # Check if username exists
    existing_user = await auth_service.get_user_by_username(user_data.username, db)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )
    
    # Check if email exists
    existing_email = await auth_service.get_user_by_email(user_data.email, db)
    if existing_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create user
    user = User(
        username=user_data.username,
        email=user_data.email,
        password_hash=auth_service.hash_password(user_data.password),
        full_name=user_data.full_name,
        role=UserRole.TRADER,
        is_active=True,
        created_at=datetime.now(timezone.utc).replace(tzinfo=None),
        updated_at=datetime.now(timezone.utc).replace(tzinfo=None),
    )
    
    db.add(user)
    await db.commit()
    await db.refresh(user)
    
    # Log registration
    await audit_service.log_event(
        action="user_register",
        entity_type="user",
        entity_id=str(user.id),
        details={"username": user.username, "email": user.email},
        user_id=user.id,
        username=user.username,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
        db=db
    )
    
    return {
        "status": "success",
        "message": "User registered successfully",
        "user_id": user.id,
        "username": user.username
    }


@router.post("/login")
async def login(
    user_data: UserLogin,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """
    User login with username/password
    
    Returns JWT access token and refresh token
    """
    from app.services.auth_service import auth_service
    
    # Authenticate user
    user = await auth_service.authenticate_user(user_data.username, user_data.password, db)
    
    if not user:
        # Log failed login attempt
        await audit_service.log_event(
            action="login_failed",
            entity_type="user",
            entity_id=user_data.username,
            details={"reason": "invalid_credentials"},
            username=user_data.username,
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
            db=db
        )
        
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Create JWT tokens
    access_token = auth_service.create_access_token(
        data={"sub": user.username, "user_id": user.id, "role": user.role.value}
    )
    refresh_token = auth_service.create_refresh_token(
        data={"sub": user.username, "user_id": user.id}
    )
    
    # Log successful login
    await audit_service.log_event(
        action="login_success",
        entity_type="user",
        entity_id=str(user.id),
        details={"username": user.username},
        user_id=user.id,
        username=user.username,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
        db=db
    )
    
    return {
        "status": "success",
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "full_name": user.full_name,
            "role": user.role.value
        }
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


@router.post("/zerodha/config")
async def update_zerodha_credentials(
    payload: ZerodhaCredentialsUpdate,
    request: Request,
):
    """Update Zerodha API credentials at runtime."""

    api_key = payload.api_key.strip()
    api_secret = payload.api_secret.strip()
    redirect_url = payload.redirect_url.strip() if payload.redirect_url else None

    if not api_key or not api_secret:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="API key and secret are required",
        )

    try:
        zerodha_service.update_credentials(api_key, api_secret, redirect_url)
    except Exception as exc:  # pragma: no cover - defensive
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to update Zerodha credentials: {exc}",
        ) from exc

    await audit_service.log_event(
        action="broker_credentials_updated",
        entity_type="broker_connection",
        entity_id="zerodha",
        details={
            "redirect_url": redirect_url or zerodha_service.redirect_url,
        },
        username="system",
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )

    return {
        "status": "success",
        "message": "Zerodha credentials updated",
        "redirect_url": redirect_url or zerodha_service.redirect_url,
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
    request: Request,
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
    
    try:
        login_url = zerodha_service.get_login_url(state)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    
    # Log audit event
    await audit_service.log_event(
        action="oauth_initiate",
        entity_type="broker_connection",
        entity_id=state or "anonymous",
        details={"broker": "zerodha", "state": state},
        username=state,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )
    
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
    request: Request,
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
    
    # Check if authorization was successful
    if status != "success" or not request_token:
        # Log failed OAuth attempt
        await audit_service.log_event(
            action="oauth_callback_failed",
            entity_type="broker_connection",
            entity_id=state or "anonymous",
            details={
                "broker": "zerodha",
                "status": status,
                "action": action,
                "request_token_received": request_token is not None
            },
            username=state,
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
            db=db
        )
        
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
        refresh_token = session_data.get("refresh_token")

        # Log successful OAuth
        await audit_service.log_event(
            action="oauth_callback_success",
            entity_type="broker_connection",
            entity_id=user_identifier,
            details={
                "broker": "zerodha",
                "user_id": session_data.get("user_id"),
                "user_name": session_data.get("user_name"),
                "has_refresh_token": refresh_token is not None,
                "expires_at": broker_session.expires_at.isoformat() if broker_session.expires_at else None
            },
            username=user_identifier,
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
            db=db
        )
        return {
            "status": "success",
            "message": "Zerodha session stored successfully",
            "user_identifier": user_identifier,
            "session": {
                "broker": broker_session.broker,
                "expires_at": broker_session.expires_at.isoformat() if broker_session.expires_at else None,
                "has_refresh_token": refresh_token is not None,
                "meta": broker_session.meta,
            },
            "next_steps": [
                f"Call /api/v1/auth/zerodha/session?user_identifier={user_identifier} to view the stored session",
                f"Use user_identifier={user_identifier} with /api/v1/data/zerodha/* endpoints to fetch data",
            ],
        }
    else:
        # Log OAuth error
        await audit_service.log_event(
            action="oauth_callback_error",
            entity_type="broker_connection",
            entity_id=state or "anonymous",
            details={
                "broker": "zerodha",
                "error_message": session_data.get("message", "Unknown error")
            },
            username=state,
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
            db=db
        )
        error_msg = session_data.get("message", "Unknown error")
        return {
            "status": "error",
            "message": error_msg,
            "details": {
                "user_identifier": state,
                "broker": "zerodha",
            },
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
    zerodha_configured = bool(zerodha_service.api_key and zerodha_service.api_secret)

    return {
        "status": "success",
        "brokers": {
            "zerodha": {
                "configured": zerodha_configured,
                "api_key_set": bool(zerodha_service.api_key),
                "redirect_url": zerodha_service.redirect_url,
                "status": "configured" if zerodha_configured else "not_configured",
                "message": (
                    "Ready for OAuth authentication"
                    if zerodha_configured
                    else "Provide API key and secret to enable Zerodha"
                ),
            },
            "groww": {
                "configured": bool(settings.GROWW_API_KEY),
                "status": "not_configured",
                "message": "Not configured yet",
            },
        },
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


@router.post("/zerodha/refresh")
async def manual_refresh_zerodha_token(
    request: Request,
    user_identifier: Optional[str] = Query(
        default=None,
        description="User identifier for the session to refresh"
    ),
    db: AsyncSession = Depends(get_db)
):
    """
    Manually refresh Zerodha access token for a user session
    
    This endpoint allows manual triggering of token refresh for a specific user.
    Useful for testing or when auto-refresh fails.
    
    Returns:
        dict: Refresh operation result
    """
    from app.services.token_refresh_service import token_refresh_service
    
    identifier = user_identifier or "default"
    
    # Find the session
    result = await db.execute(
        select(BrokerSession).where(
            BrokerSession.user_identifier == identifier,
            BrokerSession.broker == "zerodha",
        )
    )
    session = result.scalar_one_or_none()
    
    if not session:
        # Log failed manual refresh attempt
        await audit_service.log_event(
            action="token_refresh_manual_failed",
            entity_type="broker_session",
            entity_id=identifier,
            details={
                "broker": "zerodha",
                "reason": "session_not_found"
            },
            username=identifier,
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
            db=db
        )
        
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No Zerodha session found for user: {identifier}"
        )
    
    # Refresh the session
    refresh_result = await token_refresh_service.refresh_session(session)
    
    # Log manual refresh attempt
    await audit_service.log_event(
        action="token_refresh_manual",
        entity_type="broker_session",
        entity_id=identifier,
        details={
            "broker": "zerodha",
            "status": refresh_result["status"],
            "expires_at": refresh_result.get("expires_at"),
            "error": refresh_result.get("message") if refresh_result["status"] != "success" else None
        },
        username=identifier,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
        db=db
    )
    
    if refresh_result["status"] == "success":
        return {
            "status": "success",
            "message": "Token refreshed successfully",
            "user_identifier": identifier,
            "expires_at": refresh_result.get("expires_at"),
        }
    else:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=refresh_result.get("message", "Failed to refresh token")
        )


@router.get("/zerodha/refresh/status")
async def get_refresh_service_status():
    """
    Get status of the token refresh service
    
    Returns:
        dict: Refresh service status information
    """
    from app.services.token_refresh_service import token_refresh_service
    from app.config import settings
    
    status_info = token_refresh_service.get_status()
    
    return {
        "status": "success",
        "auto_refresh_enabled": settings.ZERODHA_AUTO_REFRESH_ENABLED,
        "refresh_service": status_info,
    }

