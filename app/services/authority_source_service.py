"""
Authority Source Tracking Service
Based on Reddit intelligence: "Ideally you want a series of mentions from totally unconnected sources that are authoritive"
Track mentions from high-authority industry sources for AI citation potential
"""
import asyncio
import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
import aiohttp
import json
import re
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from app.database import db_manager

logger = logging.getLogger(__name__)


class AuthorityLevel(Enum):
    TIER_1 = "tier_1"  # 90-100: Major publications, industry leaders
    TIER_2 = "tier_2"  # 80-89: Established industry publications
    TIER_3 = "tier_3"  # 70-79: Niche publications, expert blogs
    TIER_4 = "tier_4"  # 60-69: General business publications
    EMERGING = "emerging"  # 50-59: New but promising sources


class SourceType(Enum):
    NEWS_PUBLICATION = "news_publication"
    INDUSTRY_BLOG = "industry_blog"
    ANALYST_REPORT = "analyst_report"
    EXPERT_BLOG = "expert_blog"
    TRADE_PUBLICATION = "trade_publication"
    ACADEMIC_SOURCE = "academic_source"
    CONFERENCE_SITE = "conference_site"
    PODCAST_PLATFORM = "podcast_platform"


@dataclass
class AuthoritySource:
    """Authority source configuration"""
    id: str
    name: str
    domain: str
    industry: str
    source_type: SourceType
    authority_level: AuthorityLevel
    authority_score: int
    ai_citation_frequency: float
    content_types: List[str]
    contact_email: Optional[str]
    submission_guidelines: Optional[str]
    average_response_time: Optional[int]  # days
    success_rate: Optional[float]
    cost_estimate: Optional[str]
    scraping_enabled: bool
    api_available: bool
    rss_feed: Optional[str]
    notes: Optional[str]
    is_active: bool


@dataclass
class AuthorityMention:
    """Single mention found on an authority source"""
    authority_source_id: str
    source_name: str
    brand_name: str
    mention_url: str
    mention_title: str
    mention_content: str
    publish_date: datetime
    author: str
    mention_context: str
    ai_citation_potential: float
    prominence_score: float
    sentiment_score: float
    estimated_reach: int
    backlink_value: float
    discovered_at: datetime
    is_verified: bool


@dataclass
class AuthorityMonitoringResult:
    """Results from monitoring authority sources"""
    brand_name: str
    sources_monitored: List[str]
    total_mentions: int
    mentions_by_source: Dict[str, List[AuthorityMention]]
    authority_distribution: Dict[str, int]
    ai_citation_potential: float
    estimated_total_reach: int
    recommendations: List[str]
    monitoring_completed_at: datetime


