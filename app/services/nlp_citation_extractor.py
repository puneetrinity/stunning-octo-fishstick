"""
Advanced NLP Citation Extraction Service
Enhanced natural language processing for accurate brand mention detection and analysis
"""
import asyncio
import logging
from typing import List, Dict, Optional, Any, Tuple
from datetime import datetime
from dataclasses import dataclass
import re
import json
from collections import defaultdict
import numpy as np

# NLP libraries
import spacy
from spacy.matcher import Matcher
from spacy.tokens import Doc, Span, Token
from sentence_transformers import SentenceTransformer
import torch
from transformers import pipeline, AutoTokenizer, AutoModelForSequenceClassification

# Database
from app.database import db_manager

logger = logging.getLogger(__name__)


@dataclass
class EntityMention:
    """Enhanced structure for entity mentions with NLP analysis"""
    entity_name: str
    entity_type: str  # 'ORG', 'PRODUCT', 'PERSON', 'BRAND'
    text: str
    start_pos: int
    end_pos: int
    confidence: float
    context_window: str
    sentence: str
    paragraph: str
    
    # NLP-specific attributes
    dependency_relation: str
    part_of_speech: str
    named_entity_label: str
    semantic_role: str
    
    # Sentiment and prominence
    sentiment_score: float
    sentiment_confidence: float
    prominence_score: float
    authority_score: float
    
    # Contextual analysis
    comparison_context: bool
    recommendation_context: bool
    negative_context: bool
    question_context: bool
    
    # Metadata
    extracted_at: datetime
    extraction_method: str


@dataclass
class CitationAnalysis:
    """Comprehensive citation analysis result"""
    query: str
    response_text: str
    platform: str
    total_entities: int
    brand_mentions: List[EntityMention]
    competitor_mentions: List[EntityMention]
    context_analysis: Dict[str, Any]
    semantic_analysis: Dict[str, Any]
    recommendation_signals: Dict[str, Any]
    quality_score: float
    analysis_metadata: Dict[str, Any]


