from sentence_transformers import SentenceTransformer, util
import numpy as np


class DeduplicationAgent:
    def __init__(self, model_name="sentence-transformers/all-mpnet-base-v2", threshold=0.80):
        """
        Initialize the DeduplicationAgent with a sentence transformer model.
        
        Args:
            model_name: HuggingFace model for encoding text
            threshold: Cosine similarity threshold for detecting duplicates (0-1)
        """
        self.model = SentenceTransformer(model_name)
        self.threshold = threshold
    
    def run(self, articles):
        """
        Deduplicate articles based on semantic similarity.
        
        Args:
            articles: List of dicts with 'id' and 'text' keys
            
        Returns:
            {
                "unique_articles": [...],
                "clusters": [{"main_id": <id>, "merged_ids": [<id>, ...]}]
            }
        """
        if not articles:
            return {"unique_articles": [], "clusters": []}
        
        # Extract texts and encode them
        texts = [article["text"] for article in articles]
        embeddings = self.model.encode(texts, convert_to_tensor=True)
        
        # Compute pairwise cosine similarities
        similarities = util.cos_sim(embeddings, embeddings).cpu().numpy()
        
        # Track which articles have been merged
        visited = set()
        unique_articles = []
        clusters = []
        
        for i, article in enumerate(articles):
            if i in visited:
                continue
            
            # Find all similar articles (including self)
            similar_indices = np.where(similarities[i] >= self.threshold)[0]
            
            # Filter out already visited articles
            similar_indices = [idx for idx in similar_indices if idx not in visited]
            
            if not similar_indices:
                continue
            
            # Use the first article as the representative
            main_article = articles[similar_indices[0]]
            unique_articles.append(main_article)
            
            # Create cluster info
            merged_ids = [articles[idx]["id"] for idx in similar_indices]
            clusters.append({
                "main_id": main_article["id"],
                "merged_ids": merged_ids
            })
            
            # Mark all similar articles as visited
            visited.update(similar_indices)
        
        return {
            "unique_articles": unique_articles,
            "clusters": clusters
        }
