"""
Zerodha Data Management Service

Utilities to synchronize instrument metadata and historical OHLCV data from
Zerodha into the local database. Provides helper functions used by API
endpoints to manage persistent market data for analysis and backtesting.
"""

from __future__ import annotations

from datetime import datetime, date, timezone
from decimal import Decimal
from typing import Dict, Iterable, List, Optional, Sequence

from kiteconnect import KiteConnect
from sqlalchemy import Select, delete, func, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.concurrency import run_in_threadpool

from app.models.market_data import HistoricalCandle, Instrument


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _chunked(iterable: Sequence[dict], chunk_size: int = 1000) -> Iterable[List[dict]]:
    """Yield successive chunks from a list."""
    for i in range(0, len(iterable), chunk_size):
        yield iterable[i : i + chunk_size]


def _to_decimal(value: Optional[float]) -> Optional[Decimal]:
    if value is None:
        return None
    return Decimal(str(value))


def _normalize_timestamp(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def _to_int(value) -> Optional[int]:
    if value in (None, "", "null"):
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _to_float(value) -> Optional[float]:
    if value in (None, "", "null"):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _parse_expiry(value) -> Optional[date]:
    if not value:
        return None
    if isinstance(value, date) and not isinstance(value, datetime):
        return value
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, str):
        try:
            return datetime.strptime(value[:10], "%Y-%m-%d").date()
        except ValueError:
            return None
    return None


def _clean_str(value) -> Optional[str]:
    if value is None:
        return None
    value = str(value).strip()
    return value or None


# ---------------------------------------------------------------------------
# Instrument Synchronization
# ---------------------------------------------------------------------------


async def sync_instruments(
    db: AsyncSession,
    kite: KiteConnect,
    exchange: Optional[str] = None,
) -> Dict:
    """
    Synchronize instrument metadata from Zerodha.

    Args:
        db: Async database session.
        kite: Authenticated KiteConnect client.
        exchange: Optional exchange filter (NSE, BSE, NFO, etc.).

    Returns:
        dict: Summary of synchronization results.
    """
    if exchange:
        instruments = await run_in_threadpool(kite.instruments, exchange)
    else:
        instruments = await run_in_threadpool(kite.instruments)

    rows: List[dict] = []
    for item in instruments:
        instrument_token = _to_int(item.get("instrument_token"))
        if instrument_token is None:
            continue

        rows.append(
            {
                "instrument_token": instrument_token,
                "exchange_token": _to_int(item.get("exchange_token")),
                "tradingsymbol": _clean_str(item.get("tradingsymbol")),
                "name": _clean_str(item.get("name")),
                "last_price": _to_float(item.get("last_price")),
                "expiry": _parse_expiry(item.get("expiry")),
                "strike": _to_float(item.get("strike")),
                "tick_size": _to_float(item.get("tick_size")),
                "lot_size": _to_int(item.get("lot_size")),
                "instrument_type": _clean_str(item.get("instrument_type")),
                "segment": _clean_str(item.get("segment")),
                "exchange": _clean_str(item.get("exchange")),
                "underlying": _clean_str(item.get("underlying")),
            }
        )

    if not rows:
        return {"total": 0, "exchange": exchange, "message": "No instruments returned"}

    table = Instrument.__table__
    stmt = insert(Instrument)
    update_columns = {
        column.name: getattr(stmt.excluded, column.name)
        for column in table.columns
        if column.name != "instrument_token"
    }

    total = 0
    for chunk in _chunked(rows, 2000):
        chunk_stmt = stmt.values(chunk)
        chunk_stmt = chunk_stmt.on_conflict_do_update(
            index_elements=[table.c.instrument_token],
            set_=update_columns,
        )
        await db.execute(chunk_stmt)
        total += len(chunk)

    await db.commit()

    unique_symbols = len({(row.get("exchange"), row.get("tradingsymbol")) for row in rows})

    return {
        "total": total,
        "exchange": exchange,
        "unique_symbols": unique_symbols,
    }


async def search_instruments(
    db: AsyncSession,
    query: Optional[str] = None,
    exchange: Optional[str] = None,
    segment: Optional[str] = None,
    instrument_type: Optional[str] = None,
    limit: int = 50,
) -> List[dict]:
    stmt: Select = select(Instrument)

    if query:
        pattern = f"%{query.upper()}%"
        stmt = stmt.where(
            func.upper(Instrument.tradingsymbol).like(pattern)
            | func.upper(Instrument.name).like(pattern)
        )

    if exchange:
        stmt = stmt.where(Instrument.exchange == exchange)

    if segment:
        stmt = stmt.where(Instrument.segment == segment)

    if instrument_type:
        stmt = stmt.where(Instrument.instrument_type == instrument_type)

    stmt = stmt.order_by(Instrument.tradingsymbol.asc()).limit(limit)

    result = await db.execute(stmt)
    instruments = result.scalars().all()

    payload = []
    for instrument in instruments:
        payload.append(
            {
                "instrument_token": instrument.instrument_token,
                "exchange_token": instrument.exchange_token,
                "tradingsymbol": instrument.tradingsymbol,
                "name": instrument.name,
                "last_price": instrument.last_price,
                "expiry": instrument.expiry.isoformat() if instrument.expiry else None,
                "strike": instrument.strike,
                "tick_size": instrument.tick_size,
                "lot_size": instrument.lot_size,
                "instrument_type": instrument.instrument_type,
                "segment": instrument.segment,
                "exchange": instrument.exchange,
                "underlying": instrument.underlying,
                "updated_at": instrument.updated_at.isoformat() if instrument.updated_at else None,
            }
        )

    return payload


