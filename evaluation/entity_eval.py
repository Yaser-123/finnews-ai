"""
Entity Extraction Evaluation Module

Compares predicted entities against ground truth with support
for exact and partial matches.
"""

import json
import os
from typing import Dict, List, Any, Set
import logging
from difflib import SequenceMatcher

logger = logging.getLogger(__name__)

# Path to ground truth file
GROUND_TRUTH_PATH = os.path.join(
    os.path.dirname(__file__),
    "ground_truth_entities.json"
)


def load_ground_truth() -> Dict[int, Dict[str, List[str]]]:
    """Load ground truth entity annotations."""
    if not os.path.exists(GROUND_TRUTH_PATH):
        logger.warning(f"Ground truth file not found: {GROUND_TRUTH_PATH}")
        return {}
    
    try:
        with open(GROUND_TRUTH_PATH, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data.get("entities", {})
    except Exception as e:
        logger.error(f"Failed to load ground truth: {str(e)}")
        return {}


def fuzzy_match(pred: str, truth: str, threshold: float = 0.85) -> bool:
    """
    Check if two entity strings match with fuzzy comparison.
    
    Args:
        pred: Predicted entity string
        truth: Ground truth entity string
        threshold: Similarity threshold (0-1)
    
    Returns:
        True if match, False otherwise
    """
    pred_norm = pred.lower().strip()
    truth_norm = truth.lower().strip()
    
    # Exact match
    if pred_norm == truth_norm:
        return True
    
    # Fuzzy match using sequence matcher
    similarity = SequenceMatcher(None, pred_norm, truth_norm).ratio()
    return similarity >= threshold


def evaluate_entity_category(
    predicted: List[str],
    ground_truth: List[str],
    category_name: str
) -> Dict[str, float]:
    """
    Evaluate one entity category (e.g., companies, sectors).
    
    Args:
        predicted: List of predicted entities
        ground_truth: List of ground truth entities
        category_name: Name of entity category
    
    Returns:
        Dict with precision, recall, f1
    """
    if not ground_truth:
        return {"precision": 0.0, "recall": 0.0, "f1": 0.0}
    
    # Match predicted to ground truth with fuzzy matching
    matched_pred = set()
    matched_truth = set()
    
    for pred in predicted:
        for truth in ground_truth:
            if fuzzy_match(pred, truth):
                matched_pred.add(pred)
                matched_truth.add(truth)
                break
    
    tp = len(matched_pred)
    fp = len(predicted) - tp
    fn = len(ground_truth) - len(matched_truth)
    
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0
    
    return {
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "f1": round(f1, 4),
        "matched": tp,
        "false_positives": fp,
        "false_negatives": fn
    }


def evaluate_entities(
    predicted: Dict[int, Dict[str, List[str]]],
    ground_truth: Dict[int, Dict[str, List[str]]] = None
) -> Dict[str, Any]:
    """
    Evaluate entity extraction quality across all articles.
    
    Args:
        predicted: Dict mapping article_id to extracted entities
                  Format: {article_id: {"companies": [...], "sectors": [...], ...}}
        ground_truth: Optional ground truth dict (loads from file if None)
    
    Returns:
        Dict with overall metrics and per-category breakdowns
    """
    if ground_truth is None:
        ground_truth = load_ground_truth()
    
    if not ground_truth:
        logger.warning("No ground truth data available")
        return {
            "overall_precision": 0.0,
            "overall_recall": 0.0,
            "overall_f1": 0.0,
            "error": "No ground truth data"
        }
    
    # Entity categories to evaluate
    categories = ["companies", "sectors", "regulators", "people", "events", "stocks"]
    
    category_results = {}
    all_precision = []
    all_recall = []
    all_f1 = []
    
    # Evaluate each category
    for category in categories:
        cat_precision = []
        cat_recall = []
        cat_f1 = []
        
        # Evaluate each article
        for article_id_str, truth_entities in ground_truth.items():
            article_id = int(article_id_str)
            
            if article_id not in predicted:
                continue
            
            pred_entities = predicted[article_id].get(category, [])
            truth_cats = truth_entities.get(category, [])
            
            if not truth_cats:  # Skip if no ground truth for this category
                continue
            
            result = evaluate_entity_category(pred_entities, truth_cats, category)
            cat_precision.append(result["precision"])
            cat_recall.append(result["recall"])
            cat_f1.append(result["f1"])
        
        # Average across articles
        if cat_precision:
            avg_precision = sum(cat_precision) / len(cat_precision)
            avg_recall = sum(cat_recall) / len(cat_recall)
            avg_f1 = sum(cat_f1) / len(cat_f1)
            
            category_results[category] = {
                "precision": round(avg_precision, 4),
                "recall": round(avg_recall, 4),
                "f1": round(avg_f1, 4),
                "num_articles": len(cat_precision)
            }
            
            all_precision.append(avg_precision)
            all_recall.append(avg_recall)
            all_f1.append(avg_f1)
    
    # Overall metrics (macro-average across categories)
    overall_precision = sum(all_precision) / len(all_precision) if all_precision else 0.0
    overall_recall = sum(all_recall) / len(all_recall) if all_recall else 0.0
    overall_f1 = sum(all_f1) / len(all_f1) if all_f1 else 0.0
    
    logger.info(f"Entity Evaluation: P={overall_precision:.3f}, R={overall_recall:.3f}, F1={overall_f1:.3f}")
    
    return {
        "overall_precision": round(overall_precision, 4),
        "overall_recall": round(overall_recall, 4),
        "overall_f1": round(overall_f1, 4),
        "by_category": category_results,
        "total_articles_evaluated": len(ground_truth)
    }


def create_sample_ground_truth():
    """Create a sample ground truth file for testing."""
    sample_data = {
        "description": "Ground truth entity annotations for evaluation",
        "entities": {
            "1": {
                "companies": ["Reserve Bank of India", "State Bank of India"],
                "sectors": ["Banking", "Financial Services"],
                "regulators": ["RBI", "SEBI"],
                "people": ["Shaktikanta Das"],
                "events": ["Monetary Policy Committee Meeting"],
                "stocks": ["SBIN"]
            },
            "2": {
                "companies": ["Reliance Industries", "Jio Platforms"],
                "sectors": ["Telecom", "Energy", "Retail"],
                "regulators": [],
                "people": ["Mukesh Ambani"],
                "events": ["Q4 Earnings"],
                "stocks": ["RELIANCE"]
            },
            "5": {
                "companies": ["Tesla Inc", "Tesla India"],
                "sectors": ["Electric Vehicles", "Automotive"],
                "regulators": ["Ministry of Heavy Industries"],
                "people": ["Elon Musk"],
                "events": ["India Market Entry"],
                "stocks": ["TSLA"]
            }
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
        1: {
            "companies": ["Reserve Bank of India", "SBI"],  # Partial match
            "sectors": ["Banking"],
            "regulators": ["RBI"],
            "people": ["Shaktikanta Das"],
            "events": ["MPC Meeting"],
            "stocks": ["SBIN"]
        },
        2: {
            "companies": ["Reliance", "Jio"],
            "sectors": ["Telecom", "Energy"],
            "regulators": [],
            "people": ["Mukesh Ambani"],
            "events": ["Quarterly Results"],
            "stocks": ["RELIANCE"]
        }
    }
    
    results = evaluate_entities(predicted)
    print(json.dumps(results, indent=2))
