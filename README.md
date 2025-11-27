# 🚀 FinNews AI

### Multi-Agent Financial News Intelligence System

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.122.0-009688.svg?logo=fastapi)](https://fastapi.tiangolo.com)
[![HuggingFace](https://img.shields.io/badge/🤗-Transformers-yellow.svg)](https://huggingface.co)
[![ChromaDB](https://img.shields.io/badge/ChromaDB-Vector%20DB-orange.svg)](https://www.trychroma.com)
[![LangGraph](https://img.shields.io/badge/LangGraph-Pipeline-purple.svg)](https://github.com/langchain-ai/langgraph)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

---

## 🎯 Elevator Pitch

**FinNews AI** is an intelligent multi-agent system that transforms raw financial news into actionable insights. By orchestrating specialized AI agents through a sophisticated pipeline, it automatically deduplicates articles, extracts financial entities, analyzes sentiment, and enables semantic search—all through a single API call. Built for investors, analysts, and financial institutions who need to cut through the noise and identify market-moving information instantly.

---

## ✨ Key Features

🔄 **Multi-Agent Architecture** — Four specialized agents working in concert  
🎯 **Semantic Deduplication** — MPNet embeddings eliminate redundant news  
🏢 **Entity Intelligence** — Extracts companies, sectors, regulators with stock mapping  
📊 **Financial Sentiment** — FinBERT-powered sentiment analysis (positive/negative/neutral)  
🔍 **Context-Aware Search** — Hybrid semantic + metadata query engine  
⚡ **Production-Ready API** — FastAPI backend with full pipeline automation  
🧪 **Comprehensive Testing** — Test suite for every component  
📦 **Modular Design** — Clean, extensible, and maintainable codebase

---

## 🏗️ System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         FinNews AI Pipeline                      │
└─────────────────────────────────────────────────────────────────┘

    📥 Input: Raw Financial News Articles (20+ sources)
                            │
                            ▼
    ┌───────────────────────────────────────────┐
    │   Agent 1: DeduplicationAgent             │
    │   • MPNet embeddings (all-mpnet-base-v2)  │
    │   • Cosine similarity clustering          │
    │   • Threshold: 0.80                       │
    └───────────────┬───────────────────────────┘
                    │ Unique Articles
                    ▼
    ┌───────────────────────────────────────────┐
    │   Agent 2: EntityAgent                    │
    │   • spaCy NER (en_core_web_sm)            │
    │   • Financial entity classification       │
    │   • Stock symbol mapping                  │
    │   • Confidence scoring                    │
    └───────────────┬───────────────────────────┘
                    │ Enriched Articles
                    ▼
    ┌───────────────────────────────────────────┐
    │   Agent 3: SentimentAgent                 │
    │   • FinBERT (ProsusAI/finbert)            │
    │   • Financial domain-specific             │
    │   • 3-class: positive/negative/neutral    │
    └───────────────┬───────────────────────────┘
                    │ Sentiment-Annotated Articles
                    ▼
    ┌───────────────────────────────────────────┐
    │   Agent 4: QueryAgent                     │
    │   • ChromaDB vector storage               │
    │   • Semantic + metadata search            │
    │   • Context expansion                     │
    │   • Relevance ranking                     │
    └───────────────┬───────────────────────────┘
                    │
                    ▼
    📤 Output: Searchable, Sentiment-Analyzed, 
              Entity-Enriched Financial Intelligence
```

---

## 🤖 Agent Breakdown

### 1️⃣ **DeduplicationAgent**
Eliminates redundant articles using semantic similarity.

**Technology:** Sentence-Transformers (MPNet)  
**Method:** Cosine similarity clustering with configurable threshold  
**Output:** Unique articles + merge clusters

```python
# Example: 2 duplicate RBI articles → 1 cluster
Input:  ["RBI hikes repo rate by 25 bps", "Reserve Bank increases rate by 25 basis points"]
Output: 1 unique article + cluster info
```

### 2️⃣ **EntityAgent**
Extracts and classifies financial entities with stock impact scoring.

**Technology:** spaCy NER + Rule-based classification  
**Entities:** Companies, Sectors, Regulators, Events  
**Stock Mapping:** Direct (1.0) → Regulator (0.8) → Sector (0.6)

```python
# Example output
{
  "companies": ["HDFC Bank"],
  "sectors": ["Banking"],
  "regulators": ["RBI"],
  "impacted_stocks": [
    {"symbol": "HDFCBANK", "confidence": 1.0, "type": "direct"}
  ]
}
```

### 3️⃣ **SentimentAgent**
Analyzes financial sentiment using domain-specific models.

**Technology:** FinBERT (ProsusAI/finbert)  
**Classes:** Positive, Negative, Neutral  
**Confidence:** 0.0 - 1.0

```python
# Example output
{
  "sentiment": {
    "label": "positive",
    "score": 0.9566
  }
}
```

### 4️⃣ **QueryAgent**
Enables natural language search with context-aware ranking.

**Technology:** ChromaDB + Sentence-Transformers  
**Features:** 
- Semantic similarity search
- Entity-based filtering
- Confidence boosting
- Hybrid ranking

```python
# Example query
"HDFC Bank news" → Finds all HDFC articles + related banking sector news
```

---

## 📡 API Documentation

### Base URL
```
http://localhost:8000
```

### Endpoints

#### 1. Health Check
```http
GET /health
```

**Response:**
```json
{
  "status": "ok",
  "service": "finnews-ai",
  "version": "0.1"
}
```

---

#### 2. Run Full Pipeline
```http
POST /pipeline/run
```

Executes the complete multi-agent pipeline: ingestion → dedup → entity → sentiment → indexing.

**Response:**
```json
{
  "status": "ok",
  "total_input": 20,
  "unique_count": 18,
  "clusters_count": 18,
  "indexed_count": 18,
  "clusters": [
    {"main_id": 1, "merged_ids": [1, 2]},
    {"main_id": 3, "merged_ids": [3]}
  ],
  "timestamp": "2025-11-27T12:34:56.789Z"
}
```

---

#### 3. Pipeline Status
```http
GET /pipeline/status
```

Returns the status of the last pipeline execution.

**Response:**
```json
{
  "status": "completed",
  "total_input": 20,
  "unique_count": 18,
  "indexed_count": 18,
  "timestamp": "2025-11-27T12:34:56.789Z"
}
```

---

#### 4. Query Articles
```http
POST /pipeline/query
```

**Request Body:**
```json
{
  "query": "HDFC Bank news",
  "top_k": 5
}
```

**Response:**
```json
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
      "text": "HDFC Bank reports strong quarterly results...",
      "entities": {
        "companies": ["HDFC Bank"],
        "sectors": ["Banking"],
        "events": ["Profit"]
      },
      "sentiment": {
        "label": "positive",
        "score": 0.9566
      },
      "score": 0.943
    }
  ]
}
```

---

## 🛠️ Tech Stack

| Component | Technology |
|-----------|-----------|
| **Backend** | FastAPI, Uvicorn |
| **Orchestration** | LangGraph (pipeline framework) |
| **Embeddings** | Sentence-Transformers (MPNet) |
| **NER** | spaCy (en_core_web_sm) |
| **Sentiment** | FinBERT (ProsusAI/finbert) |
| **Vector DB** | ChromaDB |
| **Deep Learning** | PyTorch, Transformers |
| **Language** | Python 3.8+ |

---

## 📦 Installation

### Prerequisites
- Python 3.8 or higher
- pip

### Steps

1. **Clone the repository**
   ```bash
   git clone https://github.com/Yaser-123/finnews-ai.git
   cd finnews-ai
   ```

2. **Create virtual environment**
   ```bash
   python -m venv .venv
   
   # Windows
   .\.venv\Scripts\Activate.ps1
   
   # Linux/Mac
   source .venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Download spaCy model**
   ```bash
   python -m spacy download en_core_web_sm
   ```

5. **Configure environment variables**
   ```bash
   # Copy the example env file
   cp .env.example .env
   
   # Edit .env and add your credentials:
   # - DATABASE_URL: Your Neon PostgreSQL connection string
   # - GEMINI_API_KEY: Your Google Gemini API key
   ```

---

## 🗄️ Database Setup (PostgreSQL + Neon)

FinNews AI uses **PostgreSQL** (hosted on [Neon](https://neon.tech)) for persistent storage of articles, entities, sentiment, and query logs.

### 1. Create a Neon Database

1. Sign up at [neon.tech](https://neon.tech)
2. Create a new project
3. Copy your connection string (it will look like):
   ```
   postgresql://username:password@ep-xxx.region.aws.neon.tech/neondb?sslmode=require
   ```

### 2. Configure Database URL

Add your connection string to `.env`:
```bash
DATABASE_URL="postgresql://your-neon-connection-string-here"
```

### 3. Initialize Database

The database tables are created automatically on first run:
```bash
uvicorn main:app --reload
```

### 4. Run Database Tests (Optional)

Test your database connection:
```bash
python demo/test_db.py
```

### 5. Database Schema

The following tables are created automatically:

- **articles** - Raw financial news articles
- **dedup_clusters** - Deduplication results with cluster info
- **entities** - Extracted companies, sectors, regulators, stocks
- **sentiment** - Sentiment analysis results (positive/negative/neutral)
- **query_logs** - Query history with LLM expansion and result counts

### 6. Database Migrations (Advanced)

To create and apply custom migrations:

```bash
# Generate a new migration
alembic revision --autogenerate -m "your migration message"

# Apply migrations
alembic upgrade head

# Rollback last migration
alembic downgrade -1
```

---

## 🚀 Quick Start

### 1. Start the API Server
```bash
uvicorn main:app --reload
```

Server will start at `http://127.0.0.1:8000`

### 2. Access Interactive API Docs
Open your browser: `http://127.0.0.1:8000/docs`

### 3. Run the Pipeline
```bash
# In a new terminal
python demo/test_pipeline.py
```

---

## 🧪 Running Tests

### Test Individual Agents
```bash
# Test deduplication
python demo/test_dedup.py

# Test entity extraction
python demo/test_entity.py

# Test sentiment analysis
python demo/test_sentiment.py

# Test query engine
python demo/test_query.py
```

### Test Full Pipeline
```bash
# Make sure API server is running first
python demo/test_pipeline.py
```

**Expected Output:**
```
✅ Pipeline execution: PASSED
✅ Status check: PASSED
✅ Queries tested: 4
   - HDFC Bank news
   - banking sector update
   - RBI policy changes
   - interest rate impact
```

---

## 📂 Project Structure

```
finnews-ai/
├── main.py                      # FastAPI application entry point
├── requirements.txt             # Python dependencies
├── .env                         # Environment variables (DATABASE_URL, GEMINI_API_KEY)
├── .gitignore                   # Git ignore rules
├── README.md                    # This file
├── alembic.ini                  # Alembic migration configuration
│
├── api/                         # API layer
│   └── routes/
│       └── pipeline.py          # Pipeline & LangGraph endpoints
│
├── agents/                      # Multi-agent system
│   ├── dedup/
│   │   └── agent.py            # DeduplicationAgent
│   ├── entity/
│   │   └── agent.py            # EntityAgent
│   ├── sentiment/
│   │   └── agent.py            # SentimentAgent
│   ├── query/
│   │   └── agent.py            # QueryAgent
│   └── llm/
│       └── agent.py            # LLMAgent (Google Gemini)
│
├── database/                    # PostgreSQL integration
│   ├── db.py                   # Async database client
│   ├── schema.py               # SQLAlchemy ORM models
│   └── migrations/             # Alembic migration files
│
├── graphs/                      # LangGraph workflows
│   ├── state.py                # Pydantic state models
│   ├── pipeline_graph.py       # 6-node pipeline workflow
│   └── query_graph.py          # 5-node query workflow
│
├── ingest/
│   └── demo_data.py            # 20+ demo financial articles
│
├── models/
│   └── stock_map.json          # Stock symbol mappings
│
└── demo/                        # Test scripts
    ├── test_dedup.py
    ├── test_entity.py
    ├── test_sentiment.py
    ├── test_query.py
    ├── test_llm.py
    ├── test_db.py
    ├── test_pipeline.py
    ├── test_pipeline_graph.py
    └── test_query_graph.py
```

---

## 📊 Example Outputs

### Deduplication Results
```
Input: 10 articles
Unique: 9 articles (1 duplicate cluster found)
Cluster: Main ID 3 merged with [3, 4] (RBI rate hike duplicates)
```

### Entity Extraction
```
Article: "HDFC Bank announces 15% dividend"
Entities:
  - Companies: HDFC Bank
  - Events: Dividend
Impacted Stocks:
  - HDFCBANK (confidence: 1.0, type: direct)
```

### Sentiment Analysis
```
Article: "Banking sector faces severe challenges..."
Sentiment: NEGATIVE (confidence: 0.9609)
```

### Query Results
```
Query: "HDFC Bank news"
Matched Entities: companies=["HDFC Bank"]
Results: 2 articles
  1. ID 2 (score: 0.743) - "HDFC Bank reports strong results"
  2. ID 1 (score: 0.669) - "HDFC Bank announces dividend"
```

---

## 🔗 LangGraph Workflow Integration

FinNews AI uses **LangGraph** to orchestrate multi-agent workflows with state management and visualization.

### 📊 Pipeline Workflow (6 Nodes)

![Pipeline Graph](pipeline_graph.png)

The pipeline workflow executes agents sequentially with full state tracking:

```
START → Ingest → Dedup → Entities → Sentiment → LLM → Index → END
```

**Node Details:**
1. **Ingest** - Load demo articles and save to PostgreSQL
2. **Dedup** - Deduplicate using MPNet embeddings, save clusters
3. **Entities** - Extract financial entities with spaCy NER
4. **Sentiment** - Analyze sentiment with FinBERT, save to DB
5. **LLM** - Generate summaries using Google Gemini (first 5 articles)
6. **Index** - Store articles in ChromaDB for semantic search

**API Endpoint:**
```http
POST /pipeline/run_graph
```

**Response:**
```json
{
  "status": "success",
  "stats": {
    "total_input": 20,
    "unique_count": 19,
    "clusters_count": 19,
    "entities_extracted": 19,
    "sentiment_analyzed": 19,
    "llm_summaries": 5,
    "indexed_count": 19
  },
  "sentiment_distribution": {
    "positive": 12,
    "negative": 3,
    "neutral": 4
  },
  "timestamp": "2025-11-27T12:34:56.789Z"
}
```

---

### 🔍 Query Workflow (5 Nodes)

![Query Graph](query_graph.png)

The query workflow processes user queries with entity extraction and LLM expansion:

```
START → Parse Query → Expand Query → Semantic Search → Rerank → Format Response → END
```

**Node Details:**
1. **Parse Query** - Extract entities (companies/sectors/regulators) using spaCy
2. **Expand Query** - Use Google Gemini to enrich query with financial context
3. **Semantic Search** - Query ChromaDB with expanded text, retrieve top 10
4. **Rerank** - Boost results based on entity matches (company +0.1, regulator +0.15)
5. **Format Response** - Structure output and save query log to PostgreSQL

**API Endpoint:**
```http
POST /query_graph
```

**Request:**
```json
{
  "query": "HDFC Bank dividend announcement"
}
```

**Response:**
```json
{
  "status": "success",
  "query": "HDFC Bank dividend announcement",
  "expanded_query": "Seeking detailed news on HDFC Bank Ltd. (NSE: HDFCBANK) dividend declaration including payout ratio, ex-dividend date, record date, and impact on shareholder returns...",
  "matched_entities": {
    "companies": ["HDFC Bank"],
    "sectors": [],
    "regulators": []
  },
  "results": [
    {
      "id": 1,
      "text": "HDFC Bank announces 15% dividend payout...",
      "rerank_score": 0.843,
      "entities": {
        "companies": ["HDFC Bank"],
        "events": ["Dividend"]
      },
      "sentiment": {
        "label": "positive",
        "score": 0.9525
      }
    }
  ],
  "result_count": 2,
  "timestamp": "2025-11-27T12:35:00.123Z"
}
```

---

### 🧪 Testing LangGraph Workflows

```bash
# Test pipeline workflow
python demo/test_pipeline_graph.py

# Test query workflow
python demo/test_query_graph.py
```

---

## 🔮 Upcoming Enhancements

- [x] **PostgreSQL Integration** — Persistent storage for processed articles ✅
- [x] **LLM Summary Agent** — Generate summaries using Google Gemini ✅
- [x] **LangGraph Pipeline** — Visual workflow orchestration ✅
- [ ] **Real-Time Alerts** — WebSocket notifications for high-impact news
- [ ] **Evaluation Metrics** — Precision, recall, F1 scores for each agent
- [ ] **Multi-Language Support** — Process news in Hindi, Chinese, Spanish
- [ ] **Market Impact Predictor** — ML model for stock price movement prediction
- [ ] **News Source Integration** — RSS feeds, APIs (Bloomberg, Reuters, etc.)
- [ ] **User Authentication** — JWT-based auth for multi-tenant deployment
- [ ] **Dashboard UI** — React/Streamlit frontend for visualization

---

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 👨‍💻 Author

**T Mohamed Yaser**

- 🔗 GitHub: [@Yaser-123](https://github.com/Yaser-123)
- 🔗 Repository: [finnews-ai](https://github.com/Yaser-123/finnews-ai)
- 🔗 LinkedIn: [mohamedyaser08](linkedin.com/in/mohamedyaser08/)

---

## 🙏 Acknowledgments

- **HuggingFace** for pre-trained models (FinBERT, MPNet)
- **Chroma** for vector database technology
- **spaCy** for NLP capabilities
- **FastAPI** for the excellent web framework
- **LangChain/LangGraph** for agent orchestration patterns

---

## 📞 Contact & Support

For questions, suggestions, or collaboration:
- Open an issue on GitHub
- Star ⭐ the repository if you find it useful!

---

<div align="center">

**Built with ❤️ for the financial technology community**

*Transforming financial news into actionable intelligence, one agent at a time.*

</div>
