"""
Common helpers for Zerodha-related API modules.
"""

from fastapi import HTTPException, status
from kiteconnect import KiteConnect
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.broker_session import BrokerSession
from app.models.user import User
from app.utils.crypto import decrypt


async def get_active_zerodha_session(
    db: AsyncSession, user_identifier: str
) -> BrokerSession:
    """Fetch the active Zerodha broker session for the given user."""
    query = (
        select(BrokerSession)
        .where(BrokerSession.user_identifier == user_identifier)
        .where(BrokerSession.broker == "zerodha")
        .where(BrokerSession.status == "active")
    )
    result = await db.execute(query)
    session = result.scalars().first()

    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No active Zerodha session found for user {user_identifier}",
        )

    return session


def get_kite_client(access_token: str) -> KiteConnect:
    """Create an authenticated KiteConnect client."""
    if not settings.ZERODHA_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Zerodha API key is not configured",
        )

    kite = KiteConnect(api_key=settings.ZERODHA_API_KEY)
    kite.set_access_token(access_token)
    return kite


def decrypt_access_token(session: BrokerSession) -> str:
    """Decrypt the access token stored in the broker session."""
    return decrypt(session.access_token_encrypted)


async def validate_user_owns_session(
    current_user: User,
    user_identifier: str,
    db: AsyncSession
) -> BrokerSession:
    """
    Validate that the current user owns the Zerodha session.
    
    Security: Users can only access their own Zerodha sessions.
    This prevents unauthorized access to other users' trading accounts.
    
    Args:
        current_user: The authenticated user from JWT token
        user_identifier: The Zerodha session identifier to access
        db: Database session
    
    Raises:
        HTTPException: 404 if session not found, 403 if user doesn't own it
    
    Returns:
        BrokerSession: The validated session owned by the user
    """
    # Get the session
    session = await get_active_zerodha_session(db, user_identifier)
    
    # Check ownership - user must own this session
    if session.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"You do not have permission to access session '{user_identifier}'. "
                   f"This session belongs to another user."
        )
    
    return session


