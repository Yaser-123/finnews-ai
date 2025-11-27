# Accuracy Evaluation Module

Comprehensive evaluation framework for FinNews AI pipeline components.

## 📊 Overview

This module provides automated accuracy testing for all major pipeline components:

- **Deduplication**: Precision, Recall, F1 for clustering accuracy
- **Entity Extraction**: Multi-category entity quality metrics
- **Query Retrieval**: Hit rate, Recall@5, MRR for semantic search
- **Sentiment Analysis**: Classification accuracy with confusion matrix

## 🚀 Quick Start

Run the complete evaluation suite:

```bash
python demo/test_accuracy.py
```

This will:
1. Create sample ground truth files (if they don't exist)
2. Collect predictions from the pipeline
3. Run all evaluations
4. Print a beautiful scoreboard
5. Save results to `evaluation/metrics.json`

## 📁 Module Structure

```
evaluation/
├── __init__.py              # Module exports
├── dedup_eval.py            # Deduplication evaluation
├── entity_eval.py           # Entity extraction evaluation
├── query_eval.py            # Query retrieval evaluation
├── sentiment_eval.py        # Sentiment analysis evaluation
├── summary.py               # Combined results & scoreboard
├── ground_truth_clusters.json    # Dedup ground truth
├── ground_truth_entities.json    # Entity ground truth
├── ground_truth_sentiment.json   # Sentiment ground truth
└── metrics.json             # Latest evaluation results
```

## 🔍 Individual Module Usage

### 1. Deduplication Evaluation

```python
from evaluation.dedup_eval import evaluate_dedup

# Predicted clusters from pipeline
predicted_clusters = [
    {"main_id": 1, "merged_ids": [7, 13]},
    {"main_id": 2, "merged_ids": [8, 14]},
]

results = evaluate_dedup(predicted_clusters)
print(f"F1 Score: {results['f1']:.4f}")
```

**Metrics:**
- `precision`: Fraction of predicted pairs that are correct
- `recall`: Fraction of ground truth pairs found
- `f1`: Harmonic mean of precision and recall
- `false_merges`: Incorrectly merged article pairs
- `missed_merges`: Pairs that should have been merged

### 2. Entity Extraction Evaluation

```python
from evaluation.entity_eval import evaluate_entities

# Predicted entities from pipeline
predicted = {
    1: {
        "companies": ["Reserve Bank of India", "SBI"],
        "sectors": ["Banking"],
        "regulators": ["RBI"],
        "people": ["Shaktikanta Das"],
        "events": ["MPC Meeting"],
        "stocks": ["SBIN"]
    }
}

results = evaluate_entities(predicted)
print(f"Overall F1: {results['overall_f1']:.4f}")
```

**Features:**
- Fuzzy matching (85% similarity threshold)
- Per-category metrics (companies, sectors, regulators, people, events, stocks)
- Handles partial matches and abbreviations

### 3. Query Retrieval Evaluation

```python
import asyncio
from evaluation.query_eval import evaluate_queries

# Run benchmark queries
results = asyncio.run(evaluate_queries())
print(f"Recall@5: {results['average_recall_at_5']:.4f}")
```

**Benchmark Queries:**
1. "RBI monetary policy changes" → Articles about regulatory changes
2. "Reliance earnings and profit" → Company financial news
3. "Tesla India market expansion" → Market expansion stories
4. "Banking sector performance" → Sector-level analysis

**Metrics:**
- `hit_rate`: Was at least one relevant article retrieved?
- `recall_at_5`: Fraction of relevant articles in top 5
- `mrr`: Mean Reciprocal Rank (1/position of first relevant result)

### 4. Sentiment Analysis Evaluation

```python
from evaluation.sentiment_eval import evaluate_sentiment

# Predicted sentiment labels
predicted = {
    1: "positive",
    2: "positive",
    3: "neutral",
    9: "negative"
}

results = evaluate_sentiment(predicted)
print(f"Accuracy: {results['accuracy']:.4f}")
```

**Features:**
- Label normalization (handles "pos", "positive", "POSITIVE")
- Per-class accuracy
- Confusion matrix

## 🎯 Combined Evaluation

Run all evaluations at once:

```python
import asyncio
from evaluation.summary import evaluate_all, print_summary

async def main():
    results = await evaluate_all(
        dedup_clusters=dedup_clusters,
        entity_predictions=entity_predictions,
        sentiment_predictions=sentiment_predictions,
        run_query_eval=True  # Set False to skip query eval
    )
    
    print_summary(results)

asyncio.run(main())
```

## 📝 Ground Truth Files

### Creating Custom Ground Truth

Edit the JSON files in `evaluation/` to match your test dataset:

**ground_truth_clusters.json:**
```json
{
  "description": "Ground truth deduplication clusters",
  "clusters": [
    {
      "main_id": 1,
      "merged_ids": [7, 13],
      "reason": "Same RBI repo rate announcement"
    }
  ]
}
```

**ground_truth_entities.json:**
```json
{
  "description": "Ground truth entity annotations",
  "entities": {
    "1": {
      "companies": ["Reserve Bank of India", "State Bank of India"],
      "sectors": ["Banking", "Financial Services"],
      "regulators": ["RBI", "SEBI"],
      "people": ["Shaktikanta Das"],
      "events": ["Monetary Policy Committee Meeting"],
      "stocks": ["SBIN"]
    }
  }
}
```

**ground_truth_sentiment.json:**
```json
{
  "description": "Ground truth sentiment labels",
  "sentiments": {
    "1": "positive",
    "2": "positive",
    "3": "neutral",
    "9": "negative"
  }
}
```

## 📊 Scoreboard Example

```
============================================================
             🎯 ACCURACY EVALUATION SUMMARY 🎯
============================================================

📦 DEDUPLICATION CLUSTERING
   Precision:  1.0000
   Recall:     1.0000
   F1 Score:   1.0000

🏢 ENTITY EXTRACTION
   Overall Precision: 1.0000
   Overall Recall:    0.9398
   Overall F1 Score:  0.9611

🔍 QUERY RETRIEVAL
   Hit Rate:      0.9500
   Recall@5:      0.8800
   MRR:           0.8250

😊 SENTIMENT ANALYSIS
   Accuracy: 1.0000

============================================================
                    📊 SCOREBOARD 📊
============================================================
   Dedup F1             1.0000  ████████████████████████████
   Entity Precision     1.0000  ████████████████████████████
   Entity F1            0.9611  ██████████████████████████░░
   Query Recall@5       0.8800  ████████████████████████░░░░
   Sentiment Accuracy   1.0000  ████████████████████████████
============================================================
```

## 🔧 Integration with Pipeline

To evaluate a full pipeline run:

```python
from graphs.pipeline_graph import workflow
from evaluation.summary import evaluate_all, print_summary, save_results

# Run pipeline
result = await workflow.ainvoke(initial_state)

# Extract predictions
dedup_clusters = result["dedup_output"]["clusters"]
entity_predictions = {
    article["id"]: article["entities"]
    for article in result["entity_articles"]
}
sentiment_predictions = {
    article["id"]: article["sentiment"]["label"]
    for article in result["sentiment_articles"]
}

# Evaluate
eval_results = await evaluate_all(
    dedup_clusters=dedup_clusters,
    entity_predictions=entity_predictions,
    sentiment_predictions=sentiment_predictions,
    run_query_eval=True
)

print_summary(eval_results)
save_results(eval_results, "evaluation/metrics.json")
```

## 📈 Metrics Interpretation

### Deduplication
- **F1 > 0.95**: Excellent clustering
- **F1 0.85-0.95**: Good clustering
- **F1 < 0.85**: Review similarity thresholds

### Entity Extraction
- **Precision > 0.90**: Clean extractions, few false positives
- **Recall > 0.85**: Captures most entities
- Monitor per-category F1 to identify weak areas

### Query Retrieval
- **Recall@5 > 0.80**: Strong semantic search
- **MRR > 0.70**: Relevant results ranked high
- **Hit Rate > 0.90**: Rarely misses relevant content

### Sentiment Analysis
- **Accuracy > 0.90**: Reliable sentiment classification
- Check per-class accuracy for bias (e.g., poor negative detection)

## 🐛 Troubleshooting

**Issue**: "No ground truth data available"
- **Solution**: Run `demo/test_accuracy.py` once to generate sample ground truth files, then customize them

**Issue**: Query evaluation takes too long
- **Solution**: Set `run_query_eval=False` in `evaluate_all()` or reduce benchmark query count

**Issue**: Low recall scores
- **Solution**: Check if article IDs in ground truth match your dataset

## 📚 References

- **Precision/Recall/F1**: Standard information retrieval metrics
- **MRR**: Mean Reciprocal Rank for ranking quality
- **Fuzzy Matching**: SequenceMatcher with 85% threshold for entity comparison
- **Cluster Evaluation**: Pair-based comparison (all pairs within a cluster)

## 🎓 Best Practices

1. **Update ground truth regularly** as you add new test articles
2. **Run evaluation after major changes** to catch regressions
3. **Track metrics over time** by saving results with timestamps
4. **Focus on F1 scores** for balanced precision/recall optimization
5. **Use query evaluation** to validate semantic search improvements

---

For questions or issues, see the main project documentation.
