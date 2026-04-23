"""
Token Refresh Service
Handles automatic token refresh for broker sessions
"""

import asyncio
import logging
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from app.database import AsyncSessionLocal
from app.models import BrokerSession
from app.services.zerodha_service import zerodha_service
from app.services.audit_service import audit_service
from app.utils.crypto import encrypt, decrypt
from app.api.v1.auth import _store_broker_session, _calculate_zerodha_expiry

logger = logging.getLogger(__name__)


class TokenRefreshService:
    """
    Service for automatically refreshing broker access tokens
    """
    
    def __init__(self, refresh_interval_minutes: int = 15, expiry_buffer_minutes: int = 60):
        """
        Initialize token refresh service
        
        Args:
            refresh_interval_minutes: How often to check for tokens needing refresh
            expiry_buffer_minutes: Refresh tokens that expire within this many minutes
        """
        self.refresh_interval_minutes = refresh_interval_minutes
        self.expiry_buffer_minutes = expiry_buffer_minutes
        self._running = False
        self._task: Optional[asyncio.Task] = None
        self._lock = asyncio.Lock()
        self._last_run: Optional[datetime] = None
        self._next_run: Optional[datetime] = None
    
    @property
    def is_running(self) -> bool:
        """Check if the service is running"""
        return self._running
    
    async def refresh_session(self, broker_session: BrokerSession) -> Dict:
        """
        Refresh a single broker session
        
        Args:
            broker_session: BrokerSession instance to refresh
        
        Returns:
            dict: Result of refresh operation
        """
        if broker_session.broker != "zerodha":
            return {
                "status": "error",
                "message": f"Token refresh not supported for broker: {broker_session.broker}"
            }
        
        if not broker_session.refresh_token_encrypted:
            return {
                "status": "error",
                "message": "No refresh token available for this session"
            }
        
        try:
            # Decrypt refresh token
            refresh_token = decrypt(broker_session.refresh_token_encrypted)
            
            # Call Zerodha service to renew access token
            result = zerodha_service.renew_access_token(refresh_token)
            
            if result["status"] != "success":
                # Mark session as expired
                async with AsyncSessionLocal() as db:
                    db_result = await db.execute(
                        select(BrokerSession).where(
                            BrokerSession.id == broker_session.id
                        )
                    )
                    session_to_update = db_result.scalar_one_or_none()
                    if session_to_update:
                        session_to_update.status = "expired"
                        session_to_update.updated_at = datetime.now(timezone.utc)
                        await db.commit()
                    
                    # Log failed automatic refresh
                    await audit_service.log_event(
                        action="token_refresh_auto_failed",
                        entity_type="broker_session",
                        entity_id=broker_session.user_identifier,
                        details={
                            "broker": broker_session.broker,
                            "error_message": result.get("message", "Failed to refresh token"),
                            "expires_at": broker_session.expires_at.isoformat() if broker_session.expires_at else None
                        },
                        username=broker_session.user_identifier,
                        db=db
                    )
                
                return {
                    "status": "error",
                    "message": result.get("message", "Failed to refresh token"),
                    "user_identifier": broker_session.user_identifier
                }
            
            # Store the refreshed session data
            async with AsyncSessionLocal() as db:
                refreshed_session = await _store_broker_session(
                    db=db,
                    user_identifier=broker_session.user_identifier,
                    broker=broker_session.broker,
                    session_data=result,
                )
                
                # Log successful automatic refresh
                await audit_service.log_event(
                    action="token_refresh_auto_success",
                    entity_type="broker_session",
                    entity_id=broker_session.user_identifier,
                    details={
                        "broker": broker_session.broker,
                        "expires_at": refreshed_session.expires_at.isoformat() if refreshed_session.expires_at else None,
                        "previous_expires_at": broker_session.expires_at.isoformat() if broker_session.expires_at else None
                    },
                    username=broker_session.user_identifier,
                    db=db
                )
                
                logger.info(
                    f"✅ Successfully refreshed token for session: {broker_session.id}, "
                    f"expires at: {refreshed_session.expires_at}"
                )
                
                return {
                    "status": "success",
                    "user_identifier": broker_session.user_identifier,
                    "expires_at": refreshed_session.expires_at.isoformat() if refreshed_session.expires_at else None
                }
        
        except Exception as e:
            logger.error(f"❌ Error refreshing session for {broker_session.id}: {e}")
            
            # Mark session as expired on error
            try:
                async with AsyncSessionLocal() as db:
                    db_result = await db.execute(
                        select(BrokerSession).where(
                            BrokerSession.id == broker_session.id
                        )
                    )
                    session_to_update = db_result.scalar_one_or_none()
                    if session_to_update:
                        session_to_update.status = "expired"
                        session_to_update.updated_at = datetime.now(timezone.utc)
                        await db.commit()
                    
                    # Log error during refresh
                    await audit_service.log_event(
                        action="token_refresh_auto_error",
                        entity_type="broker_session",
                        entity_id=broker_session.user_identifier,
                        details={
                            "broker": broker_session.broker,
                            "error": str(e),
                            "error_type": type(e).__name__
                        },
                        username=broker_session.user_identifier,
                        db=db
                    )
            except Exception as db_error:
                logger.error(f"Failed to update session status: {db_error}")
            
            return {
                "status": "error",
                "message": str(e),
                "user_identifier": broker_session.user_identifier
            }
    
    async def find_sessions_needing_refresh(self) -> list[BrokerSession]:
        """
        Find all Zerodha sessions that need token refresh
        
        Returns:
            list: BrokerSession instances that need refresh
        """
        try:
            async with AsyncSessionLocal() as db:
                # Calculate threshold time (tokens expiring within buffer window)
                now_utc = datetime.now(timezone.utc)
                threshold = now_utc + timedelta(minutes=self.expiry_buffer_minutes)
                
                # Query for active Zerodha sessions expiring soon
                result = await db.execute(
                    select(BrokerSession).where(
                        and_(
                            BrokerSession.broker == "zerodha",
                            BrokerSession.status == "active",
                            BrokerSession.expires_at.isnot(None),
                            BrokerSession.expires_at <= threshold,
                            BrokerSession.refresh_token_encrypted.isnot(None)
                        )
                    )
                )
                
                sessions = result.scalars().all()
                return list(sessions)
        
        except Exception as e:
            logger.error(f"Error finding sessions needing refresh: {e}")
            return []
    
    async def refresh_all_expiring_tokens(self) -> Dict:
        """
        Refresh all tokens that are expiring soon
        
        Returns:
            dict: Summary of refresh operations
        """
        # Prevent concurrent runs
        if not await self._lock.acquire():
            logger.warning("Token refresh already running, skipping this cycle")
            return {"status": "skipped", "message": "Already running"}
        
        try:
            sessions = await self.find_sessions_needing_refresh()
            
            if not sessions:
                logger.debug("No sessions need token refresh at this time")
                return {
                    "status": "success",
                    "refreshed": 0,
                    "failed": 0,
                    "message": "No sessions need refresh"
                }
            
            logger.info(f"Found {len(sessions)} session(s) needing token refresh")
            
            refreshed = 0
            failed = 0
            
            for session in sessions:
                result = await self.refresh_session(session)
                if result["status"] == "success":
                    refreshed += 1
                else:
                    failed += 1
            
            summary = {
                "status": "success",
                "refreshed": refreshed,
                "failed": failed,
                "total": len(sessions)
            }
            
            logger.info(
                f"Token refresh cycle complete: {refreshed} succeeded, {failed} failed"
            )
            
            return summary
        
        finally:
            self._lock.release()
    
    async def _refresh_loop(self):
        """
        Background loop that periodically refreshes tokens
        """
        logger.info(
            f"🔄 Token refresh service started "
            f"(interval: {self.refresh_interval_minutes} minutes, "
            f"buffer: {self.expiry_buffer_minutes} minutes)"
        )
        
        self._running = True
        
        while self._running:
            try:
                self._last_run = datetime.now(timezone.utc)
                self._next_run = self._last_run + timedelta(minutes=self.refresh_interval_minutes)
                
                await self.refresh_all_expiring_tokens()
                
                # Wait for next interval
                await asyncio.sleep(self.refresh_interval_minutes * 60)
            
            except asyncio.CancelledError:
                logger.info("Token refresh service cancelled")
                break
            except Exception as e:
                logger.error(f"Error in token refresh loop: {e}", exc_info=True)
                # Wait a bit before retrying on error
                await asyncio.sleep(60)
    
    async def start(self):
        """Start the background refresh task"""
        if self._running:
            logger.warning("Token refresh service already running")
            return
        
        self._task = asyncio.create_task(self._refresh_loop())
        logger.info("Token refresh service started")
    
    def stop(self):
        """Stop the background refresh task"""
        if not self._running:
            return
        
        self._running = False
        if self._task:
            self._task.cancel()
        logger.info("Token refresh service stopped")
    
    def get_status(self) -> Dict:
        """
        Get current status of the refresh service
        
        Returns:
            dict: Status information
        """
        return {
            "running": self._running,
            "refresh_interval_minutes": self.refresh_interval_minutes,
            "expiry_buffer_minutes": self.expiry_buffer_minutes,
            "last_run": self._last_run.isoformat() if self._last_run else None,
            "next_run": self._next_run.isoformat() if self._next_run else None,
        }


# Global instance
token_refresh_service = TokenRefreshService()

