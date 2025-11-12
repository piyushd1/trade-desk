"""add_audit_tables

Revision ID: 20251112_062115
Revises: b49f4c6ce613
Create Date: 2025-11-12 06:21:15.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '20251112_062115'
down_revision: Union[str, None] = 'b49f4c6ce613'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create audit_logs table
    op.create_table(
        'audit_logs',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('user_id', sa.Integer(), nullable=True),  # Nullable for system events
        sa.Column('username', sa.String(length=50), nullable=True),
        sa.Column('action', sa.String(length=100), nullable=False),
        sa.Column('entity_type', sa.String(length=50), nullable=True),
        sa.Column('entity_id', sa.String(length=100), nullable=True),
        sa.Column('details', sa.JSON(), nullable=True),
        sa.Column('ip_address', sa.String(length=45), nullable=True),
        sa.Column('user_agent', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index('ix_audit_logs_user_id', 'audit_logs', ['user_id'])
    op.create_index('ix_audit_logs_action', 'audit_logs', ['action'])
    op.create_index('ix_audit_logs_created_at', 'audit_logs', ['created_at'])
    
    # Create risk_breach_logs table
    op.create_table(
        'risk_breach_logs',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('strategy_instance_id', sa.Integer(), nullable=True),
        sa.Column('breach_type', sa.String(length=50), nullable=False),
        sa.Column('breach_details', sa.JSON(), nullable=False),
        sa.Column('action_taken', sa.String(length=100), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index('ix_risk_breach_logs_user_id', 'risk_breach_logs', ['user_id'])
    op.create_index('ix_risk_breach_logs_breach_type', 'risk_breach_logs', ['breach_type'])
    op.create_index('ix_risk_breach_logs_created_at', 'risk_breach_logs', ['created_at'])
    
    # Create system_events table
    op.create_table(
        'system_events',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('event_type', sa.String(length=50), nullable=False),
        sa.Column('severity', sa.String(length=20), nullable=False),
        sa.Column('component', sa.String(length=100), nullable=True),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('details', sa.JSON(), nullable=True),
        sa.Column('stack_trace', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index('ix_system_events_event_type', 'system_events', ['event_type'])
    op.create_index('ix_system_events_severity', 'system_events', ['severity'])
    op.create_index('ix_system_events_component', 'system_events', ['component'])
    op.create_index('ix_system_events_created_at', 'system_events', ['created_at'])


def downgrade() -> None:
    op.drop_table('system_events')
    op.drop_table('risk_breach_logs')
    op.drop_table('audit_logs')

