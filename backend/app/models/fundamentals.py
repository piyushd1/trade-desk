"""
Fundamentals Data Models

Database models for storing fundamental data from Yahoo Finance,
including financial ratios, analyst data, and symbol mappings.
"""

from datetime import datetime, date
from sqlalchemy import (
    BigInteger,
    Column,
    DateTime,
    Date,
    DECIMAL,
    Float,
    Integer,
    String,
    Text,
    ForeignKey,
    func,
)
from sqlalchemy.orm import relationship

from app.database import Base


class SymbolMapping(Base):
    """
    Maps Zerodha instrument tokens to Yahoo Finance symbols.
    
    This table acts as the bridge between Zerodha's instrument identification
    and Yahoo Finance's symbol format (e.g., RELIANCE -> RELIANCE.NS).
    """
    
    __tablename__ = "symbol_mapping"
    
    instrument_token = Column(
        BigInteger,
        ForeignKey("instruments.instrument_token", ondelete="CASCADE"),
        primary_key=True,
        index=True,
    )
    yfinance_symbol = Column(String(50), nullable=False, index=True)
    exchange_suffix = Column(String(10), nullable=False)  # .NS, .BO, etc.
    mapping_status = Column(
        String(20),
        nullable=False,
        default="active",
        index=True,
    )  # active, invalid, not_found
    last_verified_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationship back to Instrument
    # instrument = relationship("Instrument", back_populates="symbol_mapping")
    
    def __repr__(self) -> str:
        return f"<SymbolMapping({self.instrument_token} -> {self.yfinance_symbol})>"


class StockFundamentals(Base):
    """
    Stores fundamental ratios and metrics for stocks.
    
    Data is fetched from Yahoo Finance and cached here for performance.
    Updates are made on-demand or through scheduled jobs.
    """
    
    __tablename__ = "stock_fundamentals"
    
    instrument_token = Column(
        BigInteger,
        ForeignKey("instruments.instrument_token", ondelete="CASCADE"),
        primary_key=True,
        index=True,
    )
    
    # Company Information
    long_name = Column(String(255))
    sector = Column(String(100), index=True)
    industry = Column(String(100), index=True)
    full_time_employees = Column(Integer)
    
    # Valuation Ratios
    trailing_pe = Column(DECIMAL(10, 2))  # Price to Earnings (trailing)
    forward_pe = Column(DECIMAL(10, 2))   # Price to Earnings (forward)
    price_to_book = Column(DECIMAL(10, 2))  # Price to Book ratio
    price_to_sales = Column(DECIMAL(10, 2))  # Price to Sales ratio
    enterprise_to_revenue = Column(DECIMAL(10, 2))
    enterprise_to_ebitda = Column(DECIMAL(10, 2))
    
    # Profitability Metrics
    trailing_eps = Column(DECIMAL(10, 2))  # Earnings Per Share (trailing)
    forward_eps = Column(DECIMAL(10, 2))   # Earnings Per Share (forward)
    earnings_quarterly_growth = Column(DECIMAL(10, 4))  # YoY quarterly growth
    revenue_growth = Column(DECIMAL(10, 4))  # Revenue growth rate
    
    # Market Data
    market_cap = Column(BigInteger, index=True)  # Market Capitalization
    enterprise_value = Column(BigInteger)
    shares_outstanding = Column(BigInteger)
    float_shares = Column(BigInteger)
    
    # Dividend Information
    dividend_yield = Column(DECIMAL(5, 4))  # As decimal (e.g., 0.0325 for 3.25%)
    payout_ratio = Column(DECIMAL(5, 4))
    trailing_annual_dividend_rate = Column(DECIMAL(10, 2))
    trailing_annual_dividend_yield = Column(DECIMAL(5, 4))
    
    # Performance Metrics
    fifty_two_week_high = Column(DECIMAL(12, 2))
    fifty_two_week_low = Column(DECIMAL(12, 2))
    beta = Column(DECIMAL(5, 3))  # Volatility measure
    average_volume = Column(BigInteger)
    average_volume_10days = Column(BigInteger)
    
    # Additional Metrics
    book_value = Column(DECIMAL(12, 2))
    profit_margins = Column(DECIMAL(10, 4))
    return_on_assets = Column(DECIMAL(10, 4))
    return_on_equity = Column(DECIMAL(10, 4))
    
    # Data Source Tracking
    data_source = Column(String(50), default="yfinance")
    data_date = Column(Date, nullable=False, default=func.current_date())
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationship back to Instrument
    # instrument = relationship("Instrument", back_populates="fundamentals")
    
    def __repr__(self) -> str:
        return f"<StockFundamentals({self.instrument_token} - {self.long_name})>"


class StockAnalystData(Base):
    """
    Stores analyst recommendations and estimates for stocks.
    
    Includes target prices, buy/sell recommendations, and earnings/revenue estimates.
    Data is time-series, so we use instrument_token + data_date as composite key.
    """
    
    __tablename__ = "stock_analyst_data"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    instrument_token = Column(
        BigInteger,
        ForeignKey("instruments.instrument_token", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    data_date = Column(Date, nullable=False, index=True)
    
    # Target Price Data
    target_mean_price = Column(DECIMAL(12, 2))
    target_high_price = Column(DECIMAL(12, 2))
    target_low_price = Column(DECIMAL(12, 2))
    target_median_price = Column(DECIMAL(12, 2))
    current_price = Column(DECIMAL(12, 2))
    
    # Analyst Recommendations
    recommendation_mean = Column(DECIMAL(3, 2))  # 1.0-5.0 scale (1=Strong Buy, 5=Sell)
    recommendation_key = Column(String(20))  # "buy", "hold", "sell", etc.
    number_of_analyst_opinions = Column(Integer)
    
    # Recommendation Breakdown
    strong_buy_count = Column(Integer)
    buy_count = Column(Integer)
    hold_count = Column(Integer)
    sell_count = Column(Integer)
    strong_sell_count = Column(Integer)
    
    # Earnings Estimates
    current_quarter_estimate = Column(DECIMAL(12, 2))
    next_quarter_estimate = Column(DECIMAL(12, 2))
    current_year_estimate = Column(DECIMAL(12, 2))
    next_year_estimate = Column(DECIMAL(12, 2))
    
    # Revenue Estimates
    current_quarter_revenue_estimate = Column(BigInteger)
    next_quarter_revenue_estimate = Column(BigInteger)
    current_year_revenue_estimate = Column(BigInteger)
    next_year_revenue_estimate = Column(BigInteger)
    
    # Earnings Calendar
    earnings_date = Column(Date)
    earnings_average = Column(DECIMAL(12, 2))
    earnings_low = Column(DECIMAL(12, 2))
    earnings_high = Column(DECIMAL(12, 2))
    
    # Additional Info
    analyst_notes = Column(Text)
    
    # Data Source Tracking
    data_source = Column(String(50), default="yfinance")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationship back to Instrument
    # instrument = relationship("Instrument", back_populates="analyst_data")
    
    def __repr__(self) -> str:
        return f"<StockAnalystData({self.instrument_token} - {self.data_date})>"

