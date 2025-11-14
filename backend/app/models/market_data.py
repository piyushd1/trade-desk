"""
Market Data Models

Contains database models for storing instrument metadata and historical candle
data fetched from Zerodha. These tables are designed to support fast lookups
and efficient backtesting across large datasets.
"""

from datetime import datetime

from sqlalchemy import (
    BigInteger,
    Column,
    Date,
    DateTime,
    DECIMAL,
    Float,
    Integer,
    PrimaryKeyConstraint,
    String,
    func,
)

from app.database import Base


class Instrument(Base):
    """
    Zerodha tradable instruments metadata table.

    We store the latest instrument snapshot returned by the `kite.instruments`
    endpoint. Data is de-duplicated by `instrument_token`.
    """

    __tablename__ = "instruments"

    instrument_token = Column(BigInteger, primary_key=True, index=True)
    exchange_token = Column(Integer, index=True)
    tradingsymbol = Column(String(50), nullable=False, index=True)
    name = Column(String(255))
    last_price = Column(Float)
    expiry = Column(Date, index=True)
    strike = Column(Float)
    tick_size = Column(Float)
    lot_size = Column(Integer)
    instrument_type = Column(String(20), index=True)
    segment = Column(String(20), index=True)
    exchange = Column(String(10), index=True)
    underlying = Column(String(50), index=True)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    __table_args__ = ()

    def __repr__(self) -> str:
        return f"<Instrument({self.exchange}:{self.tradingsymbol} token={self.instrument_token})>"


class HistoricalCandle(Base):
    """
    Stores historical OHLCV candles for instruments.

    Designed for backtesting and analytical workloads. The table uses a
    composite primary key on (instrument_token, interval, timestamp) for quick
    upserts and de-duplication.
    """

    __tablename__ = "historical_candles"

    instrument_token = Column(BigInteger, nullable=False)
    interval = Column(String(15), nullable=False)
    timestamp = Column(DateTime(timezone=True), nullable=False)
    open = Column(DECIMAL(12, 4), nullable=False)
    high = Column(DECIMAL(12, 4), nullable=False)
    low = Column(DECIMAL(12, 4), nullable=False)
    close = Column(DECIMAL(12, 4), nullable=False)
    volume = Column(BigInteger)
    oi = Column(BigInteger)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    __table_args__ = (
        PrimaryKeyConstraint("instrument_token", "interval", "timestamp", name="pk_historical_candles"),
    )

    def __repr__(self) -> str:
        iso_ts = self.timestamp.isoformat() if isinstance(self.timestamp, datetime) else self.timestamp
        return f"<HistoricalCandle({self.instrument_token} {self.interval} {iso_ts})>"


