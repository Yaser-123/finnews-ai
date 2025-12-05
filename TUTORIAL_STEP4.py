"""
STEP 4: COMPLETE SYSTEM ARCHITECTURE & USAGE GUIDE
===================================================

This tutorial covers the entire FinNews AI system architecture,
data flow, and how to use all components.
"""

print("""
╔══════════════════════════════════════════════════════════════════════╗
║                                                                      ║
║                   FINNEWS AI - STEP 4 TUTORIAL                       ║
║              SYSTEM ARCHITECTURE & COMPLETE GUIDE                    ║
║                                                                      ║
╚══════════════════════════════════════════════════════════════════════╝

┌──────────────────────────────────────────────────────────────────────┐
│                      📚 TABLE OF CONTENTS                            │
├──────────────────────────────────────────────────────────────────────┤
│  Part A: System Architecture Overview                               │
│  Part B: Data Flow (Ingestion → Query)                              │
│  Part C: Multi-Agent Pipeline                                       │
│  Part D: Query & Search System                                      │
│  Part E: API Endpoints Usage                                        │
│  Part F: Database Schema Deep Dive                                  │
│  Part G: Production Deployment Tips                                 │
└──────────────────────────────────────────────────────────────────────┘


═══════════════════════════════════════════════════════════════════════
PART A: SYSTEM ARCHITECTURE OVERVIEW
═══════════════════════════════════════════════════════════════════════

🏗️  HIGH-LEVEL ARCHITECTURE:

   ┌─────────────┐
   │  RSS Feeds  │  (Economic Times, LiveMint, Google News, etc.)
   └──────┬──────┘
          │
          ▼
   ┌─────────────────────┐
   │  Ingestion Agent    │  • Fetch RSS feeds
   │  (ingest/realtime)  │  • Parse & normalize
   └──────┬──────────────┘  • Generate hash
          │
          ▼
   ┌─────────────────────┐
   │  PostgreSQL DB      │  • Store raw articles
   │  (Neon Cloud)       │  • Auto-increment IDs
   └──────┬──────────────┘  • Hash-based dedup
          │
          ▼
   ┌─────────────────────┐
   │  Processing Pipeline│
   │  (api/routes)       │
   ├─────────────────────┤
   │  1. Entity Agent    │  → Extract companies, sectors, regulators, events
   │  2. Sentiment Agent │  → Analyze sentiment (FinBERT)
   │  3. Embedding Model │  → Generate 768-dim vectors
   │  4. ChromaDB Index  │  → Store for semantic search
   └──────┬──────────────┘
          │
          ▼
   ┌─────────────────────┐
   │  Query Agent        │  • Semantic search
   │  (agents/query)     │  • Entity matching
   └──────┬──────────────┘  • Result ranking
          │
          ▼
   ┌─────────────────────┐
   │  FastAPI Server     │  • REST endpoints
   │  (main.py)          │  • Auto docs (Swagger)
   └─────────────────────┘


═══════════════════════════════════════════════════════════════════════
PART B: DATA FLOW (End-to-End Journey)
═══════════════════════════════════════════════════════════════════════

📰 STEP-BY-STEP DATA FLOW:

1️⃣  RSS INGESTION
   ─────────────────
   File: ingest/realtime.py
   
   • fetch_all() fetches from 12 RSS feeds concurrently
   • normalize_entry() extracts:
     - Title & content
     - Source URL
     - Published timestamp
     - GUID
   • compute_hash() generates MD5 for deduplication
   • Returns list of normalized articles
   
   Example article dict:
   {
       "title": "HDFC Bank announces dividend",
       "text": "HDFC Bank announces 15% dividend payout...",
       "source": "https://economictimes.indiatimes.com/...",
       "published_at": datetime(2025, 12, 5, 10, 30),
       "guid": "https://...",
       "hash": "a8f523e792be1a2b932c..."
   }

2️⃣  DATABASE STORAGE
   ──────────────────
   File: database/db.py → save_articles()
   
   • Batch insert (50 articles at a time)
   • ON CONFLICT(hash) DO NOTHING → Skip duplicates
   • PostgreSQL auto-generates sequential IDs (1, 2, 3...)
   • Stored in 'articles' table with metadata
   
   Articles table schema:
   ┌────────────────┬──────────────┬──────────┐
   │ Column         │ Type         │ Notes    │
   ├────────────────┼──────────────┼──────────┤
   │ id             │ BIGINT       │ Primary  │
   │ text           │ TEXT         │ Required │
   │ source         │ TEXT         │ URL      │
   │ published_at   │ TIMESTAMP    │          │
   │ created_at     │ TIMESTAMP    │ Auto     │
   │ hash           │ VARCHAR      │ Unique   │
   └────────────────┴──────────────┴──────────┘

3️⃣  ENTITY EXTRACTION
   ───────────────────
   File: agents/entity/agent.py
   
   • Uses spaCy NER (en_core_web_sm) for AI extraction
   • Keyword matching for financial terms
   • Company-to-sector inference (22 major Indian companies)
   
   Extraction process:
   a) spaCy finds PERSON, ORG, GPE entities
   b) Filter to financial entities only
   c) Match against sector keywords
   d) Infer sectors from company names
   e) Detect events (dividend, merger, IPO, etc.)
   f) Deduplicate results
   
   Example output:
   {
       "companies": ["HDFC Bank", "State Bank of India"],
       "sectors": ["Banking", "Finance"],
       "regulators": ["RBI", "SEBI"],
       "events": ["Dividend", "Profit"]
   }

4️⃣  SENTIMENT ANALYSIS
   ────────────────────
   File: agents/sentiment/agent.py
   
   • Uses FinBERT (ProsusAI/finbert)
   • Financial domain-specific sentiment
   • Returns: positive/negative/neutral + confidence
   
   Example output:
   {
       "label": "positive",
       "score": 0.89
   }

5️⃣  EMBEDDING GENERATION
   ──────────────────────
   Model: sentence-transformers/all-mpnet-base-v2
   
   • Converts text → 768-dimensional vector
   • Captures semantic meaning
   • Used for similarity search
   
   text → [0.023, -0.145, 0.892, ..., 0.123] (768 dims)

6️⃣  CHROMADB INDEXING
   ───────────────────
   File: vector_store/chroma_db.py
   
   • Stores embeddings for fast similarity search
   • Metadata includes entities & sentiment
   • Collection name: "finnews_articles"
   
   Indexed data:
   {
       "id": "35",
       "embedding": [768 floats],
       "document": "HDFC Bank announces...",
       "metadata": {
           "article_id": 35,
           "companies": "['HDFC Bank']",
           "sectors": "['Banking']",
           "sentiment": "positive",
           "sentiment_score": 0.89
       }
   }

7️⃣  QUERY & SEARCH
   ───────────────
   File: agents/query/agent.py
   
   • Query embedding → ChromaDB similarity search
   • Extract entities from query
   • Boost scores for entity matches
   • Return ranked results
   
   Query: "HDFC Bank news"
   → Embedding search in ChromaDB
   → Filter/boost by company="HDFC Bank"
   → Return top 5 results with scores


═══════════════════════════════════════════════════════════════════════
PART C: MULTI-AGENT PIPELINE
═══════════════════════════════════════════════════════════════════════

🤖 THE 4 INTELLIGENT AGENTS:

┌──────────────────────────────────────────────────────────────┐
│ 1. ENTITY EXTRACTION AGENT                                   │
├──────────────────────────────────────────────────────────────┤
│ File: agents/entity/agent.py                                 │
│ Model: spaCy en_core_web_sm                                  │
│                                                              │
│ Extracts:                                                    │
│  • Companies: HDFC Bank, TCS, Infosys, etc.                 │
│  • Sectors: Banking, Technology, Finance, etc.              │
│  • Regulators: RBI, SEBI, etc.                              │
│  • Events: Dividend, Merger, IPO, Profit, etc.              │
│                                                              │
│ Special features:                                            │
│  • Sector inference from company names                       │
│  • Financial keyword matching                                │
│  • Deduplication & normalization                            │
└──────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────┐
│ 2. SENTIMENT ANALYSIS AGENT                                  │
├──────────────────────────────────────────────────────────────┤
│ File: agents/sentiment/agent.py                              │
│ Model: FinBERT (ProsusAI/finbert)                           │
│                                                              │
│ Analyzes:                                                    │
│  • Financial sentiment (not generic sentiment)               │
│  • Returns: positive / negative / neutral                    │
│  • Confidence score: 0.0 to 1.0                             │
│                                                              │
│ Use cases:                                                   │
│  • Filter positive news only                                 │
│  • Track negative sentiment trends                           │
│  • Risk assessment                                           │
└──────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────┐
│ 3. DEDUPLICATION AGENT                                       │
├──────────────────────────────────────────────────────────────┤
│ File: agents/dedup/agent.py                                  │
│ Model: Sentence Transformers (all-mpnet-base-v2)            │
│                                                              │
│ Features:                                                    │
│  • Semantic similarity (not just text matching)              │
│  • Cosine similarity threshold: 0.80                         │
│  • Clusters similar articles                                 │
│  • Returns unique articles + cluster info                    │
│                                                              │
│ Why needed:                                                  │
│  • Same story from multiple sources                          │
│  • Slightly different wording                                │
│  • Reduces noise in results                                  │
└──────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────┐
│ 4. QUERY AGENT                                               │
├──────────────────────────────────────────────────────────────┤
│ File: agents/query/agent.py                                  │
│ Model: Sentence Transformers + ChromaDB                      │
│                                                              │
│ Search flow:                                                 │
│  1. Convert query to embedding                               │
│  2. Semantic search in ChromaDB                              │
│  3. Extract entities from query                              │
│  4. Boost scores for entity matches                          │
│  5. Rank and return results                                  │
│                                                              │
│ Smart features:                                              │
│  • "HDFC" matches "HDFC Bank" articles                       │
│  • "banking" finds all bank-related news                     │
│  • Hybrid: semantic + entity matching                        │
└──────────────────────────────────────────────────────────────┘


═══════════════════════════════════════════════════════════════════════
PART D: QUERY & SEARCH SYSTEM
═══════════════════════════════════════════════════════════════════════

🔍 HOW SEARCH WORKS:

Example Query: "RBI monetary policy"

Step 1: Entity Detection
────────────────────────
Query text → EntityAgent.extract_entities()
Result: {"regulators": ["RBI"]}

Step 2: Embedding Generation
─────────────────────────────
Query text → SentenceTransformer.encode()
Result: 768-dim vector

Step 3: Semantic Search
───────────────────────
Vector → ChromaDB.query(embedding, top_k=10)
Returns: Top 10 similar articles by cosine similarity

Step 4: Entity Boosting
───────────────────────
For each result:
  - If article has matching entities → Boost score by 0.3
  - If article mentions RBI → Higher relevance

Step 5: Ranking
───────────────
Sort by final score (similarity + entity boost)
Return top 5 results

Result format:
[
    {
        "id": 16,
        "text": "RBI monetary policy committee...",
        "entities": {"regulators": ["RBI"]},
        "sentiment": {"label": "neutral", "score": 0.75},
        "score": 0.909  # Very high match!
    },
    ...
]


═══════════════════════════════════════════════════════════════════════
PART E: API ENDPOINTS USAGE
═══════════════════════════════════════════════════════════════════════

🌐 FASTAPI SERVER (http://127.0.0.1:8000)

1. PIPELINE RUN (Process Articles)
   ════════════════════════════════
   POST /pipeline/run
   
   Body: {} (optional: limit number of articles)
   
   Response:
   {
       "status": "ok",
       "total_input": 20,
       "unique_count": 19,
       "indexed_count": 19,
       "clusters": [...]
   }
   
   PowerShell example:
   Invoke-RestMethod -Uri "http://127.0.0.1:8000/pipeline/run" \\
     -Method POST -Body '{}' -ContentType "application/json"

2. QUERY SEARCH
   ═════════════
   POST /pipeline/query
   
   Body: {"query": "HDFC Bank news"}
   
   Response:
   {
       "query": "HDFC Bank news",
       "matched_entities": {
           "companies": ["HDFC Bank"],
           "sectors": [],
           "regulators": []
       },
       "results": [
           {
               "id": 1,
               "text": "HDFC Bank announces...",
               "entities": {...},
               "sentiment": {...},
               "score": 0.89
           }
       ]
   }
   
   PowerShell example:
   Invoke-RestMethod -Uri "http://127.0.0.1:8000/pipeline/query" \\
     -Method POST \\
     -Body '{"query":"HDFC Bank news"}' \\
     -ContentType "application/json"

3. INTERACTIVE API DOCS
   ═════════════════════
   GET /docs  → Swagger UI (interactive testing)
   GET /redoc → ReDoc (beautiful documentation)
   
   Visit: http://127.0.0.1:8000/docs


═══════════════════════════════════════════════════════════════════════
PART F: DATABASE SCHEMA DEEP DIVE
═══════════════════════════════════════════════════════════════════════

📊 COMPLETE SCHEMA:

┌─────────────────────────────────────────────────────────────────┐
│ TABLE: articles                                                 │
├─────────────────┬───────────────┬───────────────────────────────┤
│ id              │ BIGINT        │ Auto-increment, PRIMARY KEY   │
│ text            │ TEXT          │ Article content               │
│ source          │ TEXT          │ RSS feed URL                  │
│ published_at    │ TIMESTAMP     │ From RSS feed                 │
│ created_at      │ TIMESTAMP     │ Ingestion time                │
│ hash            │ VARCHAR       │ MD5, UNIQUE constraint        │
└─────────────────┴───────────────┴───────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│ TABLE: entities                                                 │
├─────────────────┬───────────────┬───────────────────────────────┤
│ id              │ INTEGER       │ Auto-increment, PRIMARY KEY   │
│ article_id      │ INTEGER       │ Foreign key to articles       │
│ companies       │ TEXT[]        │ Array of company names        │
│ sectors         │ TEXT[]        │ Array of sector names         │
│ regulators      │ TEXT[]        │ Array of regulator names      │
│ people          │ TEXT[]        │ Array of people names         │
│ events          │ TEXT[]        │ Array of event types          │
│ stocks          │ JSON          │ Stock symbols with metadata   │
│ created_at      │ TIMESTAMP     │ Extraction time               │
└─────────────────┴───────────────┴───────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│ TABLE: sentiment                                                │
├─────────────────┬───────────────┬───────────────────────────────┤
│ id              │ INTEGER       │ Auto-increment, PRIMARY KEY   │
│ article_id      │ INTEGER       │ Foreign key to articles       │
│ label           │ TEXT          │ positive/negative/neutral     │
│ score           │ FLOAT         │ Confidence 0.0-1.0            │
│ created_at      │ TIMESTAMP     │ Analysis time                 │
└─────────────────┴───────────────┴───────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│ TABLE: dedup_clusters                                           │
├─────────────────┬───────────────┬───────────────────────────────┤
│ id              │ INTEGER       │ Auto-increment, PRIMARY KEY   │
│ article_id      │ INTEGER       │ Foreign key to articles       │
│ cluster_main_id │ INTEGER       │ Main article in cluster       │
│ merged_ids      │ INTEGER[]     │ Array of similar article IDs  │
│ similarity_score│ FLOAT         │ Cosine similarity             │
│ created_at      │ TIMESTAMP     │ Dedup time                    │
└─────────────────┴───────────────┴───────────────────────────────┘

RELATIONSHIPS:
articles (1) ←→ (1) entities     [One-to-one]
articles (1) ←→ (1) sentiment    [One-to-one]
articles (1) ←→ (many) dedup_clusters [One-to-many]


═══════════════════════════════════════════════════════════════════════
PART G: PRODUCTION DEPLOYMENT TIPS
═══════════════════════════════════════════════════════════════════════

🚀 READY FOR PRODUCTION:

1. Environment Variables
   ═════════════════════
   Required in .env:
   • DATABASE_URL          → Neon PostgreSQL URL
   • GEMINI_API_KEY        → For LLM operations
   • RSS_FEEDS (optional)  → Custom feed URLs
   
2. Server Configuration
   ═══════════════════════
   # Development
   uvicorn main:app --reload --port 8000
   
   # Production
   uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4

3. Database Optimization
   ═════════════════════════
   • Create indexes on article_id columns
   • Vacuum regularly for performance
   • Monitor connection pool size

4. Caching Strategy
   ═══════════════════
   • Cache entity extraction results
   • Cache embedding computations
   • Use Redis for query result caching

5. Monitoring & Alerts
   ═══════════════════════
   • Track RSS feed fetch success rate
   • Monitor database write speeds
   • Alert on pipeline failures
   • Track ChromaDB index size

6. Scaling Considerations
   ═══════════════════════════
   • Horizontal: Multiple API servers
   • Vertical: Increase Neon database tier
   • ChromaDB: Consider hosted Chroma Cloud
   • Queue: Add Celery for background processing


═══════════════════════════════════════════════════════════════════════
                            🎓 TUTORIAL COMPLETE!
═══════════════════════════════════════════════════════════════════════

You now understand:
✅ System architecture (7 layers)
✅ Data flow from RSS → Query
✅ 4 AI agents and their roles
✅ Query & search mechanics
✅ API endpoints usage
✅ Database schema design
✅ Production deployment

📝 NEXT STEPS:
1. Explore code in each agent folder
2. Customize entity extraction keywords
3. Add more RSS feeds
4. Build a React/Vue frontend dashboard
5. Add WebSocket for real-time alerts

═══════════════════════════════════════════════════════════════════════
""")
