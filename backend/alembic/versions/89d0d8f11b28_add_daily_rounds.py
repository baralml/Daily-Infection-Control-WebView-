"""add_daily_rounds

Revision ID: 89d0d8f11b28
Revises: a6fa8c9c0d3f
Create Date: 2026-07-05 13:14:35.622730

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '89d0d8f11b28'
down_revision: Union[str, None] = 'a6fa8c9c0d3f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create master_observations (using existing risk_level_enum type without recreating it)
    op.create_table('master_observations',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('text', sa.String(length=500), nullable=False),
        sa.Column('category', sa.String(length=100), nullable=False),
        sa.Column('default_severity', postgresql.ENUM('LOW', 'MEDIUM', 'HIGH', 'CRITICAL', name='risk_level_enum', create_type=False), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('text')
    )

    # Create daily_rounds (status is string for maximum simplicity and safety)
    op.create_table('daily_rounds',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('hospital', sa.String(length=100), nullable=False),
        sa.Column('building', sa.String(length=100), nullable=False),
        sa.Column('floor', sa.String(length=50), nullable=False),
        sa.Column('department_id', sa.Integer(), nullable=False),
        sa.Column('round_type', sa.String(length=50), nullable=False),
        sa.Column('auditor_id', sa.UUID(), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('ended_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['auditor_id'], ['users.id'], ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['department_id'], ['departments.id'], ondelete='RESTRICT'),
        sa.PrimaryKeyConstraint('id')
    )

    # Create daily_round_observations
    op.create_table('daily_round_observations',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('round_id', sa.UUID(), nullable=False),
        sa.Column('observation_text', sa.String(length=500), nullable=False),
        sa.Column('category', sa.String(length=100), nullable=False),
        sa.Column('room_number', sa.String(length=50), nullable=True),
        sa.Column('severity', postgresql.ENUM('LOW', 'MEDIUM', 'HIGH', 'CRITICAL', name='risk_level_enum', create_type=False), nullable=False),
        sa.Column('remarks', sa.String(length=1000), nullable=True),
        sa.Column('voice_note_url', sa.String(length=1000), nullable=True),
        sa.Column('voice_text_transcript', sa.String(length=2000), nullable=True),
        sa.Column('has_capa', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['round_id'], ['daily_rounds.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    # Create daily_round_observation_media
    op.create_table('daily_round_observation_media',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('observation_id', sa.UUID(), nullable=False),
        sa.Column('media_type', sa.String(length=50), nullable=False),
        sa.Column('original_url', sa.String(length=1000), nullable=False),
        sa.Column('thumbnail_url', sa.String(length=1000), nullable=True),
        sa.Column('compressed_url', sa.String(length=1000), nullable=True),
        sa.Column('file_size', sa.Integer(), nullable=True),
        sa.Column('mime_type', sa.String(length=100), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['observation_id'], ['daily_round_observations.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    # Add daily_round_observation_id column to capas
    op.add_column('capas', sa.Column('daily_round_observation_id', sa.UUID(), nullable=True))
    op.create_foreign_key('fk_capas_daily_round_observation_id', 'capas', 'daily_round_observations', ['daily_round_observation_id'], ['id'], ondelete='SET NULL')


def downgrade() -> None:
    op.drop_constraint('fk_capas_daily_round_observation_id', 'capas', type_='foreignkey')
    op.drop_column('capas', 'daily_round_observation_id')
    op.drop_table('daily_round_observation_media')
    op.drop_table('daily_round_observations')
    op.drop_table('daily_rounds')
    op.drop_table('master_observations')
