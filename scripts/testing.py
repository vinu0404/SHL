"""
Testing Script - Generate predictions on test set

This script takes queries from Test-Set.json, gets recommendations from the API,
and saves results in the required CSV format for submission.

Usage:
    python scripts/testing.py
"""

import sys
import json
import csv
import time
from pathlib import Path
from typing import List, Dict, Any
import requests

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.utils.logger import get_logger

logger = get_logger("testing_script")


class TestRunner:
    """Class to run tests and generate predictions"""
    
    def __init__(self, api_url: str = "http://localhost:8000"):
        self.api_url = api_url
        self.recommend_endpoint = f"{api_url}/api/recommend"
        self.health_endpoint = f"{api_url}/api/health"
        
        logger.info(f"Initialized TestRunner with API: {api_url}")
    
    def check_api_health(self) -> bool:
        """
        Check if API is running and healthy
        
        Returns:
            True if API is healthy
        """
        try:
            response = requests.get(self.health_endpoint, timeout=5)
            if response.status_code == 200:
                logger.info("✅ API is healthy")
                return True
            else:
                logger.error(f"❌ API returned status {response.status_code}")
                return False
        except requests.exceptions.ConnectionError:
            logger.error("❌ Cannot connect to API. Is the server running?")
            logger.error(f"   Make sure server is running at: {self.api_url}")
            return False
        except Exception as e:
            logger.error(f"❌ API health check failed: {e}")
            return False
    
    def get_recommendations(self, query: str) -> List[str]:
        """
        Get assessment recommendations for a query
        
        Args:
            query: Job description or query text
            
        Returns:
            List of assessment URLs
        """
        try:
            logger.info(f"Getting recommendations for query: {query[:100]}...")
            
            response = requests.post(
                self.recommend_endpoint,
                json={"query": query},
                timeout=60  # 60 second timeout for longer queries
            )
            
            if response.status_code == 200:
                data = response.json()
                assessments = data.get('recommended_assessments', [])
                urls = [assessment['url'] for assessment in assessments]
                
                logger.info(f"✅ Got {len(urls)} recommendations")
                return urls
            
            elif response.status_code == 404:
                logger.warning(f"⚠️  No assessments found for query")
                return []
            
            else:
                logger.error(f"❌ API returned status {response.status_code}")
                logger.error(f"   Response: {response.text}")
                return []
                
        except requests.exceptions.Timeout:
            logger.error(f"❌ Request timeout after 60 seconds")
            return []
        except Exception as e:
            logger.error(f"❌ Failed to get recommendations: {e}")
            return []
    
    def load_test_set(self, filepath: str) -> Dict[str, str]:
        """
        Load test set from JSON file
        
        Args:
            filepath: Path to test set JSON file
            
        Returns:
            Dictionary mapping query IDs to queries
        """
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                test_set = json.load(f)
            
            logger.info(f"✅ Loaded {len(test_set)} test queries from {filepath}")
            return test_set
            
        except FileNotFoundError:
            logger.error(f"❌ Test set file not found: {filepath}")
            raise
        except json.JSONDecodeError as e:
            logger.error(f"❌ Invalid JSON in test set: {e}")
            raise
    
    def run_tests(self, test_set: Dict[str, str], delay: float = 1.0) -> List[Dict[str, str]]:
        """
        Run all tests and collect results
        
        Args:
            test_set: Dictionary of test queries
            delay: Delay between requests (seconds)
            
        Returns:
            List of prediction results
        """
        results = []
        total_queries = len(test_set)
        
        logger.info("=" * 60)
        logger.info(f"Running tests on {total_queries} queries")
        logger.info("=" * 60)
        
        for idx, (query_id, query_text) in enumerate(test_set.items(), 1):
            logger.info(f"\n[{idx}/{total_queries}] Processing Query {query_id}")
            logger.info("-" * 60)
            
            # Get recommendations
            urls = self.get_recommendations(query_text)
            
            # Store results
            if urls:
                for url in urls:
                    results.append({
                        'query_id': query_id,
                        'query': query_text,
                        'assessment_url': url
                    })
            else:
                # If no recommendations, add empty entry
                logger.warning(f"⚠️  No recommendations for Query {query_id}")
                results.append({
                    'query_id': query_id,
                    'query': query_text,
                    'assessment_url': 'NO_RECOMMENDATIONS'
                })
            
            # Delay between requests to avoid overwhelming API
            if idx < total_queries:
                time.sleep(delay)
        
        logger.info("\n" + "=" * 60)
        logger.info(f"✅ Completed {total_queries} queries")
        logger.info(f"   Total recommendations: {len(results)}")
        logger.info("=" * 60)
        
        return results
    
    def save_to_csv(self, results: List[Dict[str, str]], output_file: str):
        """
        Save results to CSV in the required format
        
        Args:
            results: List of prediction results
            output_file: Output CSV file path
        """
        try:
            with open(output_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                
                # Write header
                writer.writerow(['Query', 'Assessment_url'])
                
                # Write data
                for result in results:
                    writer.writerow([
                        result['query'],
                        result['assessment_url']
                    ])
            
            logger.info(f"✅ Saved results to {output_file}")
            logger.info(f"   Total rows: {len(results)}")
            
        except Exception as e:
            logger.error(f"❌ Failed to save CSV: {e}")
            raise
    
    def generate_summary(self, results: List[Dict[str, str]], test_set: Dict[str, str]):
        """
        Generate summary statistics
        
        Args:
            results: List of prediction results
            test_set: Original test set
        """
        logger.info("\n" + "=" * 60)
        logger.info("SUMMARY STATISTICS")
        logger.info("=" * 60)
        
        total_queries = len(test_set)
        total_recommendations = len(results)
        
        # Count recommendations per query
        query_counts = {}
        for result in results:
            query_id = result['query_id']
            query_counts[query_id] = query_counts.get(query_id, 0) + 1
        
        # Calculate stats
        queries_with_recommendations = sum(1 for count in query_counts.values() if count > 0)
        avg_recommendations = total_recommendations / total_queries if total_queries > 0 else 0
        
        logger.info(f"Total Queries: {total_queries}")
        logger.info(f"Queries with Recommendations: {queries_with_recommendations}")
        logger.info(f"Total Recommendations: {total_recommendations}")
        logger.info(f"Average Recommendations per Query: {avg_recommendations:.2f}")
        
        logger.info("\nRecommendations per Query:")
        for query_id in sorted(query_counts.keys(), key=lambda x: int(x)):
            count = query_counts[query_id]
            logger.info(f"  Query {query_id}: {count} recommendations")
        
        logger.info("=" * 60)


def main():
    """Main testing function"""
    
    # Configuration
    API_URL = "http://localhost:8000"
    TEST_SET_FILE = "data/Test-Set.json"
    OUTPUT_FILE = "predictions.csv"
    DELAY_BETWEEN_REQUESTS = 1.0  # seconds
    
    logger.info("=" * 60)
    logger.info("SHL Assessment Recommendation System - Testing Script")
    logger.info("=" * 60)
    
    try:
        # Initialize test runner
        runner = TestRunner(api_url=API_URL)
        
        # Check API health
        logger.info("\nStep 1: Checking API health...")
        if not runner.check_api_health():
            logger.error("\n❌ API is not available!")
            logger.error("Please make sure the server is running:")
            logger.error("  python run.py")
            return 1
        
        # Load test set
        logger.info("\nStep 2: Loading test set...")
        test_set_path = Path(TEST_SET_FILE)
        
        if not test_set_path.exists():
            logger.error(f"\n❌ Test set not found: {TEST_SET_FILE}")
            logger.error("Please make sure Test-Set.json is in the data/ directory")
            return 1
        
        test_set = runner.load_test_set(TEST_SET_FILE)
        
        # Run tests
        logger.info("\nStep 3: Running tests...")
        logger.info(f"  Delay between requests: {DELAY_BETWEEN_REQUESTS}s")
        
        results = runner.run_tests(test_set, delay=DELAY_BETWEEN_REQUESTS)
        
        # Save results
        logger.info("\nStep 4: Saving results...")
        output_path = Path(OUTPUT_FILE)
        runner.save_to_csv(results, str(output_path))
        
        # Generate summary
        logger.info("\nStep 5: Generating summary...")
        runner.generate_summary(results, test_set)
        
        # Final message
        logger.info("\n" + "=" * 60)
        logger.info("✅ TESTING COMPLETED SUCCESSFULLY!")
        logger.info("=" * 60)
        logger.info(f"Output file: {output_path.absolute()}")
        logger.info(f"Total queries processed: {len(test_set)}")
        logger.info(f"Total recommendations: {len(results)}")
        logger.info("=" * 60)
        
        return 0
        
    except KeyboardInterrupt:
        logger.warning("\n\n⚠️  Testing interrupted by user")
        return 1
    except Exception as e:
        logger.error(f"\n\n❌ Testing failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)