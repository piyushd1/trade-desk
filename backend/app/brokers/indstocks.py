"""
IndStocks (IndMoney) Broker Implementation

Static-bearer-token REST integration against https://api.indstocks.com.
No official Python SDK exists — this adapter uses httpx directly.

Key differences from the Zerodha (kiteconnect) implementation:

- **Auth**: a single static access token pasted from web.indstocks.com. No OAuth
  redirect flow, no API key/secret, no request signing. The Authorization header
  value is literally the token with NO `Bearer ` prefix.
- **Token lifetime**: 24 hours, no programmatic refresh. The user must paste a
  new token daily. `authenticate()` validates the current token against
  `GET /user/profile` and returns False if expired/invalid.
- **No sandbox**: every call is live money. Be conservative in tests.
- **Product enums**: IndStocks uses `MARGIN` (≈ Kite's `NRML`), `INTRADAY`
  (≈ Kite's `MIS`), and `CNC`. Translation happens in `place_order`.
- **Order types**: only `LIMIT` and `MARKET` on the normal order endpoint. No
  `SL`/`SL-M`/`BO`/`CO`. Stop-losses are GTT-only on the `/smart/order` endpoint
  (derivatives only). We reject unsupported order types with a clear error.
- **`algo_id="99999"`** is mandatory on every order — non-obvious, hardcoded.
- **Timestamps**: Unix epoch milliseconds in request/response bodies. Historical
  data returns `[[ts_ms, o, h, l, c, v], ...]` which we convert to a DataFrame
  with a datetime index.
- **Positions endpoint**: requires `segment` AND `product` as query params. We
  fan out 6 calls (equity × {cnc,intraday,margin} plus derivative × same) and
  merge into the `{net: [...], day: [...]}` shape the rest of TradeDesk expects.
- **`get_margins()` semantics**: returns available funds from `GET /funds`. The
  separate `GET /margin` endpoint is a hypothetical-trade margin calculator and
  is not used here.
- **WebSocket**: not yet implemented (parity with Zerodha adapter which stubs
  the same methods).
- **Instrument search**: not yet implemented — IndStocks has no search endpoint,
  only a CSV download via `GET /market/instruments?source=...`. Implementing
  this requires a caching layer; deferred to a later phase.

Full API audit lives in the Phase B2 research dump. See the plan file for the
comprehensive endpoint inventory, gotchas list, and rate-limit table.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

import httpx
import logging
import pandas as pd

from app.brokers.base import BaseBroker

logger = logging.getLogger(__name__)


class IndStocksBroker(BaseBroker):
    """
    IndStocks (IndMoney) broker implementation.

    Instantiate with `config={"access_token": "<paste from web.indstocks.com>"}`.
    Call `await authenticate()` to validate the token before issuing any other
    calls. Call `await close()` when done to release the httpx client.

    This class is designed for per-request instantiation from
    `app.services.indstocks_service` — mirrors the pattern used for Zerodha.
    Do not hold a long-lived instance across requests.
    """

    BASE_URL = "https://api.indstocks.com"
    TIMEOUT = 30.0  # seconds — IndStocks historical endpoints can be slow

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        # IndStocks stores the bearer token in the access_token slot. The
        # api_key/api_secret slots inherited from BaseBroker are unused.
        self.access_token = config.get("access_token", "")
        self._client: Optional[httpx.AsyncClient] = None

    # ---------- Internal helpers ----------

    def _get_client(self) -> httpx.AsyncClient:
        """Lazily construct the httpx AsyncClient with the right headers."""
        if self._client is None:
            if not self.access_token:
                raise RuntimeError("IndStocksBroker: no access_token in config")
            self._client = httpx.AsyncClient(
                base_url=self.BASE_URL,
                timeout=self.TIMEOUT,
                headers={
                    # CRITICAL: no "Bearer " prefix. IndStocks docs show the raw
                    # token as the Authorization header value. Auto-prefixing
                    # (e.g. via httpx.Auth helpers) will break authentication.
                    "Authorization": self.access_token,
                    "Content-Type": "application/json",
                },
            )
        return self._client

    def _translate_product(self, product: str) -> str:
        """Map Kite-style product names to IndStocks enum values."""
        product_upper = (product or "").upper()
        mapping = {
            "CNC": "CNC",
            "MIS": "INTRADAY",
            "NRML": "MARGIN",
            "INTRADAY": "INTRADAY",
            "MARGIN": "MARGIN",
        }
        return mapping.get(product_upper, "CNC")

    @staticmethod
    def _to_epoch_ms(date_value: Any) -> int:
        """Convert a date string or datetime to Unix epoch milliseconds."""
        if isinstance(date_value, datetime):
            return int(date_value.timestamp() * 1000)
        if isinstance(date_value, (int, float)):
            return int(date_value)
        # Accept ISO8601 or plain YYYY-MM-DD
        try:
            dt = datetime.fromisoformat(str(date_value))
        except ValueError:
            dt = datetime.strptime(str(date_value), "%Y-%m-%d")
        return int(dt.timestamp() * 1000)

    # ---------- Authentication ----------

    async def authenticate(self) -> bool:
        """
        Validate the stored access_token by calling GET /user/profile.

        Returns True if the token is accepted, False on any failure (token
        missing, expired, network error, or non-200 response). On failure,
        `self.is_authenticated` is set to False so callers can gate operations.
        """
        if not self.access_token:
            logger.error("❌ IndStocks: no access_token provided in config")
            self.is_authenticated = False
            return False

        try:
            client = self._get_client()
            response = await client.get("/user/profile")
            if response.status_code == 200:
                data = response.json()
                if data.get("status") == "success":
                    profile = data.get("data", {}) or {}
                    self.is_authenticated = True
                    logger.info(
                        "✅ IndStocks authentication successful "
                        f"(user_id={profile.get('user_id')})"
                    )
                    return True
                logger.error(
                    f"❌ IndStocks /user/profile returned status={data.get('status')}: "
                    f"{data.get('message', '(no message)')}"
                )
            else:
                logger.error(
                    f"❌ IndStocks auth failed: HTTP {response.status_code} — {response.text[:200]}"
                )
            self.is_authenticated = False
            return False
        except Exception as exc:  # noqa: BLE001
            logger.error(f"❌ IndStocks authentication error: {exc}")
            self.is_authenticated = False
            return False

    async def get_profile(self) -> Dict[str, Any]:
        """
        Fetch the user profile (GET /user/profile).

        Useful on its own as a "token still valid?" probe, and as a way to
        retrieve the user_id / email / is_nse_onboarded fields we want to
        log alongside `broker_sessions` rows when a new token is stored.

        Returns an empty dict on failure (with the usual error log).
        """
        try:
            client = self._get_client()
            response = await client.get("/user/profile")
            response.raise_for_status()
            data = response.json()
            if data.get("status") == "success":
                return data.get("data", {}) or {}
            logger.error(
                f"❌ IndStocks profile error: {data.get('message', '(no message)')}"
            )
            return {}
        except Exception as exc:  # noqa: BLE001
            logger.error(f"❌ IndStocks profile fetch failed: {exc}")
            return {}

    # ---------- Portfolio data ----------

    async def get_holdings(self) -> List[Dict[str, Any]]:
        """Fetch long-term holdings (GET /portfolio/holdings)."""
        try:
            client = self._get_client()
            response = await client.get("/portfolio/holdings")
            response.raise_for_status()
            data = response.json()
            if data.get("status") == "success":
                return data.get("data", []) or []
            logger.error(
                f"❌ IndStocks holdings error: {data.get('message', '(no message)')}"
            )
            return []
        except Exception as exc:  # noqa: BLE001
            logger.error(f"❌ IndStocks holdings fetch failed: {exc}")
            return []

    async def get_positions(self) -> Dict[str, List[Dict[str, Any]]]:
        """
        Fetch positions and merge into the {net: [...], day: [...]} shape.

        IndStocks requires both `segment` and `product` as query parameters
        and returns a different slice per combination. We fan out across all
        six combinations (equity × {cnc, intraday, margin}) + (derivative ×
        same) and union the results. Each inner call is isolated — if one
        combination errors (e.g. user has no F&O enabled), we log a warning
        and continue. Only a complete outer failure returns empty.
        """
        try:
            client = self._get_client()
            all_net: List[Dict[str, Any]] = []
            all_day: List[Dict[str, Any]] = []
            for segment in ("equity", "derivative"):
                for product in ("cnc", "intraday", "margin"):
                    try:
                        response = await client.get(
                            "/portfolio/positions",
                            params={"segment": segment, "product": product},
                        )
                        if response.status_code != 200:
                            # Some combinations will 400 for users without F&O
                            # access — that's fine, just skip silently.
                            continue
                        data = response.json()
                        if data.get("status") != "success":
                            continue
                        payload = data.get("data", {}) or {}
                        all_net.extend(payload.get("net_positions", []) or [])
                        all_day.extend(payload.get("day_positions", []) or [])
                    except Exception as inner:  # noqa: BLE001
                        logger.warning(
                            f"⚠️ IndStocks positions partial fetch failed "
                            f"({segment}/{product}): {inner}"
                        )
            return {"net": all_net, "day": all_day}
        except Exception as exc:  # noqa: BLE001
            logger.error(f"❌ IndStocks positions fetch failed: {exc}")
            return {"net": [], "day": []}

    async def get_margins(self) -> Dict[str, Any]:
        """
        Fetch available funds (GET /funds).

        NOTE: IndStocks' `/margin` endpoint is a *hypothetical pre-trade margin
        calculator*, not an account balance query. `get_margins()` semantics
        for TradeDesk are "how much cash does the user have", so we hit
        `/funds` instead.
        """
        try:
            client = self._get_client()
            response = await client.get("/funds")
            response.raise_for_status()
            data = response.json()
            if data.get("status") == "success":
                return data.get("data", {}) or {}
            logger.error(
                f"❌ IndStocks funds error: {data.get('message', '(no message)')}"
            )
            return {}
        except Exception as exc:  # noqa: BLE001
            logger.error(f"❌ IndStocks funds fetch failed: {exc}")
            return {}

    # ---------- Orders ----------

    async def place_order(self, order: Dict[str, Any]) -> Dict[str, Any]:
        """
        Place an order (POST /order).

        Only LIMIT and MARKET order types are supported by IndStocks' normal
        order endpoint. Stop-losses (SL / SL-M / BO / CO) are rejected at the
        adapter level with a clear error — they'd require the separate
        `/smart/order` GTT endpoint (derivatives only) which isn't wired yet.
        """
        try:
            order_type = str(order.get("order_type", "MARKET")).upper()
            if order_type not in ("LIMIT", "MARKET"):
                return {
                    "status": "error",
                    "message": (
                        f"IndStocks does not support order_type={order_type} "
                        f"on the normal order endpoint. Only LIMIT and MARKET "
                        f"are available (SL / SL-M / BO / CO are GTT-only)."
                    ),
                    "broker": "indstocks",
                }

            product = self._translate_product(order.get("product", "CNC"))
            # IndStocks `segment` is EQUITY for CNC/INTRADAY, DERIVATIVE for MARGIN.
            # If the caller passes an explicit segment, trust that.
            segment = (order.get("segment") or ("DERIVATIVE" if product == "MARGIN" else "EQUITY")).upper()

            payload: Dict[str, Any] = {
                "txn_type": str(order["transaction_type"]).upper(),  # BUY / SELL
                "exchange": str(order["exchange"]).upper(),
                "segment": segment,
                "product": product,
                "order_type": order_type,
                "validity": str(order.get("validity", "DAY")).upper(),
                "security_id": str(order.get("security_id") or order.get("tradingsymbol", "")),
                "qty": int(order["quantity"]),
                "is_amo": bool(order.get("is_amo", False)),
                # Mandatory — IndStocks rejects orders without this field.
                "algo_id": "99999",
            }
            if order_type == "LIMIT":
                if "price" not in order:
                    return {
                        "status": "error",
                        "message": "LIMIT order requires a price",
                        "broker": "indstocks",
                    }
                payload["limit_price"] = float(order["price"])

            client = self._get_client()
            response = await client.post("/order", json=payload)
            data = response.json()

            if data.get("status") == "success":
                order_id = (data.get("data") or {}).get("order_id", "")
                logger.info(f"✅ IndStocks order placed: {order_id}")
                return {
                    "status": "success",
                    "order_id": order_id,
                    "broker": "indstocks",
                }
            err_msg = data.get("message", "unknown error")
            logger.error(f"❌ IndStocks order failed: {err_msg}")
            return {
                "status": "error",
                "message": err_msg,
                "broker": "indstocks",
            }
        except Exception as exc:  # noqa: BLE001
            logger.error(f"❌ IndStocks order placement exception: {exc}")
            return {
                "status": "error",
                "message": str(exc),
                "broker": "indstocks",
            }

    async def cancel_order(self, order_id: str, variety: str = "regular") -> Dict[str, Any]:
        """
        Cancel an order (POST /order/cancel).

        IndStocks requires `segment` alongside `order_id`. Callers can encode
        the segment inline as "SEGMENT:order_id" (e.g. "DERIVATIVE:INDM202509..."),
        otherwise we default to EQUITY.
        """
        try:
            segment = "EQUITY"
            real_id = order_id
            if ":" in order_id:
                segment, real_id = order_id.split(":", 1)

            client = self._get_client()
            response = await client.post(
                "/order/cancel",
                json={"segment": segment, "order_id": real_id},
            )
            data = response.json()
            if data.get("status") == "success":
                return {"status": "success", "order_id": order_id}
            return {
                "status": "error",
                "message": data.get("message", "unknown error"),
            }
        except Exception as exc:  # noqa: BLE001
            logger.error(f"❌ IndStocks cancel order failed: {exc}")
            return {"status": "error", "message": str(exc)}

    async def modify_order(
        self,
        order_id: str,
        modifications: Dict[str, Any],
        variety: str = "regular",
    ) -> Dict[str, Any]:
        """
        Modify an order (POST /order/modify).

        IndStocks only accepts qty and limit_price modifications — anything
        else in the `modifications` dict is silently ignored.
        """
        try:
            payload: Dict[str, Any] = {
                "segment": str(modifications.get("segment", "EQUITY")).upper(),
                "order_id": order_id,
            }
            if "quantity" in modifications:
                payload["qty"] = int(modifications["quantity"])
            if "price" in modifications:
                payload["limit_price"] = float(modifications["price"])

            client = self._get_client()
            response = await client.post("/order/modify", json=payload)
            data = response.json()
            if data.get("status") == "success":
                return {"status": "success", "order_id": order_id}
            return {
                "status": "error",
                "message": data.get("message", "unknown error"),
            }
        except Exception as exc:  # noqa: BLE001
            logger.error(f"❌ IndStocks modify order failed: {exc}")
            return {"status": "error", "message": str(exc)}

    async def get_orders(self) -> List[Dict[str, Any]]:
        """Get all orders for the day (GET /order-book)."""
        try:
            client = self._get_client()
            response = await client.get("/order-book")
            response.raise_for_status()
            data = response.json()
            if data.get("status") == "success":
                return data.get("data", []) or []
            logger.error(
                f"❌ IndStocks orders fetch error: {data.get('message', '(no message)')}"
            )
            return []
        except Exception as exc:  # noqa: BLE001
            logger.error(f"❌ IndStocks orders fetch failed: {exc}")
            return []

    async def get_order_history(self, order_id: str) -> List[Dict[str, Any]]:
        """Get trades (fills) for a specific order (GET /trades/{order_id})."""
        try:
            client = self._get_client()
            response = await client.get(f"/trades/{order_id}")
            response.raise_for_status()
            data = response.json()
            if data.get("status") == "success":
                return data.get("data", []) or []
            return []
        except Exception as exc:  # noqa: BLE001
            logger.error(f"❌ IndStocks trades fetch failed: {exc}")
            return []

    # ---------- Market data ----------

    async def get_historical_data(
        self,
        instrument_token: str,
        from_date: str,
        to_date: str,
        interval: str,
    ) -> pd.DataFrame:
        """
        Fetch historical OHLCV (GET /market/historical/{interval}).

        The response is `[[ts_ms, o, h, l, c, v], ...]`. We return a DataFrame
        with columns [date, open, high, low, close, volume] to match the
        Zerodha adapter's return shape — note `date` is a pd.Timestamp.
        """
        try:
            # Translate Kite-style intervals to IndStocks intervals
            interval_map = {
                "minute": "1minute",
                "3minute": "5minute",  # IndStocks has no 3m; step up to 5m
                "5minute": "5minute",
                "10minute": "10minute",
                "15minute": "15minute",
                "30minute": "30minute",
                "60minute": "60minute",
                "hour": "60minute",
                "day": "1day",
                "week": "1week",
                "month": "1month",
            }
            ind_interval = interval_map.get(interval, interval)

            client = self._get_client()
            response = await client.get(
                f"/market/historical/{ind_interval}",
                params={
                    "scrip-codes": instrument_token,
                    "start_time": self._to_epoch_ms(from_date),
                    "end_time": self._to_epoch_ms(to_date),
                },
            )
            response.raise_for_status()
            data = response.json()
            if data.get("status") != "success":
                logger.error(
                    f"❌ IndStocks historical error: {data.get('message', '(no message)')}"
                )
                return pd.DataFrame()

            raw = data.get("data", []) or []
            if not raw:
                return pd.DataFrame()

            df = pd.DataFrame(
                raw, columns=["date", "open", "high", "low", "close", "volume"]
            )
            df["date"] = pd.to_datetime(df["date"], unit="ms")
            return df
        except Exception as exc:  # noqa: BLE001
            logger.error(f"❌ IndStocks historical data fetch failed: {exc}")
            return pd.DataFrame()

    async def get_quote(self, instruments: List[str]) -> Dict[str, Dict[str, Any]]:
        """Get full market quotes for up to 1000 instruments."""
        try:
            client = self._get_client()
            response = await client.get(
                "/market/quotes/full",
                params={"scrip-codes": ",".join(instruments)},
            )
            response.raise_for_status()
            data = response.json()
            if data.get("status") == "success":
                return data.get("data", {}) or {}
            return {}
        except Exception as exc:  # noqa: BLE001
            logger.error(f"❌ IndStocks quote fetch failed: {exc}")
            return {}

    async def get_ltp(self, instruments: List[str]) -> Dict[str, float]:
        """Get last traded price for up to 1000 instruments."""
        try:
            client = self._get_client()
            response = await client.get(
                "/market/quotes/ltp",
                params={"scrip-codes": ",".join(instruments)},
            )
            response.raise_for_status()
            data = response.json()
            if data.get("status") == "success":
                raw = data.get("data", {}) or {}
                return {k: float(v.get("live_price", 0.0)) for k, v in raw.items()}
            return {}
        except Exception as exc:  # noqa: BLE001
            logger.error(f"❌ IndStocks LTP fetch failed: {exc}")
            return {}

    # ---------- WebSocket (not implemented — parity with Zerodha stub) ----------

    def subscribe_live_data(self, instruments: List[str], callback: callable) -> None:
        """WebSocket subscription — not implemented yet (parity with Zerodha stub)."""
        logger.warning("⚠️ IndStocks WebSocket subscription not implemented yet")

    def unsubscribe_live_data(self, instruments: List[str]) -> None:
        """WebSocket unsubscribe — not implemented yet."""

    # ---------- Instruments ----------

    async def search_instruments(
        self,
        query: str,
        exchange: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Search instruments — not implemented in the initial cut.

        IndStocks has no search endpoint. The only way to resolve a symbol to
        a security_id is to download the instruments CSV from
        `GET /market/instruments?source=equity|fno|index` and filter it
        client-side. Implementing that requires a caching layer (the CSV is
        ~100k rows and should be refreshed daily) which is deferred until we
        actually need symbol search from the UI.
        """
        logger.warning(
            "⚠️ IndStocks instrument search not yet implemented "
            "(requires CSV download + cache)"
        )
        return []

    # ---------- Lifecycle ----------

    async def close(self) -> None:
        """
        Close the underlying httpx AsyncClient.

        Must be called after every use of the adapter when it's instantiated
        per-request in `app.services.indstocks_service`. Idempotent.
        """
        if self._client is not None:
            await self._client.aclose()
            self._client = None