async def get_instrument(
    db: AsyncSession, instrument_token: int
) -> Optional[dict]:
    stmt = select(Instrument).where(Instrument.instrument_token == instrument_token)
    result = await db.execute(stmt)
    instrument = result.scalars().first()

    if not instrument:
        return None

    return {
        "instrument_token": instrument.instrument_token,
        "exchange_token": instrument.exchange_token,
        "tradingsymbol": instrument.tradingsymbol,
        "name": instrument.name,
        "last_price": instrument.last_price,
        "expiry": instrument.expiry.isoformat() if instrument.expiry else None,
        "strike": instrument.strike,
        "tick_size": instrument.tick_size,
        "lot_size": instrument.lot_size,
        "instrument_type": instrument.instrument_type,
        "segment": instrument.segment,
        "exchange": instrument.exchange,
        "underlying": instrument.underlying,
        "updated_at": instrument.updated_at.isoformat() if instrument.updated_at else None,
    }


# ---------------------------------------------------------------------------
# Historical Data Management
# ---------------------------------------------------------------------------


async def fetch_and_store_historical_data(
    db: AsyncSession,
    kite: KiteConnect,
    instrument_token: int,
    from_date: datetime,
    to_date: datetime,
    interval: str,
    continuous: bool = False,
    oi: bool = False,
) -> Dict:
    """
    Fetch historical candles from Zerodha and store them locally.
    """
    candles = await run_in_threadpool(
        kite.historical_data,
        instrument_token,
        from_date,
        to_date,
        interval,
        continuous,
        oi,
    )

    if not candles:
        return {"count": 0, "instrument_token": instrument_token, "interval": interval}

    rows: List[dict] = []
    for candle in candles:
        timestamp = _normalize_timestamp(candle["date"])
        rows.append(
            {
                "instrument_token": instrument_token,
                "interval": interval,
                "timestamp": timestamp,
                "open": _to_decimal(candle.get("open")),
                "high": _to_decimal(candle.get("high")),
                "low": _to_decimal(candle.get("low")),
                "close": _to_decimal(candle.get("close")),
                "volume": candle.get("volume"),
                "oi": candle.get("oi"),
            }
        )

    table = HistoricalCandle.__table__
    stmt = insert(HistoricalCandle)
    update_columns = {
        column.name: getattr(stmt.excluded, column.name)
        for column in table.columns
        if column.name not in {"instrument_token", "interval", "timestamp"}
    }

    total = 0
    for chunk in _chunked(rows, 2000):
        chunk_stmt = stmt.values(chunk)
        chunk_stmt = chunk_stmt.on_conflict_do_update(
            index_elements=[
                table.c.instrument_token,
                table.c.interval,
                table.c.timestamp,
            ],
            set_=update_columns,
        )
        await db.execute(chunk_stmt)
        total += len(chunk)

    await db.commit()

    return {
        "instrument_token": instrument_token,
        "interval": interval,
        "count": total,
        "from": rows[0]["timestamp"].isoformat(),
        "to": rows[-1]["timestamp"].isoformat(),
    }


async def query_historical_data(
    db: AsyncSession,
    instrument_token: int,
    interval: str,
    start: Optional[datetime] = None,
    end: Optional[datetime] = None,
    limit: int = 500,
) -> List[dict]:
    stmt: Select = (
        select(HistoricalCandle)
        .where(HistoricalCandle.instrument_token == instrument_token)
        .where(HistoricalCandle.interval == interval)
        .order_by(HistoricalCandle.timestamp.asc())
        .limit(limit)
    )

    if start:
        stmt = stmt.where(HistoricalCandle.timestamp >= start)
    if end:
        stmt = stmt.where(HistoricalCandle.timestamp <= end)

    result = await db.execute(stmt)
    candles = result.scalars().all()

    payload = []
    for candle in candles:
        payload.append(
            {
                "timestamp": candle.timestamp.isoformat(),
                "open": float(candle.open) if candle.open is not None else None,
                "high": float(candle.high) if candle.high is not None else None,
                "low": float(candle.low) if candle.low is not None else None,
                "close": float(candle.close) if candle.close is not None else None,
                "volume": candle.volume,
                "oi": candle.oi,
            }
        )

    return payload


async def historical_data_stats(
    db: AsyncSession,
    instrument_token: Optional[int] = None,
    interval: Optional[str] = None,
) -> dict:
    stmt = select(
        func.count().label("count"),
        func.min(HistoricalCandle.timestamp).label("from"),
        func.max(HistoricalCandle.timestamp).label("to"),
    )

    if instrument_token:
        stmt = stmt.where(HistoricalCandle.instrument_token == instrument_token)
    if interval:
        stmt = stmt.where(HistoricalCandle.interval == interval)

    result = await db.execute(stmt)
    row = result.first()

    if not row or row.count == 0:
        return {"count": 0}

    return {
        "count": row.count,
        "from": row.from_.isoformat() if row.from_ else None,
        "to": row.to.isoformat() if row.to else None,
    }


async def cleanup_historical_data(
    db: AsyncSession,
    instrument_token: Optional[int] = None,
    older_than: Optional[datetime] = None,
) -> int:
    stmt = delete(HistoricalCandle)
    if instrument_token:
        stmt = stmt.where(HistoricalCandle.instrument_token == instrument_token)
    if older_than:
        stmt = stmt.where(HistoricalCandle.timestamp < older_than)

    result = await db.execute(stmt)
    await db.commit()
    return result.rowcount or 0


