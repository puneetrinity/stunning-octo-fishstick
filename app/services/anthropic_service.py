"""
Anthropic Claude Integration Service
Secondary AI platform for brand mentions and citations
"""
import asyncio
from typing import List, Dict, Optional, Any
import anthropic
from datetime import datetime, timedelta
import logging
from dataclasses import dataclass

from app.config import settings
from app.models.query import QueryResult
from app.models.citation import Citation
from app.database import db_manager

logger = logging.getLogger(__name__)


@dataclass
class ClaudeResponse:
    """Structure for Claude API responses"""
    query: str
    response: str
    model: str
    timestamp: datetime
    metadata: Dict[str, Any]


@dataclass
class BrandMention:
    """Structure for extracted brand mentions"""
    brand_name: str
    mentioned: bool
    position: Optional[int]
    context: str
    sentence: str
    confidence_score: float
    sentiment_score: Optional[float]
    prominence_score: Optional[float]


class AnthropicService:
    """
    Service for interacting with Anthropic Claude API and extracting brand mentions
    Secondary AI platform for comprehensive brand monitoring
    """
    
    def __init__(self):
        # Initialize Anthropic client
        self.client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)
        
        # Rate limiting settings
        self.rate_limit = {
            'requests_per_minute': 60,
            'requests_per_hour': 1000,
            'tokens_per_minute': 40000
        }
        
        # Query templates optimized for Claude's conversational style
        self.query_templates = {
            'recommendation': [
                "I'm looking for the best {category} tools for {use_case}. What would you recommend?",
                "Can you suggest some {category} software options for {industry}?",
                "What {category} solution would be best for {problem}?",
                "I need to choose between {category} options for {use_case}. What are your thoughts?",
                "Which {category} tools would you recommend for {scenario}?"
            ],
            'comparison': [
                "How do {brand} and {competitor} compare for {use_case}?",
                "What are the key differences between {brand} and {competitor}?",
                "If you had to choose between {brand} and {competitor}, which would you pick and why?",
                "Can you compare {brand} vs {competitor} for {use_case}?",
                "What are the pros and cons of {brand} compared to {competitor}?"
            ],
            'specific_inquiry': [
                "What can you tell me about {brand}?",
                "How does {brand} work and what makes it unique?",
                "What are the main benefits and drawbacks of {brand}?",
                "Is {brand} a good choice for my needs?",
                "Can you explain {brand}'s key features and capabilities?"
            ],
            'problem_solving': [
                "I need to solve {problem} - what {category} tools would you suggest?",
                "What's the best approach to {task} using {category} software?",
                "How can I effectively {task} with the right {category} solution?",
                "I'm struggling with {problem} - what {category} tools might help?"
            ],
            'industry_specific': [
                "What are the leading {category} solutions in {industry}?",
                "For a {industry} company, what {category} tools are essential?",
                "How do {industry} businesses typically handle {use_case}?",
                "What {category} trends are shaping the {industry} sector?"
            ]
        }
    
    async def query_claude(self, query: str, model: str = "claude-3-sonnet-20240229") -> ClaudeResponse:
        """
        Send query to Claude and get response
        """
        try:
            response = await self.client.messages.create(
                model=model,
                max_tokens=1500,
                temperature=0.7,
                messages=[
                    {
                        "role": "user",
                        "content": query
                    }
                ]
            )
            
            return ClaudeResponse(
                query=query,
                response=response.content[0].text,
                model=model,
                timestamp=datetime.utcnow(),
                metadata={
                    'input_tokens': response.usage.input_tokens,
                    'output_tokens': response.usage.output_tokens,
                    'stop_reason': response.stop_reason,
                    'model': response.model
                }
            )
            
        except Exception as e:
            logger.error(f"Error querying Claude: {e}")
            raise
    
    async def extract_brand_mentions(self, response: ClaudeResponse, brands: List[str]) -> List[BrandMention]:
        """
        Extract brand mentions from Claude response
        Similar to OpenAI but optimized for Claude's response patterns
        """
        mentions = []
        response_text = response.response.lower()
        
        for brand in brands:
            brand_lower = brand.lower()
            
            # Check if brand is mentioned
            if brand_lower in response_text:
                # Find all occurrences and their positions
                positions = []
                start = 0
                while True:
                    pos = response_text.find(brand_lower, start)
                    if pos == -1:
                        break
                    positions.append(pos)
                    start = pos + 1
                
                # Analyze each mention
                for i, pos in enumerate(positions):
                    # Extract context around mention
                    context_start = max(0, pos - 150)
                    context_end = min(len(response_text), pos + 150)
                    context = response.response[context_start:context_end]
                    
                    # Extract full sentence containing mention
                    sentence = self._extract_sentence(response.response, pos)
                    
                    # Calculate position score (earlier = higher score)
                    position_score = (len(response_text) - pos) / len(response_text)
                    
                    # Calculate confidence score
                    confidence = self._calculate_confidence(context, brand)
                    
                    # Calculate sentiment score
                    sentiment = await self._analyze_sentiment(sentence)
                    
                    mention = BrandMention(
                        brand_name=brand,
                        mentioned=True,
                        position=i,
                        context=context,
                        sentence=sentence,
                        confidence_score=confidence,
                        sentiment_score=sentiment,
                        prominence_score=position_score * 10  # Scale to 0-10
                    )
                    mentions.append(mention)
            else:
                # Brand not mentioned
                mention = BrandMention(
                    brand_name=brand,
                    mentioned=False,
                    position=None,
                    context="",
                    sentence="",
                    confidence_score=0.0,
                    sentiment_score=None,
                    prominence_score=None
                )
                mentions.append(mention)
        
        return mentions
    
    def _extract_sentence(self, text: str, position: int) -> str:
        """Extract the full sentence containing the mention"""
        # Find sentence boundaries
        sentences = text.split('.')
        current_pos = 0
        
        for sentence in sentences:
            if current_pos <= position <= current_pos + len(sentence):
                return sentence.strip()
            current_pos += len(sentence) + 1
        
        return ""
    
    def _calculate_confidence(self, context: str, brand: str) -> float:
        """Calculate confidence score for brand mention"""
        confidence = 0.5
        
        # Higher confidence for positive mentions
        if any(word in context.lower() for word in ['recommend', 'excellent', 'outstanding', 'superior', 'leading']):
            confidence += 0.3
        
        # Higher confidence for comparative mentions
        if any(word in context.lower() for word in ['better', 'preferred', 'top choice', 'best option']):
            confidence += 0.2
        
        # Higher confidence for detailed explanations
        if any(word in context.lower() for word in ['because', 'due to', 'thanks to', 'offers', 'provides']):
            confidence += 0.15
        
        # Claude tends to be more detailed, so adjust for longer contexts
        if len(context) > 200:
            confidence += 0.1
        
        return min(confidence, 1.0)
    
    async def _analyze_sentiment(self, sentence: str) -> Optional[float]:
        """Analyze sentiment of mention with Claude-specific patterns"""
        # Claude tends to be more nuanced, so we look for stronger indicators
        highly_positive = ['excellent', 'outstanding', 'superior', 'exceptional', 'remarkable']
        positive_words = ['good', 'great', 'solid', 'reliable', 'effective', 'useful', 'recommend']
        neutral_words = ['adequate', 'standard', 'typical', 'average', 'common']
        negative_words = ['limited', 'lacking', 'insufficient', 'problematic', 'challenging']
        highly_negative = ['poor', 'terrible', 'awful', 'disappointing', 'problematic']
        
        sentence_lower = sentence.lower()
        
        # Check for highly positive
        if any(word in sentence_lower for word in highly_positive):
            return 0.85
        
        # Check for positive
        positive_count = sum(1 for word in positive_words if word in sentence_lower)
        if positive_count > 0:
            return 0.65 + (positive_count * 0.1)
        
        # Check for highly negative
        if any(word in sentence_lower for word in highly_negative):
            return 0.15
        
        # Check for negative
        negative_count = sum(1 for word in negative_words if word in sentence_lower)
        if negative_count > 0:
            return 0.35 - (negative_count * 0.1)
        
        # Check for neutral
        if any(word in sentence_lower for word in neutral_words):
            return 0.5
        
        return 0.5  # Default neutral
    
    async def generate_monitoring_queries(self, brand_name: str, category: str, competitors: List[str]) -> List[str]:
        """
        Generate monitoring queries optimized for Claude's conversational style
        """
        queries = []
        
        # Recommendation queries
        for template in self.query_templates['recommendation']:
            queries.append(template.format(
                category=category,
                use_case=f"{category} for enterprise",
                industry="technology",
                problem=f"selecting {category} software",
                scenario=f"business {category} implementation"
            ))
        
        # Comparison queries with competitors
        for competitor in competitors:
            for template in self.query_templates['comparison']:
                queries.append(template.format(
                    brand=brand_name,
                    competitor=competitor,
                    use_case=f"{category} solution"
                ))
        
        # Specific brand inquiry
        for template in self.query_templates['specific_inquiry']:
            queries.append(template.format(brand=brand_name))
        
        # Problem-solving queries
        for template in self.query_templates['problem_solving']:
            queries.append(template.format(
                problem=f"optimizing {category} processes",
                task=f"implement {category} solution",
                category=category
            ))
        
        # Industry-specific queries
        for template in self.query_templates['industry_specific']:
            queries.append(template.format(
                category=category,
                industry="B2B technology",
                use_case=f"{category} automation"
            ))
        
        return queries
    
    async def run_monitoring_session(self, user_id: str, brand_names: List[str], category: str, competitors: List[str] = None) -> Dict[str, Any]:
        """
        Run a complete monitoring session for brands using Claude
        """
        competitors = competitors or []
        results = {
            'session_id': f"claude_session_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
            'user_id': user_id,
            'brands': brand_names,
            'queries_executed': 0,
            'total_mentions': 0,
            'brand_results': {},
            'session_start': datetime.utcnow(),
            'platform': 'anthropic'
        }
        
        try:
            # Generate monitoring queries
            queries = await self.generate_monitoring_queries(
                brand_names[0],  # Primary brand
                category,
                competitors
            )
            
            logger.info(f"Generated {len(queries)} Claude monitoring queries for user {user_id}")
            
            # Execute queries with rate limiting
            for query in queries:
                try:
                    # Rate limiting - Claude has lower limits
                    await asyncio.sleep(1.5)  # More conservative rate limiting
                    
                    # Query Claude
                    response = await self.query_claude(query)
                    
                    # Extract mentions
                    mentions = await self.extract_brand_mentions(response, brand_names)
                    
                    # Store results
                    await self._store_query_result(user_id, query, response, mentions)
                    
                    results['queries_executed'] += 1
                    results['total_mentions'] += len([m for m in mentions if m.mentioned])
                    
                    # Update brand results
                    for mention in mentions:
                        if mention.brand_name not in results['brand_results']:
                            results['brand_results'][mention.brand_name] = {
                                'total_mentions': 0,
                                'avg_position': 0,
                                'avg_sentiment': 0,
                                'avg_prominence': 0,
                                'avg_confidence': 0
                            }
                        
                        if mention.mentioned:
                            brand_result = results['brand_results'][mention.brand_name]
                            brand_result['total_mentions'] += 1
                            if mention.sentiment_score:
                                brand_result['avg_sentiment'] += mention.sentiment_score
                            if mention.prominence_score:
                                brand_result['avg_prominence'] += mention.prominence_score
                            if mention.confidence_score:
                                brand_result['avg_confidence'] += mention.confidence_score
                    
                    logger.info(f"Processed Claude query: {query[:50]}... - Found {len([m for m in mentions if m.mentioned])} mentions")
                    
                except Exception as e:
                    logger.error(f"Error processing Claude query '{query}': {e}")
                    continue
            
            # Calculate averages
            for brand_name, brand_result in results['brand_results'].items():
                if brand_result['total_mentions'] > 0:
                    brand_result['avg_sentiment'] /= brand_result['total_mentions']
                    brand_result['avg_prominence'] /= brand_result['total_mentions']
                    brand_result['avg_confidence'] /= brand_result['total_mentions']
            
            results['session_end'] = datetime.utcnow()
            results['duration_minutes'] = (results['session_end'] - results['session_start']).total_seconds() / 60
            
            logger.info(f"Claude monitoring session completed for user {user_id}: {results['queries_executed']} queries, {results['total_mentions']} mentions")
            
            return results
            
        except Exception as e:
            logger.error(f"Error in Claude monitoring session for user {user_id}: {e}")
            raise
    
    async def _store_query_result(self, user_id: str, query: str, response: ClaudeResponse, mentions: List[BrandMention]):
        """Store query result and citations in database"""
        try:
            # Store query result
            query_result_id = await db_manager.execute_query(
                """
                INSERT INTO query_results (user_id, query_text, platform, response_text, executed_at)
                VALUES (:user_id, :query_text, :platform, :response_text, :executed_at)
                RETURNING id
                """,
                {
                    "user_id": user_id,
                    "query_text": query,
                    "platform": "anthropic",
                    "response_text": response.response,
                    "executed_at": response.timestamp
                }
            )
            
            # Store citations
            for mention in mentions:
                if mention.mentioned:
                    await db_manager.execute_query(
                        """
                        INSERT INTO citations (query_result_id, brand_name, mentioned, position, context, sentence, 
                                             sentiment_score, prominence_score, confidence_score, entity_type)
                        VALUES (:query_result_id, :brand_name, :mentioned, :position, :context, :sentence,
                                :sentiment_score, :prominence_score, :confidence_score, :entity_type)
                        """,
                        {
                            "query_result_id": query_result_id,
                            "brand_name": mention.brand_name,
                            "mentioned": mention.mentioned,
                            "position": mention.position,
                            "context": mention.context,
                            "sentence": mention.sentence,
                            "sentiment_score": mention.sentiment_score,
                            "prominence_score": mention.prominence_score,
                            "confidence_score": mention.confidence_score,
                            "entity_type": "ORG"
                        }
                    )
            
        except Exception as e:
            logger.error(f"Error storing Claude query result: {e}")
            raise


# Global service instance
anthropic_service = AnthropicService()