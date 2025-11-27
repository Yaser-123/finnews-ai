"""
Sentiment Analysis Evaluation Module

Compares FinBERT sentiment predictions against curated labels.
"""

import json
import os
from typing import Dict, List, Any
import logging

logger = logging.getLogger(__name__)

# Path to ground truth file
GROUND_TRUTH_PATH = os.path.join(
    os.path.dirname(__file__),
    "ground_truth_sentiment.json"
)


def load_ground_truth() -> Dict[int, str]:
    """Load ground truth sentiment labels."""
    if not os.path.exists(GROUND_TRUTH_PATH):
        logger.warning(f"Ground truth file not found: {GROUND_TRUTH_PATH}")
        return {}
    
    try:
        with open(GROUND_TRUTH_PATH, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data.get("sentiments", {})
    except Exception as e:
        logger.error(f"Failed to load ground truth: {str(e)}")
        return {}


def normalize_label(label: str) -> str:
    """
    Normalize sentiment labels to standard format.
    
    Handles variations like:
    - "positive", "POSITIVE", "Positive"
    - "neg", "negative", "NEGATIVE"
    - "neu", "neutral", "NEUTRAL"
    """
    label_lower = label.lower().strip()
    
    if label_lower in ["positive", "pos", "bullish"]:
        return "positive"
    elif label_lower in ["negative", "neg", "bearish"]:
        return "negative"
    elif label_lower in ["neutral", "neu"]:
        return "neutral"
    else:
        return label_lower


def evaluate_sentiment(
    predicted: Dict[int, str],
    ground_truth: Dict[int, str] = None
) -> Dict[str, Any]:
    """
    Evaluate sentiment analysis accuracy.
    
    Args:
        predicted: Dict mapping article_id to predicted sentiment label
        ground_truth: Optional ground truth dict (loads from file if None)
    
    Returns:
        Dict with accuracy metrics and confusion matrix
    """
    if ground_truth is None:
        ground_truth_raw = load_ground_truth()
        ground_truth = {int(k): v for k, v in ground_truth_raw.items()}
    
    if not ground_truth:
        logger.warning("No ground truth data available")
        return {
            "accuracy": 0.0,
            "error": "No ground truth data"
        }
    
    # Normalize all labels
    predicted_norm = {k: normalize_label(v) for k, v in predicted.items()}
    ground_truth_norm = {k: normalize_label(v) for k, v in ground_truth.items()}
    
    # Find common article IDs
    common_ids = set(predicted_norm.keys()) & set(ground_truth_norm.keys())
    
    if not common_ids:
        logger.warning("No overlapping article IDs between predicted and ground truth")
        return {
            "accuracy": 0.0,
            "error": "No overlapping articles"
        }
    
    # Calculate accuracy
    correct = 0
    total = len(common_ids)
    
    # Confusion matrix: {(true_label, pred_label): count}
    confusion_matrix = {}
    
    # Per-class metrics
    class_stats = {
        "positive": {"correct": 0, "total": 0},
        "negative": {"correct": 0, "total": 0},
        "neutral": {"correct": 0, "total": 0}
    }
    
    for article_id in common_ids:
        true_label = ground_truth_norm[article_id]
        pred_label = predicted_norm[article_id]
        
        # Update confusion matrix
        key = (true_label, pred_label)
        confusion_matrix[key] = confusion_matrix.get(key, 0) + 1
        
        # Update class stats
        if true_label in class_stats:
            class_stats[true_label]["total"] += 1
            if true_label == pred_label:
                class_stats[true_label]["correct"] += 1
                correct += 1
    
    accuracy = correct / total if total > 0 else 0.0
    
    # Calculate per-class accuracy
    per_class_accuracy = {}
    for label, stats in class_stats.items():
        if stats["total"] > 0:
            per_class_accuracy[label] = round(stats["correct"] / stats["total"], 4)
        else:
            per_class_accuracy[label] = 0.0
    
    # Format confusion matrix for output
    confusion_matrix_formatted = {
        f"{true_label} -> {pred_label}": count
        for (true_label, pred_label), count in confusion_matrix.items()
    }
    
    logger.info(f"Sentiment Evaluation: Accuracy={accuracy:.3f}")
    
    return {
        "accuracy": round(accuracy, 4),
        "total_articles": total,
        "correct_predictions": correct,
        "incorrect_predictions": total - correct,
        "per_class_accuracy": per_class_accuracy,
        "confusion_matrix": confusion_matrix_formatted
    }


def create_sample_ground_truth():
    """Create a sample ground truth file for testing."""
    sample_data = {
        "description": "Ground truth sentiment labels for evaluation",
        "sentiments": {
            "1": "positive",
            "2": "positive",
            "3": "neutral",
            "4": "positive",
            "5": "positive",
            "6": "positive",
            "7": "positive",
            "8": "positive",
            "9": "negative",
            "10": "positive",
            "11": "positive",
            "12": "neutral",
            "13": "positive",
            "14": "positive",
            "15": "positive",
            "16": "neutral",
            "17": "neutral",
            "18": "positive",
            "19": "positive",
            "20": "positive"
        }
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
    
    # Test evaluation with dummy predictions
    predicted = {
        1: "positive",
        2: "positive",
        3: "neutral",
        4: "positive",
        5: "positive",
        6: "positive",
        7: "positive",
        8: "positive",
        9: "negative",
        10: "positive"
    }
    
    results = evaluate_sentiment(predicted)
    print(json.dumps(results, indent=2))
