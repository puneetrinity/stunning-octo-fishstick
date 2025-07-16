"""Add NLP citation extraction tables

Revision ID: 008_20250716_1500_nlp_citation_extraction
Revises: 007_20250716_1430_authority_sources
Create Date: 2025-07-16 15:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = '008_20250716_1500_nlp_citation_extraction'
down_revision = '007_20250716_1430_authority_sources'
branch_labels = None
depends_on = None


def upgrade():
    # Create citation_analyses table
    op.create_table(
        'citation_analyses',
        sa.Column('id', sa.UUID(), nullable=False, server_default=sa.text('gen_random_uuid()')),
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column('query_text', sa.Text(), nullable=False),
        sa.Column('response_text', sa.Text(), nullable=False),
        sa.Column('platform', sa.String(50), nullable=False),
        sa.Column('total_entities', sa.Integer(), nullable=False, default=0),
        sa.Column('quality_score', sa.Float(), nullable=False, default=0.0),
        sa.Column('analysis_metadata', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('NOW()')),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create entity_mentions table
    op.create_table(
        'entity_mentions',
        sa.Column('id', sa.UUID(), nullable=False, server_default=sa.text('gen_random_uuid()')),
        sa.Column('analysis_id', sa.UUID(), nullable=False),
        sa.Column('entity_name', sa.String(255), nullable=False),
        sa.Column('entity_type', sa.String(50), nullable=False),
        sa.Column('text', sa.Text(), nullable=False),
        sa.Column('start_pos', sa.Integer(), nullable=False),
        sa.Column('end_pos', sa.Integer(), nullable=False),
        sa.Column('confidence', sa.Float(), nullable=False, default=0.0),
        sa.Column('context_window', sa.Text(), nullable=True),
        sa.Column('sentence', sa.Text(), nullable=True),
        sa.Column('paragraph', sa.Text(), nullable=True),
        
        # NLP-specific columns
        sa.Column('dependency_relation', sa.String(100), nullable=True),
        sa.Column('part_of_speech', sa.String(50), nullable=True),
        sa.Column('named_entity_label', sa.String(50), nullable=True),
        sa.Column('semantic_role', sa.String(100), nullable=True),
        
        # Sentiment and prominence
        sa.Column('sentiment_score', sa.Float(), nullable=False, default=0.0),
        sa.Column('sentiment_confidence', sa.Float(), nullable=False, default=0.0),
        sa.Column('prominence_score', sa.Float(), nullable=False, default=0.0),
        sa.Column('authority_score', sa.Float(), nullable=False, default=0.0),
        
        # Contextual analysis
        sa.Column('comparison_context', sa.Boolean(), nullable=False, default=False),
        sa.Column('recommendation_context', sa.Boolean(), nullable=False, default=False),
        sa.Column('negative_context', sa.Boolean(), nullable=False, default=False),
        sa.Column('question_context', sa.Boolean(), nullable=False, default=False),
        
        # Metadata
        sa.Column('extracted_at', sa.DateTime(), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('extraction_method', sa.String(100), nullable=False, default='advanced_nlp'),
        
        sa.ForeignKeyConstraint(['analysis_id'], ['citation_analyses.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create semantic_similarities table for tracking semantic relationships
    op.create_table(
        'semantic_similarities',
        sa.Column('id', sa.UUID(), nullable=False, server_default=sa.text('gen_random_uuid()')),
        sa.Column('analysis_id', sa.UUID(), nullable=False),
        sa.Column('entity_1', sa.String(255), nullable=False),
        sa.Column('entity_2', sa.String(255), nullable=False),
        sa.Column('similarity_score', sa.Float(), nullable=False, default=0.0),
        sa.Column('similarity_type', sa.String(50), nullable=False),  # 'semantic', 'contextual', 'syntactic'
        sa.Column('calculated_at', sa.DateTime(), nullable=False, server_default=sa.text('NOW()')),
        
        sa.ForeignKeyConstraint(['analysis_id'], ['citation_analyses.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create context_classifications table
    op.create_table(
        'context_classifications',
        sa.Column('id', sa.UUID(), nullable=False, server_default=sa.text('gen_random_uuid()')),
        sa.Column('analysis_id', sa.UUID(), nullable=False),
        sa.Column('context_label', sa.String(100), nullable=False),
        sa.Column('confidence_score', sa.Float(), nullable=False, default=0.0),
        sa.Column('classification_model', sa.String(100), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('NOW()')),
        
        sa.ForeignKeyConstraint(['analysis_id'], ['citation_analyses.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes for performance
    op.create_index('idx_citation_analyses_user_created', 'citation_analyses', ['user_id', 'created_at'])
    op.create_index('idx_citation_analyses_platform', 'citation_analyses', ['platform'])
    op.create_index('idx_citation_analyses_quality', 'citation_analyses', ['quality_score'])
    
    op.create_index('idx_entity_mentions_analysis_entity', 'entity_mentions', ['analysis_id', 'entity_name'])
    op.create_index('idx_entity_mentions_entity_type', 'entity_mentions', ['entity_type'])
    op.create_index('idx_entity_mentions_sentiment', 'entity_mentions', ['sentiment_score'])
    op.create_index('idx_entity_mentions_prominence', 'entity_mentions', ['prominence_score'])
    op.create_index('idx_entity_mentions_authority', 'entity_mentions', ['authority_score'])
    op.create_index('idx_entity_mentions_context', 'entity_mentions', ['recommendation_context', 'comparison_context'])
    op.create_index('idx_entity_mentions_extraction_method', 'entity_mentions', ['extraction_method'])
    
    op.create_index('idx_semantic_similarities_entities', 'semantic_similarities', ['entity_1', 'entity_2'])
    op.create_index('idx_semantic_similarities_score', 'semantic_similarities', ['similarity_score'])
    
    op.create_index('idx_context_classifications_label', 'context_classifications', ['context_label'])
    op.create_index('idx_context_classifications_confidence', 'context_classifications', ['confidence_score'])


def downgrade():
    # Drop indexes
    op.drop_index('idx_context_classifications_confidence')
    op.drop_index('idx_context_classifications_label')
    op.drop_index('idx_semantic_similarities_score')
    op.drop_index('idx_semantic_similarities_entities')
    op.drop_index('idx_entity_mentions_extraction_method')
    op.drop_index('idx_entity_mentions_context')
    op.drop_index('idx_entity_mentions_authority')
    op.drop_index('idx_entity_mentions_prominence')
    op.drop_index('idx_entity_mentions_sentiment')
    op.drop_index('idx_entity_mentions_entity_type')
    op.drop_index('idx_entity_mentions_analysis_entity')
    op.drop_index('idx_citation_analyses_quality')
    op.drop_index('idx_citation_analyses_platform')
    op.drop_index('idx_citation_analyses_user_created')
    
    # Drop tables
    op.drop_table('context_classifications')
    op.drop_table('semantic_similarities')
    op.drop_table('entity_mentions')
    op.drop_table('citation_analyses')