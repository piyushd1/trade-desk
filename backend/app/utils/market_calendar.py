"""
NSE Market Calendar

Loads NSE holiday data from backend/config/nse_holidays.yaml and exposes
pure functions to check whether the Indian equity market (NSE/BSE) is
open at a given moment in IST.

Used by:
  - backend/app/services/snapshot_scheduler.py — gates 15-min portfolio
    snapshot captures so the scheduler only runs during market hours on
    trading days.
  - Future backfill + re-run logic that needs to know whether to fetch
    historical data for a given day.

Market hours (hardcoded):
  Regular session: 09:15 – 15:30 IST, Mon–Fri
  Pre-open:        09:00 – 09:15 IST (informational only — we don't snapshot)
  Post-close:      15:40 – 16:00 IST (closing session — ignored for now)
  Muhurat:         Diwali evening — explicitly excluded from is_market_open()
                   because snapshots don't care about a one-hour special session

Holiday data loaded lazily on first call; cached for the process lifetime.
Re-reading the YAML requires a backend restart.
"""

from __future__ import annotations

from datetime import date, datetime, time, timedelta, timezone
from pathlib import Path
from typing import Optional, Set

import logging

try:
    import yaml  # type: ignore
except ImportError:  # pragma: no cover
    yaml = None  # will raise at first use if unavailable

logger = logging.getLogger(__name__)

# IST is always UTC+5:30 — India does not observe daylight saving.
IST = timezone(timedelta(hours=5, minutes=30))

# Regular-session boundaries in IST. These never change for NSE.
MARKET_OPEN_IST = time(9, 15)
MARKET_CLOSE_IST = time(15, 30)

# Resolved lazily on first use.
_HOLIDAY_CACHE: Optional[Set[date]] = None


def _holidays_yaml_path() -> Path:
    """
    Resolve the path to nse_holidays.yaml relative to this file.

    backend/app/utils/market_calendar.py  →  backend/config/nse_holidays.yaml
    """
    return Path(__file__).resolve().parent.parent.parent / "config" / "nse_holidays.yaml"


def _load_holidays() -> Set[date]:
    """
    Parse the NSE holidays YAML into a flat set of date objects.

    The YAML is structured as:
        2026:
          - 2026-01-26
          - 2026-04-03
        2027:
          - ...

    We flatten across years into a single set. YAML's native date type
    returns `datetime.date` objects directly, so no string parsing
    needed as long as entries are written in ISO format (`YYYY-MM-DD`).
    """
    global _HOLIDAY_CACHE
    if _HOLIDAY_CACHE is not None:
        return _HOLIDAY_CACHE

    if yaml is None:
        logger.warning(
            "PyYAML is not installed; market_calendar will treat every "
            "weekday as a trading day. Install pyyaml to load nse_holidays.yaml."
        )
        _HOLIDAY_CACHE = set()
        return _HOLIDAY_CACHE

    path = _holidays_yaml_path()
    if not path.exists():
        logger.warning(
            f"NSE holidays YAML not found at {path} — market_calendar will "
            "treat every weekday as a trading day."
        )
        _HOLIDAY_CACHE = set()
        return _HOLIDAY_CACHE

    try:
        with path.open("r") as fh:
            parsed = yaml.safe_load(fh) or {}
    except Exception as exc:  # noqa: BLE001
        logger.error(f"Failed to parse {path}: {exc}")
        _HOLIDAY_CACHE = set()
        return _HOLIDAY_CACHE

    holidays: Set[date] = set()
    for year_key, entries in parsed.items():
        if not entries:
            continue
        for entry in entries:
            if isinstance(entry, date):
                holidays.add(entry)
            elif isinstance(entry, str):
                try:
                    holidays.add(date.fromisoformat(entry))
                except ValueError:
                    logger.warning(f"Skipping malformed holiday entry: {entry!r}")
            else:
                logger.warning(
                    f"Skipping non-date holiday entry under {year_key}: {entry!r}"
                )

    logger.info(
        f"Loaded {len(holidays)} NSE holiday dates from {path.name} "
        f"(years: {sorted({d.year for d in holidays})})"
    )
    _HOLIDAY_CACHE = holidays
    return _HOLIDAY_CACHE


