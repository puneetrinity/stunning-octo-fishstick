#!/usr/bin/env python3
"""
Test script for review site monitoring system
"""
import asyncio
import logging
from app.services.review_site_service import review_site_service, ReviewSiteType

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_review_site_monitoring():
    """Test the review site monitoring functionality"""
    try:
        # Test brand name
        brand_name = "Slack"
        category = "software"
        
        print(f"Testing review site monitoring for brand: {brand_name}")
        print("=" * 50)
        
        # Test monitoring across review sites
        async with review_site_service as service:
            result = await service.monitor_brand_across_review_sites(
                brand_name=brand_name,
                category=category,
                priority_sites=[
                    ReviewSiteType.G2,
                    ReviewSiteType.CAPTERRA,
                    ReviewSiteType.TRUSTRADIUS
                ],
                include_roi_analysis=True
            )
            
            print(f"Monitoring Results for {brand_name}:")
            print(f"- Total mentions: {result.total_mentions}")
            print(f"- Average rating: {result.average_rating:.2f}")
            print(f"- Sites covered: {result.review_sites_covered}")
            print(f"- Completed at: {result.monitoring_completed_at}")
            
            print("\nMentions by site:")
            for site_name, mentions in result.mentions_by_site.items():
                print(f"  {site_name}: {len(mentions)} mentions")
                for mention in mentions[:2]:  # Show first 2 mentions
                    print(f"    - {mention.title} (Rating: {mention.rating})")
            
            print("\nSentiment Analysis:")
            print(f"- Overall sentiment: {result.sentiment_analysis.get('overall_sentiment', 0):.2f}")
            print(f"- Total mentions analyzed: {result.sentiment_analysis.get('total_mentions_analyzed', 0)}")
            
            print("\nROI Analysis:")
            if result.roi_metrics:
                for site_name, roi_data in result.roi_metrics.items():
                    if site_name != "overall":
                        print(f"  {site_name}:")
                        print(f"    - Investment cost: ${roi_data.get('investment_cost', 0):,.2f}")
                        print(f"    - ROI: {roi_data.get('roi_percentage', 0):.1f}%")
                        print(f"    - Recommendation: {roi_data.get('recommendation', 'N/A')}")
            
            print("\nRecommendations:")
            for i, recommendation in enumerate(result.recommendations, 1):
                print(f"{i}. {recommendation}")
        
        print("\n" + "=" * 50)
        print("Review site monitoring test completed successfully!")
        
    except Exception as e:
        logger.error(f"Error in review site monitoring test: {e}")
        print(f"Test failed: {e}")


if __name__ == "__main__":
    asyncio.run(test_review_site_monitoring())