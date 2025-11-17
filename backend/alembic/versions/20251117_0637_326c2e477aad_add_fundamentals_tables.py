"""add_fundamentals_tables

Revision ID: 326c2e477aad
Revises: 987461a964ab
Create Date: 2025-11-17 06:37:46.415559

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '326c2e477aad'
down_revision: Union[str, None] = '987461a964ab'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create symbol_mapping table
    op.create_table(
        'symbol_mapping',
        sa.Column('instrument_token', sa.BigInteger(), nullable=False),
        sa.Column('yfinance_symbol', sa.String(50), nullable=False),
        sa.Column('exchange_suffix', sa.String(10), nullable=False),
        sa.Column('mapping_status', sa.String(20), nullable=False, server_default='active'),
        sa.Column('last_verified_at', sa.DateTime(timezone=True)),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['instrument_token'], ['instruments.instrument_token'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('instrument_token')
    )
    op.create_index(op.f('ix_symbol_mapping_instrument_token'), 'symbol_mapping', ['instrument_token'])
    op.create_index(op.f('ix_symbol_mapping_yfinance_symbol'), 'symbol_mapping', ['yfinance_symbol'])
    op.create_index(op.f('ix_symbol_mapping_mapping_status'), 'symbol_mapping', ['mapping_status'])
    
    # Create stock_fundamentals table
    op.create_table(
        'stock_fundamentals',
        sa.Column('instrument_token', sa.BigInteger(), nullable=False),
        sa.Column('long_name', sa.String(255)),
        sa.Column('sector', sa.String(100)),
        sa.Column('industry', sa.String(100)),
        sa.Column('full_time_employees', sa.Integer()),
        sa.Column('trailing_pe', sa.DECIMAL(10, 2)),
        sa.Column('forward_pe', sa.DECIMAL(10, 2)),
        sa.Column('price_to_book', sa.DECIMAL(10, 2)),
        sa.Column('price_to_sales', sa.DECIMAL(10, 2)),
        sa.Column('enterprise_to_revenue', sa.DECIMAL(10, 2)),
        sa.Column('enterprise_to_ebitda', sa.DECIMAL(10, 2)),
        sa.Column('trailing_eps', sa.DECIMAL(10, 2)),
        sa.Column('forward_eps', sa.DECIMAL(10, 2)),
        sa.Column('earnings_quarterly_growth', sa.DECIMAL(10, 4)),
        sa.Column('revenue_growth', sa.DECIMAL(10, 4)),
        sa.Column('market_cap', sa.BigInteger()),
        sa.Column('enterprise_value', sa.BigInteger()),
        sa.Column('shares_outstanding', sa.BigInteger()),
        sa.Column('float_shares', sa.BigInteger()),
        sa.Column('dividend_yield', sa.DECIMAL(5, 4)),
        sa.Column('payout_ratio', sa.DECIMAL(5, 4)),
        sa.Column('trailing_annual_dividend_rate', sa.DECIMAL(10, 2)),
        sa.Column('trailing_annual_dividend_yield', sa.DECIMAL(5, 4)),
        sa.Column('fifty_two_week_high', sa.DECIMAL(12, 2)),
        sa.Column('fifty_two_week_low', sa.DECIMAL(12, 2)),
        sa.Column('beta', sa.DECIMAL(5, 3)),
        sa.Column('average_volume', sa.BigInteger()),
        sa.Column('average_volume_10days', sa.BigInteger()),
        sa.Column('book_value', sa.DECIMAL(12, 2)),
        sa.Column('profit_margins', sa.DECIMAL(10, 4)),
        sa.Column('return_on_assets', sa.DECIMAL(10, 4)),
        sa.Column('return_on_equity', sa.DECIMAL(10, 4)),
        sa.Column('data_source', sa.String(50), server_default='yfinance'),
        sa.Column('data_date', sa.Date(), nullable=False, server_default=sa.func.current_date()),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['instrument_token'], ['instruments.instrument_token'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('instrument_token')
    )
    op.create_index(op.f('ix_stock_fundamentals_instrument_token'), 'stock_fundamentals', ['instrument_token'])
    op.create_index(op.f('ix_stock_fundamentals_sector'), 'stock_fundamentals', ['sector'])
    op.create_index(op.f('ix_stock_fundamentals_industry'), 'stock_fundamentals', ['industry'])
    op.create_index(op.f('ix_stock_fundamentals_market_cap'), 'stock_fundamentals', ['market_cap'])
    
    # Create stock_analyst_data table
    op.create_table(
        'stock_analyst_data',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('instrument_token', sa.BigInteger(), nullable=False),
        sa.Column('data_date', sa.Date(), nullable=False),
        sa.Column('target_mean_price', sa.DECIMAL(12, 2)),
        sa.Column('target_high_price', sa.DECIMAL(12, 2)),
        sa.Column('target_low_price', sa.DECIMAL(12, 2)),
        sa.Column('target_median_price', sa.DECIMAL(12, 2)),
        sa.Column('current_price', sa.DECIMAL(12, 2)),
        sa.Column('recommendation_mean', sa.DECIMAL(3, 2)),
        sa.Column('recommendation_key', sa.String(20)),
        sa.Column('number_of_analyst_opinions', sa.Integer()),
        sa.Column('strong_buy_count', sa.Integer()),
        sa.Column('buy_count', sa.Integer()),
        sa.Column('hold_count', sa.Integer()),
        sa.Column('sell_count', sa.Integer()),
        sa.Column('strong_sell_count', sa.Integer()),
        sa.Column('current_quarter_estimate', sa.DECIMAL(12, 2)),
        sa.Column('next_quarter_estimate', sa.DECIMAL(12, 2)),
        sa.Column('current_year_estimate', sa.DECIMAL(12, 2)),
        sa.Column('next_year_estimate', sa.DECIMAL(12, 2)),
        sa.Column('current_quarter_revenue_estimate', sa.BigInteger()),
        sa.Column('next_quarter_revenue_estimate', sa.BigInteger()),
        sa.Column('current_year_revenue_estimate', sa.BigInteger()),
        sa.Column('next_year_revenue_estimate', sa.BigInteger()),
        sa.Column('earnings_date', sa.Date()),
        sa.Column('earnings_average', sa.DECIMAL(12, 2)),
        sa.Column('earnings_low', sa.DECIMAL(12, 2)),
        sa.Column('earnings_high', sa.DECIMAL(12, 2)),
        sa.Column('analyst_notes', sa.Text()),
        sa.Column('data_source', sa.String(50), server_default='yfinance'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['instrument_token'], ['instruments.instrument_token'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_stock_analyst_data_instrument_token'), 'stock_analyst_data', ['instrument_token'])
    op.create_index(op.f('ix_stock_analyst_data_data_date'), 'stock_analyst_data', ['data_date'])


def downgrade() -> None:
    op.drop_index(op.f('ix_stock_analyst_data_data_date'), table_name='stock_analyst_data')
    op.drop_index(op.f('ix_stock_analyst_data_instrument_token'), table_name='stock_analyst_data')
    op.drop_table('stock_analyst_data')
    
    op.drop_index(op.f('ix_stock_fundamentals_market_cap'), table_name='stock_fundamentals')
    op.drop_index(op.f('ix_stock_fundamentals_industry'), table_name='stock_fundamentals')
    op.drop_index(op.f('ix_stock_fundamentals_sector'), table_name='stock_fundamentals')
    op.drop_index(op.f('ix_stock_fundamentals_instrument_token'), table_name='stock_fundamentals')
    op.drop_table('stock_fundamentals')
    
    op.drop_index(op.f('ix_symbol_mapping_mapping_status'), table_name='symbol_mapping')
    op.drop_index(op.f('ix_symbol_mapping_yfinance_symbol'), table_name='symbol_mapping')
    op.drop_index(op.f('ix_symbol_mapping_instrument_token'), table_name='symbol_mapping')
    op.drop_table('symbol_mapping')

