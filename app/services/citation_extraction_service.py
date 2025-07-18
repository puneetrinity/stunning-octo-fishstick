"""
Citation Extraction Service
Core engine for extracting and analyzing brand mentions from AI responses
Based on Reddit intelligence: Track mentions with context and prominence
"""
import re
import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
from dataclasses import dataclass
from enum import Enum
import asyncio
import json
from difflib import SequenceMatcher
import spacy
from app.database import db_manager

logger = logging.getLogger(__name__)


class MentionType(Enum):
    DIRECT = "direct"  # Brand name mentioned directly
    COMPARISON = "comparison"  # Brand in comparison context
    RECOMMENDATION = "recommendation"  # Brand recommended
    ALTERNATIVE = "alternative"  # Brand as alternative/competitor
    FEATURE = "feature"  # Brand features discussed
    REVIEW = "review"  # Brand review/opinion
    QUESTION = "question"  # Brand in question context


class SentimentType(Enum):
    POSITIVE = "positive"
    NEGATIVE = "negative"
    NEUTRAL = "neutral"
    MIXED = "mixed"


@dataclass
class BrandMention:
    """Single brand mention extracted from AI response"""
    brand_name: str
    mentioned: bool
    position: int  # Position in response (1-based)
    mention_text: str  # Exact text mentioning the brand
    context: str  # Surrounding context
    context_start: int
    context_end: int
    mention_type: MentionType
    sentiment_score: float  # -1 to 1
    sentiment_type: SentimentType
    prominence_score: float  # 0 to 1
    confidence_score: float  # 0 to 1
    extracted_at: datetime
    metadata: Dict[str, Any]


@dataclass
class CitationExtractionResult:
    """Result of citation extraction for a query"""
    query_text: str
    platform: str
    response_text: str
    total_brands_checked: int
    brands_mentioned: int
    brand_mentions: List[BrandMention]
    response_analysis: Dict[str, Any]
    extraction_metadata: Dict[str, Any]
    processed_at: datetime


