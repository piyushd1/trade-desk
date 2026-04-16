"""
Portfolio Snapshot Scheduler (Phase B4)

An in-process APScheduler that wakes up every 15 minutes during market
hours, iterates over every active `broker_sessions` row, and writes one
`portfolio_snapshots` row per broker per user. Aggregation across brokers
for the /portfolio/history + /portfolio/metrics endpoints happens at query
time in a later slice.

Pinned invariants:
- **One scheduler instance per backend process.** Enforced by:
    1. `uvicorn --workers 1` hardcoded in Dockerfile.backend CMD
    2. An `fcntl.flock` advisory lock on /app/data/scheduler.lock (belt
       and suspenders — catches accidental worker-count bumps)
- **Partial writes are fine.** If one broker fails mid-job, the other
  broker's snapshot is still written. Per-session errors are audit-logged
  but do not abort the tick.
- **Duplicate buckets are ignored.** The unique constraint on
  `(user_id, broker, captured_at_bucket)` catches any race; we swallow
  IntegrityError and continue.
- **Zerodha 6-AM-IST expiry is expected.** The first few ticks after
  06:00 IST will find an expired Zerodha session; we log an info event
  (`snapshot_skipped_expired_session`) and the user re-authenticates
  when they notice. Not retried — user action, not a transient error.
- **IndStocks tokens expire 24h after generation.** Same handling as
  Zerodha — log and skip.
- **Backfill on startup**: if the current market-open bucket is missing
  for any active session, capture it immediately rather than waiting up
  to 15 minutes for the next cron tick.

Main entry points:
- `snapshot_scheduler.start()` — called from FastAPI `lifespan`
- `snapshot_scheduler.shutdown()` — called from FastAPI `lifespan`
"""

from __future__ import annotations

import asyncio
import fcntl
import json
import logging
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any, Dict, List, Optional, Tuple

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from starlette.concurrency import run_in_threadpool
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import AsyncSessionLocal
from app.models.broker_session import BrokerSession
from app.models.portfolio_snapshot import PortfolioSnapshot
from app.services.audit_service import audit_service
from app.services.indstocks_service import indstocks_service
from app.services.zerodha_service import zerodha_service
from app.utils.crypto import decrypt
from app.utils.market_calendar import (
    IST,
    floor_to_15min_bucket,
    is_market_open,
)

logger = logging.getLogger(__name__)


LOCK_FILE_PATH = "/app/data/scheduler.lock"


# -----------------------------------------------------------------------------
# Per-broker totals computation
# -----------------------------------------------------------------------------
#
# Each broker's holdings/positions/margins response has a different shape.
# These helpers take the raw broker response and compute:
#   total_value       — equity exposure + available cash
#   total_pnl         — realized + unrealized
#   realized_pnl      — from closed day trades (0 until we track this)
#   unrealized_pnl    — from open holdings mark-to-market
#
# The initial implementation treats `realized_pnl = 0` because accurate
# realized-P&L attribution requires day-by-day tracking which isn't wired
# up yet. Unrealized P&L is computed from the `pnl` / `pnl_absolute` fields
# that each broker already returns.


def _safe_decimal(value: Any) -> Decimal:
    """Coerce a broker value to Decimal. Returns Decimal(0) on None/error."""
    if value is None:
        return Decimal("0")
    try:
        return Decimal(str(value))
    except (ValueError, TypeError, ArithmeticError):
        return Decimal("0")


