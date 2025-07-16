"""Add authority sources and mentions tables

Revision ID: 007
Revises: 006
Create Date: 2025-07-16 14:30:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '007'
down_revision = '006'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Check if table exists before creating
    from sqlalchemy import inspect
    conn = op.get_bind()
    inspector = inspect(conn)
    
    # Create authority_sources table for source configuration (if it doesn't exist)
    if 'authority_sources' not in inspector.get_table_names():
        op.create_table(
        'authority_sources',
        sa.Column('id', sa.String(100), primary_key=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('domain', sa.String(255), nullable=False),
        sa.Column('industry', sa.String(100), nullable=False),
        sa.Column('source_type', sa.String(50), nullable=False),  # news_publication, industry_blog, etc.
        sa.Column('authority_level', sa.String(20), nullable=False),  # tier_1, tier_2, etc.
        sa.Column('authority_score', sa.Integer(), nullable=False),
        sa.Column('ai_citation_frequency', sa.Numeric(3, 2), nullable=False),
        sa.Column('content_types', sa.Text(), nullable=True),  # JSON array
        sa.Column('contact_email', sa.String(255), nullable=True),
        sa.Column('submission_guidelines', sa.Text(), nullable=True),
        sa.Column('average_response_time', sa.Integer(), nullable=True),  # days
        sa.Column('success_rate', sa.Numeric(3, 2), nullable=True),
        sa.Column('cost_estimate', sa.String(100), nullable=True),
        sa.Column('scraping_enabled', sa.Boolean(), nullable=False, default=True),
        sa.Column('api_available', sa.Boolean(), nullable=False, default=False),
        sa.Column('rss_feed', sa.String(500), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, default=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    )
    
    # Create indexes for authority sources (if table exists and indexes don't exist)
    if 'authority_sources' in inspector.get_table_names():
        existing_indexes = [idx['name'] for idx in inspector.get_indexes('authority_sources')]
        
        if 'idx_authority_sources_industry' not in existing_indexes:
            op.create_index('idx_authority_sources_industry', 'authority_sources', ['industry', 'is_active'])
        if 'idx_authority_sources_authority' not in existing_indexes:
            op.create_index('idx_authority_sources_authority', 'authority_sources', ['authority_level', 'authority_score'])
        if 'idx_authority_sources_domain' not in existing_indexes:
            op.create_index('idx_authority_sources_domain', 'authority_sources', ['domain'])
        
        # Create unique constraint for domain (if it doesn't exist)
        existing_constraints = [c['name'] for c in inspector.get_unique_constraints('authority_sources')]
        if 'uq_authority_sources_domain' not in existing_constraints:
            op.create_unique_constraint('uq_authority_sources_domain', 'authority_sources', ['domain'])
    
    # Create authority_mentions table for tracking mentions (if it doesn't exist)
    if 'authority_mentions' not in inspector.get_table_names():
        op.create_table(
        'authority_mentions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=sa.text('gen_random_uuid()')),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('authority_source_id', sa.String(100), sa.ForeignKey('authority_sources.id'), nullable=False),
        sa.Column('brand_name', sa.String(255), nullable=False),
        sa.Column('mention_url', sa.String(1000), nullable=False),
        sa.Column('mention_title', sa.String(500), nullable=False),
        sa.Column('mention_content', sa.Text(), nullable=True),
        sa.Column('publish_date', sa.DateTime(timezone=True), nullable=False),
        sa.Column('author', sa.String(255), nullable=True),
        sa.Column('mention_context', sa.Text(), nullable=True),
        sa.Column('ai_citation_potential', sa.Numeric(3, 2), nullable=False),
        sa.Column('prominence_score', sa.Numeric(3, 2), nullable=False),
        sa.Column('sentiment_score', sa.Numeric(3, 2), nullable=True),
        sa.Column('estimated_reach', sa.Integer(), nullable=True),
        sa.Column('backlink_value', sa.Numeric(6, 2), nullable=True),
        sa.Column('discovered_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('is_verified', sa.Boolean(), nullable=False, default=False),
        sa.Column('verification_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('verification_notes', sa.Text(), nullable=True),
    )
    
    # Create indexes for authority mentions (if table exists and indexes don't exist)
    if 'authority_mentions' in inspector.get_table_names():
        existing_mentions_indexes = [idx['name'] for idx in inspector.get_indexes('authority_mentions')]
        
        if 'idx_authority_mentions_user_brand' not in existing_mentions_indexes:
            op.create_index('idx_authority_mentions_user_brand', 'authority_mentions', ['user_id', 'brand_name'])
        if 'idx_authority_mentions_source' not in existing_mentions_indexes:
            op.create_index('idx_authority_mentions_source', 'authority_mentions', ['authority_source_id'])
        if 'idx_authority_mentions_url_brand' not in existing_mentions_indexes:
            op.create_index('idx_authority_mentions_url_brand', 'authority_mentions', ['mention_url', 'brand_name'])
        if 'idx_authority_mentions_discovered' not in existing_mentions_indexes:
            op.create_index('idx_authority_mentions_discovered', 'authority_mentions', ['discovered_at'])
        if 'idx_authority_mentions_publish_date' not in existing_mentions_indexes:
            op.create_index('idx_authority_mentions_publish_date', 'authority_mentions', ['publish_date'])
        if 'idx_authority_mentions_citation_potential' not in existing_mentions_indexes:
            op.create_index('idx_authority_mentions_citation_potential', 'authority_mentions', ['ai_citation_potential'])
        if 'idx_authority_mentions_verified' not in existing_mentions_indexes:
            op.create_index('idx_authority_mentions_verified', 'authority_mentions', ['is_verified'])
        
        # Create unique constraint to prevent duplicate mentions (if it doesn't exist)
        existing_mentions_constraints = [c['name'] for c in inspector.get_unique_constraints('authority_mentions')]
        if 'uq_authority_mentions_url_brand' not in existing_mentions_constraints:
            op.create_unique_constraint('uq_authority_mentions_url_brand', 'authority_mentions', ['mention_url', 'brand_name'])
    
    # Create authority_analytics table for aggregated insights (if it doesn't exist)
    if 'authority_analytics' not in inspector.get_table_names():
        op.create_table(
        'authority_analytics',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=sa.text('gen_random_uuid()')),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('brand_name', sa.String(255), nullable=False),
        sa.Column('analysis_period', sa.String(20), nullable=False),  # 'week', 'month', 'quarter'
        sa.Column('period_start', sa.DateTime(timezone=True), nullable=False),
        sa.Column('period_end', sa.DateTime(timezone=True), nullable=False),
        sa.Column('total_mentions', sa.Integer(), nullable=False, default=0),
        sa.Column('sources_covered', sa.Integer(), nullable=False, default=0),
        sa.Column('tier_1_mentions', sa.Integer(), nullable=False, default=0),
        sa.Column('tier_2_mentions', sa.Integer(), nullable=False, default=0),
        sa.Column('tier_3_mentions', sa.Integer(), nullable=False, default=0),
        sa.Column('avg_authority_score', sa.Numeric(5, 2), nullable=True),
        sa.Column('avg_citation_potential', sa.Numeric(3, 2), nullable=True),
        sa.Column('avg_sentiment_score', sa.Numeric(3, 2), nullable=True),
        sa.Column('total_estimated_reach', sa.Integer(), nullable=True),
        sa.Column('total_backlink_value', sa.Numeric(8, 2), nullable=True),
        sa.Column('source_diversity_score', sa.Numeric(3, 2), nullable=True),
        sa.Column('authority_distribution', sa.Text(), nullable=True),  # JSON
        sa.Column('top_sources', sa.Text(), nullable=True),  # JSON
        sa.Column('recommendations', sa.Text(), nullable=True),  # JSON
        sa.Column('calculated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    )
    
    # Create indexes for authority analytics (if table exists and indexes don't exist)
    if 'authority_analytics' in inspector.get_table_names():
        existing_analytics_indexes = [idx['name'] for idx in inspector.get_indexes('authority_analytics')]
        
        if 'idx_authority_analytics_user_brand' not in existing_analytics_indexes:
            op.create_index('idx_authority_analytics_user_brand', 'authority_analytics', ['user_id', 'brand_name'])
        if 'idx_authority_analytics_period' not in existing_analytics_indexes:
            op.create_index('idx_authority_analytics_period', 'authority_analytics', ['analysis_period', 'period_start'])
        if 'idx_authority_analytics_calculated' not in existing_analytics_indexes:
            op.create_index('idx_authority_analytics_calculated', 'authority_analytics', ['calculated_at'])
        
        # Create unique constraint for analytics (if it doesn't exist)
        existing_analytics_constraints = [c['name'] for c in inspector.get_unique_constraints('authority_analytics')]
        if 'uq_authority_analytics_user_brand_period' not in existing_analytics_constraints:
            op.create_unique_constraint(
                'uq_authority_analytics_user_brand_period', 
                'authority_analytics', 
                ['user_id', 'brand_name', 'analysis_period', 'period_start']
            )
    
    # Create authority_outreach table for tracking outreach efforts (if it doesn't exist)
    if 'authority_outreach' not in inspector.get_table_names():
        op.create_table(
        'authority_outreach',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=sa.text('gen_random_uuid()')),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('authority_source_id', sa.String(100), sa.ForeignKey('authority_sources.id'), nullable=False),
        sa.Column('brand_name', sa.String(255), nullable=False),
        sa.Column('outreach_type', sa.String(50), nullable=False),  # 'guest_post', 'press_release', 'expert_quote'
        sa.Column('contact_person', sa.String(255), nullable=True),
        sa.Column('contact_email', sa.String(255), nullable=True),
        sa.Column('subject_line', sa.String(500), nullable=True),
        sa.Column('message_content', sa.Text(), nullable=True),
        sa.Column('status', sa.String(50), nullable=False, default='planned'),  # 'planned', 'sent', 'replied', 'accepted', 'rejected'
        sa.Column('sent_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('reply_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('reply_content', sa.Text(), nullable=True),
        sa.Column('outcome', sa.String(50), nullable=True),  # 'published', 'featured', 'quoted', 'declined'
        sa.Column('published_url', sa.String(1000), nullable=True),
        sa.Column('publish_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('estimated_value', sa.Numeric(8, 2), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    )
    
    # Create indexes for authority outreach (if table exists and indexes don't exist)
    if 'authority_outreach' in inspector.get_table_names():
        existing_outreach_indexes = [idx['name'] for idx in inspector.get_indexes('authority_outreach')]
        
        if 'idx_authority_outreach_user_brand' not in existing_outreach_indexes:
            op.create_index('idx_authority_outreach_user_brand', 'authority_outreach', ['user_id', 'brand_name'])
        if 'idx_authority_outreach_source' not in existing_outreach_indexes:
            op.create_index('idx_authority_outreach_source', 'authority_outreach', ['authority_source_id'])
        if 'idx_authority_outreach_status' not in existing_outreach_indexes:
            op.create_index('idx_authority_outreach_status', 'authority_outreach', ['status'])
        if 'idx_authority_outreach_type' not in existing_outreach_indexes:
            op.create_index('idx_authority_outreach_type', 'authority_outreach', ['outreach_type'])
        if 'idx_authority_outreach_sent' not in existing_outreach_indexes:
            op.create_index('idx_authority_outreach_sent', 'authority_outreach', ['sent_at'])


def downgrade() -> None:
    # Drop authority outreach table
    op.drop_index('idx_authority_outreach_sent')
    op.drop_index('idx_authority_outreach_type')
    op.drop_index('idx_authority_outreach_status')
    op.drop_index('idx_authority_outreach_source')
    op.drop_index('idx_authority_outreach_user_brand')
    op.drop_table('authority_outreach')
    
    # Drop authority analytics table
    op.drop_constraint('uq_authority_analytics_user_brand_period', 'authority_analytics')
    op.drop_index('idx_authority_analytics_calculated')
    op.drop_index('idx_authority_analytics_period')
    op.drop_index('idx_authority_analytics_user_brand')
    op.drop_table('authority_analytics')
    
    # Drop authority mentions table
    op.drop_constraint('uq_authority_mentions_url_brand', 'authority_mentions')
    op.drop_index('idx_authority_mentions_verified')
    op.drop_index('idx_authority_mentions_citation_potential')
    op.drop_index('idx_authority_mentions_publish_date')
    op.drop_index('idx_authority_mentions_discovered')
    op.drop_index('idx_authority_mentions_url_brand')
    op.drop_index('idx_authority_mentions_source')
    op.drop_index('idx_authority_mentions_user_brand')
    op.drop_table('authority_mentions')
    
    # Drop authority sources table
    op.drop_constraint('uq_authority_sources_domain', 'authority_sources')
    op.drop_index('idx_authority_sources_domain')
    op.drop_index('idx_authority_sources_authority')
    op.drop_index('idx_authority_sources_industry')
    op.drop_table('authority_sources')