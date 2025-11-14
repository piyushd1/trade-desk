"""
Zerodha Service
Handles Zerodha OAuth authentication and API interactions
"""

from typing import Dict, Optional
from urllib.parse import quote
from kiteconnect import KiteConnect
import hashlib
import logging

from app.config import settings

logger = logging.getLogger(__name__)


class ZerodhaService:
    """
    Service for Zerodha Kite Connect OAuth and API operations
    
    Based on official docs: https://kite.trade/docs/connect/v3/
    """
    
    def __init__(self):
        """Initialize Zerodha service with API credentials"""
        self.api_key = settings.ZERODHA_API_KEY
        self.api_secret = settings.ZERODHA_API_SECRET
        self.redirect_url = settings.ZERODHA_REDIRECT_URL
        self.kite = KiteConnect(api_key=self.api_key) if self.api_key else None

    def update_credentials(
        self,
        api_key: str,
        api_secret: str,
        redirect_url: Optional[str] = None,
    ) -> None:
        """Update Zerodha API credentials at runtime."""

        self.api_key = api_key
        self.api_secret = api_secret
        if redirect_url:
            self.redirect_url = redirect_url

        self.kite = KiteConnect(api_key=self.api_key)
        logger.info("Zerodha credentials updated via API")
    
    def get_login_url(self, state: Optional[str] = None) -> str:
        """
        Generate Zerodha Kite Connect login URL
        
        Returns:
            str: Login URL to redirect user to
        """
        if not self.kite:
            raise ValueError("Zerodha API key is not configured")

        login_url = self.kite.login_url()
        if state:
            # Append state parameter for tracking user sessions
            login_url = f"{login_url}&state={quote(state)}"
            logger.info(f"Generated Zerodha login URL with state={state}")
        else:
            logger.info("Generated Zerodha login URL")
        return login_url
    
    def generate_session(self, request_token: str) -> Dict:
        """
        Exchange request_token for access_token
        
        Args:
            request_token: Token received from Zerodha OAuth callback
        
        Returns:
            dict: Session data with access_token, user details, etc.
        """
        try:
            if not self.kite or not self.api_secret:
                raise ValueError("Zerodha API credentials are not configured")
            # Generate session using request token
            # Checksum = sha256(api_key + request_token + api_secret)
            data = self.kite.generate_session(
                request_token=request_token,
                api_secret=self.api_secret
            )
            
            logger.info(f"✅ Zerodha session generated successfully for user: {data.get('user_id')}")
            
            return {
                "status": "success",
                "access_token": data["access_token"],
                "refresh_token": data.get("refresh_token"),
                "public_token": data.get("public_token"),
                "login_time": data.get("login_time"),
                "api_key": data.get("api_key"),
                "user_id": data.get("user_id"),
                "user_name": data.get("user_name"),
                "email": data.get("email"),
                "user_type": data.get("user_type"),
                "broker": data.get("broker"),
                "exchanges": data.get("exchanges", []),
                "products": data.get("products", []),
                "order_types": data.get("order_types", []),
            }
        
        except Exception as e:
            logger.error(f"❌ Failed to generate Zerodha session: {e}")
            return {
                "status": "error",
                "message": str(e)
            }
    
    def set_access_token(self, access_token: str):
        """
        Set access token for API calls
        
        Args:
            access_token: Valid Zerodha access token
        """
        self.kite.set_access_token(access_token)
        logger.info("Access token set for Zerodha API")
    
    def get_profile(self) -> Dict:
        """
        Get user profile
        
        Returns:
            dict: User profile data
        """
        try:
            profile = self.kite.profile()
            return {"status": "success", "data": profile}
        except Exception as e:
            logger.error(f"Failed to fetch profile: {e}")
            return {"status": "error", "message": str(e)}
    
    def get_margins(self) -> Dict:
        """
        Get account margins
        
        Returns:
            dict: Margin data for all segments
        """
        try:
            margins = self.kite.margins()
            return {"status": "success", "data": margins}
        except Exception as e:
            logger.error(f"Failed to fetch margins: {e}")
            return {"status": "error", "message": str(e)}
    
    def get_positions(self) -> Dict:
        """
        Get current positions
        
        Returns:
            dict: Positions data (net and day)
        """
        try:
            positions = self.kite.positions()
            return {"status": "success", "data": positions}
        except Exception as e:
            logger.error(f"Failed to fetch positions: {e}")
            return {"status": "error", "message": str(e)}
    
    def get_holdings(self) -> Dict:
        """
        Get holdings
        
        Returns:
            dict: Holdings data
        """
        try:
            holdings = self.kite.holdings()
            return {"status": "success", "data": holdings}
        except Exception as e:
            logger.error(f"Failed to fetch holdings: {e}")
            return {"status": "error", "message": str(e)}
    
    def renew_access_token(self, refresh_token: str) -> Dict:
        """
        Renew access token using refresh token
        
        Args:
            refresh_token: Valid refresh token from previous session
        
        Returns:
            dict: New session data with refreshed access_token
        """
        try:
            if not self.api_key or not self.api_secret:
                raise ValueError("Zerodha API credentials are not configured")
            # Create a new Kite instance for renewal
            kite = KiteConnect(api_key=self.api_key)
            
            # Renew access token using refresh token
            data = kite.renew_access_token(
                refresh_token=refresh_token,
                api_secret=self.api_secret
            )
            
            logger.info(f"✅ Zerodha access token renewed successfully for user: {data.get('user_id')}")
            
            return {
                "status": "success",
                "access_token": data["access_token"],
                "refresh_token": data.get("refresh_token"),  # May be same or new
                "public_token": data.get("public_token"),
                "login_time": data.get("login_time"),
                "api_key": data.get("api_key"),
                "user_id": data.get("user_id"),
                "user_name": data.get("user_name"),
                "email": data.get("email"),
                "user_type": data.get("user_type"),
                "broker": data.get("broker"),
                "exchanges": data.get("exchanges", []),
                "products": data.get("products", []),
                "order_types": data.get("order_types", []),
            }
        
        except Exception as e:
            logger.error(f"❌ Failed to renew Zerodha access token: {e}")
            return {
                "status": "error",
                "message": str(e)
            }


# Global instance
zerodha_service = ZerodhaService()