def _compute_zerodha_totals(
    holdings: List[Dict[str, Any]],
    positions: Dict[str, List[Dict[str, Any]]],
    margins: Dict[str, Any],
) -> Tuple[Decimal, Decimal, Decimal, Decimal]:
    """
    Compute (total_value, total_pnl, realized_pnl, unrealized_pnl)
    from a Zerodha Kite Connect response.

    Shapes (from kiteconnect):
      holdings: [{tradingsymbol, quantity, average_price, last_price,
                  pnl, day_change, ...}]
      positions: {net: [...], day: [...]}
      margins: {equity: {available: {cash, ...}, utilised: {...}, net, ...},
                commodity: {...}}
    """
    # Equity value = sum of holdings (quantity * last_price)
    equity_value = Decimal("0")
    unrealized = Decimal("0")
    for h in holdings or []:
        qty = _safe_decimal(h.get("quantity"))
        last_price = _safe_decimal(h.get("last_price"))
        equity_value += qty * last_price
        unrealized += _safe_decimal(h.get("pnl"))

    # Include net positions in equity value and unrealized P&L — these are
    # carry-forward F&O / MIS positions that haven't been squared off yet.
    for p in (positions or {}).get("net", []) or []:
        qty = _safe_decimal(p.get("quantity"))
        last_price = _safe_decimal(p.get("last_price"))
        equity_value += qty * last_price
        unrealized += _safe_decimal(p.get("pnl") or p.get("m2m"))

    # Available cash from margins.equity.available.cash (per Kite docs)
    cash = Decimal("0")
    equity_margin = (margins or {}).get("equity", {}) or {}
    available = equity_margin.get("available", {}) or {}
    cash = _safe_decimal(available.get("cash"))
    # Some responses also include `net` — prefer the broader field when cash is 0
    if cash == 0:
        cash = _safe_decimal(equity_margin.get("net"))

    realized = Decimal("0")  # TODO: wire when day-trade P&L tracking exists
    total_value = equity_value + cash
    total_pnl = realized + unrealized
    return total_value, total_pnl, realized, unrealized


def _compute_indstocks_totals(
    holdings: List[Dict[str, Any]],
    positions: Dict[str, List[Dict[str, Any]]],
    funds: Dict[str, Any],
) -> Tuple[Decimal, Decimal, Decimal, Decimal]:
    """
    Compute (total_value, total_pnl, realized_pnl, unrealized_pnl)
    from an IndStocks response.

    Shapes (from backend/app/brokers/indstocks.py docstring + API audit):
      holdings: [{security_id, trading_symbol, quantity, average_price,
                  last_traded_price, market_value, pnl_absolute, pnl_percent}]
      positions: {net: [...], day: [...]} — net_quantity, average_price,
                  last_traded_price, market_value, pnl_absolute, multiplier
      funds: arbitrary dict — typically has `available_balance` or similar
    """
    equity_value = Decimal("0")
    unrealized = Decimal("0")
    for h in holdings or []:
        equity_value += _safe_decimal(h.get("market_value"))
        unrealized += _safe_decimal(h.get("pnl_absolute"))

    for p in (positions or {}).get("net", []) or []:
        equity_value += _safe_decimal(p.get("market_value"))
        unrealized += _safe_decimal(p.get("pnl_absolute"))

    # IndStocks /funds response shape is not tightly specified in the docs —
    # try a few plausible keys and default to 0 if none match.
    cash = Decimal("0")
    if isinstance(funds, dict):
        for key in ("available_balance", "availableBalance", "cash", "balance", "net"):
            if key in funds and funds[key] is not None:
                cash = _safe_decimal(funds[key])
                if cash != 0:
                    break

    realized = Decimal("0")
    total_value = equity_value + cash
    total_pnl = realized + unrealized
    return total_value, total_pnl, realized, unrealized


# -----------------------------------------------------------------------------
# Scheduler
# -----------------------------------------------------------------------------


