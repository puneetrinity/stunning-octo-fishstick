"""Initial database schema

Revision ID: 001
Revises: 
Create Date: 2024-12-16 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create users table
    op.create_table(
        'users',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=sa.text('gen_random_uuid()')),
        sa.Column('email', sa.String(255), nullable=False, unique=True, index=True),
        sa.Column('password_hash', sa.String(255), nullable=False),
        sa.Column('full_name', sa.String(255), nullable=True),
        sa.Column('company_name', sa.String(255), nullable=True),
        sa.Column('plan_type', sa.Enum('starter', 'professional', 'agency', 'enterprise', name='plantype'), nullable=False, default='starter'),
        sa.Column('is_active', sa.Boolean(), nullable=False, default=True),
        sa.Column('is_verified', sa.Boolean(), nullable=False, default=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('last_login', sa.DateTime(timezone=True), nullable=True),
    )
    
    # Create tracked_brands table
    op.create_table(
        'tracked_brands',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=sa.text('gen_random_uuid()')),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('aliases', sa.ARRAY(sa.String()), nullable=False, default=sa.text("'{}'::text[]")),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('website_url', sa.String(500), nullable=True),
        sa.Column('is_primary', sa.Boolean(), nullable=False, default=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, default=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    )
    
    # Create query_templates table
    op.create_table(
        'query_templates',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=sa.text('gen_random_uuid()')),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('title', sa.String(255), nullable=False),
        sa.Column('query_text', sa.Text(), nullable=False),
        sa.Column('category', sa.String(100), nullable=True),
        sa.Column('priority', sa.Enum('1', '2', '3', '4', name='querypriority'), nullable=False, default='2'),
        sa.Column('is_active', sa.Boolean(), nullable=False, default=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    )
    
    # Create query_results table
    op.create_table(
        'query_results',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=sa.text('gen_random_uuid()')),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('query_template_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('query_templates.id'), nullable=True),
        sa.Column('query_text', sa.Text(), nullable=False),
        sa.Column('platform', sa.Enum('openai', 'anthropic', 'google', 'perplexity', name='platform'), nullable=False),
        sa.Column('response_text', sa.Text(), nullable=False),
        sa.Column('response_time_ms', sa.Integer(), nullable=True),
        sa.Column('status', sa.String(50), nullable=False, default='completed'),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('executed_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    )
    
    # Create citations table
    op.create_table(
        'citations',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=sa.text('gen_random_uuid()')),
        sa.Column('query_result_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('query_results.id'), nullable=False),
        sa.Column('brand_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('tracked_brands.id'), nullable=False),
        sa.Column('brand_name', sa.String(255), nullable=False),
        sa.Column('mentioned', sa.Boolean(), nullable=False),
        sa.Column('position', sa.Integer(), nullable=True),
        sa.Column('context', sa.Text(), nullable=True),
        sa.Column('sentence', sa.Text(), nullable=True),
        sa.Column('sentiment_score', sa.Numeric(3, 2), nullable=True),
        sa.Column('prominence_score', sa.Numeric(3, 1), nullable=True),
        sa.Column('confidence_score', sa.Numeric(3, 2), nullable=True),
        sa.Column('entity_type', sa.String(50), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    )
    
    # Create subscriptions table
    op.create_table(
        'subscriptions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=sa.text('gen_random_uuid()')),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('stripe_subscription_id', sa.String(255), nullable=True, unique=True),
        sa.Column('stripe_customer_id', sa.String(255), nullable=True),
        sa.Column('plan_type', sa.Enum('starter', 'professional', 'agency', 'enterprise', name='plantype'), nullable=False),
        sa.Column('status', sa.Enum('active', 'canceled', 'past_due', 'unpaid', 'trialing', name='subscriptionstatus'), nullable=False, default='active'),
        sa.Column('price_cents', sa.Integer(), nullable=False),
        sa.Column('currency', sa.String(3), nullable=False, default='USD'),
        sa.Column('billing_cycle', sa.String(20), nullable=False, default='monthly'),
        sa.Column('trial_end', sa.DateTime(timezone=True), nullable=True),
        sa.Column('current_period_start', sa.DateTime(timezone=True), nullable=False),
        sa.Column('current_period_end', sa.DateTime(timezone=True), nullable=False),
        sa.Column('canceled_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    )
    
    # Create usage_records table
    op.create_table(
        'usage_records',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=sa.text('gen_random_uuid()')),
        sa.Column('subscription_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('subscriptions.id'), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('period_start', sa.DateTime(timezone=True), nullable=False),
        sa.Column('period_end', sa.DateTime(timezone=True), nullable=False),
        sa.Column('queries_executed', sa.Integer(), nullable=False, default=0),
        sa.Column('brands_tracked', sa.Integer(), nullable=False, default=0),
        sa.Column('api_calls_made', sa.Integer(), nullable=False, default=0),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    )
    
    # Create indexes for performance
    op.create_index('idx_citations_brand_platform', 'citations', ['brand_name', 'query_result_id'])
    op.create_index('idx_query_results_user_date', 'query_results', ['user_id', 'executed_at'])
    op.create_index('idx_citations_mentioned_created', 'citations', ['mentioned', 'created_at'])
    op.create_index('idx_tracked_brands_user_active', 'tracked_brands', ['user_id', 'is_active'])
    op.create_index('idx_query_templates_user_active', 'query_templates', ['user_id', 'is_active'])
    op.create_index('idx_subscriptions_user_status', 'subscriptions', ['user_id', 'status'])
    op.create_index('idx_usage_records_user_period', 'usage_records', ['user_id', 'period_start', 'period_end'])


def downgrade() -> None:
    # Drop indexes
    op.drop_index('idx_usage_records_user_period')
    op.drop_index('idx_subscriptions_user_status')
    op.drop_index('idx_query_templates_user_active')
    op.drop_index('idx_tracked_brands_user_active')
    op.drop_index('idx_citations_mentioned_created')
    op.drop_index('idx_query_results_user_date')
    op.drop_index('idx_citations_brand_platform')
    
    # Drop tables
    op.drop_table('usage_records')
    op.drop_table('subscriptions')
    op.drop_table('citations')
    op.drop_table('query_results')
    op.drop_table('query_templates')
    op.drop_table('tracked_brands')
    op.drop_table('users')
    
    # Drop enums
    op.execute('DROP TYPE IF EXISTS subscriptionstatus')
    op.execute('DROP TYPE IF EXISTS platform')
    op.execute('DROP TYPE IF EXISTS querypriority')
    op.execute('DROP TYPE IF EXISTS plantype')