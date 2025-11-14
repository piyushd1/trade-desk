"""
Zerodha Streaming Service

Provides utilities to stream real-time market data from Zerodha's Kite Ticker
WebSocket, measure latency, and expose metrics for monitoring data quality.

Design Goals
------------
- Manage multiple user-specific streaming sessions (one per user identifier)
- Allow subscription to arbitrary instrument tokens
- Track latency between exchange timestamp and receipt time
- Maintain rolling buffers of ticks for inspection
- Provide status/metric snapshots for API endpoints
"""

from __future__ import annotations

import logging
import threading
import time
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, Iterable, List, Optional

from kiteconnect import KiteTicker

from app.config import settings

logger = logging.getLogger(__name__)


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _serialize_tick(raw_tick: dict, received_at: datetime) -> dict:
    """Convert Kite tick dictionary into JSON-serializable format."""
    serialized = {}
    for key, value in raw_tick.items():
        if isinstance(value, datetime):
            serialized[key] = value.astimezone(timezone.utc).isoformat()
        else:
            serialized[key] = value

    serialized["received_at"] = received_at.isoformat()
    return serialized


@dataclass
class ZerodhaStreamState:
    """Represents a single user's streaming session."""

    user_identifier: str
    instrument_tokens: List[int]
    mode: str
    ticker: KiteTicker
    started_at: datetime = field(default_factory=_utcnow)
    connected_at: Optional[datetime] = None
    last_tick_at: Optional[datetime] = None
    last_error_at: Optional[datetime] = None
    last_error_message: Optional[str] = None
    total_tick_messages: int = 0
    total_ticks: int = 0
    last_ticks: deque = field(default_factory=lambda: deque(maxlen=200))
    instrument_last_tick: Dict[int, dict] = field(default_factory=dict)
    latencies_ms: deque = field(default_factory=lambda: deque(maxlen=500))
    is_connecting: bool = False
    is_connected: bool = False
    should_stop: bool = False
    lock: threading.Lock = field(default_factory=threading.Lock)
    connected_event: threading.Event = field(default_factory=threading.Event)
    thread: Optional[threading.Thread] = None

    def handle_connect(self, ws):
        with self.lock:
            self.is_connected = True
            self.is_connecting = False
            self.connected_at = _utcnow()
            logger.info(
                "✅ Zerodha stream connected | user=%s | tokens=%s",
                self.user_identifier,
                self.instrument_tokens,
            )

        try:
            ws.subscribe(self.instrument_tokens)
            mode_map = {
                "full": ws.MODE_FULL,
                "quote": ws.MODE_QUOTE,
                "ltp": ws.MODE_LTP,
            }
            ws.set_mode(mode_map.get(self.mode, ws.MODE_FULL), self.instrument_tokens)
        except Exception as exc:
            logger.error(
                "⚠️ Failed to subscribe to instruments | user=%s | error=%s",
                self.user_identifier,
                exc,
            )
            self.handle_error(ws, exc)
        finally:
            self.connected_event.set()

    def handle_close(self, ws, code: int, reason: str):
        with self.lock:
            self.is_connected = False
            self.is_connecting = False
            self.last_error_at = _utcnow()
            self.last_error_message = f"Closed: code={code}, reason={reason}"
            logger.warning(
                "ℹ️ Zerodha stream closed | user=%s | code=%s | reason=%s",
                self.user_identifier,
                code,
                reason,
            )
            self.connected_event.set()

    def handle_reconnect(self, ws, attempt_count: int):
        with self.lock:
            self.is_connecting = True
            logger.info(
                "🔄 Zerodha stream reconnect attempt #%s | user=%s",
                attempt_count,
                self.user_identifier,
            )

    def handle_noreconnect(self, ws):
        with self.lock:
            self.is_connected = False
            self.is_connecting = False
            self.last_error_at = _utcnow()
            self.last_error_message = "Maximum reconnection attempts exhausted"
            logger.error(
                "❌ Zerodha stream could not reconnect | user=%s",
                self.user_identifier,
            )

    def handle_error(self, ws, error: Exception):
        with self.lock:
            self.last_error_at = _utcnow()
            self.last_error_message = str(error)
            logger.error(
                "⚠️ Zerodha stream error | user=%s | error=%s",
                self.user_identifier,
                error,
                exc_info=True,
            )
            self.connected_event.set()

    def handle_ticks(self, ws, ticks: List[dict]):
        now = _utcnow()

        with self.lock:
            self.last_tick_at = now
            self.total_tick_messages += 1

            for tick in ticks:
                self.total_ticks += 1
                instrument_token = tick.get("instrument_token")
                serialized = _serialize_tick(tick, now)
                self.last_ticks.appendleft(serialized)

                if instrument_token is not None:
                    self.instrument_last_tick[instrument_token] = serialized

                last_trade_time = tick.get("last_trade_time")
                if isinstance(last_trade_time, datetime):
                    latency_ms = (now - last_trade_time).total_seconds() * 1000
                    if latency_ms >= 0:
                        self.latencies_ms.append(latency_ms)

    def get_metrics(self) -> dict:
        with self.lock:
            now = _utcnow()
            uptime_seconds = (now - self.started_at).total_seconds()
            tick_rate = (
                self.total_ticks / uptime_seconds if uptime_seconds > 0 else 0.0
            )
            avg_latency = (
                sum(self.latencies_ms) / len(self.latencies_ms)
                if self.latencies_ms
                else None
            )
            last_latency = self.latencies_ms[-1] if self.latencies_ms else None

            return {
                "user_identifier": self.user_identifier,
                "instrument_tokens": self.instrument_tokens,
                "mode": self.mode,
                "started_at": self.started_at.isoformat(),
                "connected_at": self.connected_at.isoformat()
                if self.connected_at
                else None,
                "last_tick_at": self.last_tick_at.isoformat()
                if self.last_tick_at
                else None,
                "is_connected": self.is_connected,
                "is_connecting": self.is_connecting,
                "uptime_seconds": uptime_seconds,
                "total_tick_messages": self.total_tick_messages,
                "total_ticks": self.total_ticks,
                "tick_rate_per_second": tick_rate,
                "average_latency_ms": avg_latency,
                "last_latency_ms": last_latency,
                "latency_observations": len(self.latencies_ms),
                "last_error_at": self.last_error_at.isoformat()
                if self.last_error_at
                else None,
                "last_error_message": self.last_error_message,
            }

    def get_recent_ticks(self, limit: int = 50) -> List[dict]:
        with self.lock:
            limited = list(list(self.last_ticks)[:limit])
        return limited


