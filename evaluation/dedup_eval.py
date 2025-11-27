"""
Deduplication Evaluation Module

Compares predicted deduplication clusters against ground truth
to compute precision, recall, and F1 scores.
"""

import json
import os
from typing import Dict, List, Set, Any
import logging

logger = logging.getLogger(__name__)

# Path to ground truth file
GROUND_TRUTH_PATH = os.path.join(
    os.path.dirname(__file__),
    "ground_truth_clusters.json"
)


def load_ground_truth() -> List[Dict[str, Any]]:
    """Load ground truth deduplication clusters."""
    if not os.path.exists(GROUND_TRUTH_PATH):
        logger.warning(f"Ground truth file not found: {GROUND_TRUTH_PATH}")
        return []
    
    try:
        with open(GROUND_TRUTH_PATH, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data.get("clusters", [])
    except Exception as e:
        logger.error(f"Failed to load ground truth: {str(e)}")
        return []


def clusters_to_pairs(clusters: List[Dict[str, Any]]) -> Set[tuple]:
    """
    Convert clusters to article pairs for comparison.
    
    Each cluster generates all possible pairs of articles within it.
    Example: {1, 2, 3} -> {(1,2), (1,3), (2,3)}
    """
    pairs = set()
    
    for cluster in clusters:
        main_id = cluster.get("main_id")
        merged_ids = cluster.get("merged_ids", [])
        
        # Get all articles in cluster (main + merged)
        all_ids = [main_id] + merged_ids if main_id else merged_ids
        
        # Generate all pairs
        for i in range(len(all_ids)):
            for j in range(i + 1, len(all_ids)):
                pair = tuple(sorted([all_ids[i], all_ids[j]]))
                pairs.add(pair)
    
    return pairs


def evaluate_dedup(predicted_clusters: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Evaluate deduplication accuracy.
    
    Args:
        predicted_clusters: List of predicted clusters from dedup agent
                          Each cluster: {"main_id": int, "merged_ids": [int]}
    
    Returns:
        Dict with metrics:
        - precision: Fraction of predicted pairs that are correct
        - recall: Fraction of ground truth pairs that were found
        - f1: Harmonic mean of precision and recall
        - false_merges: Pairs incorrectly merged
        - missed_merges: Pairs that should have been merged but weren't
        - total_predicted: Total predicted pairs
        - total_ground_truth: Total ground truth pairs
    """
    # Load ground truth
    ground_truth_clusters = load_ground_truth()
    
    if not ground_truth_clusters:
        logger.warning("No ground truth data available")
        return {
            "precision": 0.0,
            "recall": 0.0,
            "f1": 0.0,
            "false_merges": [],
            "missed_merges": [],
            "total_predicted": 0,
            "total_ground_truth": 0,
            "error": "No ground truth data"
        }
    
    # Convert clusters to pairs
    predicted_pairs = clusters_to_pairs(predicted_clusters)
    ground_truth_pairs = clusters_to_pairs(ground_truth_clusters)
    
    # Calculate metrics
    true_positives = predicted_pairs & ground_truth_pairs
    false_positives = predicted_pairs - ground_truth_pairs
    false_negatives = ground_truth_pairs - predicted_pairs
    
    tp_count = len(true_positives)
    fp_count = len(false_positives)
    fn_count = len(false_negatives)
    
    # Precision: What fraction of predicted pairs are correct?
    precision = tp_count / (tp_count + fp_count) if (tp_count + fp_count) > 0 else 0.0
    
    # Recall: What fraction of ground truth pairs did we find?
    recall = tp_count / (tp_count + fn_count) if (tp_count + fn_count) > 0 else 0.0
    
    # F1: Harmonic mean
    f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0
    
    logger.info(f"Dedup Evaluation: P={precision:.3f}, R={recall:.3f}, F1={f1:.3f}")
    
    return {
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "f1": round(f1, 4),
        "false_merges": sorted(list(false_positives))[:10],  # Top 10 errors
        "missed_merges": sorted(list(false_negatives))[:10],
        "total_predicted": len(predicted_pairs),
        "total_ground_truth": len(ground_truth_pairs),
        "true_positives": tp_count,
        "false_positives": fp_count,
        "false_negatives": fn_count
    }


def create_sample_ground_truth():
    """Create a sample ground truth file for testing."""
    sample_data = {
        "description": "Ground truth deduplication clusters for evaluation",
        "clusters": [
            {
                "main_id": 1,
                "merged_ids": [7, 13],
                "reason": "Same RBI repo rate announcement"
            },
            {
                "main_id": 2,
                "merged_ids": [8, 14],
                "reason": "Reliance profit report duplicates"
            },
            {
                "main_id": 5,
                "merged_ids": [10],
                "reason": "Tesla India expansion news"
            }
        ]
    }
    
    os.makedirs(os.path.dirname(GROUND_TRUTH_PATH), exist_ok=True)
    with open(GROUND_TRUTH_PATH, 'w', encoding='utf-8') as f:
        json.dump(sample_data, f, indent=2, ensure_ascii=False)
    
    logger.info(f"Created sample ground truth at {GROUND_TRUTH_PATH}")


if __name__ == "__main__":
    # Test with sample data
    logging.basicConfig(level=logging.INFO)
    
    # Create sample ground truth if it doesn't exist
    if not os.path.exists(GROUND_TRUTH_PATH):
        create_sample_ground_truth()
    
    # Test evaluation with dummy predicted clusters
    predicted = [
        {"main_id": 1, "merged_ids": [7, 13]},  # Correct
        {"main_id": 2, "merged_ids": [8]},      # Partial (missing 14)
        {"main_id": 5, "merged_ids": [10, 11]}, # False positive (11)
    ]
    
    results = evaluate_dedup(predicted)
    print(json.dumps(results, indent=2))
