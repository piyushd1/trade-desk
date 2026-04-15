"""add_portfolio_snapshots

Revision ID: ce420610b12a
Revises: 326c2e477aad
Create Date: 2026-04-15 21:54:35.000000

Adds the portfolio_snapshots table that the Phase B4 snapshot scheduler
writes to every 15 minutes during market hours. Schema is per-broker:
one row per (user_id, broker, captured_at_bucket) so we get partial
writes if one broker fails mid-job, and aggregation across brokers is a
SELECT SUM(...) GROUP BY captured_at_bucket at query time in Phase B6
(/portfolio/history) and B7 (/portfolio/metrics).

Columns:
    id                 — PK
    user_id            — FK → users.id
    broker             — "zerodha" | "indstocks" | future
    captured_at_bucket — UTC datetime, floored to 15-min boundary.
                         The UNIQUE constraint on (user_id, broker,
                         captured_at_bucket) is the final defense against
                         duplicate writes from the scheduler — even if
                         two jobs race for the same slot, the second
                         INSERT hits IntegrityError and we log-and-skip.
    captured_at        — UTC datetime, actual moment the snapshot was
                         taken (may differ from the bucket by seconds).
    total_value        — NUMERIC, sum of equity + cash for this broker
    total_pnl          — NUMERIC, realized + unrealized
    realized_pnl       — NUMERIC
    unrealized_pnl     — NUMERIC
    holdings_json      — TEXT, raw broker payload preserved for future
                         re-analysis (e.g. sector breakdown, per-symbol
                         history). JSON-encoded since SQLite has no
                         native JSON column on older versions.

Indexes:
    unique (user_id, broker, captured_at_bucket)
    idx (user_id, captured_at_bucket DESC)           — history queries
    idx (user_id, broker, captured_at_bucket DESC)   — per-broker drill-down
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'ce420610b12a'
down_revision: Union[str, None] = '326c2e477aad'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'portfolio_snapshots',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column(
            'user_id',
            sa.Integer(),
            sa.ForeignKey('users.id', ondelete='CASCADE'),
            nullable=False,
        ),
        sa.Column('broker', sa.String(length=50), nullable=False),
        sa.Column(
            'captured_at_bucket',
            sa.DateTime(timezone=False),
            nullable=False,
            comment='UTC, floored to 15-minute boundary',
        ),
        sa.Column(
            'captured_at',
            sa.DateTime(timezone=False),
            nullable=False,
            comment='UTC, actual capture moment',
        ),
        sa.Column('total_value', sa.Numeric(18, 4), nullable=False),
        sa.Column('total_pnl', sa.Numeric(18, 4), nullable=False),
        sa.Column('realized_pnl', sa.Numeric(18, 4), nullable=False),
        sa.Column('unrealized_pnl', sa.Numeric(18, 4), nullable=False),
        sa.Column(
            'holdings_json',
            sa.Text(),
            nullable=False,
            comment='Raw broker payload for this snapshot (JSON-encoded)',
        ),
        sa.Column(
            'created_at',
            sa.DateTime(timezone=False),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.UniqueConstraint(
            'user_id',
            'broker',
            'captured_at_bucket',
            name='uq_portfolio_snapshots_user_broker_bucket',
        ),
    )

    # Primary query path: a single user's history over a time window.
    # DESC index because we always want the most recent snapshots first.
    op.create_index(
        'ix_portfolio_snapshots_user_bucket',
        'portfolio_snapshots',
        ['user_id', sa.text('captured_at_bucket DESC')],
    )

    # Per-broker drill-down query path: ?broker=zerodha filter in
    # /portfolio/history. Separate index so the optimizer can use it
    # when the broker predicate is present.
    op.create_index(
        'ix_portfolio_snapshots_user_broker_bucket',
        'portfolio_snapshots',
        ['user_id', 'broker', sa.text('captured_at_bucket DESC')],
    )


def downgrade() -> None:
    op.drop_index(
        'ix_portfolio_snapshots_user_broker_bucket',
        table_name='portfolio_snapshots',
    )
    op.drop_index(
        'ix_portfolio_snapshots_user_bucket',
        table_name='portfolio_snapshots',
    )
    op.drop_table('portfolio_snapshots')
