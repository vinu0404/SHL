"""
Script to scrape SHL assessment catalog

This script scrapes all assessments from the SHL product catalog
and saves them to a JSON file.

Usage:
    python scripts/scrape_catalog.py
"""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.scraper_service import get_scraper_service
from app.config import settings
from app.utils.logger import get_logger

logger = get_logger("scrape_script")


async def main():
    """Main scraping function"""
    logger.info("=" * 60)
    logger.info("SHL Assessment Catalog Scraper")
    logger.info("=" * 60)
    
    try:
        scraper = get_scraper_service()
        
        # Scrape all tests
        logger.info("Starting catalog scraping...")
        assessments = await scraper.scrape_all_tests()
        
        if not assessments:
            logger.error("No assessments scraped!")
            return 1
        
        # Save to JSON
        output_file = settings.ASSESSMENTS_JSON_PATH
        logger.info(f"Saving {len(assessments)} assessments to {output_file}...")
        scraper.save_to_json(assessments, output_file)
        
        logger.info("=" * 60)
        logger.info("Scraping completed successfully!")
        logger.info(f"Total assessments: {len(assessments)}")
        logger.info(f"Output file: {output_file}")
        logger.info("=" * 60)
        
        # Print sample
        if assessments:
            logger.info("\nSample assessment:")
            sample_url = list(assessments.keys())[0]
            sample = assessments[sample_url]
            logger.info(f"Name: {sample.get('name')}")
            logger.info(f"URL: {sample.get('url')}")
            logger.info(f"Test Types: {', '.join(sample.get('test_type', []))}")
            logger.info(f"Duration: {sample.get('duration', 'N/A')} minutes")
        
        return 0
        
    except Exception as e:
        logger.error(f"Scraping failed: {e}")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)