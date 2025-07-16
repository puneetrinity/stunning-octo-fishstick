"""Enhanced citations table with detailed extraction data

Revision ID: 006
Revises: 005
Create Date: 2025-07-16 14:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '006'
down_revision = '005'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add new columns to existing citations table (skip prominence_score and confidence_score as they already exist)
    op.add_column('citations', sa.Column('mention_text', sa.String(500), nullable=True))
    op.add_column('citations', sa.Column('mention_type', sa.String(50), nullable=True, default='direct'))
    op.add_column('citations', sa.Column('sentiment_type', sa.String(20), nullable=True, default='neutral'))
    op.add_column('citations', sa.Column('context_start', sa.Integer(), nullable=True))
    op.add_column('citations', sa.Column('context_end', sa.Integer(), nullable=True))
    op.add_column('citations', sa.Column('metadata', sa.Text(), nullable=True))
    
    # Create indexes for new columns
    op.create_index('idx_citations_mention_type', 'citations', ['mention_type'])
    op.create_index('idx_citations_sentiment_type', 'citations', ['sentiment_type'])
    
    # Create citation_analytics table for aggregated analytics
    op.create_table(
        'citation_analytics',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=sa.text('gen_random_uuid()')),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('brand_name', sa.String(255), nullable=False),
        sa.Column('analysis_period', sa.String(20), nullable=False),  # 'day', 'week', 'month'
        sa.Column('period_start', sa.DateTime(timezone=True), nullable=False),
        sa.Column('period_end', sa.DateTime(timezone=True), nullable=False),
        sa.Column('total_citations', sa.Integer(), nullable=False, default=0),
        sa.Column('total_mentions', sa.Integer(), nullable=False, default=0),
        sa.Column('platforms_covered', sa.Integer(), nullable=False, default=0),
        sa.Column('avg_sentiment_score', sa.Numeric(3, 2), nullable=True),
        sa.Column('avg_prominence_score', sa.Numeric(3, 2), nullable=True),
        sa.Column('avg_confidence_score', sa.Numeric(3, 2), nullable=True),
        sa.Column('positive_mentions', sa.Integer(), nullable=False, default=0),
        sa.Column('negative_mentions', sa.Integer(), nullable=False, default=0),
        sa.Column('neutral_mentions', sa.Integer(), nullable=False, default=0),
        sa.Column('mention_type_distribution', sa.Text(), nullable=True),  # JSON
        sa.Column('platform_distribution', sa.Text(), nullable=True),      # JSON
        sa.Column('top_contexts', sa.Text(), nullable=True),               # JSON
        sa.Column('calculated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    )
    
    # Create indexes for analytics
    op.create_index('idx_citation_analytics_user_brand', 'citation_analytics', ['user_id', 'brand_name'])
    op.create_index('idx_citation_analytics_period', 'citation_analytics', ['analysis_period', 'period_start'])
    op.create_index('idx_citation_analytics_calculated', 'citation_analytics', ['calculated_at'])
    
    # Create unique constraint for analytics
    op.create_unique_constraint(
        'uq_citation_analytics_user_brand_period', 
        'citation_analytics', 
        ['user_id', 'brand_name', 'analysis_period', 'period_start']
    )
    
    # Create brand_aliases table for better brand matching
    op.create_table(
        'brand_aliases',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=sa.text('gen_random_uuid()')),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('brand_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('tracked_brands.id'), nullable=False),
        sa.Column('alias', sa.String(255), nullable=False),
        sa.Column('alias_type', sa.String(50), nullable=False, default='manual'),  # 'manual', 'auto', 'domain'
        sa.Column('is_active', sa.Boolean(), nullable=False, default=True),
        sa.Column('confidence_score', sa.Numeric(3, 2), nullable=True),
        sa.Column('usage_count', sa.Integer(), nullable=False, default=0),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    )
    
    # Create indexes for brand aliases
    op.create_index('idx_brand_aliases_user_brand', 'brand_aliases', ['user_id', 'brand_id'])
    op.create_index('idx_brand_aliases_alias', 'brand_aliases', ['alias'])
    op.create_index('idx_brand_aliases_active', 'brand_aliases', ['is_active'])
    
    # Create unique constraint for aliases
    op.create_unique_constraint('uq_brand_aliases_brand_alias', 'brand_aliases', ['brand_id', 'alias'])


def downgrade() -> None:
    # Drop brand aliases table
    op.drop_constraint('uq_brand_aliases_brand_alias', 'brand_aliases')
    op.drop_index('idx_brand_aliases_active')
    op.drop_index('idx_brand_aliases_alias')
    op.drop_index('idx_brand_aliases_user_brand')
    op.drop_table('brand_aliases')
    
    # Drop citation analytics table
    op.drop_constraint('uq_citation_analytics_user_brand_period', 'citation_analytics')
    op.drop_index('idx_citation_analytics_calculated')
    op.drop_index('idx_citation_analytics_period')
    op.drop_index('idx_citation_analytics_user_brand')
    op.drop_table('citation_analytics')
    
    # Drop new indexes from citations table
    op.drop_index('idx_citations_sentiment_type')
    op.drop_index('idx_citations_mention_type')
    
    # Remove new columns from citations table (skip prominence_score and confidence_score as they existed before)
    op.drop_column('citations', 'metadata')
    op.drop_column('citations', 'context_end')
    op.drop_column('citations', 'context_start')
    op.drop_column('citations', 'sentiment_type')
    op.drop_column('citations', 'mention_type')
    op.drop_column('citations', 'mention_text')