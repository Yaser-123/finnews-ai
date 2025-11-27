"""
Accuracy Evaluation Test Script

Runs the complete evaluation pipeline and generates metrics report.
"""

import asyncio
import sys
import os
import logging

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from evaluation.summary import evaluate_all, print_summary, save_results
from evaluation.dedup_eval import create_sample_ground_truth as create_dedup_gt
from evaluation.entity_eval import create_sample_ground_truth as create_entity_gt
from evaluation.sentiment_eval import create_sample_ground_truth as create_sentiment_gt

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


async def collect_pipeline_predictions():
    """
    Collect predictions from a full pipeline run.
    
    In a real scenario, this would:
    1. Run the pipeline
    2. Collect dedup clusters, entities, sentiment labels
    3. Return them for evaluation
    
    For demo purposes, we'll use dummy data.
    """
    logger.info("Collecting predictions from pipeline...")
    
    # Dummy dedup clusters (would come from pipeline)
    dedup_clusters = [
        {"main_id": 1, "merged_ids": [7, 13]},
        {"main_id": 2, "merged_ids": [8, 14]},
        {"main_id": 5, "merged_ids": [10]},
    ]
    
    # Dummy entity predictions (would come from entity extraction)
    entity_predictions = {
        1: {
            "companies": ["Reserve Bank of India", "State Bank of India"],
            "sectors": ["Banking", "Financial Services"],
            "regulators": ["RBI"],
            "people": ["Shaktikanta Das"],
            "events": ["Monetary Policy Committee Meeting"],
            "stocks": ["SBIN"]
        },
        2: {
            "companies": ["Reliance Industries", "Jio Platforms"],
            "sectors": ["Telecom", "Energy"],
            "regulators": [],
            "people": ["Mukesh Ambani"],
            "events": ["Q4 Earnings"],
            "stocks": ["RELIANCE"]
        },
        5: {
            "companies": ["Tesla Inc", "Tesla India"],
            "sectors": ["Electric Vehicles", "Automotive"],
            "regulators": ["Ministry of Heavy Industries"],
            "people": ["Elon Musk"],
            "events": ["India Market Entry"],
            "stocks": ["TSLA"]
        }
    }
    
    # Dummy sentiment predictions (would come from FinBERT)
    sentiment_predictions = {
        1: "positive",
        2: "positive",
        3: "neutral",
        4: "positive",
        5: "positive",
        6: "positive",
        7: "positive",
        8: "positive",
        9: "negative",
        10: "positive",
        11: "positive",
        12: "neutral",
        13: "positive",
        14: "positive",
        15: "positive",
        16: "neutral",
        17: "neutral",
        18: "positive",
        19: "positive",
        20: "positive"
    }
    
    return dedup_clusters, entity_predictions, sentiment_predictions


async def main():
    """Main evaluation script."""
    print("\n" + "=" * 70)
    print("🎯 FinNews AI - Accuracy Evaluation Pipeline")
    print("=" * 70 + "\n")
    
    # Ensure ground truth files exist
    logger.info("Checking ground truth files...")
    
    eval_dir = os.path.join(os.path.dirname(__file__), "..", "evaluation")
    
    # Create sample ground truth files if they don't exist
    if not os.path.exists(os.path.join(eval_dir, "ground_truth_clusters.json")):
        logger.info("Creating sample dedup ground truth...")
        create_dedup_gt()
    
    if not os.path.exists(os.path.join(eval_dir, "ground_truth_entities.json")):
        logger.info("Creating sample entity ground truth...")
        create_entity_gt()
    
    if not os.path.exists(os.path.join(eval_dir, "ground_truth_sentiment.json")):
        logger.info("Creating sample sentiment ground truth...")
        create_sentiment_gt()
    
    # Collect predictions from pipeline
    logger.info("\nCollecting predictions from pipeline...")
    dedup_clusters, entity_predictions, sentiment_predictions = await collect_pipeline_predictions()
    
    # Run all evaluations
    logger.info("\nRunning comprehensive evaluation...")
    results = await evaluate_all(
        dedup_clusters=dedup_clusters,
        entity_predictions=entity_predictions,
        sentiment_predictions=sentiment_predictions,
        run_query_eval=False  # Set to True to test query evaluation (requires ChromaDB)
    )
    
    # Print beautiful summary
    print_summary(results)
    
    # Save results to file
    metrics_path = os.path.join(eval_dir, "metrics.json")
    save_results(results, metrics_path)
    
    print(f"\n✅ Evaluation complete! Metrics saved to: {metrics_path}\n")


if __name__ == "__main__":
    asyncio.run(main())
