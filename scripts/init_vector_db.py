"""
Script to initialize ChromaDB with assessment data

This script loads assessments from the JSON file and indexes them
into the ChromaDB vector store.

Usage:
    python scripts/init_vector_db.py
"""

import asyncio
import sys
import json
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.database.chroma_db import init_chroma
from app.services.vector_store_service import get_vector_store_service
from app.config import settings
from app.utils.logger import get_logger

logger = get_logger("init_vector_db_script")


async def main():
    """Main initialization function"""
    logger.info("=" * 60)
    logger.info("ChromaDB Vector Store Initialization")
    logger.info("=" * 60)
    
    try:
        # Initialize ChromaDB
        logger.info("Initializing ChromaDB...")
        init_chroma()
        
        vector_store = get_vector_store_service()
        
        # Check current state
        current_count = vector_store.chroma_manager.count_documents()
        logger.info(f"Current documents in vector store: {current_count}")
        
        # Load assessments from JSON
        assessments_file = Path(settings.ASSESSMENTS_JSON_PATH)
        
        if not assessments_file.exists():
            logger.error(f"Assessments file not found: {assessments_file}")
            logger.info("Please run scripts/scrape_catalog.py first to scrape the data")
            return 1
        
        logger.info(f"Loading assessments from {assessments_file}...")
        
        with open(assessments_file, 'r', encoding='utf-8') as f:
            assessments = json.load(f)
        
        logger.info(f"Loaded {len(assessments)} assessments from JSON")
        
        # Ask for confirmation if vector store already has data
        if current_count > 0:
            logger.warning(f"Vector store already contains {current_count} documents")
            response = input("Do you want to clear and re-index? (yes/no): ")
            
            if response.lower() not in ['yes', 'y']:
                logger.info("Initialization cancelled")
                return 0
            
            logger.info("Clearing existing vector store...")
            await vector_store.clear_collection()
        
        # Index assessments
        logger.info("Indexing assessments into ChromaDB...")
        logger.info("This may take several minutes...")
        
        indexed_count = await vector_store.index_assessments(assessments)
        
        logger.info("=" * 60)
        logger.info("Initialization completed successfully!")
        logger.info(f"Indexed assessments: {indexed_count}")
        logger.info(f"Collection: {settings.CHROMA_COLLECTION_NAME}")
        logger.info(f"Storage path: {settings.CHROMA_DB_PATH}")
        logger.info("=" * 60)
        
        # Verify by doing a test search
        logger.info("\nTesting vector store with sample query...")
        test_results = await vector_store.search_assessments(
            query="Python programming assessment",
            top_k=3
        )
        
        if test_results:
            logger.info(f"Test search returned {len(test_results)} results:")
            for i, result in enumerate(test_results[:3], 1):
                logger.info(f"  {i}. {result.get('name')} (score: {result.get('similarity_score', 0):.3f})")
        else:
            logger.warning("Test search returned no results")
        
        return 0
        
    except Exception as e:
        logger.error(f"Initialization failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)