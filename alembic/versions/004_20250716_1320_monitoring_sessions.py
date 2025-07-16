"""Add monitoring sessions table

Revision ID: 004
Revises: 003
Create Date: 2025-07-16 13:20:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '004'
down_revision = '003'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create monitoring_sessions table
    op.create_table(
        'monitoring_sessions',
        sa.Column('id', sa.String(100), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('brand_names', sa.String(1000), nullable=False),
        sa.Column('category', sa.String(100), nullable=False),
        sa.Column('competitors', sa.String(1000), nullable=True),
        sa.Column('include_reddit', sa.Boolean(), nullable=False, default=True),
        sa.Column('include_chatgpt', sa.Boolean(), nullable=False, default=True),
        sa.Column('time_range', sa.String(20), nullable=False, default='week'),
        sa.Column('status', sa.String(20), nullable=False, default='running'),
        sa.Column('progress_percentage', sa.Numeric(5, 2), nullable=True),
        sa.Column('current_task', sa.String(200), nullable=True),
        sa.Column('results_data', sa.Text(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
    )
    
    # Create indexes for performance
    op.create_index('idx_monitoring_sessions_user', 'monitoring_sessions', ['user_id'])
    op.create_index('idx_monitoring_sessions_status', 'monitoring_sessions', ['status'])
    op.create_index('idx_monitoring_sessions_created', 'monitoring_sessions', ['created_at'])
    op.create_index('idx_monitoring_sessions_user_status', 'monitoring_sessions', ['user_id', 'status'])


def downgrade() -> None:
    # Drop indexes
    op.drop_index('idx_monitoring_sessions_user_status')
    op.drop_index('idx_monitoring_sessions_created')
    op.drop_index('idx_monitoring_sessions_status')
    op.drop_index('idx_monitoring_sessions_user')
    
    # Drop table
    op.drop_table('monitoring_sessions')