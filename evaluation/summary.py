"""
Evaluation Summary Module

Combines all evaluation results into a comprehensive report.
"""

import json
import asyncio
from typing import Dict, Any
import logging
from datetime import datetime

from .dedup_eval import evaluate_dedup
from .entity_eval import evaluate_entities
from .query_eval import evaluate_queries
from .sentiment_eval import evaluate_sentiment

logger = logging.getLogger(__name__)


async def evaluate_all(
    dedup_clusters: list = None,
    entity_predictions: dict = None,
    sentiment_predictions: dict = None,
    run_query_eval: bool = True
) -> Dict[str, Any]:
    """
    Run all evaluations and combine results.
    
    Args:
        dedup_clusters: Predicted deduplication clusters (None to skip)
        entity_predictions: Predicted entities dict (None to skip)
        sentiment_predictions: Predicted sentiment dict (None to skip)
        run_query_eval: Whether to run query evaluation (can be slow)
    
    Returns:
        Combined evaluation results
    """
    logger.info("=" * 50)
    logger.info("Starting comprehensive accuracy evaluation...")
    logger.info("=" * 50)
    
    results = {
        "timestamp": datetime.now().isoformat(),
        "evaluations": {}
    }
    
    # 1. Deduplication Evaluation
    if dedup_clusters is not None:
        logger.info("\n📊 Evaluating Deduplication...")
        results["evaluations"]["dedup"] = evaluate_dedup(dedup_clusters)
    else:
        logger.info("\n⏭️  Skipping deduplication evaluation (no data provided)")
        results["evaluations"]["dedup"] = {"skipped": True}
    
    # 2. Entity Extraction Evaluation
    if entity_predictions is not None:
        logger.info("\n📊 Evaluating Entity Extraction...")
        results["evaluations"]["entities"] = evaluate_entities(entity_predictions)
    else:
        logger.info("\n⏭️  Skipping entity evaluation (no data provided)")
        results["evaluations"]["entities"] = {"skipped": True}
    
    # 3. Query Retrieval Evaluation
    if run_query_eval:
        logger.info("\n📊 Evaluating Query Retrieval...")
        results["evaluations"]["query"] = await evaluate_queries()
    else:
        logger.info("\n⏭️  Skipping query evaluation (disabled)")
        results["evaluations"]["query"] = {"skipped": True}
    
    # 4. Sentiment Analysis Evaluation
    if sentiment_predictions is not None:
        logger.info("\n📊 Evaluating Sentiment Analysis...")
        results["evaluations"]["sentiment"] = evaluate_sentiment(sentiment_predictions)
    else:
        logger.info("\n⏭️  Skipping sentiment evaluation (no data provided)")
        results["evaluations"]["sentiment"] = {"skipped": True}
    
    logger.info("\n✅ All evaluations complete!")
    
    return results