class CitationExtractionService:
    """
    Advanced citation extraction engine
    Extracts brand mentions with context, sentiment, and prominence analysis
    """
    
    def __init__(self):
        self.nlp = None  # Will be loaded lazily
        self.brand_aliases = {}  # Cache for brand aliases
        self.extraction_patterns = self._build_extraction_patterns()
        self.sentiment_keywords = self._build_sentiment_keywords()
        self.prominence_indicators = self._build_prominence_indicators()
        
    async def initialize(self):
        """Initialize NLP model and other resources"""
        if self.nlp is None:
            try:
                # Try to load spaCy model
                import spacy
                self.nlp = spacy.load("en_core_web_sm")
                logger.info("Loaded spaCy model for citation extraction")
            except (ImportError, OSError):
                logger.warning("spaCy model not available, using basic extraction")
                self.nlp = None
    
    def _build_extraction_patterns(self) -> Dict[str, List[str]]:
        """Build regex patterns for different mention types"""
        return {
            'direct': [
                r'\b{brand}\b',
                r'\b{brand}(?:\'s|\s+is|\s+are|\s+has|\s+does)',
                r'(?:using|with|via|through)\s+{brand}\b',
            ],
            'comparison': [
                r'{brand}\s+(?:vs\.?|versus|compared to|against)',
                r'(?:vs\.?|versus|compared to|against)\s+{brand}',
                r'{brand}\s+(?:or|and)\s+\w+',
                r'(?:between|among)\s+.*{brand}',
            ],
            'recommendation': [
                r'(?:recommend|suggest|advise|consider)\s+.*{brand}',
                r'{brand}\s+(?:is recommended|is suggested)',
                r'(?:try|use|check out|go with)\s+{brand}',
                r'{brand}\s+(?:would be|might be|could be)\s+(?:good|great|excellent)',
            ],
            'alternative': [
                r'(?:alternative|option|choice|substitute)\s+.*{brand}',
                r'{brand}\s+(?:as an alternative|as another option)',
                r'(?:instead of|rather than).*{brand}',
                r'{brand}\s+(?:alternatively|otherwise)',
            ],
            'feature': [
                r'{brand}(?:\'s)?\s+(?:feature|capability|function|tool)',
                r'(?:feature|capability|function|tool)\s+(?:of|in)\s+{brand}',
                r'{brand}\s+(?:offers|provides|includes|has)',
                r'(?:with|using)\s+{brand}(?:\'s)?\s+\w+',
            ],
            'review': [
                r'{brand}\s+(?:is|are)\s+(?:good|great|excellent|bad|poor|terrible)',
                r'(?:love|like|hate|dislike)\s+{brand}',
                r'{brand}\s+(?:works|performs|functions)',
                r'(?:experience with|opinion on|thoughts about)\s+{brand}',
            ]
        }
    
    def _build_sentiment_keywords(self) -> Dict[str, List[str]]:
        """Build sentiment keyword lists"""
        return {
            'positive': [
                'excellent', 'outstanding', 'great', 'good', 'amazing', 'fantastic',
                'wonderful', 'impressive', 'reliable', 'efficient', 'helpful',
                'easy', 'simple', 'intuitive', 'powerful', 'robust', 'solid',
                'recommend', 'love', 'like', 'prefer', 'best', 'top', 'leading',
                'superior', 'advanced', 'innovative', 'seamless', 'smooth'
            ],
            'negative': [
                'terrible', 'awful', 'bad', 'poor', 'horrible', 'disappointing',
                'frustrating', 'difficult', 'hard', 'complex', 'confusing',
                'slow', 'unreliable', 'buggy', 'broken', 'expensive', 'costly',
                'hate', 'dislike', 'avoid', 'worst', 'lacking', 'limited',
                'problematic', 'issues', 'problems', 'complaints', 'concerns'
            ],
            'neutral': [
                'okay', 'fine', 'decent', 'average', 'standard', 'normal',
                'typical', 'basic', 'simple', 'plain', 'adequate', 'sufficient',
                'acceptable', 'reasonable', 'moderate', 'fair', 'balanced'
            ]
        }
    
    def _build_prominence_indicators(self) -> Dict[str, float]:
        """Build prominence score multipliers based on position and context"""
        return {
            'first_sentence': 1.5,
            'first_paragraph': 1.3,
            'bullet_point': 1.2,
            'numbered_list': 1.2,
            'quoted': 1.4,
            'emphasized': 1.3,  # ALL CAPS, **bold**, etc.
            'last_sentence': 1.1,
            'middle_content': 1.0,
            'parenthetical': 0.8,
            'footnote': 0.7,
        }
    
    async def extract_citations(
        self,
        response_text: str,
        query_text: str,
        brand_names: List[str],
        platform: str = "unknown",
        include_context: bool = True,
        context_window: int = 150
    ) -> CitationExtractionResult:
        """
        Extract brand citations from AI response text
        Main entry point for citation extraction
        """
        await self.initialize()
        
        logger.info(f"Extracting citations for {len(brand_names)} brands from {platform} response")
        
        # Preprocess response
        cleaned_response = self._preprocess_response(response_text)
        
        # Extract mentions for each brand
        all_mentions = []
        brands_mentioned = 0
        
        for brand_name in brand_names:
            mentions = await self._extract_brand_mentions(
                cleaned_response,
                brand_name,
                include_context,
                context_window
            )
            
            if mentions:
                brands_mentioned += 1
                all_mentions.extend(mentions)
        
        # Analyze overall response
        response_analysis = self._analyze_response_structure(cleaned_response, all_mentions)
        
        # Build extraction metadata
        extraction_metadata = {
            "response_length": len(response_text),
            "cleaned_response_length": len(cleaned_response),
            "total_sentences": len(self._split_into_sentences(cleaned_response)),
            "nlp_available": self.nlp is not None,
            "extraction_method": "advanced" if self.nlp else "pattern_based",
            "context_window": context_window
        }
        
        result = CitationExtractionResult(
            query_text=query_text,
            platform=platform,
            response_text=response_text,
            total_brands_checked=len(brand_names),
            brands_mentioned=brands_mentioned,
            brand_mentions=all_mentions,
            response_analysis=response_analysis,
            extraction_metadata=extraction_metadata,
            processed_at=datetime.utcnow()
        )
        
        logger.info(f"Citation extraction completed: {brands_mentioned}/{len(brand_names)} brands mentioned")
        return result
    
    def _preprocess_response(self, response_text: str) -> str:
        """Clean and preprocess response text"""
        # Remove excessive whitespace
        cleaned = re.sub(r'\s+', ' ', response_text.strip())
        
        # Normalize quotes
        cleaned = re.sub(r'["""]', '"', cleaned)
        cleaned = re.sub(r"[''']", "'", cleaned)
        
        # Remove markdown formatting but preserve structure
        cleaned = re.sub(r'\*\*(.*?)\*\*', r'\1', cleaned)  # Bold
        cleaned = re.sub(r'\*(.*?)\*', r'\1', cleaned)      # Italic
        cleaned = re.sub(r'`(.*?)`', r'\1', cleaned)        # Code
        
        return cleaned
    
    async def _extract_brand_mentions(
        self,
        response_text: str,
        brand_name: str,
        include_context: bool,
        context_window: int
    ) -> List[BrandMention]:
        """Extract all mentions of a specific brand"""
        mentions = []
        
        # Get brand aliases (including the brand name itself)
        brand_aliases = await self._get_brand_aliases(brand_name)
        
        # Search for each alias
        for alias in brand_aliases:
            alias_mentions = self._find_brand_mentions(
                response_text, alias, brand_name, include_context, context_window
            )
            mentions.extend(alias_mentions)
        
        # Remove duplicates and sort by position
        mentions = self._deduplicate_mentions(mentions)
        mentions.sort(key=lambda m: m.position)
        
        return mentions
    
    async def _get_brand_aliases(self, brand_name: str) -> List[str]:
        """Get brand aliases from database or generate common variations"""
        if brand_name in self.brand_aliases:
            return self.brand_aliases[brand_name]
        
        aliases = [brand_name]
        
        # Add common variations
        if ' ' in brand_name:
            # Add version without spaces
            aliases.append(brand_name.replace(' ', ''))
            # Add version with different separators
            aliases.append(brand_name.replace(' ', '-'))
            aliases.append(brand_name.replace(' ', '_'))
        
        # Add lowercase version
        if brand_name.lower() not in [a.lower() for a in aliases]:
            aliases.append(brand_name.lower())
        
        # Cache the result
        self.brand_aliases[brand_name] = aliases
        return aliases
    
    def _find_brand_mentions(
        self,
        response_text: str,
        search_term: str,
        brand_name: str,
        include_context: bool,
        context_window: int
    ) -> List[BrandMention]:
        """Find mentions of a specific search term (brand alias)"""
        mentions = []
        
        # Try different mention types
        for mention_type_name, patterns in self.extraction_patterns.items():
            mention_type = MentionType(mention_type_name)
            
            for pattern_template in patterns:
                # Create regex pattern
                pattern = pattern_template.format(brand=re.escape(search_term))
                
                for match in re.finditer(pattern, response_text, re.IGNORECASE):
                    mention = self._create_mention_from_match(
                        match, response_text, brand_name, search_term,
                        mention_type, include_context, context_window
                    )
                    mentions.append(mention)
        
        # If no pattern matches found, try simple exact match
        if not mentions:
            for match in re.finditer(re.escape(search_term), response_text, re.IGNORECASE):
                mention = self._create_mention_from_match(
                    match, response_text, brand_name, search_term,
                    MentionType.DIRECT, include_context, context_window
                )
                mentions.append(mention)
        
        return mentions
    
    def _create_mention_from_match(
        self,
        match: re.Match,
        response_text: str,
        brand_name: str,
        search_term: str,
        mention_type: MentionType,
        include_context: bool,
        context_window: int
    ) -> BrandMention:
        """Create a BrandMention object from a regex match"""
        start_pos = match.start()
        end_pos = match.end()
        mention_text = match.group()
        
        # Calculate position (1-based)
        position = self._calculate_mention_position(response_text, start_pos)
        
        # Extract context
        context, context_start, context_end = self._extract_context(
            response_text, start_pos, end_pos, context_window
        ) if include_context else ("", start_pos, end_pos)
        
        # Analyze sentiment
        sentiment_score, sentiment_type = self._analyze_sentiment(context or mention_text)
        
        # Calculate prominence score
        prominence_score = self._calculate_prominence_score(
            response_text, start_pos, end_pos, position, mention_text
        )
        
        # Calculate confidence score
        confidence_score = self._calculate_confidence_score(
            mention_text, search_term, brand_name, context, mention_type
        )
        
        # Build metadata
        metadata = {
            "search_term": search_term,
            "match_start": start_pos,
            "match_end": end_pos,
            "pattern_type": mention_type.value,
            "case_sensitive_match": search_term in response_text,
            "full_word_match": self._is_full_word_match(response_text, start_pos, end_pos)
        }
        
        return BrandMention(
            brand_name=brand_name,
            mentioned=True,
            position=position,
            mention_text=mention_text,
            context=context,
            context_start=context_start,
            context_end=context_end,
            mention_type=mention_type,
            sentiment_score=sentiment_score,
            sentiment_type=sentiment_type,
            prominence_score=prominence_score,
            confidence_score=confidence_score,
            extracted_at=datetime.utcnow(),
            metadata=metadata
        )
    
    def _calculate_mention_position(self, response_text: str, start_pos: int) -> int:
        """Calculate relative position of mention in response (1-based)"""
        # Count sentences before this position
        sentences = self._split_into_sentences(response_text[:start_pos])
        return len(sentences) + 1
    
    def _extract_context(
        self, response_text: str, start_pos: int, end_pos: int, context_window: int
    ) -> Tuple[str, int, int]:
        """Extract context around the mention"""
        # Calculate context boundaries
        context_start = max(0, start_pos - context_window // 2)
        context_end = min(len(response_text), end_pos + context_window // 2)
        
        # Try to break at word boundaries
        if context_start > 0:
            # Find the next space after context_start
            space_pos = response_text.find(' ', context_start)
            if space_pos != -1 and space_pos < start_pos:
                context_start = space_pos + 1
        
        if context_end < len(response_text):
            # Find the previous space before context_end
            space_pos = response_text.rfind(' ', end_pos, context_end)
            if space_pos != -1:
                context_end = space_pos
        
        context = response_text[context_start:context_end].strip()
        return context, context_start, context_end
    
    def _analyze_sentiment(self, text: str) -> Tuple[float, SentimentType]:
        """Analyze sentiment of text"""
        if not text:
            return 0.0, SentimentType.NEUTRAL
        
        text_lower = text.lower()
        positive_count = 0
        negative_count = 0
        
        # Count sentiment keywords
        for word in self.sentiment_keywords['positive']:
            positive_count += text_lower.count(word)
        
        for word in self.sentiment_keywords['negative']:
            negative_count += text_lower.count(word)
        
        # Calculate sentiment score
        total_words = len(text.split())
        if total_words == 0:
            return 0.0, SentimentType.NEUTRAL
        
        # Normalize by text length
        positive_ratio = positive_count / max(total_words / 10, 1)
        negative_ratio = negative_count / max(total_words / 10, 1)
        
        sentiment_score = positive_ratio - negative_ratio
        sentiment_score = max(-1.0, min(1.0, sentiment_score))
        
        # Determine sentiment type
        if sentiment_score > 0.1:
            sentiment_type = SentimentType.POSITIVE
        elif sentiment_score < -0.1:
            sentiment_type = SentimentType.NEGATIVE
        elif positive_count > 0 and negative_count > 0:
            sentiment_type = SentimentType.MIXED
        else:
            sentiment_type = SentimentType.NEUTRAL
        
        return sentiment_score, sentiment_type
    
    def _calculate_prominence_score(
        self, response_text: str, start_pos: int, end_pos: int, position: int, mention_text: str
    ) -> float:
        """Calculate prominence score based on position and context"""
        base_score = 0.5
        
        # Position-based scoring
        sentences = self._split_into_sentences(response_text)
        total_sentences = len(sentences)
        
        if position == 1:
            base_score += self.prominence_indicators['first_sentence'] - 1.0
        elif position <= 3:
            base_score += self.prominence_indicators['first_paragraph'] - 1.0
        elif position == total_sentences:
            base_score += self.prominence_indicators['last_sentence'] - 1.0
        
        # Context-based scoring
        context_before = response_text[max(0, start_pos - 50):start_pos]
        context_after = response_text[end_pos:min(len(response_text), end_pos + 50)]
        
        # Check for list items
        if re.search(r'^\s*[-*•]\s*', context_before, re.MULTILINE):
            base_score += self.prominence_indicators['bullet_point'] - 1.0
        elif re.search(r'^\s*\d+\.\s*', context_before, re.MULTILINE):
            base_score += self.prominence_indicators['numbered_list'] - 1.0
        
        # Check for quotes
        if '"' in context_before and '"' in context_after:
            base_score += self.prominence_indicators['quoted'] - 1.0
        
        # Check for emphasis
        if mention_text.isupper() or '**' in context_before + context_after:
            base_score += self.prominence_indicators['emphasized'] - 1.0
        
        # Check for parenthetical
        if '(' in context_before and ')' in context_after:
            base_score += self.prominence_indicators['parenthetical'] - 1.0
        
        return max(0.0, min(1.0, base_score))
    
    def _calculate_confidence_score(
        self, mention_text: str, search_term: str, brand_name: str, context: str, mention_type: MentionType
    ) -> float:
        """Calculate confidence score for the mention"""
        confidence = 0.5
        
        # Exact match bonus
        if mention_text.lower() == brand_name.lower():
            confidence += 0.3
        elif mention_text.lower() == search_term.lower():
            confidence += 0.2
        
        # Context relevance
        if context:
            context_lower = context.lower()
            # Business/software context indicators
            business_terms = ['software', 'tool', 'platform', 'service', 'company', 'solution', 'product']
            business_count = sum(1 for term in business_terms if term in context_lower)
            confidence += min(0.2, business_count * 0.05)
        
        # Mention type confidence
        type_confidence = {
            MentionType.DIRECT: 0.9,
            MentionType.RECOMMENDATION: 0.8,
            MentionType.COMPARISON: 0.8,
            MentionType.REVIEW: 0.7,
            MentionType.FEATURE: 0.7,
            MentionType.ALTERNATIVE: 0.6,
            MentionType.QUESTION: 0.5
        }
        confidence *= type_confidence.get(mention_type, 0.6)
        
        return max(0.0, min(1.0, confidence))
    
    def _is_full_word_match(self, text: str, start_pos: int, end_pos: int) -> bool:
        """Check if match is a full word (not part of another word)"""
        # Check character before
        if start_pos > 0 and text[start_pos - 1].isalnum():
            return False
        
        # Check character after
        if end_pos < len(text) and text[end_pos].isalnum():
            return False
        
        return True
    
    def _split_into_sentences(self, text: str) -> List[str]:
        """Split text into sentences"""
        if self.nlp:
            doc = self.nlp(text)
            return [sent.text.strip() for sent in doc.sents]
        else:
            # Simple sentence splitting
            sentences = re.split(r'[.!?]+', text)
            return [s.strip() for s in sentences if s.strip()]
    
    def _deduplicate_mentions(self, mentions: List[BrandMention]) -> List[BrandMention]:
        """Remove duplicate mentions"""
        unique_mentions = []
        seen_positions = set()
        
        for mention in mentions:
            # Create a key based on position and context
            key = (mention.position, mention.context_start, mention.context_end)
            
            if key not in seen_positions:
                seen_positions.add(key)
                unique_mentions.append(mention)
            else:
                # If duplicate, keep the one with higher confidence
                for i, existing in enumerate(unique_mentions):
                    if (existing.position, existing.context_start, existing.context_end) == key:
                        if mention.confidence_score > existing.confidence_score:
                            unique_mentions[i] = mention
                        break
        
        return unique_mentions
    
    def _analyze_response_structure(
        self, response_text: str, mentions: List[BrandMention]
    ) -> Dict[str, Any]:
        """Analyze overall structure of the response"""
        sentences = self._split_into_sentences(response_text)
        
        analysis = {
            "total_sentences": len(sentences),
            "total_words": len(response_text.split()),
            "total_characters": len(response_text),
            "mentions_per_sentence": len(mentions) / max(len(sentences), 1),
            "avg_sentence_length": sum(len(s.split()) for s in sentences) / max(len(sentences), 1),
            "has_lists": bool(re.search(r'^\s*[-*•]\s*', response_text, re.MULTILINE)),
            "has_numbered_lists": bool(re.search(r'^\s*\d+\.\s*', response_text, re.MULTILINE)),
            "has_quotes": '"' in response_text,
            "mention_positions": [m.position for m in mentions],
            "mention_density": len(mentions) / max(len(response_text.split()), 1),
            "sentiment_distribution": {
                sentiment_type.value: len([m for m in mentions if m.sentiment_type == sentiment_type])
                for sentiment_type in SentimentType
            }
        }
        
        return analysis
    
    async def store_citations(self, user_id: str, result: CitationExtractionResult):
        """Store citation extraction results in database"""
        try:
            # Store query result
            query_result_id = f"query_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{user_id}"
            
            await db_manager.execute_query(
                """
                INSERT INTO query_results (id, user_id, query_text, platform, response_text, executed_at)
                VALUES (:id, :user_id, :query_text, :platform, :response_text, :executed_at)
                """,
                {
                    "id": query_result_id,
                    "user_id": user_id,
                    "query_text": result.query_text,
                    "platform": result.platform,
                    "response_text": result.response_text,
                    "executed_at": result.processed_at
                }
            )
            
            # Store individual citations
            for mention in result.brand_mentions:
                citation_id = f"citation_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{mention.brand_name}_{mention.position}"
                
                await db_manager.execute_query(
                    """
                    INSERT INTO citations (id, query_result_id, brand_name, mentioned, position, 
                                         mention_text, context, mention_type, sentiment_score, 
                                         sentiment_type, prominence_score, confidence_score, 
                                         created_at, metadata)
                    VALUES (:id, :query_result_id, :brand_name, :mentioned, :position, 
                           :mention_text, :context, :mention_type, :sentiment_score, 
                           :sentiment_type, :prominence_score, :confidence_score, 
                           :created_at, :metadata)
                    """,
                    {
                        "id": citation_id,
                        "query_result_id": query_result_id,
                        "brand_name": mention.brand_name,
                        "mentioned": mention.mentioned,
                        "position": mention.position,
                        "mention_text": mention.mention_text,
                        "context": mention.context,
                        "mention_type": mention.mention_type.value,
                        "sentiment_score": mention.sentiment_score,
                        "sentiment_type": mention.sentiment_type.value,
                        "prominence_score": mention.prominence_score,
                        "confidence_score": mention.confidence_score,
                        "created_at": mention.extracted_at,
                        "metadata": json.dumps(mention.metadata)
                    }
                )
            
            logger.info(f"Stored {len(result.brand_mentions)} citations for user {user_id}")
            
        except Exception as e:
            logger.error(f"Error storing citations: {e}")
    
    async def get_citation_analytics(
        self, user_id: str, brand_name: Optional[str] = None, days: int = 30
    ) -> Dict[str, Any]:
        """Get citation analytics for a user"""
        try:
            # Build query conditions
            conditions = ["qr.user_id = :user_id", "c.created_at >= NOW() - INTERVAL ':days days'"]
            params = {"user_id": user_id, "days": days}
            
            if brand_name:
                conditions.append("c.brand_name = :brand_name")
                params["brand_name"] = brand_name
            
            where_clause = " AND ".join(conditions)
            
            # Get citation statistics
            stats = await db_manager.fetch_one(
                f"""
                SELECT COUNT(*) as total_citations,
                       COUNT(DISTINCT c.brand_name) as brands_mentioned,
                       COUNT(DISTINCT qr.platform) as platforms_covered,
                       AVG(c.sentiment_score) as avg_sentiment,
                       AVG(c.prominence_score) as avg_prominence,
                       AVG(c.confidence_score) as avg_confidence
                FROM citations c
                JOIN query_results qr ON c.query_result_id = qr.id
                WHERE {where_clause}
                """,
                params
            )
            
            # Get sentiment distribution
            sentiment_dist = await db_manager.fetch_all(
                f"""
                SELECT c.sentiment_type, COUNT(*) as count
                FROM citations c
                JOIN query_results qr ON c.query_result_id = qr.id
                WHERE {where_clause}
                GROUP BY c.sentiment_type
                """,
                params
            )
            
            # Get mention type distribution
            mention_types = await db_manager.fetch_all(
                f"""
                SELECT c.mention_type, COUNT(*) as count
                FROM citations c
                JOIN query_results qr ON c.query_result_id = qr.id
                WHERE {where_clause}
                GROUP BY c.mention_type
                """,
                params
            )
            
            # Get platform performance
            platform_stats = await db_manager.fetch_all(
                f"""
                SELECT qr.platform, COUNT(*) as citations, AVG(c.sentiment_score) as avg_sentiment
                FROM citations c
                JOIN query_results qr ON c.query_result_id = qr.id
                WHERE {where_clause}
                GROUP BY qr.platform
                ORDER BY citations DESC
                """,
                params
            )
            
            analytics = {
                "summary": {
                    "total_citations": stats.total_citations if stats else 0,
                    "brands_mentioned": stats.brands_mentioned if stats else 0,
                    "platforms_covered": stats.platforms_covered if stats else 0,
                    "avg_sentiment": float(stats.avg_sentiment) if stats and stats.avg_sentiment else 0.0,
                    "avg_prominence": float(stats.avg_prominence) if stats and stats.avg_prominence else 0.0,
                    "avg_confidence": float(stats.avg_confidence) if stats and stats.avg_confidence else 0.0
                },
                "sentiment_distribution": {row.sentiment_type: row.count for row in sentiment_dist},
                "mention_types": {row.mention_type: row.count for row in mention_types},
                "platform_performance": [
                    {
                        "platform": row.platform,
                        "citations": row.citations,
                        "avg_sentiment": float(row.avg_sentiment) if row.avg_sentiment else 0.0
                    }
                    for row in platform_stats
                ],
                "period_days": days,
                "generated_at": datetime.utcnow()
            }
            
            return analytics
            
        except Exception as e:
            logger.error(f"Error getting citation analytics: {e}")
            return {"summary": {}, "sentiment_distribution": {}, "mention_types": {}, "platform_performance": []}


# Global service instance
citation_extraction_service = CitationExtractionService()
citation_extractor = citation_extraction_service  # Alias for compatibility