class SnapshotScheduler:
    """
    Wraps an APScheduler `AsyncIOScheduler` with cron + startup backfill.

    Lifecycle:
      snapshot_scheduler.start()    # called from FastAPI lifespan startup
      snapshot_scheduler.shutdown() # called from FastAPI lifespan shutdown
    """

    def __init__(self) -> None:
        self.scheduler: Optional[AsyncIOScheduler] = None
        self._lock_fd: Optional[int] = None
        self._started: bool = False

    # ------------ Lifecycle ------------

    async def start(self) -> None:
        """
        Start the scheduler, acquire the file lock, add the cron job,
        and run a one-time backfill for the current bucket if market is
        open at startup.

        Idempotent — calling start() when already started is a no-op.
        """
        if self._started:
            return

        # Try to acquire the advisory lock. If another process has it
        # (shouldn't happen under --workers 1 but defensive), log and
        # bail without crashing the backend.
        if not self._acquire_lock():
            logger.warning(
                "⚠️  snapshot scheduler could not acquire lock at "
                f"{LOCK_FILE_PATH} — another backend worker must be "
                "running. Scheduler NOT started in this process."
            )
            return

        self.scheduler = AsyncIOScheduler(timezone=IST)
        # Cron: every 15 minutes, Monday through Friday. IST-aware because
        # the scheduler is constructed with tz=IST above — CronTrigger
        # inherits the scheduler's timezone by default.
        self.scheduler.add_job(
            self._tick,
            trigger=CronTrigger(day_of_week="mon-fri", minute="0,15,30,45"),
            id="portfolio_snapshot_tick",
            name="Portfolio Snapshot (15m)",
            max_instances=1,  # never run two copies in parallel
            coalesce=True,  # if multiple ticks missed, run once
            misfire_grace_time=300,  # 5 min grace
            replace_existing=True,
        )
        self.scheduler.start()
        self._started = True
        logger.info(
            "✅ Portfolio snapshot scheduler started "
            "(cron: */15 min Mon-Fri, IST, max_instances=1)"
        )

        # Backfill: if market is currently open AND the most-recent
        # 15-min bucket is missing for any active session, capture it
        # now rather than waiting up to 15 min for the next tick.
        try:
            await self._backfill_if_missing()
        except Exception as exc:  # noqa: BLE001
            logger.error(f"❌ snapshot backfill at startup failed: {exc}")

    async def shutdown(self) -> None:
        """Stop the scheduler and release the file lock. Idempotent."""
        if self.scheduler is not None:
            try:
                self.scheduler.shutdown(wait=True)
            except Exception as exc:  # noqa: BLE001
                logger.warning(f"⚠️  scheduler.shutdown() raised: {exc}")
            self.scheduler = None
        self._release_lock()
        self._started = False
        logger.info("🛑 Portfolio snapshot scheduler shut down")

    # ------------ File lock ------------

    def _acquire_lock(self) -> bool:
        """
        Acquire an exclusive non-blocking advisory lock on LOCK_FILE_PATH.

        Returns True on success, False if another process holds the lock.
        On any unexpected error (e.g. lock directory missing) also returns
        True and logs a warning — we don't want to hard-fail startup on
        cosmetic lock issues.
        """
        try:
            # Open in append mode so the file is created if missing but
            # existing content (none — we don't write to it) is preserved.
            self._lock_fd = open(LOCK_FILE_PATH, "a+")  # noqa: SIM115
            fcntl.flock(self._lock_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            return True
        except BlockingIOError:
            # Another process has the lock
            if self._lock_fd is not None:
                try:
                    self._lock_fd.close()
                except Exception:  # noqa: BLE001
                    pass
                self._lock_fd = None
            return False
        except Exception as exc:  # noqa: BLE001
            logger.warning(
                f"⚠️  could not acquire scheduler lock at {LOCK_FILE_PATH}: "
                f"{exc}. Continuing without lock."
            )
            return True

    def _release_lock(self) -> None:
        """Release the advisory lock. Safe to call when lock was never held."""
        if self._lock_fd is not None:
            try:
                fcntl.flock(self._lock_fd, fcntl.LOCK_UN)
                self._lock_fd.close()
            except Exception:  # noqa: BLE001
                pass
            self._lock_fd = None

    # ------------ Tick logic ------------

    async def _tick(self) -> None:
        """
        Cron-triggered entry point. Runs every 15 minutes Mon-Fri.

        Guards against out-of-hours invocations (e.g. scheduler still
        running over a holiday) by consulting `is_market_open()` before
        doing any work.
        """
        if not is_market_open():
            logger.debug("snapshot tick skipped: market is closed")
            return

        try:
            await self._capture_all_sessions()
        except Exception as exc:  # noqa: BLE001
            logger.error(f"❌ snapshot tick unhandled error: {exc}")

    async def _capture_all_sessions(self) -> None:
        """
        Query all active broker_sessions and capture a snapshot for each.

        Uses its own AsyncSessionLocal since this runs outside any request
        context. Iterates in a single session to batch audit-log writes
        at the end of the tick.
        """
        now_utc = datetime.now(timezone.utc)
        bucket = floor_to_15min_bucket(now_utc)

        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(BrokerSession).where(BrokerSession.status == "active")
            )
            sessions = result.scalars().all()

            if not sessions:
                logger.info("snapshot tick: no active broker sessions, nothing to capture")
                return

            captured = 0
            skipped_expired = 0
            errored = 0

            for session in sessions:
                # Skip sessions bound to no user (shouldn't happen after the
                # Phase A claim-fix, but defensive)
                if not session.user_id:
                    continue

                # Skip expired sessions with an info audit event — this is
                # the "Zerodha daily re-auth" + "IndStocks 24h expiry" path.
                if session.expires_at is not None:
                    expires_at_utc = session.expires_at
                    if expires_at_utc.tzinfo is None:
                        expires_at_utc = expires_at_utc.replace(tzinfo=timezone.utc)
                    if expires_at_utc <= now_utc:
                        await audit_service.log_event(
                            action="snapshot_skipped_expired_session",
                            entity_type="broker_session",
                            entity_id=str(session.id),
                            details={
                                "broker": session.broker,
                                "user_identifier": session.user_identifier,
                                "expires_at": expires_at_utc.isoformat(),
                            },
                            user_id=session.user_id,
                            db=db,
                        )
                        skipped_expired += 1
                        continue

                # Capture for this session. Each per-session call is isolated
                # — a failure in one does not abort the tick.
                try:
                    await self._capture_for_session(db, session, bucket, now_utc)
                    captured += 1
                except Exception as exc:  # noqa: BLE001
                    errored += 1
                    logger.error(
                        f"❌ snapshot error for session id={session.id} "
                        f"broker={session.broker}: {exc}"
                    )
                    await audit_service.log_event(
                        action="snapshot_broker_error",
                        entity_type="broker_session",
                        entity_id=str(session.id),
                        details={
                            "broker": session.broker,
                            "user_identifier": session.user_identifier,
                            "error": str(exc),
                        },
                        user_id=session.user_id,
                        db=db,
                    )

            await db.commit()
            logger.info(
                f"snapshot tick complete: "
                f"captured={captured} skipped_expired={skipped_expired} "
                f"errored={errored} bucket={bucket.isoformat()}"
            )

    async def _capture_for_session(
        self,
        db: AsyncSession,
        session: BrokerSession,
        bucket: datetime,
        now_utc: datetime,
    ) -> None:
        """
        Fetch + compute + insert a snapshot for a single broker session.

        Raises on any unrecoverable error so the caller's except block
        can log an audit event. Swallows IntegrityError on duplicate
        bucket (race condition from overlapping ticks).
        """
        access_token = decrypt(session.access_token_encrypted)

        holdings: List[Dict[str, Any]] = []
        positions: Dict[str, List[Dict[str, Any]]] = {"net": [], "day": []}
        margins_or_funds: Dict[str, Any] = {}

        if session.broker == "zerodha":
            # The Zerodha service uses a shared KiteConnect instance with
            # an explicit set_access_token call. Respect that pattern
            # even though it's mildly stateful.
            zerodha_service.set_access_token(access_token)

            # Parallelize synchronous Zerodha API calls using run_in_threadpool
            h_resp, p_resp, m_resp = await asyncio.gather(
                run_in_threadpool(zerodha_service.get_holdings),
                run_in_threadpool(zerodha_service.get_positions),
                run_in_threadpool(zerodha_service.get_margins),
            )

            if h_resp.get("status") == "success":
                holdings = h_resp.get("data") or []
            if p_resp.get("status") == "success":
                positions = p_resp.get("data") or {"net": [], "day": []}
            if m_resp.get("status") == "success":
                margins_or_funds = m_resp.get("data") or {}

            total_value, total_pnl, realized, unrealized = _compute_zerodha_totals(
                holdings, positions, margins_or_funds
            )

        elif session.broker == "indstocks":
            h_resp = await indstocks_service.get_holdings(access_token=access_token)
            p_resp = await indstocks_service.get_positions(access_token=access_token)
            m_resp = await indstocks_service.get_margins(access_token=access_token)
            if h_resp.get("status") == "success":
                holdings = h_resp.get("data") or []
            if p_resp.get("status") == "success":
                positions = p_resp.get("data") or {"net": [], "day": []}
            if m_resp.get("status") == "success":
                margins_or_funds = m_resp.get("data") or {}

            total_value, total_pnl, realized, unrealized = _compute_indstocks_totals(
                holdings, positions, margins_or_funds
            )

        else:
            logger.warning(
                f"snapshot skipped: unsupported broker '{session.broker}' "
                f"on session id={session.id}"
            )
            return

        # Persist a JSON blob of the raw holdings + positions + margins for
        # future re-analysis. Keep it compact — newline-separated JSON is
        # already valid and avoids the overhead of indented formatting.
        holdings_blob = json.dumps(
            {
                "holdings": holdings,
                "positions": positions,
                "margins_or_funds": margins_or_funds,
            },
            default=str,
        )

        snapshot = PortfolioSnapshot(
            user_id=session.user_id,
            broker=session.broker,
            captured_at_bucket=bucket,
            captured_at=now_utc.replace(tzinfo=None),
            total_value=total_value,
            total_pnl=total_pnl,
            realized_pnl=realized,
            unrealized_pnl=unrealized,
            holdings_json=holdings_blob,
        )
        db.add(snapshot)
        try:
            await db.flush()
        except IntegrityError:
            # Duplicate bucket — another tick already captured this slot.
            # Not an error, just log and move on.
            await db.rollback()
            logger.info(
                f"snapshot duplicate bucket skipped: "
                f"user_id={session.user_id} broker={session.broker} "
                f"bucket={bucket.isoformat()}"
            )
            return

        await audit_service.log_event(
            action="snapshot_captured",
            entity_type="portfolio_snapshot",
            entity_id=str(session.user_identifier),
            details={
                "broker": session.broker,
                "bucket": bucket.isoformat(),
                "total_value": str(total_value),
                "total_pnl": str(total_pnl),
                "holdings_count": len(holdings),
            },
            user_id=session.user_id,
            db=db,
        )

    # ------------ Backfill ------------

    async def _backfill_if_missing(self) -> None:
        """
        Run one immediate capture on startup if the current bucket isn't
        already present for any active session.

        This closes the "backend restarted mid-day and we lost the next
        scheduled tick" gap. Safe to call when market is closed — the
        inner `_capture_all_sessions` guards against that internally
        via `is_market_open()`.
        """
        if not is_market_open():
            return

        now_utc = datetime.now(timezone.utc)
        bucket = floor_to_15min_bucket(now_utc)

        async with AsyncSessionLocal() as db:
            # Are there any active sessions with a snapshot already in
            # this bucket? If yes, skip backfill. Otherwise fire a tick.
            result = await db.execute(
                select(PortfolioSnapshot).where(
                    PortfolioSnapshot.captured_at_bucket == bucket
                )
            )
            existing = result.scalars().first()
            if existing is not None:
                logger.info(
                    "snapshot backfill skipped: current bucket "
                    f"{bucket.isoformat()} already has at least one row"
                )
                return

        logger.info(
            f"snapshot backfill: capturing current bucket "
            f"{bucket.isoformat()} immediately (startup)"
        )
        await self._capture_all_sessions()


# Global singleton — imported by main.py lifespan
snapshot_scheduler = SnapshotScheduler()
