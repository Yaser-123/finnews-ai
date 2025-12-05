import spacy
import json
import os
from pathlib import Path


class EntityAgent:
    def __init__(self, model_name="en_core_web_sm", stock_map_path=None):
        """
        Initialize the EntityAgent with spaCy NER and stock mapping.
        
        Args:
            model_name: spaCy model to use for NER
            stock_map_path: Path to stock symbol mapping JSON file
        """
        try:
            self.nlp = spacy.load(model_name)
        except OSError:
            raise Exception(
                f"spaCy model '{model_name}' not found. "
                f"Please install it with: python -m spacy download {model_name}"
            )
        
        # Load stock mapping
        if stock_map_path is None:
            # Default path relative to this file
            base_dir = Path(__file__).parent.parent.parent
            stock_map_path = base_dir / "models" / "stock_map.json"
        
        self.stock_map = {}
        if os.path.exists(stock_map_path):
            with open(stock_map_path, 'r') as f:
                self.stock_map = json.load(f)
        
        # Financial entity classification rules
        self.regulators = {"RBI", "SEBI", "Reserve Bank of India", "Securities and Exchange Board"}
        self.sectors = {"banking", "technology", "pharma", "auto", "finance", "insurance"}
        self.event_keywords = {"dividend", "merger", "acquisition", "IPO", "earnings", "profit", "loss"}
        
        # Company-to-sector mapping for major Indian companies
        self.company_sectors = {
            "hdfc": "Banking",
            "icici": "Banking",
            "sbi": "Banking",
            "axis": "Banking",
            "kotak": "Banking",
            "indusind": "Banking",
            "tcs": "Technology",
            "infosys": "Technology",
            "wipro": "Technology",
            "hcl": "Technology",
            "tech mahindra": "Technology",
            "reliance": "Finance",
            "adani": "Finance",
            "tata": "Auto",
            "mahindra": "Auto",
            "maruti": "Auto",
            "bajaj": "Auto",
            "dr reddy": "Pharma",
            "sun pharma": "Pharma",
            "cipla": "Pharma",
            "lupin": "Pharma",
            "divi": "Pharma"
        }
    
    def extract_entities(self, text):
        """
        Extract named entities from text using spaCy.
        
        Returns:
            dict with entity types and their values
        """
        doc = self.nlp(text)
        
        entities = {
            "companies": [],
            "persons": [],
            "locations": [],
            "money": [],
            "dates": [],
            "regulators": [],
            "sectors": [],
            "events": []
        }
        
        # Extract standard NER entities
        for ent in doc.ents:
            if ent.label_ == "ORG":
                # Check if it's a regulator
                if any(reg.lower() in ent.text.lower() for reg in self.regulators):
                    entities["regulators"].append(ent.text)
                else:
                    entities["companies"].append(ent.text)
            elif ent.label_ == "PERSON":
                entities["persons"].append(ent.text)
            elif ent.label_ == "GPE":
                entities["locations"].append(ent.text)
            elif ent.label_ == "MONEY":
                entities["money"].append(ent.text)
            elif ent.label_ == "DATE":
                entities["dates"].append(ent.text)
        
        # Extract sector mentions
        text_lower = text.lower()
        for sector in self.sectors:
            if sector in text_lower:
                entities["sectors"].append(sector.title())
        
        # Infer sectors from company names
        for company in entities["companies"]:
            company_lower = company.lower()
            for keyword, sector in self.company_sectors.items():
                if keyword in company_lower:
                    entities["sectors"].append(sector)
                    break  # Only add one sector per company
        
        # Extract event keywords
        for event in self.event_keywords:
            if event.lower() in text_lower:
                entities["events"].append(event.title())
        
        # Deduplicate lists
        for key in entities:
            entities[key] = list(set(entities[key]))
        
        return entities
    
    def map_to_stocks(self, entities):
        """
        Map extracted entities to stock symbols with confidence scores.
        
        Returns:
            list of dicts with symbol, confidence, and type
        """
        impacted_stocks = []
        
        # Direct company mentions
        for company in entities["companies"]:
            if company in self.stock_map:
                impacted_stocks.append({
                    "symbol": self.stock_map[company],
                    "confidence": 1.0,
                    "type": "direct",
                    "entity": company
                })
        
        # Regulator actions (affects market broadly)
        for regulator in entities["regulators"]:
            if regulator in self.stock_map:
                impacted_stocks.append({
                    "symbol": self.stock_map[regulator],
                    "confidence": 0.8,
                    "type": "regulator",
                    "entity": regulator
                })
        
        # Sector mentions (lower confidence)
        for sector in entities["sectors"]:
            sector_key = f"{sector} Sector"
            if sector_key in self.stock_map:
                impacted_stocks.append({
                    "symbol": self.stock_map[sector_key],
                    "confidence": 0.6,
                    "type": "sector",
                    "entity": sector
                })
        
        return impacted_stocks
    
    def run(self, articles):
        """
        Enrich articles with extracted entities and stock mappings.
        
        Args:
            articles: List of dicts with 'id' and 'text' keys
            
        Returns:
            List of enriched articles with entities and impacted_stocks
        """
        enriched_articles = []
        
        for article in articles:
            # Create a copy to avoid mutating original
            enriched = article.copy()
            
            # Extract entities
            entities = self.extract_entities(article["text"])
            enriched["entities"] = entities
            
            # Map to stock symbols
            impacted_stocks = self.map_to_stocks(entities)
            enriched["impacted_stocks"] = impacted_stocks
            
            enriched_articles.append(enriched)
        
        return enriched_articles
