"""
OpenAI/ChatGPT Integration Service
Primary intelligence source for brand mentions and citations
"""
import asyncio
from typing import List, Dict, Optional, Any
import openai
from datetime import datetime, timedelta
import logging
from dataclasses import dataclass

from app.config import settings
from app.models.query import QueryResult
from app.models.citation import Citation
from app.database import db_manager

logger = logging.getLogger(__name__)


@dataclass
class ChatGPTResponse:
    """Structure for ChatGPT API responses"""
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


class OpenAIService:
    """
    Service for interacting with OpenAI API and extracting brand mentions
    Based on Reddit intelligence: Primary source for ChatGPT citations
    """
    
    def __init__(self):
        # Initialize OpenAI client
        openai.api_key = settings.openai_api_key
        self.client = openai.AsyncOpenAI(api_key=settings.openai_api_key)
        
        # Rate limiting settings
        self.rate_limit = {
            'requests_per_minute': 60,
            'requests_per_hour': 3500,
            'tokens_per_minute': 150000
        }
        
        # Query templates based on Reddit intelligence
        self.query_templates = {
            'recommendation': [
                "What are the best {category} tools for {use_case}?",
                "Recommend {category} software for {industry}",
                "What {category} solution should I use for {problem}?",
                "Compare {category} options for {use_case}",
                "Which {category} tools do you recommend for {scenario}?"
            ],
            'comparison': [
                "Compare {brand} vs {competitor}",
                "{brand} vs {competitor} - which is better?",
                "What's the difference between {brand} and {competitor}?",
                "{brand} or {competitor} for {use_case}?",
                "Should I choose {brand} or {competitor}?"
            ],
            'specific_inquiry': [
                "Tell me about {brand}",
                "What is {brand} used for?",
                "How does {brand} work?",
                "What are the pros and cons of {brand}?",
                "Is {brand} worth it?"
            ],
            'problem_solving': [
                "How to solve {problem} with {category} tools?",
                "Best way to {task} using {category} software?",
                "What's the most effective {category} solution for {problem}?",
                "I need to {task}, what {category} tool should I use?"
            ]
        }
    
    async def query_chatgpt(self, query: str, model: str = "gpt-4") -> ChatGPTResponse:
        """
        Send query to ChatGPT and get response
        """
        try:
            response = await self.client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": "You are a helpful assistant providing informative recommendations and comparisons."},
                    {"role": "user", "content": query}
                ],
                temperature=0.7,
                max_tokens=1000,
                top_p=1.0,
                frequency_penalty=0.0,
                presence_penalty=0.0
            )
            
            return ChatGPTResponse(
                query=query,
                response=response.choices[0].message.content,
                model=model,
                timestamp=datetime.utcnow(),
                metadata={
                    'tokens_used': response.usage.total_tokens,
                    'prompt_tokens': response.usage.prompt_tokens,
                    'completion_tokens': response.usage.completion_tokens,
                    'finish_reason': response.choices[0].finish_reason
                }
            )
            
        except Exception as e:
            logger.error(f"Error querying ChatGPT: {e}")
            raise
    
    async def extract_brand_mentions(self, response: ChatGPTResponse, brands: List[str]) -> List[BrandMention]:
        """
        Extract brand mentions from ChatGPT response
        Based on Reddit intelligence: Track mentions, position, and context
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
                    context_start = max(0, pos - 100)
                    context_end = min(len(response_text), pos + 100)
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
        # Simple heuristic - can be improved with ML
        confidence = 0.5
        
        # Higher confidence if brand is mentioned with specific context
        if any(word in context.lower() for word in ['recommend', 'best', 'good', 'excellent']):
            confidence += 0.2
        
        # Higher confidence if brand is mentioned in comparison
        if any(word in context.lower() for word in ['vs', 'versus', 'compared to', 'better than']):
            confidence += 0.1
        
        # Higher confidence if brand is mentioned with features
        if any(word in context.lower() for word in ['features', 'capabilities', 'offers', 'provides']):
            confidence += 0.1
        
        return min(confidence, 1.0)
    
    async def _analyze_sentiment(self, sentence: str) -> Optional[float]:
        """Analyze sentiment of mention (simple implementation)"""
        # Simple sentiment analysis - can be improved with proper NLP
        positive_words = ['good', 'great', 'excellent', 'best', 'recommend', 'love', 'amazing', 'perfect']
        negative_words = ['bad', 'terrible', 'worst', 'awful', 'hate', 'disappointing', 'poor']
        
        sentence_lower = sentence.lower()
        
        positive_count = sum(1 for word in positive_words if word in sentence_lower)
        negative_count = sum(1 for word in negative_words if word in sentence_lower)
        
        if positive_count > negative_count:
            return 0.5 + (positive_count - negative_count) * 0.1
        elif negative_count > positive_count:
            return 0.5 - (negative_count - positive_count) * 0.1
        else:
            return 0.0  # Neutral
    
    async def generate_monitoring_queries(self, brand_name: str, category: str, competitors: List[str]) -> List[str]:
        """
        Generate monitoring queries based on Reddit intelligence
        Focus on scenarios where brands are typically mentioned
        """
        queries = []
        
        # Recommendation queries
        for template in self.query_templates['recommendation']:
            queries.append(template.format(
                category=category,
                use_case=f"{category} for business",
                industry="B2B",
                problem=f"choosing {category} software",
                scenario=f"enterprise {category}"
            ))
        
        # Comparison queries with competitors
        for competitor in competitors:
            for template in self.query_templates['comparison']:
                queries.append(template.format(
                    brand=brand_name,
                    competitor=competitor,
                    use_case=f"{category} implementation"
                ))
        
        # Specific brand inquiry
        for template in self.query_templates['specific_inquiry']:
            queries.append(template.format(brand=brand_name))
        
        # Problem-solving queries
        for template in self.query_templates['problem_solving']:
            queries.append(template.format(
                problem=f"improving {category} processes",
                task=f"implement {category} solution",
                category=category
            ))
        
        return queries
    
    async def run_monitoring_session(self, user_id: str, brand_names: List[str], category: str, competitors: List[str] = None) -> Dict[str, Any]:
        """
        Run a complete monitoring session for brands
        Based on Reddit intelligence: Comprehensive query approach
        """
        competitors = competitors or []
        results = {
            'session_id': f"session_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
            'user_id': user_id,
            'brands': brand_names,
            'queries_executed': 0,
            'total_mentions': 0,
            'brand_results': {},
            'session_start': datetime.utcnow()
        }
        
        try:
            # Generate monitoring queries
            queries = await self.generate_monitoring_queries(
                brand_names[0],  # Primary brand
                category,
                competitors
            )
            
            logger.info(f"Generated {len(queries)} monitoring queries for user {user_id}")
            
            # Execute queries with rate limiting
            for query in queries:
                try:
                    # Rate limiting
                    await asyncio.sleep(1.0)  # Simple rate limiting
                    
                    # Query ChatGPT
                    response = await self.query_chatgpt(query)
                    
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
                                'avg_prominence': 0
                            }
                        
                        if mention.mentioned:
                            brand_result = results['brand_results'][mention.brand_name]
                            brand_result['total_mentions'] += 1
                            if mention.sentiment_score:
                                brand_result['avg_sentiment'] += mention.sentiment_score
                            if mention.prominence_score:
                                brand_result['avg_prominence'] += mention.prominence_score
                    
                    logger.info(f"Processed query: {query[:50]}... - Found {len([m for m in mentions if m.mentioned])} mentions")
                    
                except Exception as e:
                    logger.error(f"Error processing query '{query}': {e}")
                    continue
            
            # Calculate averages
            for brand_name, brand_result in results['brand_results'].items():
                if brand_result['total_mentions'] > 0:
                    brand_result['avg_sentiment'] /= brand_result['total_mentions']
                    brand_result['avg_prominence'] /= brand_result['total_mentions']
            
            results['session_end'] = datetime.utcnow()
            results['duration_minutes'] = (results['session_end'] - results['session_start']).total_seconds() / 60
            
            logger.info(f"Monitoring session completed for user {user_id}: {results['queries_executed']} queries, {results['total_mentions']} mentions")
            
            return results
            
        except Exception as e:
            logger.error(f"Error in monitoring session for user {user_id}: {e}")
            raise
    
    async def _store_query_result(self, user_id: str, query: str, response: ChatGPTResponse, mentions: List[BrandMention]):
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
                    "platform": "openai",
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
            logger.error(f"Error storing query result: {e}")
            raise


# Global service instance
openai_service = OpenAIService()