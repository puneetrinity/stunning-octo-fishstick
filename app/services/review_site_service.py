"""
Review Site Monitoring Service
Based on Reddit intelligence: "Review sites are extremely expensive but effective for GEO as AI likes to reference reviews"
Target sites: G2, Capterra, TrustRadius, Gartner
"""
import asyncio
import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
import aiohttp
import json
from bs4 import BeautifulSoup
import re
from urllib.parse import urljoin, urlparse
from app.database import db_manager

logger = logging.getLogger(__name__)


class ReviewSiteType(Enum):
    G2 = "g2"
    CAPTERRA = "capterra"
    TRUSTRADIUS = "trustradius"
    GARTNER = "gartner"
    GETAPP = "getapp"
    SOFTWARE_ADVICE = "software_advice"


@dataclass
class ReviewSiteConfig:
    """Configuration for review site monitoring"""
    name: str
    domain: str
    authority_score: int
    average_cost_per_review: float
    ai_citation_frequency: float
    scraping_enabled: bool
    api_available: bool
    search_template: str
    review_template: str
    listing_template: str


@dataclass
class ReviewSiteMention:
    """Single mention found on a review site"""
    review_site: str
    brand_name: str
    url: str
    title: str
    content: str
    rating: Optional[float]
    review_date: datetime
    author: str
    sentiment_score: float
    ai_citation_potential: float
    discovered_at: datetime
    mention_type: str  # 'review', 'listing', 'comparison', 'featured'


@dataclass
class ReviewSiteMonitoringResult:
    """Results from monitoring a brand across review sites"""
    brand_name: str
    total_mentions: int
    review_sites_covered: List[str]
    mentions_by_site: Dict[str, List[ReviewSiteMention]]
    average_rating: float
    sentiment_analysis: Dict[str, Any]
    roi_metrics: Dict[str, Any]
    recommendations: List[str]
    monitoring_completed_at: datetime