class AdvancedNLPCitationExtractor:
    """
    Advanced NLP service for extracting and analyzing brand citations
    Uses state-of-the-art NLP models for accurate entity detection and sentiment analysis
    """
    
    def __init__(self):
        # Load spaCy model
        try:
            self.nlp = spacy.load("en_core_web_lg")
        except OSError:
            logger.warning("Large spaCy model not found, using smaller model")
            self.nlp = spacy.load("en_core_web_sm")
        
        # Initialize sentence transformer for semantic analysis
        self.sentence_model = SentenceTransformer('all-MiniLM-L6-v2')
        
        # Initialize sentiment analysis pipeline
        self.sentiment_analyzer = pipeline(
            "sentiment-analysis",
            model="cardiffnlp/twitter-roberta-base-sentiment-latest",
            return_all_scores=True
        )
        
        # Initialize NER pipeline for additional entity recognition
        self.ner_pipeline = pipeline(
            "ner",
            model="dbmdz/bert-large-cased-finetuned-conll03-english",
            aggregation_strategy="simple"
        )
        
        # Initialize text classification for context analysis
        self.context_classifier = pipeline(
            "zero-shot-classification",
            model="facebook/bart-large-mnli"
        )
        
        # Setup custom matchers for brand patterns
        self.matcher = Matcher(self.nlp.vocab)
        self._setup_brand_patterns()
        
        # Contextual keywords for analysis
        self.context_keywords = {
            'recommendation': [
                'recommend', 'suggest', 'advise', 'prefer', 'choose', 'select',
                'best', 'top', 'leading', 'excellent', 'outstanding', 'superior',
                'ideal', 'perfect', 'optimal', 'recommended', 'suggested'
            ],
            'comparison': [
                'vs', 'versus', 'compared to', 'against', 'better than', 'worse than',
                'similar to', 'like', 'unlike', 'alternative to', 'instead of',
                'rather than', 'over', 'competitor', 'rival'
            ],
            'negative': [
                'avoid', 'terrible', 'awful', 'bad', 'poor', 'disappointing',
                'problematic', 'issues', 'problems', 'concerns', 'limitations',
                'drawbacks', 'disadvantages', 'not recommended', 'stay away'
            ],
            'question': [
                'what', 'which', 'how', 'why', 'when', 'where', 'should i',
                'can you', 'do you', 'is it', 'are there', 'help me'
            ]
        }
    
    def _setup_brand_patterns(self):
        """Setup spaCy matcher patterns for brand detection"""
        # Pattern for brand names (proper nouns)
        brand_pattern = [
            {"POS": "PROPN", "OP": "+"},
            {"LOWER": {"IN": ["inc", "corp", "llc", "ltd", "co"]}, "OP": "?"}
        ]
        
        # Pattern for software/product names
        software_pattern = [
            {"POS": "PROPN"},
            {"LOWER": {"IN": ["software", "platform", "tool", "app", "service"]}, "OP": "?"}
        ]
        
        # Pattern for company mentions
        company_pattern = [
            {"POS": "PROPN", "OP": "+"},
            {"LOWER": {"IN": ["company", "corporation", "enterprise", "solutions"]}, "OP": "?"}
        ]
        
        self.matcher.add("BRAND_PATTERN", [brand_pattern])
        self.matcher.add("SOFTWARE_PATTERN", [software_pattern])
        self.matcher.add("COMPANY_PATTERN", [company_pattern])
    
    async def extract_citations(
        self,
        response_text: str,
        query: str,
        platform: str,
        target_brands: List[str],
        competitor_brands: List[str] = None
    ) -> CitationAnalysis:
        """
        Extract and analyze citations with advanced NLP techniques
        """
        competitor_brands = competitor_brands or []
        
        try:
            # Process text with spaCy
            doc = self.nlp(response_text)
            
            # Extract brand mentions
            brand_mentions = await self._extract_brand_mentions(
                doc, target_brands, response_text
            )
            
            # Extract competitor mentions
            competitor_mentions = await self._extract_brand_mentions(
                doc, competitor_brands, response_text
            )
            
            # Perform contextual analysis
            context_analysis = await self._analyze_context(doc, response_text)
            
            # Perform semantic analysis
            semantic_analysis = await self._analyze_semantics(response_text, query)
            
            # Analyze recommendation signals
            recommendation_signals = await self._analyze_recommendation_signals(
                doc, brand_mentions, competitor_mentions
            )
            
            # Calculate quality score
            quality_score = self._calculate_quality_score(
                brand_mentions, competitor_mentions, context_analysis
            )
            
            # Create analysis result
            analysis = CitationAnalysis(
                query=query,
                response_text=response_text,
                platform=platform,
                total_entities=len(brand_mentions) + len(competitor_mentions),
                brand_mentions=brand_mentions,
                competitor_mentions=competitor_mentions,
                context_analysis=context_analysis,
                semantic_analysis=semantic_analysis,
                recommendation_signals=recommendation_signals,
                quality_score=quality_score,
                analysis_metadata={
                    'extraction_method': 'advanced_nlp',
                    'models_used': ['spacy', 'sentence_transformers', 'transformers'],
                    'processed_at': datetime.utcnow().isoformat(),
                    'text_length': len(response_text),
                    'sentence_count': len(list(doc.sents))
                }
            )
            
            return analysis
            
        except Exception as e:
            logger.error(f"Error in citation extraction: {e}")
            raise
    
    async def _extract_brand_mentions(
        self, 
        doc: Doc, 
        brands: List[str], 
        full_text: str
    ) -> List[EntityMention]:
        """Extract brand mentions with advanced NLP analysis"""
        mentions = []
        
        for brand in brands:
            brand_lower = brand.lower()
            
            # Find all occurrences of the brand
            for token in doc:
                if token.text.lower() == brand_lower or brand_lower in token.text.lower():
                    # Find the full span
                    start_idx = token.i
                    end_idx = token.i + 1
                    
                    # Extend span if brand is multi-word
                    brand_tokens = brand.split()
                    if len(brand_tokens) > 1:
                        # Try to match multi-word brand
                        for i in range(len(doc) - len(brand_tokens) + 1):
                            if ' '.join([doc[i+j].text for j in range(len(brand_tokens))]).lower() == brand_lower:
                                start_idx = i
                                end_idx = i + len(brand_tokens)
                                break
                    
                    # Extract mention details
                    mention_span = doc[start_idx:end_idx]
                    mention = await self._analyze_mention(
                        mention_span, brand, doc, full_text
                    )
                    mentions.append(mention)
        
        # Also use custom patterns
        matches = self.matcher(doc)
        for match_id, start, end in matches:
            span = doc[start:end]
            span_text = span.text.lower()
            
            # Check if this matches any of our brands
            for brand in brands:
                if brand.lower() in span_text:
                    mention = await self._analyze_mention(
                        span, brand, doc, full_text
                    )
                    mentions.append(mention)
        
        # Remove duplicates
        unique_mentions = []
        seen_positions = set()
        for mention in mentions:
            pos_key = (mention.start_pos, mention.end_pos, mention.entity_name)
            if pos_key not in seen_positions:
                unique_mentions.append(mention)
                seen_positions.add(pos_key)
        
        return unique_mentions
    
    async def _analyze_mention(
        self, 
        span: Span, 
        brand_name: str, 
        doc: Doc, 
        full_text: str
    ) -> EntityMention:
        """Analyze a single mention with comprehensive NLP"""
        
        # Get sentence and paragraph context
        sentence = span.sent.text
        paragraph = self._extract_paragraph(span.sent, doc)
        
        # Extract context window
        context_start = max(0, span.start_char - 200)
        context_end = min(len(full_text), span.end_char + 200)
        context_window = full_text[context_start:context_end]
        
        # Analyze dependency relations
        dependency_relation = self._analyze_dependency(span)
        
        # Analyze semantic role
        semantic_role = self._analyze_semantic_role(span, sentence)
        
        # Analyze sentiment
        sentiment_score, sentiment_confidence = await self._analyze_mention_sentiment(
            sentence, context_window
        )
        
        # Calculate prominence score
        prominence_score = self._calculate_prominence_score(span, doc)
        
        # Calculate authority score
        authority_score = self._calculate_authority_score(span, sentence)
        
        # Analyze contextual flags
        comparison_context = self._is_comparison_context(sentence)
        recommendation_context = self._is_recommendation_context(sentence)
        negative_context = self._is_negative_context(sentence)
        question_context = self._is_question_context(sentence)
        
        # Determine entity type
        entity_type = self._determine_entity_type(span)
        
        return EntityMention(
            entity_name=brand_name,
            entity_type=entity_type,
            text=span.text,
            start_pos=span.start_char,
            end_pos=span.end_char,
            confidence=self._calculate_mention_confidence(span, brand_name),
            context_window=context_window,
            sentence=sentence,
            paragraph=paragraph,
            dependency_relation=dependency_relation,
            part_of_speech=span.root.pos_,
            named_entity_label=span.label_ if span.label_ else "ORG",
            semantic_role=semantic_role,
            sentiment_score=sentiment_score,
            sentiment_confidence=sentiment_confidence,
            prominence_score=prominence_score,
            authority_score=authority_score,
            comparison_context=comparison_context,
            recommendation_context=recommendation_context,
            negative_context=negative_context,
            question_context=question_context,
            extracted_at=datetime.utcnow(),
            extraction_method='advanced_nlp'
        )
    
    def _extract_paragraph(self, sent: Span, doc: Doc) -> str:
        """Extract paragraph containing the sentence"""
        # Simple paragraph extraction - in practice, you'd want more sophisticated logic
        sentences = list(doc.sents)
        sent_idx = sentences.index(sent)
        
        # Get surrounding sentences
        start_idx = max(0, sent_idx - 2)
        end_idx = min(len(sentences), sent_idx + 3)
        
        return ' '.join([s.text for s in sentences[start_idx:end_idx]])
    
    def _analyze_dependency(self, span: Span) -> str:
        """Analyze dependency relation of the mention"""
        root = span.root
        return f"{root.dep_}:{root.head.text}" if root.head else root.dep_
    
    def _analyze_semantic_role(self, span: Span, sentence: str) -> str:
        """Analyze semantic role of the mention in the sentence"""
        root = span.root
        
        # Simple semantic role analysis
        if root.dep_ == "nsubj":
            return "subject"
        elif root.dep_ == "dobj":
            return "direct_object"
        elif root.dep_ == "pobj":
            return "prepositional_object"
        elif root.dep_ == "compound":
            return "compound"
        else:
            return root.dep_
    
    async def _analyze_mention_sentiment(
        self, 
        sentence: str, 
        context: str
    ) -> Tuple[float, float]:
        """Analyze sentiment of mention with confidence"""
        try:
            # Analyze sentence sentiment
            sentence_sentiment = self.sentiment_analyzer(sentence)[0]
            
            # Analyze context sentiment
            context_sentiment = self.sentiment_analyzer(context)[0]
            
            # Combine sentiments (weighted toward sentence)
            sentence_score = self._sentiment_to_score(sentence_sentiment)
            context_score = self._sentiment_to_score(context_sentiment)
            
            combined_score = 0.7 * sentence_score + 0.3 * context_score
            
            # Calculate confidence
            sentence_conf = max([s['score'] for s in sentence_sentiment])
            context_conf = max([s['score'] for s in context_sentiment])
            combined_confidence = 0.7 * sentence_conf + 0.3 * context_conf
            
            return combined_score, combined_confidence
            
        except Exception as e:
            logger.error(f"Error in sentiment analysis: {e}")
            return 0.5, 0.5
    
    def _sentiment_to_score(self, sentiment_result: List[Dict]) -> float:
        """Convert sentiment result to score"""
        # Find the highest scoring sentiment
        best_sentiment = max(sentiment_result, key=lambda x: x['score'])
        
        if best_sentiment['label'] == 'POSITIVE':
            return 0.5 + (best_sentiment['score'] * 0.5)
        elif best_sentiment['label'] == 'NEGATIVE':
            return 0.5 - (best_sentiment['score'] * 0.5)
        else:
            return 0.5
    
    def _calculate_prominence_score(self, span: Span, doc: Doc) -> float:
        """Calculate prominence score based on position and context"""
        # Position in document (earlier = higher score)
        position_score = 1.0 - (span.start / len(doc))
        
        # Sentence position (beginning = higher score)
        sent_position_score = 1.0 - (span.start - span.sent.start) / len(span.sent)
        
        # Length of mention (longer = higher score)
        length_score = min(len(span.text) / 50, 1.0)
        
        # Combine scores
        prominence = 0.4 * position_score + 0.3 * sent_position_score + 0.3 * length_score
        return min(prominence * 10, 10.0)  # Scale to 0-10
    
    def _calculate_authority_score(self, span: Span, sentence: str) -> float:
        """Calculate authority score based on context"""
        authority_indicators = [
            'according to', 'research shows', 'studies indicate', 'experts say',
            'industry leader', 'market leader', 'established', 'proven',
            'trusted', 'reliable', 'reputable', 'well-known'
        ]
        
        sentence_lower = sentence.lower()
        authority_count = sum(1 for indicator in authority_indicators if indicator in sentence_lower)
        
        return min(authority_count * 2.0, 10.0)  # Scale to 0-10
    
    def _is_comparison_context(self, sentence: str) -> bool:
        """Check if mention is in comparison context"""
        return any(keyword in sentence.lower() for keyword in self.context_keywords['comparison'])
    
    def _is_recommendation_context(self, sentence: str) -> bool:
        """Check if mention is in recommendation context"""
        return any(keyword in sentence.lower() for keyword in self.context_keywords['recommendation'])
    
    def _is_negative_context(self, sentence: str) -> bool:
        """Check if mention is in negative context"""
        return any(keyword in sentence.lower() for keyword in self.context_keywords['negative'])
    
    def _is_question_context(self, sentence: str) -> bool:
        """Check if mention is in question context"""
        return any(keyword in sentence.lower() for keyword in self.context_keywords['question'])
    
    def _determine_entity_type(self, span: Span) -> str:
        """Determine entity type of the mention"""
        if span.label_:
            return span.label_
        
        # Fallback to heuristic classification
        text_lower = span.text.lower()
        
        if any(suffix in text_lower for suffix in ['inc', 'corp', 'llc', 'ltd', 'co']):
            return 'ORG'
        elif any(type_word in text_lower for type_word in ['software', 'platform', 'tool', 'app']):
            return 'PRODUCT'
        else:
            return 'ORG'
    
    def _calculate_mention_confidence(self, span: Span, brand_name: str) -> float:
        """Calculate confidence score for the mention"""
        # Exact match = higher confidence
        if span.text.lower() == brand_name.lower():
            return 1.0
        
        # Partial match = lower confidence
        if brand_name.lower() in span.text.lower():
            return 0.8
        
        # Context-based confidence
        if span.label_ == 'ORG':
            return 0.9
        
        return 0.6
    
    async def _analyze_context(self, doc: Doc, full_text: str) -> Dict[str, Any]:
        """Analyze overall context of the response"""
        context_analysis = {
            'document_type': 'response',
            'sentence_count': len(list(doc.sents)),
            'word_count': len(doc),
            'entity_count': len(doc.ents),
            'context_categories': {}
        }
        
        try:
            # Classify document context
            context_labels = [
                'recommendation', 'comparison', 'review', 'tutorial',
                'news', 'discussion', 'question', 'answer'
            ]
            
            classification = self.context_classifier(full_text, context_labels)
            context_analysis['context_categories'] = {
                label: score for label, score in zip(
                    classification['labels'], classification['scores']
                )
            }
            
        except Exception as e:
            logger.error(f"Error in context classification: {e}")
            context_analysis['context_categories'] = {}
        
        return context_analysis
    
    async def _analyze_semantics(self, response_text: str, query: str) -> Dict[str, Any]:
        """Analyze semantic relationship between query and response"""
        try:
            # Generate embeddings
            query_embedding = self.sentence_model.encode(query)
            response_embedding = self.sentence_model.encode(response_text)
            
            # Calculate similarity
            similarity = np.dot(query_embedding, response_embedding) / (
                np.linalg.norm(query_embedding) * np.linalg.norm(response_embedding)
            )
            
            return {
                'query_response_similarity': float(similarity),
                'embedding_model': 'all-MiniLM-L6-v2',
                'semantic_coherence': float(similarity > 0.7)
            }
            
        except Exception as e:
            logger.error(f"Error in semantic analysis: {e}")
            return {
                'query_response_similarity': 0.5,
                'embedding_model': 'error',
                'semantic_coherence': False
            }
    
    async def _analyze_recommendation_signals(
        self, 
        doc: Doc, 
        brand_mentions: List[EntityMention], 
        competitor_mentions: List[EntityMention]
    ) -> Dict[str, Any]:
        """Analyze recommendation signals in the text"""
        signals = {
            'total_recommendations': 0,
            'positive_recommendations': 0,
            'negative_recommendations': 0,
            'comparative_mentions': 0,
            'question_responses': 0,
            'authority_citations': 0
        }
        
        # Analyze each mention
        for mention in brand_mentions + competitor_mentions:
            if mention.recommendation_context:
                signals['total_recommendations'] += 1
                if mention.sentiment_score > 0.6:
                    signals['positive_recommendations'] += 1
                elif mention.sentiment_score < 0.4:
                    signals['negative_recommendations'] += 1
            
            if mention.comparison_context:
                signals['comparative_mentions'] += 1
            
            if mention.question_context:
                signals['question_responses'] += 1
            
            if mention.authority_score > 5:
                signals['authority_citations'] += 1
        
        return signals
    
    def _calculate_quality_score(
        self, 
        brand_mentions: List[EntityMention], 
        competitor_mentions: List[EntityMention], 
        context_analysis: Dict[str, Any]
    ) -> float:
        """Calculate overall quality score for the citation analysis"""
        if not brand_mentions and not competitor_mentions:
            return 0.0
        
        # Base score from mention count
        mention_score = min(len(brand_mentions) * 0.3, 1.0)
        
        # Confidence score
        if brand_mentions:
            avg_confidence = sum(m.confidence for m in brand_mentions) / len(brand_mentions)
            confidence_score = avg_confidence * 0.3
        else:
            confidence_score = 0.0
        
        # Context quality score
        context_score = 0.2 if context_analysis.get('entity_count', 0) > 0 else 0.0
        
        # Sentiment quality score
        if brand_mentions:
            sentiment_diversity = len(set(
                'positive' if m.sentiment_score > 0.6 else 
                'negative' if m.sentiment_score < 0.4 else 
                'neutral' for m in brand_mentions
            ))
            sentiment_score = min(sentiment_diversity * 0.1, 0.2)
        else:
            sentiment_score = 0.0
        
        total_score = mention_score + confidence_score + context_score + sentiment_score
        return min(total_score * 10, 10.0)  # Scale to 0-10
    
    async def store_citation_analysis(self, user_id: str, analysis: CitationAnalysis):
        """Store citation analysis results in database"""
        try:
            # Store main analysis
            analysis_id = await db_manager.execute_query(
                """
                INSERT INTO citation_analyses (user_id, query_text, response_text, platform, 
                                             total_entities, quality_score, analysis_metadata, created_at)
                VALUES (:user_id, :query_text, :response_text, :platform, 
                        :total_entities, :quality_score, :analysis_metadata, :created_at)
                RETURNING id
                """,
                {
                    "user_id": user_id,
                    "query_text": analysis.query,
                    "response_text": analysis.response_text,
                    "platform": analysis.platform,
                    "total_entities": analysis.total_entities,
                    "quality_score": analysis.quality_score,
                    "analysis_metadata": json.dumps(analysis.analysis_metadata),
                    "created_at": datetime.utcnow()
                }
            )
            
            # Store entity mentions
            for mention in analysis.brand_mentions + analysis.competitor_mentions:
                await db_manager.execute_query(
                    """
                    INSERT INTO entity_mentions (analysis_id, entity_name, entity_type, text, 
                                               start_pos, end_pos, confidence, context_window, 
                                               sentence, paragraph, dependency_relation, 
                                               part_of_speech, named_entity_label, semantic_role,
                                               sentiment_score, sentiment_confidence, prominence_score, 
                                               authority_score, comparison_context, recommendation_context, 
                                               negative_context, question_context, extracted_at, extraction_method)
                    VALUES (:analysis_id, :entity_name, :entity_type, :text, :start_pos, :end_pos, 
                            :confidence, :context_window, :sentence, :paragraph, :dependency_relation, 
                            :part_of_speech, :named_entity_label, :semantic_role, :sentiment_score, 
                            :sentiment_confidence, :prominence_score, :authority_score, 
                            :comparison_context, :recommendation_context, :negative_context, 
                            :question_context, :extracted_at, :extraction_method)
                    """,
                    {
                        "analysis_id": analysis_id,
                        "entity_name": mention.entity_name,
                        "entity_type": mention.entity_type,
                        "text": mention.text,
                        "start_pos": mention.start_pos,
                        "end_pos": mention.end_pos,
                        "confidence": mention.confidence,
                        "context_window": mention.context_window,
                        "sentence": mention.sentence,
                        "paragraph": mention.paragraph,
                        "dependency_relation": mention.dependency_relation,
                        "part_of_speech": mention.part_of_speech,
                        "named_entity_label": mention.named_entity_label,
                        "semantic_role": mention.semantic_role,
                        "sentiment_score": mention.sentiment_score,
                        "sentiment_confidence": mention.sentiment_confidence,
                        "prominence_score": mention.prominence_score,
                        "authority_score": mention.authority_score,
                        "comparison_context": mention.comparison_context,
                        "recommendation_context": mention.recommendation_context,
                        "negative_context": mention.negative_context,
                        "question_context": mention.question_context,
                        "extracted_at": mention.extracted_at,
                        "extraction_method": mention.extraction_method
                    }
                )
            
            logger.info(f"Stored citation analysis {analysis_id} for user {user_id}")
            return analysis_id
            
        except Exception as e:
            logger.error(f"Error storing citation analysis: {e}")
            raise
    
    async def get_citation_insights(self, user_id: str, brand_name: str, days: int = 30) -> Dict[str, Any]:
        """Get citation insights for a brand"""
        try:
            since_date = datetime.utcnow() - timedelta(days=days)
            
            # Get citation statistics
            stats = await db_manager.fetch_one(
                """
                SELECT 
                    COUNT(DISTINCT ca.id) as total_analyses,
                    COUNT(em.id) as total_mentions,
                    AVG(em.confidence) as avg_confidence,
                    AVG(em.sentiment_score) as avg_sentiment,
                    AVG(em.prominence_score) as avg_prominence,
                    AVG(em.authority_score) as avg_authority,
                    AVG(ca.quality_score) as avg_quality
                FROM citation_analyses ca
                LEFT JOIN entity_mentions em ON ca.id = em.analysis_id
                WHERE ca.user_id = :user_id 
                AND em.entity_name = :brand_name
                AND ca.created_at >= :since_date
                """,
                {
                    "user_id": user_id,
                    "brand_name": brand_name,
                    "since_date": since_date
                }
            )
            
            # Get context analysis
            context_stats = await db_manager.fetch_all(
                """
                SELECT 
                    em.entity_type,
                    em.semantic_role,
                    COUNT(*) as mention_count,
                    AVG(em.sentiment_score) as avg_sentiment
                FROM entity_mentions em
                JOIN citation_analyses ca ON em.analysis_id = ca.id
                WHERE ca.user_id = :user_id 
                AND em.entity_name = :brand_name
                AND ca.created_at >= :since_date
                GROUP BY em.entity_type, em.semantic_role
                """,
                {
                    "user_id": user_id,
                    "brand_name": brand_name,
                    "since_date": since_date
                }
            )
            
            return {
                "total_analyses": stats.total_analyses or 0,
                "total_mentions": stats.total_mentions or 0,
                "avg_confidence": float(stats.avg_confidence or 0),
                "avg_sentiment": float(stats.avg_sentiment or 0),
                "avg_prominence": float(stats.avg_prominence or 0),
                "avg_authority": float(stats.avg_authority or 0),
                "avg_quality": float(stats.avg_quality or 0),
                "context_breakdown": [
                    {
                        "entity_type": row.entity_type,
                        "semantic_role": row.semantic_role,
                        "mention_count": row.mention_count,
                        "avg_sentiment": float(row.avg_sentiment or 0)
                    }
                    for row in context_stats
                ]
            }
            
        except Exception as e:
            logger.error(f"Error getting citation insights: {e}")
            return {}


# Global service instance
nlp_citation_extractor = AdvancedNLPCitationExtractor()