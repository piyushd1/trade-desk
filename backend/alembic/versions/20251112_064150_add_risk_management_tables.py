"""add_risk_management_tables

Revision ID: 20251112_064150
Revises: 20251112_062115
Create Date: 2025-11-12 06:41:50.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '20251112_064150'
down_revision: Union[str, None] = '20251112_062115'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create risk_configs table
    op.create_table(
        'risk_configs',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('max_position_value', sa.Float(), nullable=False, server_default='50000.0'),
        sa.Column('max_positions', sa.Integer(), nullable=False, server_default='5'),
        sa.Column('max_position_pct', sa.Float(), nullable=False, server_default='25.0'),
        sa.Column('max_order_value', sa.Float(), nullable=False, server_default='100000.0'),
        sa.Column('max_orders_per_day', sa.Integer(), nullable=False, server_default='50'),
        sa.Column('ops_limit', sa.Integer(), nullable=False, server_default='10'),
        sa.Column('max_daily_loss', sa.Float(), nullable=False, server_default='5000.0'),
        sa.Column('max_weekly_loss', sa.Float(), nullable=False, server_default='15000.0'),
        sa.Column('max_monthly_loss', sa.Float(), nullable=False, server_default='50000.0'),
        sa.Column('max_drawdown_pct', sa.Float(), nullable=False, server_default='15.0'),
        sa.Column('default_stop_loss_pct', sa.Float(), nullable=False, server_default='2.0'),
        sa.Column('default_target_profit_pct', sa.Float(), nullable=False, server_default='4.0'),
        sa.Column('enforce_stop_loss', sa.Boolean(), nullable=False, server_default='1'),
        sa.Column('allow_pre_market', sa.Boolean(), nullable=False, server_default='0'),
        sa.Column('allow_after_market', sa.Boolean(), nullable=False, server_default='0'),
        sa.Column('trading_enabled', sa.Boolean(), nullable=False, server_default='1'),
        sa.Column('additional_limits', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index('ix_risk_configs_user_id', 'risk_configs', ['user_id'])
    
    # Create daily_risk_metrics table
    op.create_table(
        'daily_risk_metrics',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('trading_date', sa.DateTime(timezone=True), nullable=False),
        sa.Column('orders_placed', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('orders_executed', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('orders_rejected', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('max_positions_held', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('current_positions', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('realized_pnl', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('unrealized_pnl', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('total_pnl', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('max_loss_hit', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('loss_limit_breached', sa.Boolean(), nullable=False, server_default='0'),
        sa.Column('total_turnover', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('risk_breaches', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index('ix_daily_risk_metrics_user_id', 'daily_risk_metrics', ['user_id'])
    op.create_index('ix_daily_risk_metrics_trading_date', 'daily_risk_metrics', ['trading_date'])


def downgrade() -> None:
    op.drop_table('daily_risk_metrics')
    op.drop_table('risk_configs')

