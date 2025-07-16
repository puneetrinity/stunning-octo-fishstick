"""Add review site mentions table

Revision ID: 005
Revises: 004
Create Date: 2025-07-16 13:40:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '005'
down_revision = '004'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create review_site_mentions table
    op.create_table(
        'review_site_mentions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=sa.text('gen_random_uuid()')),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('review_site_name', sa.String(100), nullable=False),
        sa.Column('brand_name', sa.String(255), nullable=False),
        sa.Column('mention_url', sa.String(1000), nullable=False),
        sa.Column('mention_title', sa.String(500), nullable=False),
        sa.Column('mention_content', sa.Text(), nullable=True),
        sa.Column('rating', sa.Numeric(3, 1), nullable=True),
        sa.Column('review_date', sa.DateTime(timezone=True), nullable=False),
        sa.Column('author', sa.String(255), nullable=False),
        sa.Column('sentiment_score', sa.Numeric(3, 2), nullable=True),
        sa.Column('ai_citation_potential', sa.Numeric(3, 2), nullable=True),
        sa.Column('discovered_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('mention_type', sa.String(50), nullable=False, default='listing'),
        sa.Column('authority_score', sa.Integer(), nullable=True),
        sa.Column('estimated_traffic_value', sa.Numeric(10, 2), nullable=True),
        sa.Column('is_verified', sa.Boolean(), nullable=False, default=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    )
    
    # Create indexes for performance
    op.create_index('idx_review_site_mentions_user_brand', 'review_site_mentions', ['user_id', 'brand_name'])
    op.create_index('idx_review_site_mentions_site', 'review_site_mentions', ['review_site_name'])
    op.create_index('idx_review_site_mentions_url_brand', 'review_site_mentions', ['mention_url', 'brand_name'])
    op.create_index('idx_review_site_mentions_discovered', 'review_site_mentions', ['discovered_at'])
    op.create_index('idx_review_site_mentions_rating', 'review_site_mentions', ['rating'])
    op.create_index('idx_review_site_mentions_sentiment', 'review_site_mentions', ['sentiment_score'])
    
    # Create unique constraint to prevent duplicate mentions
    op.create_unique_constraint('uq_review_site_mentions_url_brand', 'review_site_mentions', ['mention_url', 'brand_name'])
    
    # Create review_site_roi_tracking table for investment tracking
    op.create_table(
        'review_site_roi_tracking',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=sa.text('gen_random_uuid()')),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('brand_name', sa.String(255), nullable=False),
        sa.Column('review_site_name', sa.String(100), nullable=False),
        sa.Column('investment_amount', sa.Numeric(10, 2), nullable=False),
        sa.Column('investment_date', sa.DateTime(timezone=True), nullable=False),
        sa.Column('investment_type', sa.String(50), nullable=False),  # 'listing', 'featured', 'sponsored'
        sa.Column('expected_roi', sa.Numeric(5, 2), nullable=True),
        sa.Column('actual_roi', sa.Numeric(5, 2), nullable=True),
        sa.Column('mentions_generated', sa.Integer(), nullable=False, default=0),
        sa.Column('ai_citations_tracked', sa.Integer(), nullable=False, default=0),
        sa.Column('estimated_traffic_value', sa.Numeric(10, 2), nullable=True),
        sa.Column('payback_period_months', sa.Numeric(5, 2), nullable=True),
        sa.Column('status', sa.String(50), nullable=False, default='active'),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    )
    
    # Create indexes for ROI tracking
    op.create_index('idx_review_site_roi_user_brand', 'review_site_roi_tracking', ['user_id', 'brand_name'])
    op.create_index('idx_review_site_roi_site', 'review_site_roi_tracking', ['review_site_name'])
    op.create_index('idx_review_site_roi_date', 'review_site_roi_tracking', ['investment_date'])
    op.create_index('idx_review_site_roi_status', 'review_site_roi_tracking', ['status'])
    op.create_index('idx_review_site_roi_roi', 'review_site_roi_tracking', ['actual_roi'])


def downgrade() -> None:
    # Drop indexes for ROI tracking
    op.drop_index('idx_review_site_roi_roi')
    op.drop_index('idx_review_site_roi_status')
    op.drop_index('idx_review_site_roi_date')
    op.drop_index('idx_review_site_roi_site')
    op.drop_index('idx_review_site_roi_user_brand')
    
    # Drop ROI tracking table
    op.drop_table('review_site_roi_tracking')
    
    # Drop indexes for mentions
    op.drop_index('idx_review_site_mentions_sentiment')
    op.drop_index('idx_review_site_mentions_rating')
    op.drop_index('idx_review_site_mentions_discovered')
    op.drop_index('idx_review_site_mentions_url_brand')
    op.drop_index('idx_review_site_mentions_site')
    op.drop_index('idx_review_site_mentions_user_brand')
    
    # Drop unique constraint
    op.drop_constraint('uq_review_site_mentions_url_brand', 'review_site_mentions')
    
    # Drop mentions table
    op.drop_table('review_site_mentions')