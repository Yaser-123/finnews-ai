# FinNews AI

A hackathon project for financial news processing using Python and FastAPI.

## Folder Structure

```
finnews-ai/
  main.py              # FastAPI application entry point
  requirements.txt     # Python dependencies
  .gitignore          # Git ignore rules
  README.md           # This file
  
  ingest/             # News ingestion modules
  agents/             # AI agents
    dedup/            # Deduplication agent
    entity/           # Entity extraction agent
    query/            # Query agent
  models/             # Data models
  vector_store/       # Vector database integration
  api/                # API layer
    routes/           # API route handlers
  utils/              # Utility functions
  demo/               # Demo scripts
  docs/               # Documentation
```

## Quickstart

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Run the FastAPI server:
   ```bash
   uvicorn main:app --reload
   ```

3. Access the API at `http://localhost:8000`
   - Health check: `GET http://localhost:8000/health`
   - Run graph: `POST http://localhost:8000/run_graph`
