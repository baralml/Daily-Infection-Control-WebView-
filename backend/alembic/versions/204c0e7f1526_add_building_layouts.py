"""add_building_layouts

Revision ID: 204c0e7f1526
Revises: 89d0d8f11b28
Create Date: 2026-07-05 14:11:53.663611

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '204c0e7f1526'
down_revision: Union[str, None] = '89d0d8f11b28'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Create layout tables
    op.create_table('buildings',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name')
    )
    op.create_table('building_floors',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('building_id', sa.UUID(), nullable=False),
        sa.Column('floor_name', sa.String(length=50), nullable=False),
        sa.Column('order_index', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['building_id'], ['buildings.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_table('building_departments',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('floor_id', sa.UUID(), nullable=False),
        sa.Column('department_id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['department_id'], ['departments.id'], ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['floor_id'], ['building_floors.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_table('building_rooms',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('building_department_id', sa.UUID(), nullable=False),
        sa.Column('room_number', sa.String(length=50), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['building_department_id'], ['building_departments.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_table('daily_round_floor_states',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('round_id', sa.UUID(), nullable=False),
        sa.Column('floor_id', sa.UUID(), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='BLUE'),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['floor_id'], ['building_floors.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['round_id'], ['daily_rounds.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('round_id', 'floor_id', name='uq_round_floor_state')
    )

    # 2. Modify daily_rounds table
    op.add_column('daily_rounds', sa.Column('building_id', sa.UUID(), nullable=True))
    op.create_foreign_key('fk_daily_rounds_building_id', 'daily_rounds', 'buildings', ['building_id'], ['id'], ondelete='SET NULL')
    op.alter_column('daily_rounds', 'floor', existing_type=sa.String(length=50), nullable=True)
    op.alter_column('daily_rounds', 'department_id', existing_type=sa.Integer(), nullable=True)

    # 3. Modify daily_round_observations table
    op.add_column('daily_round_observations', sa.Column('floor_name', sa.String(length=50), nullable=True))
    op.add_column('daily_round_observations', sa.Column('department_id', sa.Integer(), nullable=True))
    op.add_column('daily_round_observations', sa.Column('floor_id', sa.UUID(), nullable=True))
    op.add_column('daily_round_observations', sa.Column('building_department_id', sa.UUID(), nullable=True))
    
    op.create_foreign_key('fk_obs_floor_id', 'daily_round_observations', 'building_floors', ['floor_id'], ['id'], ondelete='SET NULL')
    op.create_foreign_key('fk_obs_building_department_id', 'daily_round_observations', 'building_departments', ['building_department_id'], ['id'], ondelete='SET NULL')
    op.create_foreign_key('fk_obs_department_id', 'daily_round_observations', 'departments', ['department_id'], ['id'], ondelete='RESTRICT')


def downgrade() -> None:
    op.drop_constraint('fk_obs_department_id', 'daily_round_observations', type_='foreignkey')
    op.drop_constraint('fk_obs_building_department_id', 'daily_round_observations', type_='foreignkey')
    op.drop_constraint('fk_obs_floor_id', 'daily_round_observations', type_='foreignkey')
    
    op.drop_column('daily_round_observations', 'building_department_id')
    op.drop_column('daily_round_observations', 'floor_id')
    op.drop_column('daily_round_observations', 'department_id')
    op.drop_column('daily_round_observations', 'floor_name')

    op.alter_column('daily_rounds', 'department_id', existing_type=sa.Integer(), nullable=False)
    op.alter_column('daily_rounds', 'floor', existing_type=sa.String(length=50), nullable=False)
    op.drop_constraint('fk_daily_rounds_building_id', 'daily_rounds', type_='foreignkey')
    op.drop_column('daily_rounds', 'building_id')

    op.drop_table('daily_round_floor_states')
    op.drop_table('building_rooms')
    op.drop_table('building_departments')
    op.drop_table('building_floors')
    op.drop_table('buildings')
