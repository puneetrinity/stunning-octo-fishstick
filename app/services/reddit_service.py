"""
Reddit Monitoring Service
Based on Reddit intelligence: 6% of ChatGPT references are from Reddit
Critical for tracking brand mentions in discussions
"""
import asyncio
import aiohttp
from typing import List, Dict, Optional, Any
from datetime import datetime, timedelta
import logging
from dataclasses import dataclass
import re
import json

from app.config import settings
from app.database import db_manager

logger = logging.getLogger(__name__)


@dataclass
class RedditMention:
    """Structure for Reddit brand mentions"""
    brand_name: str
    subreddit: str
    post_id: str
    comment_id: Optional[str]
    title: str
    content: str
    url: str
    score: int
    created_utc: datetime
    author: str
    mention_context: str
    sentiment_score: Optional[float]
    upvotes: int
    is_post: bool  # True if post, False if comment


@dataclass
class SubredditTarget:
    """Structure for targeted subreddit monitoring"""
    name: str
    industry: str
    authority_score: int
    member_count: int
    activity_level: str  # 'high', 'medium', 'low'


class RedditService:
    """
    Reddit monitoring service for tracking brand mentions
    Based on Reddit intelligence: 6% of ChatGPT sources are Reddit
    """
    
    def __init__(self):
        self.base_url = "https://www.reddit.com"
        self.api_url = "https://oauth.reddit.com"
        
        # Reddit API credentials (would need to be configured)
        self.client_id = getattr(settings, 'reddit_client_id', 'dummy_client_id')
        self.client_secret = getattr(settings, 'reddit_client_secret', 'dummy_secret')
        self.user_agent = f"ChatSEO-Platform/1.0 by /u/chatseo_bot"
        
        # Industry-specific subreddit targets based on Reddit intelligence
        self.subreddit_targets = {
            'saas': [
                SubredditTarget('r/SaaS', 'saas', 85, 150000, 'high'),
                SubredditTarget('r/entrepreneur', 'business', 90, 800000, 'high'),
                SubredditTarget('r/startups', 'business', 88, 600000, 'high'),
                SubredditTarget('r/Entrepreneur', 'business', 87, 400000, 'medium'),
                SubredditTarget('r/smallbusiness', 'business', 75, 300000, 'medium'),
                SubredditTarget('r/marketing', 'marketing', 80, 200000, 'medium'),
                SubredditTarget('r/digitalmarketing', 'marketing', 78, 150000, 'medium'),
                SubredditTarget('r/productivity', 'productivity', 82, 250000, 'medium'),
            ],
            'b2b': [
                SubredditTarget('r/B2B', 'b2b', 85, 50000, 'medium'),
                SubredditTarget('r/sales', 'sales', 88, 180000, 'high'),
                SubredditTarget('r/marketing', 'marketing', 80, 200000, 'medium'),
                SubredditTarget('r/business', 'business', 90, 500000, 'high'),
                SubredditTarget('r/entrepreneur', 'business', 90, 800000, 'high'),
                SubredditTarget('r/consulting', 'consulting', 75, 80000, 'low'),
                SubredditTarget('r/freelance', 'freelance', 70, 120000, 'medium'),
            ],
            'tech': [
                SubredditTarget('r/technology', 'tech', 95, 12000000, 'high'),
                SubredditTarget('r/programming', 'programming', 92, 4000000, 'high'),
                SubredditTarget('r/webdev', 'webdev', 85, 800000, 'high'),
                SubredditTarget('r/MachineLearning', 'ai', 88, 2000000, 'high'),
                SubredditTarget('r/artificial', 'ai', 82, 500000, 'medium'),
                SubredditTarget('r/DevOps', 'devops', 80, 300000, 'medium'),
                SubredditTarget('r/cybersecurity', 'security', 85, 600000, 'medium'),
            ],
            'fintech': [
                SubredditTarget('r/fintech', 'fintech', 85, 80000, 'medium'),
                SubredditTarget('r/investing', 'finance', 88, 1800000, 'high'),
                SubredditTarget('r/SecurityAnalysis', 'finance', 82, 150000, 'medium'),
                SubredditTarget('r/CryptoCurrency', 'crypto', 90, 5000000, 'high'),
                SubredditTarget('r/personalfinance', 'finance', 85, 15000000, 'high'),
                SubredditTarget('r/financialindependence', 'finance', 80, 1000000, 'medium'),
            ],
            'martech': [
                SubredditTarget('r/marketing', 'marketing', 80, 200000, 'medium'),
                SubredditTarget('r/digitalmarketing', 'marketing', 78, 150000, 'medium'),
                SubredditTarget('r/PPC', 'advertising', 75, 50000, 'medium'),
                SubredditTarget('r/SEO', 'seo', 85, 180000, 'high'),
                SubredditTarget('r/content_marketing', 'marketing', 70, 30000, 'low'),
                SubredditTarget('r/socialmedia', 'marketing', 75, 100000, 'medium'),
            ]
        }
    
    async def get_access_token(self) -> str:
        """Get Reddit API access token"""
        try:
            auth_url = "https://www.reddit.com/api/v1/access_token"
            
            auth_data = {
                'grant_type': 'client_credentials'
            }
            
            auth = aiohttp.BasicAuth(self.client_id, self.client_secret)
            
            headers = {
                'User-Agent': self.user_agent
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(auth_url, data=auth_data, auth=auth, headers=headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data['access_token']
                    else:
                        logger.error(f"Failed to get Reddit access token: {response.status}")
                        return None
        
        except Exception as e:
            logger.error(f"Error getting Reddit access token: {e}")
            return None
    
    async def search_subreddit_mentions(self, brand_name: str, subreddit: str, time_range: str = 'week') -> List[RedditMention]:
        """
        Search for brand mentions in a specific subreddit
        Using Reddit API or web scraping as fallback
        """
        try:
            # For MVP, we'll use web scraping approach
            # In production, use proper Reddit API
            mentions = await self._scrape_subreddit_mentions(brand_name, subreddit, time_range)
            
            logger.info(f"Found {len(mentions)} mentions for {brand_name} in {subreddit}")
            return mentions
            
        except Exception as e:
            logger.error(f"Error searching {subreddit} for {brand_name}: {e}")
            return []
    
    async def _scrape_subreddit_mentions(self, brand_name: str, subreddit: str, time_range: str) -> List[RedditMention]:
        """
        Scrape Reddit for brand mentions (fallback when API not available)
        """
        mentions = []
        
        try:
            # Search URL for Reddit
            search_url = f"{self.base_url}/{subreddit}/search"
            
            # Search parameters
            params = {
                'q': brand_name,
                'restrict_sr': 'on',
                'sort': 'new',
                't': time_range,
                'limit': 100
            }
            
            headers = {
                'User-Agent': self.user_agent
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(search_url, params=params, headers=headers) as response:
                    if response.status == 200:
                        # Parse Reddit HTML response
                        html = await response.text()
                        mentions = self._parse_reddit_html(html, brand_name, subreddit)
                    else:
                        logger.warning(f"Failed to search Reddit: {response.status}")
            
            return mentions
            
        except Exception as e:
            logger.error(f"Error scraping Reddit mentions: {e}")
            return []
    
    def _parse_reddit_html(self, html: str, brand_name: str, subreddit: str) -> List[RedditMention]:
        """
        Parse Reddit HTML to extract mentions
        Simplified parser for MVP - would need more robust parsing in production
        """
        mentions = []
        
        # This is a simplified implementation
        # In production, you'd want to use proper HTML parsing
        # and handle Reddit's dynamic content loading
        
        # For now, return empty list as placeholder
        # Real implementation would parse Reddit's HTML structure
        
        return mentions
    
    async def get_reddit_json_data(self, brand_name: str, subreddit: str, time_range: str = 'week') -> List[RedditMention]:
        """
        Get Reddit data using JSON API (more reliable than HTML scraping)
        """
        mentions = []
        
        try:
            # Use Reddit's JSON API
            json_url = f"{self.base_url}/{subreddit}/search.json"
            
            params = {
                'q': brand_name,
                'restrict_sr': 'on',
                'sort': 'new',
                't': time_range,
                'limit': 100
            }
            
            headers = {
                'User-Agent': self.user_agent
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(json_url, params=params, headers=headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        # Parse Reddit JSON response
                        if 'data' in data and 'children' in data['data']:
                            for post in data['data']['children']:
                                post_data = post['data']
                                
                                # Check if brand is mentioned in title or content
                                if self._contains_brand_mention(post_data, brand_name):
                                    mention = await self._create_reddit_mention(post_data, brand_name, subreddit)
                                    mentions.append(mention)
                    
                    else:
                        logger.warning(f"Failed to get Reddit JSON: {response.status}")
            
            return mentions
            
        except Exception as e:
            logger.error(f"Error getting Reddit JSON data: {e}")
            return []
    
    def _contains_brand_mention(self, post_data: Dict, brand_name: str) -> bool:
        """Check if post contains brand mention"""
        brand_lower = brand_name.lower()
        
        # Check title
        title = post_data.get('title', '').lower()
        if brand_lower in title:
            return True
        
        # Check selftext (post content)
        selftext = post_data.get('selftext', '').lower()
        if brand_lower in selftext:
            return True
        
        # Check URL
        url = post_data.get('url', '').lower()
        if brand_lower in url:
            return True
        
        return False
    
    async def _create_reddit_mention(self, post_data: Dict, brand_name: str, subreddit: str) -> RedditMention:
        """Create RedditMention object from post data"""
        
        # Extract mention context
        title = post_data.get('title', '')
        selftext = post_data.get('selftext', '')
        
        # Find the specific mention context
        content = f"{title} {selftext}"
        mention_context = self._extract_mention_context(content, brand_name)
        
        # Calculate sentiment
        sentiment = await self._analyze_reddit_sentiment(mention_context)
        
        return RedditMention(
            brand_name=brand_name,
            subreddit=subreddit,
            post_id=post_data.get('id', ''),
            comment_id=None,
            title=title,
            content=selftext,
            url=f"{self.base_url}{post_data.get('permalink', '')}",
            score=post_data.get('score', 0),
            created_utc=datetime.fromtimestamp(post_data.get('created_utc', 0)),
            author=post_data.get('author', ''),
            mention_context=mention_context,
            sentiment_score=sentiment,
            upvotes=post_data.get('ups', 0),
            is_post=True
        )
    
    def _extract_mention_context(self, content: str, brand_name: str) -> str:
        """Extract context around brand mention"""
        brand_lower = brand_name.lower()
        content_lower = content.lower()
        
        # Find mention position
        pos = content_lower.find(brand_lower)
        if pos == -1:
            return ""
        
        # Extract 200 characters around mention
        start = max(0, pos - 100)
        end = min(len(content), pos + len(brand_name) + 100)
        
        return content[start:end].strip()
    
    async def _analyze_reddit_sentiment(self, context: str) -> Optional[float]:
        """Analyze sentiment of Reddit mention"""
        # Simple sentiment analysis for Reddit context
        positive_indicators = [
            'recommend', 'great', 'excellent', 'love', 'amazing', 'perfect',
            'best', 'awesome', 'fantastic', 'good', 'solid', 'works well',
            'impressed', 'satisfied', 'happy', 'pleased'
        ]
        
        negative_indicators = [
            'terrible', 'awful', 'hate', 'worst', 'disappointed', 'frustrating',
            'bad', 'poor', 'useless', 'waste', 'regret', 'avoid', 'broken',
            'buggy', 'crash', 'failed', 'sucks'
        ]
        
        context_lower = context.lower()
        
        positive_count = sum(1 for word in positive_indicators if word in context_lower)
        negative_count = sum(1 for word in negative_indicators if word in context_lower)
        
        if positive_count > negative_count:
            return 0.5 + min(0.5, (positive_count - negative_count) * 0.1)
        elif negative_count > positive_count:
            return 0.5 - min(0.5, (negative_count - positive_count) * 0.1)
        else:
            return 0.0  # Neutral
    
    async def monitor_brand_across_subreddits(self, brand_name: str, industry: str, time_range: str = 'week') -> Dict[str, Any]:
        """
        Monitor brand mentions across all relevant subreddits for an industry
        Based on Reddit intelligence: Comprehensive subreddit coverage
        """
        results = {
            'brand_name': brand_name,
            'industry': industry,
            'time_range': time_range,
            'subreddits_monitored': 0,
            'total_mentions': 0,
            'mentions_by_subreddit': {},
            'top_mentions': [],
            'sentiment_analysis': {
                'positive': 0,
                'negative': 0,
                'neutral': 0,
                'average_sentiment': 0
            },
            'monitoring_timestamp': datetime.utcnow()
        }
        
        try:
            # Get subreddit targets for industry
            subreddit_targets = self.subreddit_targets.get(industry, [])
            
            if not subreddit_targets:
                logger.warning(f"No subreddit targets found for industry: {industry}")
                return results
            
            # Monitor each subreddit
            for target in subreddit_targets:
                try:
                    # Rate limiting
                    await asyncio.sleep(2.0)  # Respect Reddit's rate limits
                    
                    # Search for mentions
                    mentions = await self.get_reddit_json_data(brand_name, target.name, time_range)
                    
                    if mentions:
                        results['mentions_by_subreddit'][target.name] = {
                            'mention_count': len(mentions),
                            'authority_score': target.authority_score,
                            'member_count': target.member_count,
                            'mentions': mentions
                        }
                        
                        results['total_mentions'] += len(mentions)
                        
                        # Add to top mentions
                        for mention in mentions:
                            if mention.score > 5:  # Only high-scoring mentions
                                results['top_mentions'].append(mention)
                        
                        # Update sentiment analysis
                        for mention in mentions:
                            if mention.sentiment_score is not None:
                                if mention.sentiment_score > 0.1:
                                    results['sentiment_analysis']['positive'] += 1
                                elif mention.sentiment_score < -0.1:
                                    results['sentiment_analysis']['negative'] += 1
                                else:
                                    results['sentiment_analysis']['neutral'] += 1
                    
                    results['subreddits_monitored'] += 1
                    
                    logger.info(f"Monitored {target.name}: {len(mentions)} mentions for {brand_name}")
                    
                except Exception as e:
                    logger.error(f"Error monitoring {target.name}: {e}")
                    continue
            
            # Calculate average sentiment
            total_sentiment_mentions = sum(results['sentiment_analysis'].values())
            if total_sentiment_mentions > 0:
                weighted_sentiment = (
                    results['sentiment_analysis']['positive'] * 1.0 +
                    results['sentiment_analysis']['negative'] * -1.0 +
                    results['sentiment_analysis']['neutral'] * 0.0
                ) / total_sentiment_mentions
                results['sentiment_analysis']['average_sentiment'] = weighted_sentiment
            
            # Sort top mentions by score
            results['top_mentions'].sort(key=lambda x: x.score, reverse=True)
            results['top_mentions'] = results['top_mentions'][:10]  # Top 10
            
            logger.info(f"Reddit monitoring completed for {brand_name}: {results['total_mentions']} mentions across {results['subreddits_monitored']} subreddits")
            
            return results
            
        except Exception as e:
            logger.error(f"Error in Reddit monitoring for {brand_name}: {e}")
            raise
    
    async def store_reddit_mentions(self, user_id: str, monitoring_results: Dict[str, Any]):
        """Store Reddit mentions in database"""
        try:
            for subreddit, data in monitoring_results['mentions_by_subreddit'].items():
                for mention in data['mentions']:
                    await db_manager.execute_query(
                        """
                        INSERT INTO reddit_mentions (user_id, brand_name, subreddit, post_id, title, content, 
                                                   url, score, created_utc, author, mention_context, 
                                                   sentiment_score, upvotes, is_post)
                        VALUES (:user_id, :brand_name, :subreddit, :post_id, :title, :content, 
                                :url, :score, :created_utc, :author, :mention_context, 
                                :sentiment_score, :upvotes, :is_post)
                        ON CONFLICT (post_id, brand_name) DO UPDATE SET
                        score = EXCLUDED.score,
                        upvotes = EXCLUDED.upvotes,
                        sentiment_score = EXCLUDED.sentiment_score
                        """,
                        {
                            "user_id": user_id,
                            "brand_name": mention.brand_name,
                            "subreddit": mention.subreddit,
                            "post_id": mention.post_id,
                            "title": mention.title,
                            "content": mention.content,
                            "url": mention.url,
                            "score": mention.score,
                            "created_utc": mention.created_utc,
                            "author": mention.author,
                            "mention_context": mention.mention_context,
                            "sentiment_score": mention.sentiment_score,
                            "upvotes": mention.upvotes,
                            "is_post": mention.is_post
                        }
                    )
            
            logger.info(f"Stored Reddit mentions for user {user_id}")
            
        except Exception as e:
            logger.error(f"Error storing Reddit mentions: {e}")
            raise
    
    async def get_reddit_mention_analytics(self, user_id: str, brand_name: str, days: int = 30) -> Dict[str, Any]:
        """Get analytics for Reddit mentions"""
        try:
            since_date = datetime.utcnow() - timedelta(days=days)
            
            analytics = await db_manager.fetch_one(
                """
                SELECT 
                    COUNT(*) as total_mentions,
                    COUNT(DISTINCT subreddit) as subreddits_mentioned,
                    AVG(score) as average_score,
                    AVG(sentiment_score) as average_sentiment,
                    SUM(upvotes) as total_upvotes,
                    MAX(score) as highest_score
                FROM reddit_mentions
                WHERE user_id = :user_id 
                AND brand_name = :brand_name 
                AND created_utc >= :since_date
                """,
                {
                    "user_id": user_id,
                    "brand_name": brand_name,
                    "since_date": since_date
                }
            )
            
            return {
                "total_mentions": analytics.total_mentions or 0,
                "subreddits_mentioned": analytics.subreddits_mentioned or 0,
                "average_score": float(analytics.average_score or 0),
                "average_sentiment": float(analytics.average_sentiment or 0),
                "total_upvotes": analytics.total_upvotes or 0,
                "highest_score": analytics.highest_score or 0,
                "chatgpt_relevance": "6% of ChatGPT sources are Reddit - tracking these mentions is critical"
            }
            
        except Exception as e:
            logger.error(f"Error getting Reddit analytics: {e}")
            return {}


# Global service instance
reddit_service = RedditService()