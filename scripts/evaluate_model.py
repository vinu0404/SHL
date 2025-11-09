"""
Script to evaluate model performance using Mean Recall@K metric

This script evaluates the recommendation system against the labeled training set
and calculates Mean Recall@10.

Usage:
    python scripts/evaluate_model.py
"""

import asyncio
import sys
import json
from pathlib import Path
from typing import List, Dict

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.graph.workflow import execute_query
from app.database import init_db, init_chroma
from app.config import settings
from app.utils.logger import get_logger

logger = get_logger("evaluate_script")


def calculate_recall_at_k(predicted_urls: List[str], relevant_urls: List[str], k: int = 10) -> float:
    """
    Calculate Recall@K for a single query
    
    Args:
        predicted_urls: List of predicted assessment URLs
        relevant_urls: List of relevant assessment URLs
        k: Number of top predictions to consider
        
    Returns:
        Recall@K score
    """
    if not relevant_urls:
        return 0.0
    
    # Take top K predictions
    top_k_predictions = predicted_urls[:k]
    
    # Normalize URLs for comparison
    predicted_normalized = [url.rstrip('/').lower() for url in top_k_predictions]
    relevant_normalized = [url.rstrip('/').lower() for url in relevant_urls]
    
    # Count relevant items in top K
    relevant_in_top_k = sum(
        1 for url in predicted_normalized
        if url in relevant_normalized
    )
    
    # Calculate recall
    recall = relevant_in_top_k / len(relevant_urls)
    
    return recall


async def evaluate_on_test_set(test_data: Dict[str, str]) -> Dict[str, any]:
    """
    Evaluate model on test set
    
    Args:
        test_data: Dictionary mapping queries to expected URLs
        
    Returns:
        Evaluation results
    """
    results = []
    recall_scores = []
    
    logger.info(f"Evaluating on {len(test_data)} test queries...")
    
    for idx, (query, expected_url) in enumerate(test_data.items(), 1):
        logger.info(f"\n{'='*60}")
        logger.info(f"Query {idx}/{len(test_data)}")
        logger.info(f"Query: {query[:100]}...")
        logger.info(f"Expected: {expected_url}")
        
        try:
            # Execute query
            session_id = f"eval_{idx}"
            final_state = await execute_query(query, session_id)
            
            # Extract recommendations
            recommendations = final_state.get('final_recommendations', [])
            predicted_urls = [rec.get('url') for rec in recommendations if rec.get('url')]
            
            logger.info(f"Predicted {len(predicted_urls)} assessments")
            
            # Calculate recall
            # Note: The training set has single URLs, but we'll treat them as lists
            relevant_urls = [expected_url] if isinstance(expected_url, str) else expected_url
            
            recall = calculate_recall_at_k(predicted_urls, relevant_urls, k=10)
            recall_scores.append(recall)
            
            # Check if expected URL is in predictions
            expected_found = expected_url.rstrip('/').lower() in [
                url.rstrip('/').lower() for url in predicted_urls
            ]
            
            result = {
                'query': query,
                'expected_url': expected_url,
                'predicted_urls': predicted_urls[:10],
                'recall_at_10': recall,
                'expected_found': expected_found,
                'num_predictions': len(predicted_urls)
            }
            
            results.append(result)
            
            logger.info(f"Recall@10: {recall:.3f}")
            logger.info(f"Expected URL found: {expected_found}")
            
            if predicted_urls:
                logger.info(f"Top prediction: {predicted_urls[0]}")
            
        except Exception as e:
            logger.error(f"Error evaluating query {idx}: {e}")
            results.append({
                'query': query,
                'expected_url': expected_url,
                'error': str(e),
                'recall_at_10': 0.0,
                'expected_found': False
            })
            recall_scores.append(0.0)
    
    # Calculate mean recall
    mean_recall = sum(recall_scores) / len(recall_scores) if recall_scores else 0.0
    
    # Calculate accuracy (how many times expected URL was found)
    accuracy = sum(1 for r in results if r.get('expected_found', False)) / len(results)
    
    return {
        'mean_recall_at_10': mean_recall,
        'accuracy': accuracy,
        'total_queries': len(results),
        'detailed_results': results
    }


async def main():
    """Main evaluation function"""
    logger.info("=" * 60)
    logger.info("Model Evaluation Script")
    logger.info("=" * 60)
    
    try:
        # Initialize databases
        logger.info("Initializing databases...")
        init_db()
        init_chroma()
        
        # Load test data
        test_file = Path(settings.TRAIN_SET_PATH)
        
        if not test_file.exists():
            logger.error(f"Test data file not found: {test_file}")
            return 1
        
        logger.info(f"Loading test data from {test_file}...")
        
        with open(test_file, 'r', encoding='utf-8') as f:
            test_data = json.load(f)
        
        logger.info(f"Loaded {len(test_data)} test queries")
        
        # Run evaluation
        eval_results = await evaluate_on_test_set(test_data)
        
        # Print summary
        logger.info("\n" + "=" * 60)
        logger.info("EVALUATION RESULTS")
        logger.info("=" * 60)
        logger.info(f"Total Queries: {eval_results['total_queries']}")
        logger.info(f"Mean Recall@10: {eval_results['mean_recall_at_10']:.4f}")
        logger.info(f"Accuracy (Expected URL Found): {eval_results['accuracy']:.4f}")
        logger.info("=" * 60)
        
        # Save detailed results
        output_file = Path("evaluation_results.json")
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(eval_results, f, indent=2, ensure_ascii=False)
        
        logger.info(f"\nDetailed results saved to {output_file}")
        
        # Print per-query results
        logger.info("\nPer-Query Results:")
        logger.info("-" * 60)
        
        for idx, result in enumerate(eval_results['detailed_results'], 1):
            logger.info(f"\n{idx}. Query: {result['query'][:80]}...")
            logger.info(f"   Recall@10: {result.get('recall_at_10', 0):.3f}")
            logger.info(f"   Expected Found: {result.get('expected_found', False)}")
            
            if result.get('error'):
                logger.info(f"   Error: {result['error']}")
        
        return 0
        
    except Exception as e:
        logger.error(f"Evaluation failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)