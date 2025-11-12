"""add_broker_sessions_table

Revision ID: b49f4c6ce613
Revises: 
Create Date: 2025-11-11 13:21:39.132305

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b49f4c6ce613'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'broker_sessions',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('user_identifier', sa.String(length=100), nullable=False),
        sa.Column('broker', sa.String(length=50), nullable=False),
        sa.Column('access_token_encrypted', sa.Text(), nullable=False),
        sa.Column('refresh_token_encrypted', sa.Text(), nullable=True),
        sa.Column('public_token', sa.String(length=100), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=True),
        sa.Column('meta', sa.JSON(), nullable=True),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint('user_identifier', 'broker', name='uq_broker_sessions_user_broker')
    )


def downgrade() -> None:
    op.drop_table('broker_sessions')