def _to_ist(moment: Optional[datetime] = None) -> datetime:
    """Return the given datetime (or now) as an IST-aware datetime."""
    if moment is None:
        moment = datetime.now(timezone.utc)
    if moment.tzinfo is None:
        # Treat naive datetimes as UTC — the whole backend operates in UTC
        moment = moment.replace(tzinfo=timezone.utc)
    return moment.astimezone(IST)


def is_trading_day(day: Optional[date] = None) -> bool:
    """
    True if the given calendar date is a weekday AND not a listed NSE holiday.

    Pure date check — does not consider the time of day. Use
    `is_market_open` for the full "is the market currently open" answer.
    """
    if day is None:
        day = _to_ist().date()
    if day.weekday() >= 5:  # 5 = Sat, 6 = Sun
        return False
    return day not in _load_holidays()


def is_market_open(moment: Optional[datetime] = None) -> bool:
    """
    True if the Indian equity market is open at the given moment.

    A moment is "open" iff:
      - It's a trading day (weekday, not in the holiday YAML), AND
      - The IST time of day is within [09:15, 15:30].

    Works for any timezone — the input datetime is converted to IST
    before the window check. Naive datetimes are treated as UTC.

    Args:
        moment: A timezone-aware or naive datetime. If None, uses now (UTC).

    Returns:
        bool
    """
    moment_ist = _to_ist(moment)
    if not is_trading_day(moment_ist.date()):
        return False
    tod = moment_ist.time()
    return MARKET_OPEN_IST <= tod <= MARKET_CLOSE_IST


def next_market_open(after: Optional[datetime] = None) -> datetime:
    """
    Return the next datetime at which `is_market_open()` will be True.

    If called during an open session, returns the same session's start
    (in the past) — callers who want "the next FUTURE open" should
    check `is_market_open(now)` first and skip this if currently open.

    Search is bounded at 30 days forward to avoid infinite loops if the
    holiday YAML is ever badly malformed.

    Args:
        after: Reference datetime (defaults to now UTC). Search starts
               from the next calendar day after this moment's IST date
               unless the current IST time is before 09:15.

    Returns:
        A timezone-aware IST datetime at the next market open.
    """
    ref_ist = _to_ist(after)
    candidate_date = ref_ist.date()

    # If we're before 09:15 IST today and today is a trading day, today is it.
    if ref_ist.time() < MARKET_OPEN_IST and is_trading_day(candidate_date):
        return datetime.combine(candidate_date, MARKET_OPEN_IST, tzinfo=IST)

    # Otherwise, scan forward day by day.
    for _ in range(30):
        candidate_date = candidate_date + timedelta(days=1)
        if is_trading_day(candidate_date):
            return datetime.combine(candidate_date, MARKET_OPEN_IST, tzinfo=IST)

    # Fallback if something's very wrong with the calendar — return a
    # sentinel a month out so the caller at least doesn't crash.
    logger.error(
        "next_market_open() could not find a trading day within 30 days — "
        "check nse_holidays.yaml for malformed entries."
    )
    return datetime.combine(
        candidate_date + timedelta(days=1), MARKET_OPEN_IST, tzinfo=IST
    )


def floor_to_15min_bucket(moment: Optional[datetime] = None) -> datetime:
    """
    Floor a datetime to the nearest 15-minute boundary (UTC, naive).

    Used by the snapshot scheduler as the `captured_at_bucket` value for
    the UNIQUE constraint on `portfolio_snapshots`. Returns naive UTC to
    match SQLite column types across the codebase.

    Examples:
        2026-04-15 09:17:23 UTC  →  2026-04-15 09:15:00 UTC
        2026-04-15 09:29:59 UTC  →  2026-04-15 09:15:00 UTC
        2026-04-15 09:30:00 UTC  →  2026-04-15 09:30:00 UTC
    """
    if moment is None:
        moment = datetime.now(timezone.utc)
    if moment.tzinfo is None:
        moment = moment.replace(tzinfo=timezone.utc)
    utc = moment.astimezone(timezone.utc)
    floored_minute = (utc.minute // 15) * 15
    return utc.replace(minute=floored_minute, second=0, microsecond=0, tzinfo=None)
