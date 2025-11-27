from transformers import AutoTokenizer, AutoModelForSequenceClassification
import torch
from typing import List, Dict, Any


class SentimentAgent:
    def __init__(self, model_name="ProsusAI/finbert"):
        """
        Initialize the SentimentAgent with FinBERT model.
        
        Args:
            model_name: HuggingFace model for financial sentiment analysis
        """
        try:
            self.tokenizer = AutoTokenizer.from_pretrained(model_name)
            self.model = AutoModelForSequenceClassification.from_pretrained(model_name)
            self.model.eval()  # Set to evaluation mode
            
            # FinBERT label mapping
            self.labels = ["positive", "negative", "neutral"]
            
        except Exception as e:
            raise Exception(f"Failed to load FinBERT model: {str(e)}")
    
    def analyze_sentiment(self, text: str) -> Dict[str, Any]:
        """
        Analyze sentiment of a single text.
        
        Args:
            text: Input text to analyze
            
        Returns:
            Dict with label and confidence score
        """
        # Tokenize input
        inputs = self.tokenizer(
            text,
            return_tensors="pt",
            truncation=True,
            max_length=512,
            padding=True
        )
        
        # Get model predictions
        with torch.no_grad():
            outputs = self.model(**inputs)
            predictions = torch.nn.functional.softmax(outputs.logits, dim=-1)
        
        # Get the predicted class and confidence
        confidence, predicted_class = torch.max(predictions, dim=1)
        
        label = self.labels[predicted_class.item()]
        score = confidence.item()
        
        return {
            "label": label,
            "score": round(score, 4)
        }
    
    def run(self, articles: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Analyze sentiment for a list of articles.
        
        Args:
            articles: List of article dicts with 'id' and 'text' keys
            
        Returns:
            List of articles enriched with sentiment analysis
        """
        enriched_articles = []
        
        for article in articles:
            # Create a copy to avoid mutating original
            enriched = article.copy()
            
            # Analyze sentiment
            text = article.get("text", "")
            if text:
                sentiment = self.analyze_sentiment(text)
                enriched["sentiment"] = sentiment
            else:
                # Handle empty text
                enriched["sentiment"] = {
                    "label": "neutral",
                    "score": 0.0
                }
            
            enriched_articles.append(enriched)
        
        return enriched_articles