class AuthoritySourceService:
    """
    Track brand mentions from authoritative industry sources
    Focus on "totally unconnected sources that are authoritive" for AI citation potential
    """
    
    def __init__(self):
        self.session = None
        self.authority_sources = self._build_authority_sources_database()
        
        # Headers for web scraping
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession(
            headers=self.headers,
            timeout=aiohttp.ClientTimeout(total=30)
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    def _build_authority_sources_database(self) -> Dict[str, Dict[str, List[AuthoritySource]]]:
        """Build comprehensive database of authority sources by industry"""
        return {
            "saas": {
                "tier_1": [
                    AuthoritySource(
                        id="techcrunch",
                        name="TechCrunch",
                        domain="techcrunch.com",
                        industry="saas",
                        source_type=SourceType.NEWS_PUBLICATION,
                        authority_level=AuthorityLevel.TIER_1,
                        authority_score=95,
                        ai_citation_frequency=0.85,
                        content_types=["news", "reviews", "analysis"],
                        contact_email="tips@techcrunch.com",
                        submission_guidelines="https://techcrunch.com/tips/",
                        average_response_time=7,
                        success_rate=0.15,
                        cost_estimate="Free editorial",
                        scraping_enabled=True,
                        api_available=False,
                        rss_feed="https://techcrunch.com/feed/",
                        notes="High authority, frequently cited by AI",
                        is_active=True
                    ),
                    AuthoritySource(
                        id="venturebeat",
                        name="VentureBeat",
                        domain="venturebeat.com",
                        industry="saas",
                        source_type=SourceType.NEWS_PUBLICATION,
                        authority_level=AuthorityLevel.TIER_1,
                        authority_score=90,
                        ai_citation_frequency=0.78,
                        content_types=["news", "analysis", "enterprise"],
                        contact_email="news@venturebeat.com",
                        submission_guidelines="https://venturebeat.com/about/",
                        average_response_time=10,
                        success_rate=0.12,
                        cost_estimate="Free editorial",
                        scraping_enabled=True,
                        api_available=False,
                        rss_feed="https://venturebeat.com/feed/",
                        notes="Strong enterprise focus",
                        is_active=True
                    )
                ],
                "tier_2": [
                    AuthoritySource(
                        id="saasmag",
                        name="SaaS Magazine",
                        domain="saasmagazine.com",
                        industry="saas",
                        source_type=SourceType.TRADE_PUBLICATION,
                        authority_level=AuthorityLevel.TIER_2,
                        authority_score=82,
                        ai_citation_frequency=0.65,
                        content_types=["reviews", "guides", "comparisons"],
                        contact_email="editor@saasmagazine.com",
                        submission_guidelines="Contributor guidelines available",
                        average_response_time=14,
                        success_rate=0.25,
                        cost_estimate="Free or $500-1500 sponsored",
                        scraping_enabled=True,
                        api_available=False,
                        rss_feed="https://saasmagazine.com/feed/",
                        notes="SaaS-specific content",
                        is_active=True
                    ),
                    AuthoritySource(
                        id="producthunt",
                        name="Product Hunt",
                        domain="producthunt.com",
                        industry="saas",
                        source_type=SourceType.INDUSTRY_BLOG,
                        authority_level=AuthorityLevel.TIER_2,
                        authority_score=85,
                        ai_citation_frequency=0.70,
                        content_types=["product launches", "reviews"],
                        contact_email="hello@producthunt.com",
                        submission_guidelines="Self-serve platform",
                        average_response_time=1,
                        success_rate=0.80,
                        cost_estimate="Free",
                        scraping_enabled=True,
                        api_available=True,
                        rss_feed="https://producthunt.com/feed",
                        notes="Launch platform, high AI visibility",
                        is_active=True
                    )
                ]
            },
            "fintech": {
                "tier_1": [
                    AuthoritySource(
                        id="american_banker",
                        name="American Banker",
                        domain="americanbanker.com",
                        industry="fintech",
                        source_type=SourceType.TRADE_PUBLICATION,
                        authority_level=AuthorityLevel.TIER_1,
                        authority_score=93,
                        ai_citation_frequency=0.80,
                        content_types=["news", "analysis", "regulation"],
                        contact_email="newsroom@americanbanker.com",
                        submission_guidelines="Professional journalists only",
                        average_response_time=14,
                        success_rate=0.08,
                        cost_estimate="Editorial only",
                        scraping_enabled=True,
                        api_available=False,
                        rss_feed="https://americanbanker.com/feed",
                        notes="Regulatory authority",
                        is_active=True
                    )
                ],
                "tier_2": [
                    AuthoritySource(
                        id="fintechnews",
                        name="FinTech News",
                        domain="fintechnews.org",
                        industry="fintech",
                        source_type=SourceType.INDUSTRY_BLOG,
                        authority_level=AuthorityLevel.TIER_2,
                        authority_score=80,
                        ai_citation_frequency=0.60,
                        content_types=["news", "interviews", "analysis"],
                        contact_email="editor@fintechnews.org",
                        submission_guidelines="Guest posts accepted",
                        average_response_time=7,
                        success_rate=0.30,
                        cost_estimate="Free or $300-800 sponsored",
                        scraping_enabled=True,
                        api_available=False,
                        rss_feed="https://fintechnews.org/feed/",
                        notes="Global fintech focus",
                        is_active=True
                    )
                ]
            },
            "martech": {
                "tier_1": [
                    AuthoritySource(
                        id="marketing_land",
                        name="Marketing Land",
                        domain="marketingland.com",
                        industry="martech",
                        source_type=SourceType.NEWS_PUBLICATION,
                        authority_level=AuthorityLevel.TIER_1,
                        authority_score=88,
                        ai_citation_frequency=0.75,
                        content_types=["news", "guides", "tool reviews"],
                        contact_email="tips@marketingland.com",
                        submission_guidelines="Expert contributors only",
                        average_response_time=10,
                        success_rate=0.15,
                        cost_estimate="Editorial only",
                        scraping_enabled=True,
                        api_available=False,
                        rss_feed="https://marketingland.com/feed",
                        notes="Marketing technology authority",
                        is_active=True
                    )
                ],
                "tier_2": [
                    AuthoritySource(
                        id="martech_today",
                        name="MarTech Today",
                        domain="martechtoday.com",
                        industry="martech",
                        source_type=SourceType.TRADE_PUBLICATION,
                        authority_level=AuthorityLevel.TIER_2,
                        authority_score=83,
                        ai_citation_frequency=0.68,
                        content_types=["analysis", "vendor spotlights", "trends"],
                        contact_email="editor@martechtoday.com",
                        submission_guidelines="Industry experts welcomed",
                        average_response_time=14,
                        success_rate=0.20,
                        cost_estimate="Free or $400-1000 sponsored",
                        scraping_enabled=True,
                        api_available=False,
                        rss_feed="https://martechtoday.com/feed",
                        notes="MarTech ecosystem focus",
                        is_active=True
                    )
                ]
            },
            "general": {
                "tier_1": [
                    AuthoritySource(
                        id="forbes",
                        name="Forbes",
                        domain="forbes.com",
                        industry="general",
                        source_type=SourceType.NEWS_PUBLICATION,
                        authority_level=AuthorityLevel.TIER_1,
                        authority_score=98,
                        ai_citation_frequency=0.90,
                        content_types=["business news", "profiles", "analysis"],
                        contact_email="tips@forbes.com",
                        submission_guidelines="Contributors council",
                        average_response_time=21,
                        success_rate=0.05,
                        cost_estimate="Editorial only",
                        scraping_enabled=True,
                        api_available=False,
                        rss_feed="https://forbes.com/innovation/feed/",
                        notes="Highest authority score",
                        is_active=True
                    ),
                    AuthoritySource(
                        id="inc_magazine",
                        name="Inc. Magazine",
                        domain="inc.com",
                        industry="general",
                        source_type=SourceType.NEWS_PUBLICATION,
                        authority_level=AuthorityLevel.TIER_1,
                        authority_score=92,
                        ai_citation_frequency=0.82,
                        content_types=["startup news", "growth", "leadership"],
                        contact_email="editors@inc.com",
                        submission_guidelines="Expert bylines accepted",
                        average_response_time=14,
                        success_rate=0.10,
                        cost_estimate="Editorial only",
                        scraping_enabled=True,
                        api_available=False,
                        rss_feed="https://inc.com/rss.xml",
                        notes="Startup and growth focus",
                        is_active=True
                    )
                ]
            }
        }
    
    async def monitor_brand_across_authority_sources(
        self,
        brand_name: str,
        industry: str = "saas",
        authority_levels: Optional[List[AuthorityLevel]] = None,
        max_sources_per_tier: int = 5,
        days_back: int = 30
    ) -> AuthorityMonitoringResult:
        """
        Monitor a brand across authority sources for mentions
        Focus on high-authority, unconnected sources for AI citation potential
        """
        logger.info(f"Starting authority source monitoring for brand: {brand_name}")
        
        # Default to top tiers if not specified
        if authority_levels is None:
            authority_levels = [AuthorityLevel.TIER_1, AuthorityLevel.TIER_2]
        
        # Get authority sources for industry
        industry_sources = self.authority_sources.get(industry, {})
        general_sources = self.authority_sources.get("general", {})
        
        all_sources = []
        sources_monitored = []
        
        # Collect sources from specified tiers
        for level in authority_levels:
            level_key = level.value
            
            # Add industry-specific sources
            if level_key in industry_sources:
                industry_tier_sources = industry_sources[level_key][:max_sources_per_tier]
                all_sources.extend(industry_tier_sources)
                sources_monitored.extend([s.name for s in industry_tier_sources])
            
            # Add general sources for broader coverage
            if level_key in general_sources:
                general_tier_sources = general_sources[level_key][:2]  # Limit general sources
                all_sources.extend(general_tier_sources)
                sources_monitored.extend([s.name for s in general_tier_sources])
        
        # Monitor each source
        mentions_by_source = {}
        total_mentions = 0
        authority_distribution = {}
        total_ai_citation_potential = 0.0
        total_reach = 0
        
        for source in all_sources:
            if not source.scraping_enabled:
                logger.info(f"Skipping {source.name} - scraping disabled")
                continue
            
            try:
                mentions = await self._monitor_single_authority_source(
                    source, brand_name, days_back
                )
                
                mentions_by_source[source.name] = mentions
                total_mentions += len(mentions)
                
                # Track authority distribution
                level_key = source.authority_level.value
                authority_distribution[level_key] = authority_distribution.get(level_key, 0) + len(mentions)
                
                # Calculate AI citation potential
                for mention in mentions:
                    total_ai_citation_potential += mention.ai_citation_potential
                    total_reach += mention.estimated_reach
                
                logger.info(f"Found {len(mentions)} mentions on {source.name}")
                
                # Rate limiting between sources
                await asyncio.sleep(3)
                
            except Exception as e:
                logger.error(f"Error monitoring {source.name}: {e}")
                mentions_by_source[source.name] = []
        
        # Calculate average AI citation potential
        avg_ai_citation_potential = total_ai_citation_potential / max(total_mentions, 1)
        
        # Generate recommendations
        recommendations = self._generate_authority_recommendations(
            mentions_by_source, authority_distribution, total_mentions, avg_ai_citation_potential
        )
        
        result = AuthorityMonitoringResult(
            brand_name=brand_name,
            sources_monitored=sources_monitored,
            total_mentions=total_mentions,
            mentions_by_source=mentions_by_source,
            authority_distribution=authority_distribution,
            ai_citation_potential=avg_ai_citation_potential,
            estimated_total_reach=total_reach,
            recommendations=recommendations,
            monitoring_completed_at=datetime.utcnow()
        )
        
        logger.info(f"Authority source monitoring completed for {brand_name}: {total_mentions} mentions found")
        return result
    
    async def _monitor_single_authority_source(
        self,
        source: AuthoritySource,
        brand_name: str,
        days_back: int
    ) -> List[AuthorityMention]:
        """Monitor a single authority source for brand mentions"""
        mentions = []
        
        try:
            # Try RSS feed first if available
            if source.rss_feed:
                mentions.extend(await self._check_rss_feed(source, brand_name, days_back))
            
            # Fallback to site search
            if len(mentions) == 0:
                mentions.extend(await self._search_authority_site(source, brand_name))
            
        except Exception as e:
            logger.error(f"Error monitoring {source.name}: {e}")
        
        return mentions
    
    async def _check_rss_feed(
        self,
        source: AuthoritySource,
        brand_name: str,
        days_back: int
    ) -> List[AuthorityMention]:
        """Check RSS feed for brand mentions"""
        mentions = []
        
        try:
            async with self.session.get(source.rss_feed) as response:
                if response.status != 200:
                    return mentions
                
                rss_content = await response.text()
                soup = BeautifulSoup(rss_content, 'xml')
                
                # Parse RSS items
                items = soup.find_all('item')
                cutoff_date = datetime.utcnow() - timedelta(days=days_back)
                
                for item in items:
                    try:
                        title = item.title.text if item.title else ""
                        description = item.description.text if item.description else ""
                        link = item.link.text if item.link else ""
                        pub_date_str = item.pubDate.text if item.pubDate else ""
                        
                        # Parse publication date
                        pub_date = self._parse_rss_date(pub_date_str)
                        if pub_date and pub_date < cutoff_date:
                            continue
                        
                        # Check for brand mention
                        if brand_name.lower() in title.lower() or brand_name.lower() in description.lower():
                            mention = self._create_authority_mention(
                                source, brand_name, link, title, description, pub_date or datetime.utcnow()
                            )
                            mentions.append(mention)
                    
                    except Exception as e:
                        logger.debug(f"Error parsing RSS item: {e}")
                        continue
        
        except Exception as e:
            logger.error(f"Error checking RSS feed for {source.name}: {e}")
        
        return mentions
    
    async def _search_authority_site(
        self,
        source: AuthoritySource,
        brand_name: str
    ) -> List[AuthorityMention]:
        """Search authority site for brand mentions"""
        mentions = []
        
        try:
            # Common search URL patterns
            search_urls = [
                f"https://{source.domain}/search?q={brand_name}",
                f"https://{source.domain}/?s={brand_name}",
                f"https://www.google.com/search?q=site:{source.domain} {brand_name}"
            ]
            
            for search_url in search_urls:
                try:
                    async with self.session.get(search_url) as response:
                        if response.status == 200:
                            html = await response.text()
                            soup = BeautifulSoup(html, 'html.parser')
                            
                            # Parse search results (basic implementation)
                            links = soup.find_all('a', href=True)
                            for link in links[:5]:  # Limit to first 5 results
                                href = link.get('href')
                                if href and source.domain in href and brand_name.lower() in link.text.lower():
                                    mention = self._create_authority_mention(
                                        source, brand_name, href, link.text.strip(), "", datetime.utcnow()
                                    )
                                    mentions.append(mention)
                            
                            if mentions:
                                break  # Found mentions, no need to try other search patterns
                
                except Exception as e:
                    logger.debug(f"Error with search URL {search_url}: {e}")
                    continue
        
        except Exception as e:
            logger.error(f"Error searching {source.name}: {e}")
        
        return mentions
    
    def _create_authority_mention(
        self,
        source: AuthoritySource,
        brand_name: str,
        url: str,
        title: str,
        content: str,
        pub_date: datetime
    ) -> AuthorityMention:
        """Create an AuthorityMention from parsed data"""
        # Calculate AI citation potential based on source authority and content
        ai_citation_potential = source.ai_citation_frequency * 0.8  # Base potential
        
        # Boost for title mentions
        if brand_name.lower() in title.lower():
            ai_citation_potential += 0.1
        
        # Calculate prominence score
        prominence_score = self._calculate_authority_prominence_score(
            title, content, brand_name, source.authority_score
        )
        
        # Calculate sentiment score
        sentiment_score = self._calculate_authority_sentiment_score(title + " " + content)
        
        # Estimate reach based on authority score
        estimated_reach = source.authority_score * 1000  # Simple estimation
        
        # Calculate backlink value
        backlink_value = source.authority_score * 0.01  # $1 per authority point
        
        return AuthorityMention(
            authority_source_id=source.id,
            source_name=source.name,
            brand_name=brand_name,
            mention_url=url,
            mention_title=title,
            mention_content=content,
            publish_date=pub_date,
            author="Unknown",  # Would need deeper parsing
            mention_context=content[:200],
            ai_citation_potential=min(1.0, ai_citation_potential),
            prominence_score=prominence_score,
            sentiment_score=sentiment_score,
            estimated_reach=estimated_reach,
            backlink_value=backlink_value,
            discovered_at=datetime.utcnow(),
            is_verified=False
        )
    
    def _parse_rss_date(self, date_str: str) -> Optional[datetime]:
        """Parse RSS date string to datetime"""
        if not date_str:
            return None
        
        # Common RSS date formats
        formats = [
            "%a, %d %b %Y %H:%M:%S %z",
            "%a, %d %b %Y %H:%M:%S GMT",
            "%Y-%m-%dT%H:%M:%S%z",
            "%Y-%m-%d %H:%M:%S"
        ]
        
        for fmt in formats:
            try:
                return datetime.strptime(date_str, fmt)
            except ValueError:
                continue
        
        return None
    
    def _calculate_authority_prominence_score(
        self, title: str, content: str, brand_name: str, authority_score: int
    ) -> float:
        """Calculate prominence score for authority mention"""
        score = 0.5  # Base score
        
        # Title mention is very prominent
        if brand_name.lower() in title.lower():
            score += 0.3
        
        # Authority score boost
        score += (authority_score / 100) * 0.2
        
        # Content length consideration
        if content and len(content) > 100:
            score += 0.1
        
        return min(1.0, score)
    
    def _calculate_authority_sentiment_score(self, text: str) -> float:
        """Calculate sentiment score for authority mention"""
        if not text:
            return 0.0
        
        positive_keywords = ['innovative', 'leading', 'excellent', 'outstanding', 'award', 'winner', 'top', 'best']
        negative_keywords = ['controversy', 'issue', 'problem', 'lawsuit', 'criticism', 'decline', 'struggle']
        
        text_lower = text.lower()
        positive_count = sum(1 for word in positive_keywords if word in text_lower)
        negative_count = sum(1 for word in negative_keywords if word in text_lower)
        
        # Calculate sentiment
        total_words = len(text.split())
        sentiment = (positive_count - negative_count) / max(total_words / 20, 1)
        
        return max(-1.0, min(1.0, sentiment))
    
    def _generate_authority_recommendations(
        self,
        mentions_by_source: Dict[str, List[AuthorityMention]],
        authority_distribution: Dict[str, int],
        total_mentions: int,
        avg_ai_citation_potential: float
    ) -> List[str]:
        """Generate recommendations based on authority source analysis"""
        recommendations = []
        
        # Overall analysis
        if total_mentions == 0:
            recommendations.append("No authority source mentions found - focus on building relationships with tier 1 publications")
            recommendations.append("Consider guest posting on industry publications to build authority")
            recommendations.append("Target unconnected authoritative sources as recommended by Reddit intelligence")
        else:
            recommendations.append(f"Found {total_mentions} authority mentions - good for AI citation potential")
        
        # Authority tier analysis
        tier_1_mentions = authority_distribution.get("tier_1", 0)
        tier_2_mentions = authority_distribution.get("tier_2", 0)
        
        if tier_1_mentions > 0:
            recommendations.append(f"Excellent: {tier_1_mentions} tier 1 authority mentions found")
        else:
            recommendations.append("Missing tier 1 authority mentions - target Forbes, TechCrunch, Inc.")
        
        if tier_2_mentions > tier_1_mentions * 2:
            recommendations.append("Good tier 2 coverage - consider upgrading to tier 1 sources")
        
        # AI citation potential analysis
        if avg_ai_citation_potential > 0.8:
            recommendations.append("High AI citation potential - these sources are frequently referenced")
        elif avg_ai_citation_potential > 0.6:
            recommendations.append("Good AI citation potential - monitor for citation tracking")
        else:
            recommendations.append("Low AI citation potential - focus on higher authority sources")
        
        # Source diversity recommendations
        unique_sources = len([s for s, mentions in mentions_by_source.items() if mentions])
        if unique_sources < 3:
            recommendations.append("Need more diverse authority sources - target unconnected publications")
        
        return recommendations[:5]  # Return top 5 recommendations
    
    async def store_authority_mentions(self, user_id: str, results: AuthorityMonitoringResult):
        """Store authority source mentions in database"""
        try:
            for source_name, mentions in results.mentions_by_source.items():
                for mention in mentions:
                    await db_manager.execute_query(
                        """
                        INSERT INTO authority_mentions (user_id, authority_source_id, brand_name, 
                                                      mention_url, mention_title, mention_content, 
                                                      publish_date, author, mention_context,
                                                      ai_citation_potential, prominence_score, 
                                                      sentiment_score, estimated_reach, 
                                                      backlink_value, discovered_at, is_verified)
                        VALUES (:user_id, :authority_source_id, :brand_name, :mention_url, 
                               :mention_title, :mention_content, :publish_date, :author, 
                               :mention_context, :ai_citation_potential, :prominence_score, 
                               :sentiment_score, :estimated_reach, :backlink_value, 
                               :discovered_at, :is_verified)
                        ON CONFLICT (mention_url, brand_name) DO UPDATE SET
                        ai_citation_potential = :ai_citation_potential,
                        discovered_at = :discovered_at
                        """,
                        {
                            "user_id": user_id,
                            "authority_source_id": mention.authority_source_id,
                            "brand_name": mention.brand_name,
                            "mention_url": mention.mention_url,
                            "mention_title": mention.mention_title,
                            "mention_content": mention.mention_content,
                            "publish_date": mention.publish_date,
                            "author": mention.author,
                            "mention_context": mention.mention_context,
                            "ai_citation_potential": mention.ai_citation_potential,
                            "prominence_score": mention.prominence_score,
                            "sentiment_score": mention.sentiment_score,
                            "estimated_reach": mention.estimated_reach,
                            "backlink_value": mention.backlink_value,
                            "discovered_at": mention.discovered_at,
                            "is_verified": mention.is_verified
                        }
                    )
            
            logger.info(f"Stored {results.total_mentions} authority mentions for user {user_id}")
            
        except Exception as e:
            logger.error(f"Error storing authority mentions: {e}")
    
    async def get_authority_sources_by_industry(self, industry: str) -> List[Dict[str, Any]]:
        """Get authority sources for a specific industry"""
        try:
            industry_sources = self.authority_sources.get(industry, {})
            general_sources = self.authority_sources.get("general", {})
            
            all_sources = []
            
            # Combine industry and general sources
            for tier_name, sources in {**industry_sources, **general_sources}.items():
                for source in sources:
                    all_sources.append({
                        "id": source.id,
                        "name": source.name,
                        "domain": source.domain,
                        "industry": source.industry,
                        "source_type": source.source_type.value,
                        "authority_level": source.authority_level.value,
                        "authority_score": source.authority_score,
                        "ai_citation_frequency": source.ai_citation_frequency,
                        "content_types": source.content_types,
                        "contact_email": source.contact_email,
                        "submission_guidelines": source.submission_guidelines,
                        "average_response_time": source.average_response_time,
                        "success_rate": source.success_rate,
                        "cost_estimate": source.cost_estimate,
                        "is_active": source.is_active
                    })
            
            # Sort by authority score
            all_sources.sort(key=lambda x: x["authority_score"], reverse=True)
            return all_sources
            
        except Exception as e:
            logger.error(f"Error getting authority sources: {e}")
            return []
    
    async def get_authority_summary(self, user_id: str, brand_name: str) -> Dict[str, Any]:
        """Get summary of authority source mentions for a brand"""
        try:
            results = await db_manager.fetch_all(
                """
                SELECT authority_source_id, COUNT(*) as mention_count, 
                       AVG(ai_citation_potential) as avg_citation_potential,
                       AVG(sentiment_score) as avg_sentiment,
                       SUM(estimated_reach) as total_reach,
                       MAX(discovered_at) as latest_mention
                FROM authority_mentions 
                WHERE user_id = :user_id AND brand_name = :brand_name
                GROUP BY authority_source_id
                ORDER BY mention_count DESC
                """,
                {"user_id": user_id, "brand_name": brand_name}
            )
            
            summary = {
                "total_mentions": sum(row.mention_count for row in results),
                "sources_covered": len(results),
                "avg_citation_potential": 0.0,
                "total_estimated_reach": sum(row.total_reach for row in results if row.total_reach),
                "by_source": {}
            }
            
            total_mentions = summary["total_mentions"]
            if total_mentions > 0:
                weighted_citation_potential = sum(
                    (row.mention_count / total_mentions) * (row.avg_citation_potential or 0)
                    for row in results
                )
                summary["avg_citation_potential"] = weighted_citation_potential
            
            for row in results:
                summary["by_source"][row.authority_source_id] = {
                    "mention_count": row.mention_count,
                    "avg_citation_potential": float(row.avg_citation_potential) if row.avg_citation_potential else 0.0,
                    "avg_sentiment": float(row.avg_sentiment) if row.avg_sentiment else 0.0,
                    "total_reach": row.total_reach if row.total_reach else 0,
                    "latest_mention": row.latest_mention
                }
            
            return summary
            
        except Exception as e:
            logger.error(f"Error getting authority summary: {e}")
            return {"total_mentions": 0, "sources_covered": 0, "by_source": {}}


# Global service instance
authority_source_service = AuthoritySourceService()