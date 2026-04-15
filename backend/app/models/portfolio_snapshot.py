"""
Portfolio Snapshot Model

Per-broker portfolio value snapshots captured on a 15-minute cadence
during market hours by the Phase B4 snapshot_scheduler. One row per
(user_id, broker, captured_at_bucket) — aggregation across brokers
happens at query time in /portfolio/history and /portfolio/metrics.
"""

from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


class PortfolioSnapshot(Base):
    """
    A single broker's portfolio value at a specific 15-minute bucket.

    The scheduler runs every 15 minutes Mon–Fri during market hours and
    writes one row per active broker session for the user. If one broker
    fails mid-job (e.g. Zerodha session expired at 6 AM IST, IndStocks
    token expired), the other broker's row still gets written — partial
    writes are fine and preferred over all-or-nothing.

    Queries in /portfolio/history and /portfolio/metrics `SUM()` over the
    broker column to present a portfolio-wide view; callers that want a
    per-broker drill-down filter on `broker` first.
    """

    __tablename__ = "portfolio_snapshots"
    __table_args__ = (
        UniqueConstraint(
            "user_id",
            "broker",
            "captured_at_bucket",
            name="uq_portfolio_snapshots_user_broker_bucket",
        ),
        Index(
            "ix_portfolio_snapshots_user_bucket",
            "user_id",
            "captured_at_bucket",
        ),
        Index(
            "ix_portfolio_snapshots_user_broker_bucket",
            "user_id",
            "broker",
            "captured_at_bucket",
        ),
    )

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    broker = Column(String(50), nullable=False, index=True)
    # captured_at_bucket is UTC, floored to the 15-minute boundary that
    # corresponds to the scheduler tick that produced this row. Used as
    # the grouping key for aggregation across brokers.
    captured_at_bucket = Column(DateTime(timezone=False), nullable=False)
    # captured_at is the actual moment the snapshot was taken, may differ
    # from the bucket by a few seconds. Useful for debugging scheduler
    # lag / drift, not used for grouping.
    captured_at = Column(DateTime(timezone=False), nullable=False)

    total_value = Column(Numeric(18, 4), nullable=False)
    total_pnl = Column(Numeric(18, 4), nullable=False)
    realized_pnl = Column(Numeric(18, 4), nullable=False)
    unrealized_pnl = Column(Numeric(18, 4), nullable=False)

    # Raw broker payload JSON-encoded for future re-analysis (per-symbol
    # history, sector breakdown, etc). Kept as TEXT because older SQLite
    # builds don't have a JSON column type and we want the schema to be
    # portable if we ever migrate to Postgres.
    holdings_json = Column(Text, nullable=False)

    created_at = Column(
        DateTime(timezone=False),
        server_default=func.now(),
        nullable=False,
    )

    # Relationship to User model. The User model has a `back_populates`
    # hook for broker_sessions — if we want to access user.portfolio_snapshots
    # similarly, add a matching relationship() on the User side.
    user = relationship("User")

    def __repr__(self) -> str:
        return (
            f"<PortfolioSnapshot(user_id={self.user_id}, broker={self.broker}, "
            f"bucket={self.captured_at_bucket}, value={self.total_value})>"
        )