def print_summary(results: Dict[str, Any]):
    """
    Print a beautiful scoreboard of evaluation results.
    
    Args:
        results: Combined evaluation results from evaluate_all()
    """
    print("\n")
    print("=" * 60)
    print("             🎯 ACCURACY EVALUATION SUMMARY 🎯")
    print("=" * 60)
    print(f"Timestamp: {results.get('timestamp', 'N/A')}")
    print("=" * 60)
    
    evals = results.get("evaluations", {})
    
    # Deduplication
    print("\n📦 DEDUPLICATION CLUSTERING")
    print("-" * 60)
    dedup = evals.get("dedup", {})
    if dedup.get("skipped"):
        print("   Status: SKIPPED")
    elif "error" in dedup:
        print(f"   Status: ERROR - {dedup['error']}")
    else:
        print(f"   Precision:  {dedup.get('precision', 0.0):.4f}")
        print(f"   Recall:     {dedup.get('recall', 0.0):.4f}")
        print(f"   F1 Score:   {dedup.get('f1', 0.0):.4f}")
        print(f"   True Positives:  {dedup.get('true_positives', 0)}")
        print(f"   False Positives: {dedup.get('false_positives', 0)}")
        print(f"   False Negatives: {dedup.get('false_negatives', 0)}")
    
    # Entity Extraction
    print("\n🏢 ENTITY EXTRACTION")
    print("-" * 60)
    entities = evals.get("entities", {})
    if entities.get("skipped"):
        print("   Status: SKIPPED")
    elif "error" in entities:
        print(f"   Status: ERROR - {entities['error']}")
    else:
        print(f"   Overall Precision: {entities.get('overall_precision', 0.0):.4f}")
        print(f"   Overall Recall:    {entities.get('overall_recall', 0.0):.4f}")
        print(f"   Overall F1 Score:  {entities.get('overall_f1', 0.0):.4f}")
        print(f"   Articles Evaluated: {entities.get('total_articles_evaluated', 0)}")
        
        by_cat = entities.get("by_category", {})
        if by_cat:
            print("\n   By Category:")
            for cat, metrics in by_cat.items():
                print(f"      {cat.capitalize():15} - F1: {metrics.get('f1', 0.0):.4f}")
    
    # Query Retrieval
    print("\n🔍 QUERY RETRIEVAL")
    print("-" * 60)
    query = evals.get("query", {})
    if query.get("skipped"):
        print("   Status: SKIPPED")
    elif "error" in query:
        print(f"   Status: ERROR - {query['error']}")
    else:
        print(f"   Hit Rate:      {query.get('average_hit_rate', 0.0):.4f}")
        print(f"   Recall@5:      {query.get('average_recall_at_5', 0.0):.4f}")
        print(f"   Mean Reciprocal Rank (MRR): {query.get('average_mrr', 0.0):.4f}")
        print(f"   Queries Tested: {query.get('total_queries', 0)}")
    
    # Sentiment Analysis
    print("\n😊 SENTIMENT ANALYSIS")
    print("-" * 60)
    sentiment = evals.get("sentiment", {})
    if sentiment.get("skipped"):
        print("   Status: SKIPPED")
    elif "error" in sentiment:
        print(f"   Status: ERROR - {sentiment['error']}")
    else:
        print(f"   Accuracy: {sentiment.get('accuracy', 0.0):.4f}")
        print(f"   Correct:  {sentiment.get('correct_predictions', 0)}")
        print(f"   Incorrect: {sentiment.get('incorrect_predictions', 0)}")
        print(f"   Total:    {sentiment.get('total_articles', 0)}")
        
        per_class = sentiment.get("per_class_accuracy", {})
        if per_class:
            print("\n   By Class:")
            for label, acc in per_class.items():
                print(f"      {label.capitalize():10} - Accuracy: {acc:.4f}")
    
    # Summary Scoreboard
    print("\n")
    print("=" * 60)
    print("                    📊 SCOREBOARD 📊")
    print("=" * 60)
    
    scoreboard = []
    
    if not dedup.get("skipped") and "error" not in dedup:
        scoreboard.append(("Dedup F1", dedup.get("f1", 0.0)))
    
    if not entities.get("skipped") and "error" not in entities:
        scoreboard.append(("Entity Precision", entities.get("overall_precision", 0.0)))
        scoreboard.append(("Entity F1", entities.get("overall_f1", 0.0)))
    
    if not query.get("skipped") and "error" not in query:
        scoreboard.append(("Query Recall@5", query.get("average_recall_at_5", 0.0)))
        scoreboard.append(("Query MRR", query.get("average_mrr", 0.0)))
    
    if not sentiment.get("skipped") and "error" not in sentiment:
        scoreboard.append(("Sentiment Accuracy", sentiment.get("accuracy", 0.0)))
    
    for metric_name, score in scoreboard:
        bar_length = int(score * 40)  # 40 chars max
        bar = "█" * bar_length + "░" * (40 - bar_length)
        print(f"   {metric_name:20} {score:.4f}  {bar}")
    
    print("=" * 60)
    print("\n")


def save_results(results: Dict[str, Any], filepath: str):
    """
    Save evaluation results to JSON file.
    
    Args:
        results: Evaluation results dict
        filepath: Path to save JSON file
    """
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        logger.info(f"✅ Results saved to {filepath}")
    except Exception as e:
        logger.error(f"❌ Failed to save results: {str(e)}")


if __name__ == "__main__":
    # Test summary with dummy data
    logging.basicConfig(level=logging.INFO)
    
    async def test():
        results = await evaluate_all(
            dedup_clusters=[],
            entity_predictions={},
            sentiment_predictions={},
            run_query_eval=False
        )
        print_summary(results)
    
    asyncio.run(test())