class ReviewSiteService:
    """
    Monitor brand mentions across major review sites
    Track ROI for expensive review site investments
    """
    
    def __init__(self):
        self.session = None
        self.review_sites_config = {
            ReviewSiteType.G2: ReviewSiteConfig(
                name="G2",
                domain="g2.com",
                authority_score=95,
                average_cost_per_review=4000.0,
                ai_citation_frequency=0.78,
                scraping_enabled=True,
                api_available=False,
                search_template="https://www.g2.com/search?query={brand_name}",
                review_template="https://www.g2.com/products/{slug}/reviews",
                listing_template="https://www.g2.com/products/{slug}"
            ),
            ReviewSiteType.CAPTERRA: ReviewSiteConfig(
                name="Capterra",
                domain="capterra.com",
                authority_score=90,
                average_cost_per_review=2500.0,
                ai_citation_frequency=0.65,
                scraping_enabled=True,
                api_available=False,
                search_template="https://www.capterra.com/search/?query={brand_name}",
                review_template="https://www.capterra.com/p/{slug}/reviews/",
                listing_template="https://www.capterra.com/p/{slug}/"
            ),
            ReviewSiteType.TRUSTRADIUS: ReviewSiteConfig(
                name="TrustRadius",
                domain="trustradius.com",
                authority_score=85,
                average_cost_per_review=1800.0,
                ai_citation_frequency=0.52,
                scraping_enabled=True,
                api_available=False,
                search_template="https://www.trustradius.com/search?query={brand_name}",
                review_template="https://www.trustradius.com/products/{slug}/reviews",
                listing_template="https://www.trustradius.com/products/{slug}"
            ),
            ReviewSiteType.GARTNER: ReviewSiteConfig(
                name="Gartner",
                domain="gartner.com",
                authority_score=98,
                average_cost_per_review=12000.0,
                ai_citation_frequency=0.85,
                scraping_enabled=False,  # Requires special access
                api_available=True,
                search_template="https://www.gartner.com/reviews/search?query={brand_name}",
                review_template="https://www.gartner.com/reviews/market/{market}/vendor/{vendor}",
                listing_template="https://www.gartner.com/reviews/market/{market}/vendor/{vendor}"
            ),
            ReviewSiteType.GETAPP: ReviewSiteConfig(
                name="GetApp",
                domain="getapp.com",
                authority_score=75,
                average_cost_per_review=1200.0,
                ai_citation_frequency=0.35,
                scraping_enabled=True,
                api_available=False,
                search_template="https://www.getapp.com/search?query={brand_name}",
                review_template="https://www.getapp.com/p/{slug}/reviews/",
                listing_template="https://www.getapp.com/p/{slug}/"
            ),
            ReviewSiteType.SOFTWARE_ADVICE: ReviewSiteConfig(
                name="Software Advice",
                domain="softwareadvice.com",
                authority_score=80,
                average_cost_per_review=1500.0,
                ai_citation_frequency=0.40,
                scraping_enabled=True,
                api_available=False,
                search_template="https://www.softwareadvice.com/search/?query={brand_name}",
                review_template="https://www.softwareadvice.com/{category}/{slug}/reviews/",
                listing_template="https://www.softwareadvice.com/{category}/{slug}/"
            )
        }
        
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
    
    async def monitor_brand_across_review_sites(
        self,
        brand_name: str,
        category: str = "software",
        priority_sites: Optional[List[ReviewSiteType]] = None,
        include_roi_analysis: bool = True
    ) -> ReviewSiteMonitoringResult:
        """
        Monitor a brand across all major review sites
        Based on Reddit intelligence: Track expensive review site investments
        """
        logger.info(f"Starting review site monitoring for brand: {brand_name}")
        
        # Default to high-priority sites if not specified
        if priority_sites is None:
            priority_sites = [
                ReviewSiteType.G2,
                ReviewSiteType.CAPTERRA,
                ReviewSiteType.TRUSTRADIUS,
                ReviewSiteType.GARTNER
            ]
        
        mentions_by_site = {}
        total_mentions = 0
        all_ratings = []
        
        # Monitor each review site
        for site_type in priority_sites:
            site_config = self.review_sites_config[site_type]
            
            if not site_config.scraping_enabled:
                logger.info(f"Skipping {site_config.name} - scraping disabled")
                continue
            
            try:
                mentions = await self._monitor_single_review_site(
                    brand_name, site_type, category
                )
                
                mentions_by_site[site_config.name] = mentions
                total_mentions += len(mentions)
                
                # Collect ratings for analysis
                for mention in mentions:
                    if mention.rating:
                        all_ratings.append(mention.rating)
                
                logger.info(f"Found {len(mentions)} mentions on {site_config.name}")
                
                # Rate limiting between sites
                await asyncio.sleep(2)
                
            except Exception as e:
                logger.error(f"Error monitoring {site_config.name}: {e}")
                mentions_by_site[site_config.name] = []
        
        # Calculate average rating
        average_rating = sum(all_ratings) / len(all_ratings) if all_ratings else 0.0
        
        # Analyze sentiment across all mentions
        sentiment_analysis = self._analyze_review_sentiment(mentions_by_site)
        
        # Calculate ROI metrics if requested
        roi_metrics = {}
        if include_roi_analysis:
            roi_metrics = await self._calculate_review_site_roi(
                brand_name, mentions_by_site, priority_sites
            )
        
        # Generate recommendations
        recommendations = self._generate_review_site_recommendations(
            mentions_by_site, roi_metrics, average_rating
        )
        
        result = ReviewSiteMonitoringResult(
            brand_name=brand_name,
            total_mentions=total_mentions,
            review_sites_covered=[site.value for site in priority_sites],
            mentions_by_site=mentions_by_site,
            average_rating=average_rating,
            sentiment_analysis=sentiment_analysis,
            roi_metrics=roi_metrics,
            recommendations=recommendations,
            monitoring_completed_at=datetime.utcnow()
        )
        
        logger.info(f"Review site monitoring completed for {brand_name}: {total_mentions} mentions found")
        return result
    
    async def _monitor_single_review_site(
        self,
        brand_name: str,
        site_type: ReviewSiteType,
        category: str
    ) -> List[ReviewSiteMention]:
        """Monitor a single review site for brand mentions"""
        site_config = self.review_sites_config[site_type]
        mentions = []
        
        try:
            # Search for the brand
            search_url = site_config.search_template.format(brand_name=brand_name)
            
            async with self.session.get(search_url) as response:
                if response.status != 200:
                    logger.warning(f"Failed to search {site_config.name}: {response.status}")
                    return mentions
                
                html = await response.text()
                soup = BeautifulSoup(html, 'html.parser')
                
                # Parse search results based on site type
                if site_type == ReviewSiteType.G2:
                    mentions.extend(await self._parse_g2_results(soup, brand_name))
                elif site_type == ReviewSiteType.CAPTERRA:
                    mentions.extend(await self._parse_capterra_results(soup, brand_name))
                elif site_type == ReviewSiteType.TRUSTRADIUS:
                    mentions.extend(await self._parse_trustradius_results(soup, brand_name))
                elif site_type == ReviewSiteType.GETAPP:
                    mentions.extend(await self._parse_getapp_results(soup, brand_name))
                elif site_type == ReviewSiteType.SOFTWARE_ADVICE:
                    mentions.extend(await self._parse_software_advice_results(soup, brand_name))
                
        except Exception as e:
            logger.error(f"Error monitoring {site_config.name}: {e}")
        
        return mentions
    
    async def _parse_g2_results(self, soup: BeautifulSoup, brand_name: str) -> List[ReviewSiteMention]:
        """Parse G2 search results"""
        mentions = []
        
        # Find product listings
        product_cards = soup.find_all('div', class_='product-listing')
        
        for card in product_cards:
            try:
                # Extract product information
                title_elem = card.find('h3') or card.find('h2')
                title = title_elem.text.strip() if title_elem else "Unknown Product"
                
                # Check if this is actually our brand
                if brand_name.lower() not in title.lower():
                    continue
                
                # Extract URL
                link_elem = card.find('a', href=True)
                url = urljoin("https://www.g2.com", link_elem['href']) if link_elem else ""
                
                # Extract rating
                rating_elem = card.find('div', class_='rating') or card.find('span', class_='rating')
                rating = None
                if rating_elem:
                    rating_text = rating_elem.text.strip()
                    rating_match = re.search(r'(\d+\.?\d*)', rating_text)
                    if rating_match:
                        rating = float(rating_match.group(1))
                
                # Extract description/content
                desc_elem = card.find('p') or card.find('div', class_='description')
                content = desc_elem.text.strip() if desc_elem else ""
                
                mention = ReviewSiteMention(
                    review_site="G2",
                    brand_name=brand_name,
                    url=url,
                    title=title,
                    content=content,
                    rating=rating,
                    review_date=datetime.utcnow(),
                    author="G2 Platform",
                    sentiment_score=self._calculate_sentiment_score(title + " " + content),
                    ai_citation_potential=0.78,  # G2 has high AI citation frequency
                    discovered_at=datetime.utcnow(),
                    mention_type="listing"
                )
                mentions.append(mention)
                
            except Exception as e:
                logger.error(f"Error parsing G2 result: {e}")
                continue
        
        return mentions
    
    async def _parse_capterra_results(self, soup: BeautifulSoup, brand_name: str) -> List[ReviewSiteMention]:
        """Parse Capterra search results"""
        mentions = []
        
        # Find product listings
        product_cards = soup.find_all('div', class_='product-card') or soup.find_all('div', class_='listing-item')
        
        for card in product_cards:
            try:
                # Extract product information
                title_elem = card.find('h3') or card.find('h2') or card.find('a')
                title = title_elem.text.strip() if title_elem else "Unknown Product"
                
                # Check if this is our brand
                if brand_name.lower() not in title.lower():
                    continue
                
                # Extract URL
                link_elem = card.find('a', href=True)
                url = urljoin("https://www.capterra.com", link_elem['href']) if link_elem else ""
                
                # Extract rating
                rating_elem = card.find('div', class_='rating') or card.find('span', class_='stars')
                rating = None
                if rating_elem:
                    rating_text = rating_elem.text.strip()
                    rating_match = re.search(r'(\d+\.?\d*)', rating_text)
                    if rating_match:
                        rating = float(rating_match.group(1))
                
                # Extract description
                desc_elem = card.find('p') or card.find('div', class_='description')
                content = desc_elem.text.strip() if desc_elem else ""
                
                mention = ReviewSiteMention(
                    review_site="Capterra",
                    brand_name=brand_name,
                    url=url,
                    title=title,
                    content=content,
                    rating=rating,
                    review_date=datetime.utcnow(),
                    author="Capterra Platform",
                    sentiment_score=self._calculate_sentiment_score(title + " " + content),
                    ai_citation_potential=0.65,
                    discovered_at=datetime.utcnow(),
                    mention_type="listing"
                )
                mentions.append(mention)
                
            except Exception as e:
                logger.error(f"Error parsing Capterra result: {e}")
                continue
        
        return mentions
    
    async def _parse_trustradius_results(self, soup: BeautifulSoup, brand_name: str) -> List[ReviewSiteMention]:
        """Parse TrustRadius search results"""
        mentions = []
        
        # Find product listings
        product_cards = soup.find_all('div', class_='product-card') or soup.find_all('div', class_='vendor-card')
        
        for card in product_cards:
            try:
                # Extract product information
                title_elem = card.find('h3') or card.find('h2') or card.find('a')
                title = title_elem.text.strip() if title_elem else "Unknown Product"
                
                # Check if this is our brand
                if brand_name.lower() not in title.lower():
                    continue
                
                # Extract URL
                link_elem = card.find('a', href=True)
                url = urljoin("https://www.trustradius.com", link_elem['href']) if link_elem else ""
                
                # Extract rating
                rating_elem = card.find('div', class_='rating') or card.find('span', class_='score')
                rating = None
                if rating_elem:
                    rating_text = rating_elem.text.strip()
                    rating_match = re.search(r'(\d+\.?\d*)', rating_text)
                    if rating_match:
                        rating = float(rating_match.group(1))
                
                # Extract description
                desc_elem = card.find('p') or card.find('div', class_='description')
                content = desc_elem.text.strip() if desc_elem else ""
                
                mention = ReviewSiteMention(
                    review_site="TrustRadius",
                    brand_name=brand_name,
                    url=url,
                    title=title,
                    content=content,
                    rating=rating,
                    review_date=datetime.utcnow(),
                    author="TrustRadius Platform",
                    sentiment_score=self._calculate_sentiment_score(title + " " + content),
                    ai_citation_potential=0.52,
                    discovered_at=datetime.utcnow(),
                    mention_type="listing"
                )
                mentions.append(mention)
                
            except Exception as e:
                logger.error(f"Error parsing TrustRadius result: {e}")
                continue
        
        return mentions
    
    async def _parse_getapp_results(self, soup: BeautifulSoup, brand_name: str) -> List[ReviewSiteMention]:
        """Parse GetApp search results"""
        mentions = []
        
        # Find product listings
        product_cards = soup.find_all('div', class_='product-listing') or soup.find_all('div', class_='app-card')
        
        for card in product_cards:
            try:
                # Extract product information
                title_elem = card.find('h3') or card.find('h2') or card.find('a')
                title = title_elem.text.strip() if title_elem else "Unknown Product"
                
                # Check if this is our brand
                if brand_name.lower() not in title.lower():
                    continue
                
                # Extract URL
                link_elem = card.find('a', href=True)
                url = urljoin("https://www.getapp.com", link_elem['href']) if link_elem else ""
                
                # Extract rating
                rating_elem = card.find('div', class_='rating') or card.find('span', class_='score')
                rating = None
                if rating_elem:
                    rating_text = rating_elem.text.strip()
                    rating_match = re.search(r'(\d+\.?\d*)', rating_text)
                    if rating_match:
                        rating = float(rating_match.group(1))
                
                # Extract description
                desc_elem = card.find('p') or card.find('div', class_='description')
                content = desc_elem.text.strip() if desc_elem else ""
                
                mention = ReviewSiteMention(
                    review_site="GetApp",
                    brand_name=brand_name,
                    url=url,
                    title=title,
                    content=content,
                    rating=rating,
                    review_date=datetime.utcnow(),
                    author="GetApp Platform",
                    sentiment_score=self._calculate_sentiment_score(title + " " + content),
                    ai_citation_potential=0.35,
                    discovered_at=datetime.utcnow(),
                    mention_type="listing"
                )
                mentions.append(mention)
                
            except Exception as e:
                logger.error(f"Error parsing GetApp result: {e}")
                continue
        
        return mentions
    
    async def _parse_software_advice_results(self, soup: BeautifulSoup, brand_name: str) -> List[ReviewSiteMention]:
        """Parse Software Advice search results"""
        mentions = []
        
        # Find product listings
        product_cards = soup.find_all('div', class_='product-card') or soup.find_all('div', class_='sa-product-card')
        
        for card in product_cards:
            try:
                # Extract product information
                title_elem = card.find('h3') or card.find('h2') or card.find('a')
                title = title_elem.text.strip() if title_elem else "Unknown Product"
                
                # Check if this is our brand
                if brand_name.lower() not in title.lower():
                    continue
                
                # Extract URL
                link_elem = card.find('a', href=True)
                url = urljoin("https://www.softwareadvice.com", link_elem['href']) if link_elem else ""
                
                # Extract rating
                rating_elem = card.find('div', class_='rating') or card.find('span', class_='score')
                rating = None
                if rating_elem:
                    rating_text = rating_elem.text.strip()
                    rating_match = re.search(r'(\d+\.?\d*)', rating_text)
                    if rating_match:
                        rating = float(rating_match.group(1))
                
                # Extract description
                desc_elem = card.find('p') or card.find('div', class_='description')
                content = desc_elem.text.strip() if desc_elem else ""
                
                mention = ReviewSiteMention(
                    review_site="Software Advice",
                    brand_name=brand_name,
                    url=url,
                    title=title,
                    content=content,
                    rating=rating,
                    review_date=datetime.utcnow(),
                    author="Software Advice Platform",
                    sentiment_score=self._calculate_sentiment_score(title + " " + content),
                    ai_citation_potential=0.40,
                    discovered_at=datetime.utcnow(),
                    mention_type="listing"
                )
                mentions.append(mention)
                
            except Exception as e:
                logger.error(f"Error parsing Software Advice result: {e}")
                continue
        
        return mentions
    
    def _calculate_sentiment_score(self, text: str) -> float:
        """Calculate sentiment score for review text"""
        if not text:
            return 0.0
        
        # Simple sentiment analysis based on keywords
        positive_keywords = ['excellent', 'great', 'good', 'outstanding', 'impressive', 'helpful', 'easy', 'efficient', 'reliable']
        negative_keywords = ['bad', 'poor', 'terrible', 'awful', 'disappointing', 'difficult', 'slow', 'unreliable', 'expensive']
        
        text_lower = text.lower()
        positive_count = sum(1 for keyword in positive_keywords if keyword in text_lower)
        negative_count = sum(1 for keyword in negative_keywords if keyword in text_lower)
        
        total_words = len(text.split())
        if total_words == 0:
            return 0.0
        
        # Score between -1 and 1
        score = (positive_count - negative_count) / max(total_words / 10, 1)
        return max(-1.0, min(1.0, score))
    
    def _analyze_review_sentiment(self, mentions_by_site: Dict[str, List[ReviewSiteMention]]) -> Dict[str, Any]:
        """Analyze sentiment across all review sites"""
        all_sentiments = []
        site_sentiments = {}
        
        for site_name, mentions in mentions_by_site.items():
            site_scores = [mention.sentiment_score for mention in mentions if mention.sentiment_score is not None]
            
            if site_scores:
                site_sentiments[site_name] = {
                    'average_sentiment': sum(site_scores) / len(site_scores),
                    'total_mentions': len(mentions),
                    'positive_mentions': len([s for s in site_scores if s > 0.1]),
                    'negative_mentions': len([s for s in site_scores if s < -0.1]),
                    'neutral_mentions': len([s for s in site_scores if -0.1 <= s <= 0.1])
                }
                all_sentiments.extend(site_scores)
            else:
                site_sentiments[site_name] = {
                    'average_sentiment': 0.0,
                    'total_mentions': 0,
                    'positive_mentions': 0,
                    'negative_mentions': 0,
                    'neutral_mentions': 0
                }
        
        overall_sentiment = sum(all_sentiments) / len(all_sentiments) if all_sentiments else 0.0
        
        return {
            'overall_sentiment': overall_sentiment,
            'total_mentions_analyzed': len(all_sentiments),
            'by_site': site_sentiments,
            'sentiment_distribution': {
                'positive': len([s for s in all_sentiments if s > 0.1]),
                'negative': len([s for s in all_sentiments if s < -0.1]),
                'neutral': len([s for s in all_sentiments if -0.1 <= s <= 0.1])
            }
        }
    
    async def _calculate_review_site_roi(
        self,
        brand_name: str,
        mentions_by_site: Dict[str, List[ReviewSiteMention]],
        priority_sites: List[ReviewSiteType]
    ) -> Dict[str, Any]:
        """Calculate ROI for review site investments"""
        roi_analysis = {}
        
        for site_type in priority_sites:
            site_config = self.review_sites_config[site_type]
            site_mentions = mentions_by_site.get(site_config.name, [])
            
            # Calculate potential value
            mentions_count = len(site_mentions)
            ai_citation_value = mentions_count * site_config.ai_citation_frequency * 100  # $100 per AI citation
            
            # Calculate cost
            investment_cost = site_config.average_cost_per_review
            
            # Calculate ROI
            roi_percentage = ((ai_citation_value - investment_cost) / investment_cost * 100) if investment_cost > 0 else 0
            
            roi_analysis[site_config.name] = {
                'investment_cost': investment_cost,
                'mentions_found': mentions_count,
                'ai_citation_frequency': site_config.ai_citation_frequency,
                'estimated_ai_citation_value': ai_citation_value,
                'roi_percentage': roi_percentage,
                'payback_period_months': (investment_cost / (ai_citation_value / 12)) if ai_citation_value > 0 else float('inf'),
                'authority_score': site_config.authority_score,
                'recommendation': self._get_roi_recommendation(roi_percentage, site_config.name)
            }
        
        # Calculate overall ROI
        total_investment = sum(data['investment_cost'] for data in roi_analysis.values())
        total_value = sum(data['estimated_ai_citation_value'] for data in roi_analysis.values())
        overall_roi = ((total_value - total_investment) / total_investment * 100) if total_investment > 0 else 0
        
        roi_analysis['overall'] = {
            'total_investment': total_investment,
            'total_estimated_value': total_value,
            'overall_roi_percentage': overall_roi,
            'cost_per_mention': total_investment / sum(data['mentions_found'] for data in roi_analysis.values() if data['mentions_found'] > 0) if any(data['mentions_found'] > 0 for data in roi_analysis.values()) else 0
        }
        
        return roi_analysis
    
    def _get_roi_recommendation(self, roi_percentage: float, site_name: str) -> str:
        """Get recommendation based on ROI percentage"""
        if roi_percentage > 200:
            return f"Excellent ROI - {site_name} is highly profitable, consider increasing investment"
        elif roi_percentage > 50:
            return f"Good ROI - {site_name} is profitable, maintain current investment"
        elif roi_percentage > 0:
            return f"Marginal ROI - {site_name} is barely profitable, monitor closely"
        else:
            return f"Negative ROI - {site_name} investment not justified, consider reducing or stopping"
    
    def _generate_review_site_recommendations(
        self,
        mentions_by_site: Dict[str, List[ReviewSiteMention]],
        roi_metrics: Dict[str, Any],
        average_rating: float
    ) -> List[str]:
        """Generate recommendations based on review site analysis"""
        recommendations = []
        
        # Overall recommendations
        total_mentions = sum(len(mentions) for mentions in mentions_by_site.values())
        
        if total_mentions == 0:
            recommendations.append("No review site presence detected - consider investing in G2 or Capterra for AI visibility")
            recommendations.append("Review sites are expensive but effective for GEO as AI likes to reference reviews")
        else:
            recommendations.append(f"Found {total_mentions} mentions across review sites - good for AI citation potential")
        
        # Site-specific recommendations
        for site_name, mentions in mentions_by_site.items():
            if len(mentions) == 0:
                recommendations.append(f"No presence on {site_name} - consider listing for AI visibility")
            elif len(mentions) > 0:
                avg_rating = sum(m.rating for m in mentions if m.rating) / len([m for m in mentions if m.rating])
                if avg_rating and avg_rating < 4.0:
                    recommendations.append(f"{site_name} rating ({avg_rating:.1f}/5) needs improvement - focus on customer satisfaction")
        
        # ROI-based recommendations
        if roi_metrics and 'overall' in roi_metrics:
            overall_roi = roi_metrics['overall']['overall_roi_percentage']
            if overall_roi > 50:
                recommendations.append(f"Review site ROI is {overall_roi:.1f}% - excellent investment, consider expanding")
            elif overall_roi > 0:
                recommendations.append(f"Review site ROI is {overall_roi:.1f}% - profitable but could be optimized")
            else:
                recommendations.append(f"Review site ROI is {overall_roi:.1f}% - reevaluate investment strategy")
        
        # Rating-based recommendations
        if average_rating > 0:
            if average_rating >= 4.5:
                recommendations.append(f"Excellent average rating ({average_rating:.1f}/5) - leverage for marketing")
            elif average_rating >= 4.0:
                recommendations.append(f"Good average rating ({average_rating:.1f}/5) - maintain quality")
            elif average_rating >= 3.0:
                recommendations.append(f"Average rating ({average_rating:.1f}/5) needs improvement - focus on customer experience")
            else:
                recommendations.append(f"Low average rating ({average_rating:.1f}/5) - critical priority to improve")
        
        return recommendations[:5]  # Return top 5 recommendations
    
    async def store_review_site_mentions(self, user_id: str, results: ReviewSiteMonitoringResult):
        """Store review site mentions in database"""
        try:
            for site_name, mentions in results.mentions_by_site.items():
                for mention in mentions:
                    await db_manager.execute_query(
                        """
                        INSERT INTO review_mentions (user_id, review_site_name, brand_name, mention_url, 
                                                   mention_title, mention_content, rating, review_date, 
                                                   author, sentiment_score, ai_citation_potential, 
                                                   discovered_at, mention_type)
                        VALUES (:user_id, :review_site_name, :brand_name, :mention_url, :mention_title, 
                               :mention_content, :rating, :review_date, :author, :sentiment_score, 
                               :ai_citation_potential, :discovered_at, :mention_type)
                        ON CONFLICT (mention_url, brand_name) DO UPDATE SET
                        sentiment_score = :sentiment_score,
                        discovered_at = :discovered_at
                        """,
                        {
                            "user_id": user_id,
                            "review_site_name": mention.review_site,
                            "brand_name": mention.brand_name,
                            "mention_url": mention.url,
                            "mention_title": mention.title,
                            "mention_content": mention.content,
                            "rating": mention.rating,
                            "review_date": mention.review_date,
                            "author": mention.author,
                            "sentiment_score": mention.sentiment_score,
                            "ai_citation_potential": mention.ai_citation_potential,
                            "discovered_at": mention.discovered_at,
                            "mention_type": mention.mention_type
                        }
                    )
            
            logger.info(f"Stored {results.total_mentions} review site mentions for user {user_id}")
            
        except Exception as e:
            logger.error(f"Error storing review site mentions: {e}")
    
    async def get_review_site_summary(self, user_id: str, brand_name: str) -> Dict[str, Any]:
        """Get summary of review site mentions for a brand"""
        try:
            results = await db_manager.fetch_all(
                """
                SELECT review_site_name, COUNT(*) as mention_count, 
                       AVG(rating) as avg_rating, AVG(sentiment_score) as avg_sentiment,
                       MAX(discovered_at) as latest_mention
                FROM review_mentions 
                WHERE user_id = :user_id AND brand_name = :brand_name
                GROUP BY review_site_name
                ORDER BY mention_count DESC
                """,
                {"user_id": user_id, "brand_name": brand_name}
            )
            
            summary = {
                "total_mentions": sum(row.mention_count for row in results),
                "sites_covered": len(results),
                "by_site": {}
            }
            
            for row in results:
                summary["by_site"][row.review_site_name] = {
                    "mention_count": row.mention_count,
                    "avg_rating": float(row.avg_rating) if row.avg_rating else None,
                    "avg_sentiment": float(row.avg_sentiment) if row.avg_sentiment else None,
                    "latest_mention": row.latest_mention
                }
            
            return summary
            
        except Exception as e:
            logger.error(f"Error getting review site summary: {e}")
            return {"total_mentions": 0, "sites_covered": 0, "by_site": {}}


# Global service instance
review_site_service = ReviewSiteService()