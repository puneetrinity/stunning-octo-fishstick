"""Add Reddit mentions table

Revision ID: 003
Revises: 002
Create Date: 2025-07-16 13:08:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '003'
down_revision = '002'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create reddit_mentions table
    op.create_table(
        'reddit_mentions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=sa.text('gen_random_uuid()')),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('brand_name', sa.String(255), nullable=False),
        sa.Column('subreddit', sa.String(100), nullable=False),
        sa.Column('post_id', sa.String(20), nullable=False),
        sa.Column('comment_id', sa.String(20), nullable=True),
        sa.Column('title', sa.String(500), nullable=False),
        sa.Column('content', sa.Text(), nullable=True),
        sa.Column('url', sa.String(1000), nullable=False),
        sa.Column('score', sa.Integer(), nullable=False, default=0),
        sa.Column('created_utc', sa.DateTime(timezone=True), nullable=False),
        sa.Column('author', sa.String(100), nullable=False),
        sa.Column('mention_context', sa.Text(), nullable=True),
        sa.Column('sentiment_score', sa.Numeric(3, 2), nullable=True),
        sa.Column('upvotes', sa.Integer(), nullable=False, default=0),
        sa.Column('is_post', sa.Boolean(), nullable=False, default=True),
        sa.Column('discovered_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    )
    
    # Create indexes for performance
    op.create_index('idx_reddit_mentions_user_brand', 'reddit_mentions', ['user_id', 'brand_name'])
    op.create_index('idx_reddit_mentions_subreddit', 'reddit_mentions', ['subreddit'])
    op.create_index('idx_reddit_mentions_post_brand', 'reddit_mentions', ['post_id', 'brand_name'])
    op.create_index('idx_reddit_mentions_created', 'reddit_mentions', ['created_utc'])
    op.create_index('idx_reddit_mentions_score', 'reddit_mentions', ['score'])
    
    # Create unique constraint to prevent duplicate mentions
    op.create_unique_constraint('uq_reddit_mentions_post_brand', 'reddit_mentions', ['post_id', 'brand_name'])


def downgrade() -> None:
    # Drop indexes
    op.drop_index('idx_reddit_mentions_score')
    op.drop_index('idx_reddit_mentions_created')
    op.drop_index('idx_reddit_mentions_post_brand')
    op.drop_index('idx_reddit_mentions_subreddit')
    op.drop_index('idx_reddit_mentions_user_brand')
    
    # Drop unique constraint
    op.drop_constraint('uq_reddit_mentions_post_brand', 'reddit_mentions')
    
    # Drop table
    op.drop_table('reddit_mentions')