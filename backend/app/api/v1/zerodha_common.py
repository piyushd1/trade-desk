"""
Common helpers for Zerodha-related API modules.
"""

from fastapi import HTTPException, status
from kiteconnect import KiteConnect
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.broker_session import BrokerSession
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


