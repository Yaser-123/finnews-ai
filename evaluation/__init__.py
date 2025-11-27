"""
Accuracy Evaluation Module for FinNews AI

This module provides comprehensive evaluation metrics for:
- Deduplication clustering accuracy
- Entity extraction quality
- Query retrieval performance
- Sentiment analysis accuracy
"""

from .dedup_eval import evaluate_dedup
from .entity_eval import evaluate_entities
from .query_eval import evaluate_queries
from .sentiment_eval import evaluate_sentiment
from .summary import evaluate_all, print_summary

__all__ = [
    "evaluate_dedup",
    "evaluate_entities",
    "evaluate_queries",
    "evaluate_sentiment",
    "evaluate_all",
    "print_summary"
]
