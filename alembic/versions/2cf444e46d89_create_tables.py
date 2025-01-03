"""create tables

Revision ID: 2cf444e46d89
Revises: 
Create Date: 2024-12-31 01:28:43.912300

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '2cf444e46d89'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('admin_users',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('email', sa.String(length=255), nullable=True),
    sa.Column('name', sa.String(length=255), nullable=True),
    sa.Column('password', sa.String(length=255), nullable=False),
    sa.Column('created_by', sa.Integer(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('updated_by', sa.Integer(), nullable=True),
    sa.Column('updated_at', sa.DateTime(), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_admin_users_email'), 'admin_users', ['email'], unique=True)
    op.create_index(op.f('ix_admin_users_id'), 'admin_users', ['id'], unique=False)
    op.create_table('devices',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('device_id', sa.String(length=255), nullable=True),
    sa.Column('name', sa.String(length=255), nullable=True),
    sa.Column('created_by', sa.Integer(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('updated_by', sa.Integer(), nullable=True),
    sa.Column('updated_at', sa.DateTime(), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_devices_device_id'), 'devices', ['device_id'], unique=True)
    op.create_index(op.f('ix_devices_id'), 'devices', ['id'], unique=False)
    op.create_table('zitadel_users',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('email', sa.String(length=255), nullable=True),
    sa.Column('zitadel_user_id', sa.String(length=255), nullable=True),
    sa.Column('tenant_id', sa.String(length=255), nullable=True),
    sa.Column('name', sa.String(length=255), nullable=True),
    sa.Column('pin', sa.String(length=255), nullable=True),
    sa.Column('created_by', sa.Integer(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('updated_by', sa.Integer(), nullable=True),
    sa.Column('updated_at', sa.DateTime(), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_zitadel_users_email'), 'zitadel_users', ['email'], unique=True)
    op.create_index(op.f('ix_zitadel_users_id'), 'zitadel_users', ['id'], unique=False)
    op.create_index(op.f('ix_zitadel_users_zitadel_user_id'), 'zitadel_users', ['zitadel_user_id'], unique=True)
    op.create_table('device_users',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('device_id', sa.Integer(), nullable=False),
    sa.Column('zitadel_user_id', sa.Integer(), nullable=False),
    sa.Column('device_username', sa.String(length=255), nullable=False),
    sa.Column('created_by', sa.Integer(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('updated_by', sa.Integer(), nullable=True),
    sa.Column('updated_at', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['device_id'], ['devices.id'], ),
    sa.ForeignKeyConstraint(['zitadel_user_id'], ['zitadel_users.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_device_users_id'), 'device_users', ['id'], unique=False)
    op.create_table('device_activity_logs',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('zitadel_user_id', sa.Integer(), nullable=True),
    sa.Column('device_id', sa.Integer(), nullable=True),
    sa.Column('device_username', sa.Integer(), nullable=True),
    sa.Column('login_as', sa.String(length=255), nullable=True),
    sa.Column('activity_type', sa.String(length=255), nullable=False),
    sa.Column('timestamp', sa.DateTime(), nullable=True),
    sa.Column('created_by', sa.Integer(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('updated_by', sa.Integer(), nullable=True),
    sa.Column('updated_at', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['device_id'], ['devices.id'], ),
    sa.ForeignKeyConstraint(['device_username'], ['device_users.id'], ),
    sa.ForeignKeyConstraint(['zitadel_user_id'], ['zitadel_users.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_device_activity_logs_id'), 'device_activity_logs', ['id'], unique=False)
    op.create_table('shared_users',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('device_user_id', sa.Integer(), nullable=False),
    sa.Column('shared_with_user_id', sa.Integer(), nullable=False),
    sa.Column('created_by', sa.Integer(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('updated_by', sa.Integer(), nullable=True),
    sa.Column('updated_at', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['device_user_id'], ['device_users.id'], ),
    sa.ForeignKeyConstraint(['shared_with_user_id'], ['zitadel_users.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_shared_users_id'), 'shared_users', ['id'], unique=False)
    op.create_table('admin_activity_logs',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('admin_user_id', sa.Integer(), nullable=True),
    sa.Column('endpoint', sa.String(length=255), nullable=False),
    sa.Column('action', sa.String(length=255), nullable=True),
    sa.Column('timestamp', sa.DateTime(), nullable=True),
    sa.Column('zitadel_user_id', sa.Integer(), nullable=True),
    sa.Column('device_id', sa.Integer(), nullable=True),
    sa.Column('device_user_id', sa.Integer(), nullable=True),
    sa.Column('shared_user_id', sa.Integer(), nullable=True),
    sa.Column('created_by', sa.Integer(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('updated_by', sa.Integer(), nullable=True),
    sa.Column('updated_at', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['admin_user_id'], ['admin_users.id'], ondelete='SET NULL'),
    sa.ForeignKeyConstraint(['device_id'], ['devices.id'], ),
    sa.ForeignKeyConstraint(['device_user_id'], ['device_users.id'], ),
    sa.ForeignKeyConstraint(['shared_user_id'], ['shared_users.id'], ),
    sa.ForeignKeyConstraint(['zitadel_user_id'], ['zitadel_users.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_admin_activity_logs_id'), 'admin_activity_logs', ['id'], unique=False)
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(op.f('ix_admin_activity_logs_id'), table_name='admin_activity_logs')
    op.drop_table('admin_activity_logs')
    op.drop_index(op.f('ix_shared_users_id'), table_name='shared_users')
    op.drop_table('shared_users')
    op.drop_index(op.f('ix_device_activity_logs_id'), table_name='device_activity_logs')
    op.drop_table('device_activity_logs')
    op.drop_index(op.f('ix_device_users_id'), table_name='device_users')
    op.drop_table('device_users')
    op.drop_index(op.f('ix_zitadel_users_zitadel_user_id'), table_name='zitadel_users')
    op.drop_index(op.f('ix_zitadel_users_id'), table_name='zitadel_users')
    op.drop_index(op.f('ix_zitadel_users_email'), table_name='zitadel_users')
    op.drop_table('zitadel_users')
    op.drop_index(op.f('ix_devices_id'), table_name='devices')
    op.drop_index(op.f('ix_devices_device_id'), table_name='devices')
    op.drop_table('devices')
    op.drop_index(op.f('ix_admin_users_id'), table_name='admin_users')
    op.drop_index(op.f('ix_admin_users_email'), table_name='admin_users')
    op.drop_table('admin_users')
    # ### end Alembic commands ###
