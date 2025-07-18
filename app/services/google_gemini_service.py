"""
Google Gemini Integration Service
Third AI platform for comprehensive brand monitoring
"""
import asyncio
from typing import List, Dict, Optional, Any
import google.generativeai as genai
from datetime import datetime, timedelta
import logging
from dataclasses import dataclass
import json

from app.config import settings
from app.models.query import QueryResult
from app.models.citation import Citation
from app.database import db_manager

logger = logging.getLogger(__name__)


@dataclass
class GeminiResponse:
    """Structure for Gemini API responses"""
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


class GoogleGeminiService:
    """
    Service for interacting with Google Gemini API and extracting brand mentions
    Third AI platform for comprehensive brand monitoring coverage
    """
    
    def __init__(self):
        # Configure Gemini API (lazy initialization)
        self._model = None
        
        # Rate limiting settings
        self.rate_limit = {
            'requests_per_minute': 60,
            'requests_per_hour': 1000,
            'tokens_per_minute': 32000
        }
        
        # Query templates optimized for Gemini's response style
        self.query_templates = {
            'recommendation': [
                "What are the top {category} solutions for {use_case}? Please provide detailed recommendations.",
                "I need {category} software for {industry}. What would you suggest and why?",
                "Help me choose the best {category} tool for {problem}. What are the key options?",
                "What {category} platforms would you recommend for {scenario}? Explain your reasoning.",
                "List and compare the leading {category} solutions for {use_case}."
            ],
            'comparison': [
                "Compare {brand} and {competitor} for {use_case}. What are the key differences?",
                "Which is better for {use_case}: {brand} or {competitor}? Explain your analysis.",
                "Analyze {brand} vs {competitor} - strengths, weaknesses, and best use cases.",
                "How do {brand} and {competitor} stack up against each other?",
                "Provide a detailed comparison of {brand} and {competitor} for {use_case}."
            ],
            'specific_inquiry': [
                "Provide a comprehensive overview of {brand} - features, benefits, and use cases.",
                "What makes {brand} unique in the market? Analyze its key differentiators.",
                "Explain {brand}'s capabilities and how it compares to alternatives.",
                "Is {brand} a good solution? Analyze its pros and cons thoroughly.",
                "Break down {brand}'s value proposition and target market."
            ],
            'problem_solving': [
                "I need to solve {problem} in {industry}. What {category} tools can help?",
                "What's the most effective way to {task} using {category} technology?",
                "How can {category} solutions address {problem}? Recommend specific tools.",
                "What {category} approach would work best for {problem}? Provide detailed guidance."
            ],
            'market_analysis': [
                "What are the current trends in {category} for {industry}?",
                "Analyze the {category} market landscape and key players.",
                "What's driving innovation in {category} solutions?",
                "How is the {category} market evolving? Identify key trends and leaders."
            ],
            'use_case_specific': [
                "For {use_case}, what are the most important {category} features to consider?",
                "How do different {category} solutions handle {use_case}?",
                "What {category} capabilities are essential for {use_case}?",
                "Compare how leading {category} platforms approach {use_case}."
            ]
        }
    
    @property
    def model(self):
        """Lazy initialization of Gemini model"""
        if self._model is None:
            try:
                genai.configure(api_key=settings.google_api_key)
                self._model = genai.GenerativeModel('gemini-pro')
            except Exception as e:
                logger.error(f"Failed to initialize Gemini model: {e}")
                self._model = None
        return self._model
    
    async def query_gemini(self, query: str, model: str = "gemini-pro") -> GeminiResponse:
        """
        Send query to Gemini and get response
        """
        try:
            if self.model is None:
                return GeminiResponse(
                    query=query,
                    response="Gemini model not available",
                    model=model,
                    usage={"total_tokens": 0, "prompt_tokens": 0, "completion_tokens": 0},
                    response_id="mock_response",
                    created_at=datetime.utcnow()
                )
            
            # Configure generation settings
            generation_config = genai.types.GenerationConfig(
                temperature=0.7,
                top_p=0.8,
                top_k=40,
                max_output_tokens=2048,
            )
            
            # Generate response
            response = self.model.generate_content(
                query,
                generation_config=generation_config,
                safety_settings={
                    genai.types.HarmCategory.HARM_CATEGORY_HARASSMENT: genai.types.HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
                    genai.types.HarmCategory.HARM_CATEGORY_HATE_SPEECH: genai.types.HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
                    genai.types.HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: genai.types.HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
                    genai.types.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: genai.types.HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
                }
            )
            
            return GeminiResponse(
                query=query,
                response=response.text,
                model=model,
                timestamp=datetime.utcnow(),
                metadata={
                    'finish_reason': str(response.candidates[0].finish_reason),
                    'safety_ratings': [
                        {
                            'category': str(rating.category),
                            'probability': str(rating.probability)
                        }
                        for rating in response.candidates[0].safety_ratings
                    ],
                    'model': model
                }
            )
            
        except Exception as e:
            logger.error(f"Error querying Gemini: {e}")
            raise
    
    async def extract_brand_mentions(self, response: GeminiResponse, brands: List[str]) -> List[BrandMention]:
        """
        Extract brand mentions from Gemini response
        Optimized for Gemini's structured response patterns
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
                    context_start = max(0, pos - 200)
                    context_end = min(len(response_text), pos + 200)
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
        
        # Higher confidence for structured recommendations
        if any(word in context.lower() for word in ['recommended', 'top choice', 'leading', 'best', 'preferred']):
            confidence += 0.25
        
        # Higher confidence for detailed analysis
        if any(word in context.lower() for word in ['analysis', 'comparison', 'evaluation', 'assessment']):
            confidence += 0.2
        
        # Higher confidence for specific features/benefits
        if any(word in context.lower() for word in ['features', 'benefits', 'capabilities', 'advantages']):
            confidence += 0.15
        
        # Gemini provides structured responses, so look for listing patterns
        if any(pattern in context.lower() for pattern in ['1.', '2.', '•', '*', '-']):
            confidence += 0.1
        
        # Higher confidence for comparative statements
        if any(word in context.lower() for word in ['compared to', 'versus', 'against', 'alternative']):
            confidence += 0.15
        
        return min(confidence, 1.0)
    
    async def _analyze_sentiment(self, sentence: str) -> Optional[float]:
        """Analyze sentiment of mention with Gemini-specific patterns"""
        # Gemini tends to be analytical and structured
        highly_positive = ['excellent', 'outstanding', 'superior', 'leading', 'top-tier', 'industry-leading']
        positive_words = ['good', 'effective', 'solid', 'reliable', 'recommended', 'preferred', 'strong']
        neutral_words = ['available', 'option', 'alternative', 'standard', 'typical', 'common']
        negative_words = ['limited', 'lacking', 'weak', 'challenges', 'issues', 'problems']
        highly_negative = ['poor', 'inadequate', 'problematic', 'disappointing', 'insufficient']
        
        sentence_lower = sentence.lower()
        
        # Check for highly positive indicators
        if any(word in sentence_lower for word in highly_positive):
            return 0.9
        
        # Check for positive indicators
        positive_count = sum(1 for word in positive_words if word in sentence_lower)
        if positive_count > 0:
            return 0.7 + (positive_count * 0.05)
        
        # Check for highly negative indicators
        if any(word in sentence_lower for word in highly_negative):
            return 0.1
        
        # Check for negative indicators
        negative_count = sum(1 for word in negative_words if word in sentence_lower)
        if negative_count > 0:
            return 0.3 - (negative_count * 0.05)
        
        # Check for neutral indicators
        if any(word in sentence_lower for word in neutral_words):
            return 0.5
        
        return 0.5  # Default neutral
    
    async def generate_monitoring_queries(self, brand_name: str, category: str, competitors: List[str]) -> List[str]:
        """
        Generate monitoring queries optimized for Gemini's analytical style
        """
        queries = []
        
        # Recommendation queries
        for template in self.query_templates['recommendation']:
            queries.append(template.format(
                category=category,
                use_case=f"enterprise {category}",
                industry="B2B technology",
                problem=f"choosing {category} solution",
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
                problem=f"optimizing {category} workflow",
                task=f"streamline {category} processes",
                category=category,
                industry="technology"
            ))
        
        # Market analysis queries
        for template in self.query_templates['market_analysis']:
            queries.append(template.format(
                category=category,
                industry="technology"
            ))
        
        # Use case specific queries
        for template in self.query_templates['use_case_specific']:
            queries.append(template.format(
                use_case=f"enterprise {category}",
                category=category
            ))
        
        return queries
    
    async def run_monitoring_session(self, user_id: str, brand_names: List[str], category: str, competitors: List[str] = None) -> Dict[str, Any]:
        """
        Run a complete monitoring session for brands using Gemini
        """
        competitors = competitors or []
        results = {
            'session_id': f"gemini_session_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
            'user_id': user_id,
            'brands': brand_names,
            'queries_executed': 0,
            'total_mentions': 0,
            'brand_results': {},
            'session_start': datetime.utcnow(),
            'platform': 'google_gemini'
        }
        
        try:
            # Generate monitoring queries
            queries = await self.generate_monitoring_queries(
                brand_names[0],  # Primary brand
                category,
                competitors
            )
            
            logger.info(f"Generated {len(queries)} Gemini monitoring queries for user {user_id}")
            
            # Execute queries with rate limiting
            for query in queries:
                try:
                    # Rate limiting for Gemini
                    await asyncio.sleep(2.0)  # Conservative rate limiting
                    
                    # Query Gemini
                    response = await self.query_gemini(query)
                    
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
                    
                    logger.info(f"Processed Gemini query: {query[:50]}... - Found {len([m for m in mentions if m.mentioned])} mentions")
                    
                except Exception as e:
                    logger.error(f"Error processing Gemini query '{query}': {e}")
                    continue
            
            # Calculate averages
            for brand_name, brand_result in results['brand_results'].items():
                if brand_result['total_mentions'] > 0:
                    brand_result['avg_sentiment'] /= brand_result['total_mentions']
                    brand_result['avg_prominence'] /= brand_result['total_mentions']
                    brand_result['avg_confidence'] /= brand_result['total_mentions']
            
            results['session_end'] = datetime.utcnow()
            results['duration_minutes'] = (results['session_end'] - results['session_start']).total_seconds() / 60
            
            logger.info(f"Gemini monitoring session completed for user {user_id}: {results['queries_executed']} queries, {results['total_mentions']} mentions")
            
            return results
            
        except Exception as e:
            logger.error(f"Error in Gemini monitoring session for user {user_id}: {e}")
            raise
    
    async def _store_query_result(self, user_id: str, query: str, response: GeminiResponse, mentions: List[BrandMention]):
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
                    "platform": "google_gemini",
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
            logger.error(f"Error storing Gemini query result: {e}")
            raise


# Global service instance
google_gemini_service = GoogleGeminiService()