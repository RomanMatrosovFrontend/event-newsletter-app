"""fix_relationship_with_batch_mode

Revision ID: de5be64336f8
Revises: 895d62a56b81
Create Date: 2025-08-20 21:15:21.899162

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'de5be64336f8'
down_revision: Union[str, None] = '895d62a56b81'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Для SQLite используем batch operations
    with op.batch_alter_table('newsletter_logs') as batch_op:
        batch_op.add_column(sa.Column('schedule_id', sa.Integer(), nullable=True))
        batch_op.create_foreign_key(
            'fk_newsletter_logs_schedule_id',
            'newsletter_schedules',
            ['schedule_id'],
            ['id']
        )


def downgrade() -> None:
    with op.batch_alter_table('newsletter_logs') as batch_op:
        batch_op.drop_constraint('fk_newsletter_logs_schedule_id', type_='foreignkey')
        batch_op.drop_column('schedule_id')