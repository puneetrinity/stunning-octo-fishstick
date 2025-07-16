"""Add dual approach models for agencies and brands

Revision ID: 002
Revises: 001
Create Date: 2024-12-16 15:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = '002'
down_revision = '001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create enum types first
    op.execute("CREATE TYPE usertype AS ENUM ('brand', 'agency')")
    
    # Update user table to support dual approach
    op.add_column('users', sa.Column('user_type', sa.Enum('brand', 'agency', name='usertype'), nullable=False, server_default='brand'))
    
    # Update plan_type enum to support new tiers
    op.execute("ALTER TYPE plantype ADD VALUE 'brand_starter'")
    op.execute("ALTER TYPE plantype ADD VALUE 'brand_professional'")
    op.execute("ALTER TYPE plantype ADD VALUE 'agency_starter'")
    op.execute("ALTER TYPE plantype ADD VALUE 'agency_pro'")
    op.execute("ALTER TYPE plantype ADD VALUE 'agency_enterprise'")
    
    # Create clients table for agencies
    op.create_table(
        'clients',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=sa.text('gen_random_uuid()')),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('company_name', sa.String(255), nullable=False),
        sa.Column('website_url', sa.String(500), nullable=True),
        sa.Column('industry', sa.String(100), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('contact_email', sa.String(255), nullable=True),
        sa.Column('contact_name', sa.String(255), nullable=True),
        sa.Column('status', sa.String(20), nullable=False, default='active'),
        sa.Column('monthly_budget', sa.String(50), nullable=True),
        sa.Column('onboarding_completed', sa.Boolean(), nullable=False, default=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    )
    
    # Create client_brands table
    op.create_table(
        'client_brands',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=sa.text('gen_random_uuid()')),
        sa.Column('client_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('clients.id'), nullable=False),
        sa.Column('brand_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('tracked_brands.id'), nullable=False),
        sa.Column('is_primary', sa.Boolean(), nullable=False, default=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    )
    
    # Create client_reports table
    op.create_table(
        'client_reports',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=sa.text('gen_random_uuid()')),
        sa.Column('client_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('clients.id'), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('title', sa.String(255), nullable=False),
        sa.Column('report_type', sa.String(50), nullable=False),
        sa.Column('period_start', sa.DateTime(timezone=True), nullable=False),
        sa.Column('period_end', sa.DateTime(timezone=True), nullable=False),
        sa.Column('report_data', sa.Text(), nullable=False),
        sa.Column('is_white_labeled', sa.Boolean(), nullable=False, default=False),
        sa.Column('generated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    )
    
    # Create roi_investments table
    op.create_table(
        'roi_investments',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=sa.text('gen_random_uuid()')),
        sa.Column('client_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('clients.id'), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('investment_type', sa.String(50), nullable=False),
        sa.Column('platform', sa.String(100), nullable=False),
        sa.Column('investment_amount', sa.Numeric(10, 2), nullable=False),
        sa.Column('currency', sa.String(3), nullable=False, default='USD'),
        sa.Column('investment_date', sa.DateTime(timezone=True), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('expected_roi', sa.Numeric(5, 2), nullable=True),
        sa.Column('actual_roi', sa.Numeric(5, 2), nullable=True),
        sa.Column('status', sa.String(50), nullable=False, default='active'),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    )
    
    # Create roi_performance_metrics table
    op.create_table(
        'roi_performance_metrics',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=sa.text('gen_random_uuid()')),
        sa.Column('investment_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('roi_investments.id'), nullable=False),
        sa.Column('metric_date', sa.DateTime(timezone=True), nullable=False),
        sa.Column('mentions_generated', sa.Integer(), nullable=False, default=0),
        sa.Column('ai_citations', sa.Integer(), nullable=False, default=0),
        sa.Column('estimated_traffic', sa.Integer(), nullable=False, default=0),
        sa.Column('estimated_traffic_value', sa.Numeric(10, 2), nullable=False, default=0),
        sa.Column('brand_visibility_score', sa.Numeric(3, 1), nullable=True),
        sa.Column('sentiment_score', sa.Numeric(3, 2), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    )
    
    # Create review_sites table
    op.create_table(
        'review_sites',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=sa.text('gen_random_uuid()')),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('domain', sa.String(255), unique=True, nullable=False),
        sa.Column('category', sa.String(100), nullable=False),
        sa.Column('authority_score', sa.Integer(), nullable=True),
        sa.Column('average_cost_per_review', sa.Numeric(8, 2), nullable=True),
        sa.Column('ai_citation_frequency', sa.Numeric(3, 2), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, default=True),
        sa.Column('scraping_enabled', sa.Boolean(), nullable=False, default=False),
        sa.Column('api_available', sa.Boolean(), nullable=False, default=False),
        sa.Column('api_documentation', sa.Text(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    )
    
    # Create review_mentions table
    op.create_table(
        'review_mentions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=sa.text('gen_random_uuid()')),
        sa.Column('review_site_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('review_sites.id'), nullable=False),
        sa.Column('brand_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('tracked_brands.id'), nullable=False),
        sa.Column('mention_url', sa.String(1000), nullable=True),
        sa.Column('mention_title', sa.String(500), nullable=True),
        sa.Column('mention_content', sa.Text(), nullable=True),
        sa.Column('rating', sa.Numeric(3, 1), nullable=True),
        sa.Column('review_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('ai_citation_count', sa.Integer(), nullable=False, default=0),
        sa.Column('last_ai_citation', sa.DateTime(timezone=True), nullable=True),
        sa.Column('sentiment_score', sa.Numeric(3, 2), nullable=True),
        sa.Column('is_verified', sa.Boolean(), nullable=False, default=False),
        sa.Column('discovered_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    )
    
    # Create content_gaps table
    op.create_table(
        'content_gaps',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=sa.text('gen_random_uuid()')),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('client_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('clients.id'), nullable=True),
        sa.Column('title', sa.String(500), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('content_type', sa.String(50), nullable=False),
        sa.Column('industry', sa.String(100), nullable=True),
        sa.Column('target_keywords', sa.Text(), nullable=True),
        sa.Column('competitor_content', sa.Text(), nullable=True),
        sa.Column('opportunity_score', sa.Numeric(3, 1), nullable=True),
        sa.Column('ai_citation_potential', sa.Numeric(3, 1), nullable=True),
        sa.Column('difficulty_score', sa.Numeric(3, 1), nullable=True),
        sa.Column('status', sa.String(50), nullable=False, default='identified'),
        sa.Column('assigned_to', sa.String(255), nullable=True),
        sa.Column('due_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    )
    
    # Create content_recommendations table
    op.create_table(
        'content_recommendations',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=sa.text('gen_random_uuid()')),
        sa.Column('content_gap_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('content_gaps.id'), nullable=False),
        sa.Column('recommendation_type', sa.String(50), nullable=False),
        sa.Column('recommendation_text', sa.Text(), nullable=False),
        sa.Column('confidence_score', sa.Numeric(3, 2), nullable=True),
        sa.Column('ai_model_used', sa.String(100), nullable=True),
        sa.Column('is_approved', sa.Boolean(), nullable=False, default=False),
        sa.Column('feedback', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    )
    
    # Create competitor_content table
    op.create_table(
        'competitor_content',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=sa.text('gen_random_uuid()')),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('competitor_name', sa.String(255), nullable=False),
        sa.Column('competitor_domain', sa.String(255), nullable=True),
        sa.Column('content_url', sa.String(1000), nullable=True),
        sa.Column('content_title', sa.String(500), nullable=False),
        sa.Column('content_type', sa.String(50), nullable=False),
        sa.Column('content_summary', sa.Text(), nullable=True),
        sa.Column('publish_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('ai_citation_count', sa.Integer(), nullable=False, default=0),
        sa.Column('last_ai_citation', sa.DateTime(timezone=True), nullable=True),
        sa.Column('estimated_traffic', sa.Integer(), nullable=True),
        sa.Column('social_shares', sa.Integer(), nullable=False, default=0),
        sa.Column('backlinks_count', sa.Integer(), nullable=False, default=0),
        sa.Column('content_quality_score', sa.Numeric(3, 1), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, default=True),
        sa.Column('discovered_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    )
    
    # Create authority_sources table
    op.create_table(
        'authority_sources',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=sa.text('gen_random_uuid()')),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('domain', sa.String(255), unique=True, nullable=False),
        sa.Column('industry', sa.String(100), nullable=False),
        sa.Column('authority_score', sa.Integer(), nullable=True),
        sa.Column('ai_citation_frequency', sa.Numeric(3, 2), nullable=True),
        sa.Column('content_types', sa.Text(), nullable=True),
        sa.Column('contact_email', sa.String(255), nullable=True),
        sa.Column('submission_guidelines', sa.Text(), nullable=True),
        sa.Column('average_response_time', sa.Integer(), nullable=True),
        sa.Column('success_rate', sa.Numeric(3, 2), nullable=True),
        sa.Column('cost_estimate', sa.String(100), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, default=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    )
    
    # Create authority_mentions table
    op.create_table(
        'authority_mentions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=sa.text('gen_random_uuid()')),
        sa.Column('authority_source_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('authority_sources.id'), nullable=False),
        sa.Column('brand_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('tracked_brands.id'), nullable=False),
        sa.Column('mention_url', sa.String(1000), nullable=True),
        sa.Column('mention_title', sa.String(500), nullable=True),
        sa.Column('mention_content', sa.Text(), nullable=True),
        sa.Column('publish_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('ai_citation_count', sa.Integer(), nullable=False, default=0),
        sa.Column('last_ai_citation', sa.DateTime(timezone=True), nullable=True),
        sa.Column('sentiment_score', sa.Numeric(3, 2), nullable=True),
        sa.Column('prominence_score', sa.Numeric(3, 1), nullable=True),
        sa.Column('estimated_reach', sa.Integer(), nullable=True),
        sa.Column('is_verified', sa.Boolean(), nullable=False, default=False),
        sa.Column('discovered_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    )
    
    # Update usage_records table with new metrics
    op.add_column('usage_records', sa.Column('clients_managed', sa.Integer(), nullable=False, default=0))
    op.add_column('usage_records', sa.Column('reports_generated', sa.Integer(), nullable=False, default=0))
    op.add_column('usage_records', sa.Column('roi_calculations', sa.Integer(), nullable=False, default=0))
    op.add_column('usage_records', sa.Column('content_gaps_identified', sa.Integer(), nullable=False, default=0))
    op.add_column('usage_records', sa.Column('competitor_content_analyzed', sa.Integer(), nullable=False, default=0))
    
    # Create indexes for performance
    op.create_index('idx_clients_user_status', 'clients', ['user_id', 'status'])
    op.create_index('idx_client_brands_client', 'client_brands', ['client_id'])
    op.create_index('idx_client_reports_client_date', 'client_reports', ['client_id', 'generated_at'])
    op.create_index('idx_roi_investments_client', 'roi_investments', ['client_id'])
    op.create_index('idx_roi_performance_date', 'roi_performance_metrics', ['investment_id', 'metric_date'])
    op.create_index('idx_review_sites_domain', 'review_sites', ['domain'])
    op.create_index('idx_review_mentions_site_brand', 'review_mentions', ['review_site_id', 'brand_id'])
    op.create_index('idx_content_gaps_user', 'content_gaps', ['user_id', 'status'])
    op.create_index('idx_competitor_content_user', 'competitor_content', ['user_id', 'is_active'])
    op.create_index('idx_authority_sources_industry', 'authority_sources', ['industry', 'is_active'])
    op.create_index('idx_authority_mentions_source_brand', 'authority_mentions', ['authority_source_id', 'brand_id'])


def downgrade() -> None:
    # Drop indexes
    op.drop_index('idx_authority_mentions_source_brand')
    op.drop_index('idx_authority_sources_industry')
    op.drop_index('idx_competitor_content_user')
    op.drop_index('idx_content_gaps_user')
    op.drop_index('idx_review_mentions_site_brand')
    op.drop_index('idx_review_sites_domain')
    op.drop_index('idx_roi_performance_date')
    op.drop_index('idx_roi_investments_client')
    op.drop_index('idx_client_reports_client_date')
    op.drop_index('idx_client_brands_client')
    op.drop_index('idx_clients_user_status')
    
    # Drop columns from usage_records
    op.drop_column('usage_records', 'competitor_content_analyzed')
    op.drop_column('usage_records', 'content_gaps_identified')
    op.drop_column('usage_records', 'roi_calculations')
    op.drop_column('usage_records', 'reports_generated')
    op.drop_column('usage_records', 'clients_managed')
    
    # Drop tables
    op.drop_table('authority_mentions')
    op.drop_table('authority_sources')
    op.drop_table('competitor_content')
    op.drop_table('content_recommendations')
    op.drop_table('content_gaps')
    op.drop_table('review_mentions')
    op.drop_table('review_sites')
    op.drop_table('roi_performance_metrics')
    op.drop_table('roi_investments')
    op.drop_table('client_reports')
    op.drop_table('client_brands')
    op.drop_table('clients')
    
    # Drop user_type column
    op.drop_column('users', 'user_type')
    
    # Drop enums
    op.execute('DROP TYPE IF EXISTS usertype')