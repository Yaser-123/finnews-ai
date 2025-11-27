import chromadb
from sentence_transformers import SentenceTransformer
import spacy
from typing import List, Dict, Any


class QueryAgent:
    def __init__(self, model_name="sentence-transformers/all-mpnet-base-v2", collection_name="news"):
        """
        Initialize the QueryAgent with ChromaDB and sentence transformers.
        
        Args:
            model_name: Sentence transformer model for embeddings
            collection_name: Name of the ChromaDB collection
        """
        # Initialize embedding model
        self.model = SentenceTransformer(model_name)
        
        # Initialize ChromaDB
        self.client = chromadb.Client()
        self.collection = self.client.get_or_create_collection(collection_name)
        
        # Load spaCy for query intent extraction
        try:
            self.nlp = spacy.load("en_core_web_sm")
        except OSError:
            raise Exception(
                "spaCy model 'en_core_web_sm' not found. "
                "Please install it with: python -m spacy download en_core_web_sm"
            )
        
        # Financial entity keywords for context expansion
        self.sector_keywords = {
            "banking", "technology", "pharma", "pharmaceutical", 
            "auto", "automobile", "finance", "insurance", "it", "tech"
        }
        self.regulator_keywords = {
            "rbi", "sebi", "reserve bank", "securities board"
        }
    
    def index_articles(self, articles: List[Dict[str, Any]]):
        """
        Index articles into ChromaDB with embeddings and metadata.
        
        Args:
            articles: List of enriched articles with entities
        """
        if not articles:
            return
        
        # Prepare data for ChromaDB
        ids = []
        embeddings = []
        documents = []
        metadatas = []
        
        for article in articles:
            # Extract text and generate embedding
            text = article.get("text", "")
            embedding = self.model.encode(text).tolist()
            
            # Extract entities for metadata
            entities = article.get("entities", {})
            metadata = {
                "companies": ",".join(entities.get("companies", [])),
                "sectors": ",".join(entities.get("sectors", [])),
                "regulators": ",".join(entities.get("regulators", [])),
                "events": ",".join(entities.get("events", []))
            }
            
            ids.append(str(article["id"]))
            embeddings.append(embedding)
            documents.append(text)
            metadatas.append(metadata)
        
        # Add to ChromaDB collection
        self.collection.add(
            ids=ids,
            embeddings=embeddings,
            documents=documents,
            metadatas=metadatas
        )
    
    def extract_query_intent(self, query_text: str) -> Dict[str, List[str]]:
        """
        Extract entities and intent from the query using NER.
        
        Args:
            query_text: Natural language query
            
        Returns:
            Dict with extracted companies, sectors, and regulators
        """
        doc = self.nlp(query_text)
        query_lower = query_text.lower()
        
        intent = {
            "companies": [],
            "sectors": [],
            "regulators": []
        }
        
        # Extract organizations (potential companies)
        for ent in doc.ents:
            if ent.label_ == "ORG":
                # Check if it's a regulator
                if any(reg in ent.text.lower() for reg in self.regulator_keywords):
                    intent["regulators"].append(ent.text)
                else:
                    intent["companies"].append(ent.text)
        
        # Extract sector mentions from query
        for sector in self.sector_keywords:
            if sector in query_lower:
                intent["sectors"].append(sector.title())
        
        # Check for regulator keywords
        for regulator in self.regulator_keywords:
            if regulator in query_lower:
                intent["regulators"].append(regulator.upper())
        
        # Deduplicate
        for key in intent:
            intent[key] = list(set(intent[key]))
        
        return intent
    
    def query(self, text: str, n_results: int = 10) -> Dict[str, Any]:
        """
        Query the indexed articles using semantic search and context expansion.
        
        Args:
            text: Natural language query
            n_results: Maximum number of results to return
            
        Returns:
            Dict with query, matched entities, and ranked results
        """
        # Extract intent from query
        matched_entities = self.extract_query_intent(text)
        
        # Generate query embedding for semantic search
        query_embedding = self.model.encode(text).tolist()
        
        # Perform semantic search
        try:
            search_results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=n_results * 2  # Get more to filter and rank
            )
        except Exception:
            # Handle case where collection is empty
            return {
                "query": text,
                "matched_entities": matched_entities,
                "results": []
            }
        
        # Process and rank results
        results = []
        seen_ids = set()
        
        if search_results['ids'] and len(search_results['ids'][0]) > 0:
            for idx, doc_id in enumerate(search_results['ids'][0]):
                if doc_id in seen_ids:
                    continue
                
                seen_ids.add(doc_id)
                
                # Calculate relevance score
                distance = search_results['distances'][0][idx] if 'distances' in search_results else 0
                # Convert distance to similarity score (lower distance = higher similarity)
                score = 1.0 / (1.0 + distance)
                
                # Get metadata
                metadata = search_results['metadatas'][0][idx]
                document = search_results['documents'][0][idx]
                
                # Context expansion: boost score if matches query intent
                boost = 0.0
                
                # Check company matches
                if matched_entities["companies"]:
                    companies_in_doc = metadata.get("companies", "").split(",")
                    for company in matched_entities["companies"]:
                        if any(company.lower() in doc_comp.lower() for doc_comp in companies_in_doc if doc_comp):
                            boost += 0.2
                
                # Check sector matches
                if matched_entities["sectors"]:
                    sectors_in_doc = metadata.get("sectors", "").split(",")
                    for sector in matched_entities["sectors"]:
                        if any(sector.lower() in doc_sect.lower() for doc_sect in sectors_in_doc if doc_sect):
                            boost += 0.15
                
                # Check regulator matches
                if matched_entities["regulators"]:
                    regulators_in_doc = metadata.get("regulators", "").split(",")
                    for regulator in matched_entities["regulators"]:
                        if any(regulator.lower() in doc_reg.lower() for doc_reg in regulators_in_doc if doc_reg):
                            boost += 0.25
                
                # Apply boost (cap at 1.0)
                final_score = min(score + boost, 1.0)
                
                # Parse entities from metadata
                entities = {
                    "companies": [c for c in metadata.get("companies", "").split(",") if c],
                    "sectors": [s for s in metadata.get("sectors", "").split(",") if s],
                    "regulators": [r for r in metadata.get("regulators", "").split(",") if r],
                    "events": [e for e in metadata.get("events", "").split(",") if e]
                }
                
                results.append({
                    "id": int(doc_id),
                    "text": document,
                    "entities": entities,
                    "score": round(final_score, 3)
                })
        
        # Sort by score (descending) and limit results
        results.sort(key=lambda x: x["score"], reverse=True)
        results = results[:n_results]
        
        return {
            "query": text,
            "matched_entities": matched_entities,
            "results": results
        }
