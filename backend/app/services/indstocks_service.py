"""
IndStocks (IndMoney) Service

Thin wrapper around `app.brokers.indstocks.IndStocksBroker` for use from
API endpoints and the snapshot scheduler. Every public helper method
instantiates a fresh `IndStocksBroker` for the duration of the call,
executes the operation with the supplied access_token, and closes the
broker's underlying httpx client before returning.

Unlike `zerodha_service`, this service holds NO persistent API credentials
at the module level — IndStocks has no api_key / api_secret. The token is
always supplied per-call by the caller, who typically reads it from an
encrypted `broker_sessions` row. A `default_access_token` is loaded from
`settings.INDSTOCKS_ACCESS_TOKEN` at module import for convenience (e.g.
quick dev testing), but the authenticated API paths should always pass
an explicit token from the user's own `broker_session` row.
"""

from typing import Any, Dict, Optional
import logging

from app.brokers.indstocks import IndStocksBroker
from app.config import settings

logger = logging.getLogger(__name__)


class IndStocksService:
    """
    Service layer for IndStocks operations.

    Stateless. Every public method instantiates a fresh `IndStocksBroker`
    with the supplied access_token, runs the operation, and releases the
    broker's httpx client before returning. No shared HTTP connection pool,
    no persistent broker instance — simpler lifecycle, no cross-request
    state leakage.

    The `default_access_token` loaded from settings is a convenience for
    dev setups that put a single token in `.env`. Production paths should
    read the token from the user's `broker_sessions` row and pass it
    explicitly to each method.
    """

    def __init__(self) -> None:
        self.default_access_token: Optional[str] = settings.INDSTOCKS_ACCESS_TOKEN

    def update_credentials(self, access_token: str) -> None:
        """
        Update the service-level default access token at runtime.

        Analogous to `zerodha_service.update_credentials` but simpler — no
        api_key / api_secret, just the single static bearer token. Used by
        the `POST /api/v1/auth/indstocks/config` endpoint so the user can
        rotate the default token without restarting the backend.
        """
        self.default_access_token = access_token
        logger.info("IndStocks default access token updated via API")

    def _make_broker(self, access_token: Optional[str] = None) -> IndStocksBroker:
        """
        Instantiate a fresh `IndStocksBroker`. Caller MUST call `await
        broker.close()` when done (the public methods on this class all do).
        """
        token = access_token or self.default_access_token
        if not token:
            raise ValueError(
                "IndStocks access_token not provided and no default set in "
                "INDSTOCKS_ACCESS_TOKEN environment variable"
            )
        return IndStocksBroker({"access_token": token})

    # ---------- Token lifecycle ----------

    async def validate_token(self, access_token: str) -> Dict[str, Any]:
        """
        Validate a freshly pasted access token against GET /user/profile.

        Used by the `POST /api/v1/auth/indstocks/token` endpoint to verify
        a token before storing it in `broker_sessions`. Does NOT store the
        token — that's the caller's responsibility.

        Returns:
            `{"status": "success", "user_id": ..., "email": ..., ...}` on success.
            `{"status": "error", "message": ...}` on failure.
        """
        broker = IndStocksBroker({"access_token": access_token})
        try:
            authenticated = await broker.authenticate()
            if not authenticated:
                return {
                    "status": "error",
                    "message": (
                        "IndStocks token validation failed. The token may be "
                        "expired, invalid, or the IndStocks API may be "
                        "temporarily unreachable. Generate a fresh token at "
                        "https://web.indstocks.com and try again."
                    ),
                }

            profile = await broker.get_profile()
            logger.info(
                f"✅ IndStocks token validated "
                f"(user_id={profile.get('user_id', '?')}, "
                f"email={profile.get('email', '?')})"
            )
            return {
                "status": "success",
                "user_id": profile.get("user_id"),
                "email": profile.get("email"),
                "first_name": profile.get("first_name"),
                "is_nse_onboarded": profile.get("is_nse_onboarded"),
            }
        except Exception as exc:  # noqa: BLE001
            logger.error(f"❌ IndStocks validate_token unexpected error: {exc}")
            return {"status": "error", "message": str(exc)}
        finally:
            await broker.close()

    # ---------- Portfolio data helpers ----------

    async def get_profile(self, access_token: Optional[str] = None) -> Dict[str, Any]:
        """Fetch user profile. Returns `{status, data}` envelope."""
        broker = self._make_broker(access_token)
        try:
            profile = await broker.get_profile()
            return {"status": "success", "data": profile}
        except Exception as exc:  # noqa: BLE001
            logger.error(f"❌ IndStocks service get_profile error: {exc}")
            return {"status": "error", "message": str(exc)}
        finally:
            await broker.close()

    async def get_holdings(self, access_token: Optional[str] = None) -> Dict[str, Any]:
        """Fetch long-term holdings. Returns `{status, data}` envelope."""
        broker = self._make_broker(access_token)
        try:
            holdings = await broker.get_holdings()
            return {"status": "success", "data": holdings}
        except Exception as exc:  # noqa: BLE001
            logger.error(f"❌ IndStocks service get_holdings error: {exc}")
            return {"status": "error", "message": str(exc)}
        finally:
            await broker.close()

    async def get_positions(self, access_token: Optional[str] = None) -> Dict[str, Any]:
        """Fetch positions (merged net + day). Returns `{status, data: {net, day}}` envelope."""
        broker = self._make_broker(access_token)
        try:
            positions = await broker.get_positions()
            return {"status": "success", "data": positions}
        except Exception as exc:  # noqa: BLE001
            logger.error(f"❌ IndStocks service get_positions error: {exc}")
            return {"status": "error", "message": str(exc)}
        finally:
            await broker.close()

    async def get_margins(self, access_token: Optional[str] = None) -> Dict[str, Any]:
        """
        Fetch available funds (from IndStocks `/funds`, not `/margin`).

        The naming mirrors `zerodha_service.get_margins()` for interface
        parity even though the underlying endpoints are different — Kite's
        `margins()` returns available funds, IndStocks' `/margin` is a
        pre-trade calculator so we hit `/funds` instead. See the adapter
        docstring for the full rationale.
        """
        broker = self._make_broker(access_token)
        try:
            funds = await broker.get_margins()  # internally calls /funds
            return {"status": "success", "data": funds}
        except Exception as exc:  # noqa: BLE001
            logger.error(f"❌ IndStocks service get_margins error: {exc}")
            return {"status": "error", "message": str(exc)}
        finally:
            await broker.close()


# Global instance — mirrors the `zerodha_service` module pattern so API
# endpoints can `from app.services.indstocks_service import indstocks_service`.
indstocks_service = IndStocksService()