class ZerodhaStreamingManager:
    """Singleton manager responsible for all Zerodha streaming sessions."""

    def __init__(self):
        self._streams: Dict[str, ZerodhaStreamState] = {}
        self._lock = threading.Lock()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def start_stream(
        self,
        user_identifier: str,
        access_token: str,
        instrument_tokens: Iterable[int],
        mode: str = "full",
    ) -> dict:
        """
        Start streaming ticks for the specified user.

        Returns status dictionary with connection metadata.
        """
        if not settings.ZERODHA_API_KEY:
            raise ValueError("Zerodha API key is not configured")

        tokens = list({int(token) for token in instrument_tokens if int(token) > 0})
        if not tokens:
            raise ValueError("At least one instrument token is required")

        with self._lock:
            # Stop any existing stream for this user
            if user_identifier in self._streams:
                self.stop_stream(user_identifier)

            ticker = KiteTicker(settings.ZERODHA_API_KEY, access_token)
            # Disable auto reconnection? Not necessary but we can configure.
            ticker.enable_reconnect(reconnect=True, reconnect_interval=5, reconnect_tries=50)

            state = ZerodhaStreamState(
                user_identifier=user_identifier,
                instrument_tokens=tokens,
                mode=mode.lower(),
                ticker=ticker,
            )

            self._bind_callbacks(state)
            self._streams[user_identifier] = state

        # Connect in threaded mode and wait briefly for connection confirmation.
        state.is_connecting = True
        ticker.connect(threaded=True)

        # Wait for connection confirmation (success or failure)
        connected = state.connected_event.wait(timeout=10)
        status = state.get_metrics()
        status["connection_confirmed"] = connected

        return status

    def stop_stream(self, user_identifier: str) -> bool:
        """Stop streaming for the given user. Returns True if a stream existed."""
        with self._lock:
            state = self._streams.pop(user_identifier, None)

        if not state:
            return False

        state.should_stop = True
        try:
            state.ticker.close()
        except Exception as exc:
            logger.warning(
                "⚠️ Error while closing Zerodha stream | user=%s | error=%s",
                user_identifier,
                exc,
            )
        return True

    def update_subscription(
        self, user_identifier: str, instrument_tokens: Iterable[int], mode: Optional[str] = None
    ) -> dict:
        """Update subscription for an active stream."""
        with self._lock:
            state = self._streams.get(user_identifier)

        if not state:
            raise ValueError(f"No active stream found for user {user_identifier}")

        tokens = list({int(token) for token in instrument_tokens if int(token) > 0})
        if not tokens:
            raise ValueError("At least one instrument token is required")

        with state.lock:
            state.instrument_tokens = tokens
            if mode:
                state.mode = mode.lower()

        try:
            state.ticker.subscribe(tokens)
            if mode:
                mode_value = {
                    "full": state.ticker.MODE_FULL,
                    "quote": state.ticker.MODE_QUOTE,
                    "ltp": state.ticker.MODE_LTP,
                }.get(mode.lower(), state.ticker.MODE_FULL)
                state.ticker.set_mode(mode_value, tokens)
        except Exception as exc:
            logger.error(
                "⚠️ Failed to update Zerodha subscription | user=%s | error=%s",
                user_identifier,
                exc,
                exc_info=True,
            )
            raise

        return state.get_metrics()

    def get_status(self, user_identifier: Optional[str] = None) -> List[dict]:
        """Return status for one stream or all streams."""
        with self._lock:
            if user_identifier:
                state = self._streams.get(user_identifier)
                if not state:
                    return []
                return [state.get_metrics()]

            return [state.get_metrics() for state in self._streams.values()]

    def get_ticks(self, user_identifier: str, limit: int = 50) -> List[dict]:
        with self._lock:
            state = self._streams.get(user_identifier)

        if not state:
            raise ValueError(f"No active stream found for user {user_identifier}")

        return state.get_recent_ticks(limit)

    def stop_all(self):
        with self._lock:
            identifiers = list(self._streams.keys())

        for user_identifier in identifiers:
            self.stop_stream(user_identifier)

    # ------------------------------------------------------------------
    # Internal utilities
    # ------------------------------------------------------------------
    def _bind_callbacks(self, state: ZerodhaStreamState):
        ticker = state.ticker

        ticker.on_connect = state.handle_connect
        ticker.on_close = state.handle_close
        ticker.on_reconnect = state.handle_reconnect
        ticker.on_noreconnect = state.handle_noreconnect
        ticker.on_error = state.handle_error
        ticker.on_ticks = state.handle_ticks


# Singleton instance
zerodha_streaming_manager = ZerodhaStreamingManager()


