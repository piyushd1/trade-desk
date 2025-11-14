"""add user_id to broker_sessions

Revision ID: 987461a964ab
Revises: 20251112_064150
Create Date: 2025-11-14 07:29:57.753136

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '987461a964ab'
down_revision: Union[str, None] = '20251112_064150'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # SQLite doesn't support ALTER TABLE for foreign keys, use batch mode
    with op.batch_alter_table('broker_sessions', schema=None) as batch_op:
        # Add user_id column
        batch_op.add_column(sa.Column('user_id', sa.Integer(), nullable=True))
        
        # Create foreign key constraint
        batch_op.create_foreign_key(
            'fk_broker_sessions_user_id',
            'users',
            ['user_id'], ['id'],
            ondelete='CASCADE'
        )
        
        # Create index for performance
        batch_op.create_index('ix_broker_sessions_user_id', ['user_id'])


def downgrade() -> None:
    # Use batch mode for SQLite
    with op.batch_alter_table('broker_sessions', schema=None) as batch_op:
        # Drop index
        batch_op.drop_index('ix_broker_sessions_user_id')
        
        # Drop foreign key constraint
        batch_op.drop_constraint('fk_broker_sessions_user_id', type_='foreignkey')
        
        # Drop column
        batch_op.drop_column('user_id')

