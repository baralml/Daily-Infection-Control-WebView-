"""add staff reports table

Revision ID: eb27c2cd3d5d
Revises: 204c0e7f1526
Create Date: 2026-07-05 17:29:24.835120

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'eb27c2cd3d5d'
down_revision: Union[str, None] = '204c0e7f1526'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('staff_reports',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('description', sa.String(length=2000), nullable=False),
    sa.Column('latitude', sa.Float(), nullable=True),
    sa.Column('longitude', sa.Float(), nullable=True),
    sa.Column('photo_url', sa.String(length=1000), nullable=True),
    sa.Column('is_resolved', sa.Boolean(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )


def downgrade() -> None:
    op.drop_table('staff_reports')
