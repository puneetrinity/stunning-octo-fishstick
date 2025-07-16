#!/usr/bin/env python3
"""
Test script for citation extraction engine
"""
import asyncio
import logging
from app.services.citation_extraction_service import citation_extraction_service

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_citation_extraction():
    """Test the citation extraction functionality"""
    try:
        print("Testing Citation Extraction Engine")
        print("=" * 50)
        
        # Test response with multiple brand mentions
        test_response = """
        When choosing project management software, there are several excellent options to consider. 
        Slack is great for team communication and has excellent integrations. For more comprehensive 
        project management, Asana offers robust task tracking and team collaboration features. 
        Many teams also use Trello for its simple Kanban board interface, though it may lack some 
        advanced features. Microsoft Teams is another solid choice, especially for organizations 
        already using Office 365. Ultimately, the best choice depends on your team's specific needs 
        and workflow preferences.
        """
        
        test_query = "What are the best project management tools for teams?"
        test_brands = ["Slack", "Asana", "Trello", "Microsoft Teams", "Notion", "Monday.com"]
        
        print(f"Query: {test_query}")
        print(f"Brands to check: {test_brands}")
        print(f"Response length: {len(test_response)} characters")
        print()
        
        # Run citation extraction
        result = await citation_extraction_service.extract_citations(
            response_text=test_response,
            query_text=test_query,
            brand_names=test_brands,
            platform="test",
            include_context=True,
            context_window=100
        )
        
        print("CITATION EXTRACTION RESULTS:")
        print(f"- Total brands checked: {result.total_brands_checked}")
        print(f"- Brands mentioned: {result.brands_mentioned}")
        print(f"- Total mentions found: {len(result.brand_mentions)}")
        print()
        
        print("DETAILED MENTIONS:")
        for i, mention in enumerate(result.brand_mentions, 1):
            print(f"{i}. Brand: {mention.brand_name}")
            print(f"   Position: {mention.position}")
            print(f"   Mention: \"{mention.mention_text}\"")
            print(f"   Type: {mention.mention_type.value}")
            print(f"   Sentiment: {mention.sentiment_type.value} ({mention.sentiment_score:.2f})")
            print(f"   Prominence: {mention.prominence_score:.2f}")
            print(f"   Confidence: {mention.confidence_score:.2f}")
            print(f"   Context: \"{mention.context[:100]}...\"")
            print()
        
        print("RESPONSE ANALYSIS:")
        analysis = result.response_analysis
        print(f"- Total sentences: {analysis.get('total_sentences', 0)}")
        print(f"- Total words: {analysis.get('total_words', 0)}")
        print(f"- Mentions per sentence: {analysis.get('mentions_per_sentence', 0):.2f}")
        print(f"- Has lists: {analysis.get('has_lists', False)}")
        print(f"- Has quotes: {analysis.get('has_quotes', False)}")
        
        sentiment_dist = analysis.get('sentiment_distribution', {})
        print(f"- Sentiment distribution:")
        for sentiment, count in sentiment_dist.items():
            print(f"  {sentiment}: {count}")
        
        print()
        print("EXTRACTION METADATA:")
        metadata = result.extraction_metadata
        print(f"- NLP available: {metadata.get('nlp_available', False)}")
        print(f"- Extraction method: {metadata.get('extraction_method', 'unknown')}")
        print(f"- Context window: {metadata.get('context_window', 0)}")
        
        print()
        print("=" * 50)
        print("Citation extraction test completed successfully!")
        
        # Test edge cases
        print("\nTesting Edge Cases:")
        print("-" * 30)
        
        # Test with no mentions
        no_mention_response = "This is a response that doesn't mention any of the brands we're looking for."
        no_mention_result = await citation_extraction_service.extract_citations(
            response_text=no_mention_response,
            query_text="Test query",
            brand_names=["NonExistentBrand"],
            platform="test"
        )
        print(f"No mentions test: {no_mention_result.brands_mentioned} mentions found (expected: 0)")
        
        # Test with partial matches
        partial_response = "I love using slack for communication, and asana is great for project management."
        partial_result = await citation_extraction_service.extract_citations(
            response_text=partial_response,
            query_text="Test query",
            brand_names=["Slack", "Asana"],
            platform="test"
        )
        print(f"Partial matches test: {partial_result.brands_mentioned} mentions found (expected: 2)")
        
        # Test with complex context
        complex_response = """
        Here's a comparison of project management tools:
        
        1. Slack - Excellent for team communication
        2. Asana vs Trello - Both good, but Asana has more features
        3. Microsoft Teams is recommended for enterprise use
        
        I would avoid Slack for project management and use Asana instead.
        """
        complex_result = await citation_extraction_service.extract_citations(
            response_text=complex_response,
            query_text="Compare project management tools",
            brand_names=["Slack", "Asana", "Trello", "Microsoft Teams"],
            platform="test"
        )
        print(f"Complex context test: {complex_result.brands_mentioned} mentions found")
        print(f"Mention types found: {[m.mention_type.value for m in complex_result.brand_mentions]}")
        
        print("\nAll tests completed successfully!")
        
    except Exception as e:
        logger.error(f"Error in citation extraction test: {e}")
        print(f"Test failed: {e}")


if __name__ == "__main__":
    asyncio.run(test_citation_extraction())