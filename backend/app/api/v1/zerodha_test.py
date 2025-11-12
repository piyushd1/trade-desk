"""
Zerodha Testing Endpoints
For testing Zerodha API integration (Development only)
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Optional
import logging

from app.services.zerodha_service import zerodha_service
from app.config import settings

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/test/zerodha/profile")
async def test_zerodha_profile(access_token: str = Query(..., description="Zerodha access token")):
    """
    Test Zerodha API by fetching user profile
    
    Args:
        access_token: Access token obtained from OAuth flow
    
    Returns:
        dict: User profile data from Zerodha
    """
    try:
        zerodha_service.set_access_token(access_token)
        result = zerodha_service.get_profile()
        return result
    except Exception as e:
        logger.error(f"Profile test failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/test/zerodha/margins")
async def test_zerodha_margins(access_token: str = Query(..., description="Zerodha access token")):
    """
    Test Zerodha API by fetching margins
    
    Args:
        access_token: Access token obtained from OAuth flow
    
    Returns:
        dict: Margin data from Zerodha
    """
    try:
        zerodha_service.set_access_token(access_token)
        result = zerodha_service.get_margins()
        return result
    except Exception as e:
        logger.error(f"Margins test failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/test/zerodha/positions")
async def test_zerodha_positions(access_token: str = Query(..., description="Zerodha access token")):
    """
    Test Zerodha API by fetching positions
    
    Args:
        access_token: Access token obtained from OAuth flow
    
    Returns:
        dict: Positions data from Zerodha
    """
    try:
        zerodha_service.set_access_token(access_token)
        result = zerodha_service.get_positions()
        return result
    except Exception as e:
        logger.error(f"Positions test failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/test/zerodha/holdings")
async def test_zerodha_holdings(access_token: str = Query(..., description="Zerodha access token")):
    """
    Test Zerodha API by fetching holdings
    
    Args:
        access_token: Access token obtained from OAuth flow
    
    Returns:
        dict: Holdings data from Zerodha
    """
    try:
        zerodha_service.set_access_token(access_token)
        result = zerodha_service.get_holdings()
        return result
    except Exception as e:
        logger.error(f"Holdings test failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

