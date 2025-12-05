"""
STEP 5: REAL-TIME NEWS INGESTION & AUTOMATION
==============================================

Learn how to automate news fetching and keep your system updated 24/7
"""

print("""
╔══════════════════════════════════════════════════════════════════════╗
║                                                                      ║
║                   FINNEWS AI - STEP 5 TUTORIAL                       ║
║              REAL-TIME INGESTION & AUTOMATION                        ║
║                                                                      ║
╚══════════════════════════════════════════════════════════════════════╝

┌──────────────────────────────────────────────────────────────────────┐
│                      📚 TABLE OF CONTENTS                            │
├──────────────────────────────────────────────────────────────────────┤
│  Part A: Manual News Fetching                                       │
│  Part B: Scheduled Automation (Background Jobs)                     │
│  Part C: RSS Feed Management                                        │
│  Part D: Monitoring & Alerts                                        │
│  Part E: Production Deployment                                      │
└──────────────────────────────────────────────────────────────────────┘


═══════════════════════════════════════════════════════════════════════
PART A: MANUAL NEWS FETCHING
═══════════════════════════════════════════════════════════════════════

🎯 CONCEPT: Fetch fresh news on-demand

Your system can fetch news from RSS feeds anytime you want. The articles are:
✅ Automatically deduplicated (hash-based)
✅ Stored in PostgreSQL
✅ Ready for processing through the pipeline

┌──────────────────────────────────────────────────────────────────────┐
│ METHOD 1: Using the Ingestion Module (Programmatic)                 │
└──────────────────────────────────────────────────────────────────────┘

File: ingest/realtime.py

from ingest.realtime import fetch_all
from database.db import save_articles

# Fetch articles from all RSS feeds
articles = fetch_all()
print(f"Fetched {len(articles)} articles")

# Save to database (auto-deduplicates)
await save_articles(articles)

┌──────────────────────────────────────────────────────────────────────┐
│ METHOD 2: Using the Pipeline API                                    │
└──────────────────────────────────────────────────────────────────────┘

The /pipeline/run endpoint automatically:
1. Loads demo/fresh articles
2. Deduplicates them
3. Extracts entities
4. Analyzes sentiment
5. Indexes in ChromaDB

PowerShell:
Invoke-RestMethod -Uri "http://127.0.0.1:8000/pipeline/run" `
  -Method POST -Body '{}' -ContentType "application/json"

Response:
{
    "status": "ok",
    "total_input": 20,
    "unique_count": 19,
    "indexed_count": 19,
    "clusters": [...]
}

┌──────────────────────────────────────────────────────────────────────┐
│ METHOD 3: Direct RSS Ingestion (Custom Script)                      │
└──────────────────────────────────────────────────────────────────────┘

Create: scripts/fetch_news.py

import asyncio
from ingest.realtime import fetch_all
from database.db import init_db, save_articles

async def fetch_and_save():
    init_db()
    
    print("Fetching articles from RSS feeds...")
    articles = fetch_all()
    print(f"✅ Fetched {len(articles)} articles")
    
    print("Saving to database...")
    await save_articles(articles)
    print("✅ Articles saved!")

if __name__ == "__main__":
    asyncio.run(fetch_and_save())

Run it:
python scripts/fetch_news.py


═══════════════════════════════════════════════════════════════════════
PART B: SCHEDULED AUTOMATION (Background Jobs)
═══════════════════════════════════════════════════════════════════════

🎯 CONCEPT: Run tasks automatically at intervals

Your system has a built-in scheduler using APScheduler!

┌──────────────────────────────────────────────────────────────────────┐
│ THE SCHEDULER SYSTEM                                                 │
└──────────────────────────────────────────────────────────────────────┘

File: api/scheduler.py

Features:
✅ Fetch news every X minutes
✅ Process articles through pipeline
✅ Run in background (non-blocking)
✅ Configurable intervals
✅ Start/stop via API

┌──────────────────────────────────────────────────────────────────────┐
│ HOW TO USE THE SCHEDULER                                             │
└──────────────────────────────────────────────────────────────────────┘

1️⃣  START SCHEDULED INGESTION (Every 30 minutes)
   ────────────────────────────────────────────────

POST http://127.0.0.1:8000/scheduler/start

Body:
{
    "interval_minutes": 30
}

PowerShell:
Invoke-RestMethod -Uri "http://127.0.0.1:8000/scheduler/start" `
  -Method POST `
  -Body '{"interval_minutes": 30}' `
  -ContentType "application/json"

Response:
{
    "status": "started",
    "interval_minutes": 30,
    "message": "Scheduler started - will run every 30 minutes"
}

What happens:
• Fetches RSS feeds every 30 minutes
• Saves new articles to database
• Processes them through pipeline (entities, sentiment, indexing)
• Runs in background without blocking API


2️⃣  CHECK SCHEDULER STATUS
   ───────────────────────

GET http://127.0.0.1:8000/scheduler/status

PowerShell:
Invoke-RestMethod -Uri "http://127.0.0.1:8000/scheduler/status"

Response:
{
    "status": "running",
    "interval_minutes": 30,
    "is_running": true,
    "next_run": "2025-12-05T08:15:00",
    "jobs": [
        {
            "id": "ingest_job",
            "next_run_time": "2025-12-05T08:15:00"
        }
    ]
}


3️⃣  STOP SCHEDULER
   ──────────────

POST http://127.0.0.1:8000/scheduler/stop

PowerShell:
Invoke-RestMethod -Uri "http://127.0.0.1:8000/scheduler/stop" `
  -Method POST

Response:
{
    "status": "stopped",
    "message": "Scheduler stopped successfully"
}


4️⃣  TRIGGER MANUAL RUN (Don't wait for schedule)
   ──────────────────────────────────────────────

POST http://127.0.0.1:8000/scheduler/run-now

PowerShell:
Invoke-RestMethod -Uri "http://127.0.0.1:8000/scheduler/run-now" `
  -Method POST

Response:
{
    "status": "triggered",
    "message": "Ingestion job triggered manually"
}


═══════════════════════════════════════════════════════════════════════
PART C: RSS FEED MANAGEMENT
═══════════════════════════════════════════════════════════════════════

🎯 CONCEPT: Customize your news sources

┌──────────────────────────────────────────────────────────────────────┐
│ CURRENT RSS FEEDS (12 configured)                                   │
└──────────────────────────────────────────────────────────────────────┘

File: ingest/realtime.py

✅ Economic Times (3 feeds):
   • Banking & Finance
   • Stock Market
   • Top Stories

✅ LiveMint (2 feeds):
   • Markets
   • Money

✅ Financial Times (1 feed):
   • India Coverage

✅ Google News (4 feeds):
   • Indian Banking Sector
   • RBI Policy
   • Indian Stock Market
   • India Economy

⚠️ NDTV Business (1 feed):
   • Status: 403 Forbidden (blocking bots)

⚠️ CNBC TV18 (1 feed):
   • Status: XML parsing error

┌──────────────────────────────────────────────────────────────────────┐
│ HOW TO ADD NEW RSS FEEDS                                             │
└──────────────────────────────────────────────────────────────────────┘

Edit: ingest/realtime.py

1. Find the RSS_FEEDS list (around line 30)

2. Add your feed:

RSS_FEEDS = [
    # ... existing feeds ...
    
    # Add your new feed
    "https://your-news-site.com/rss/business.xml",
]

3. Restart the server

4. Test it:
   python -c "from ingest.realtime import fetch_all; print(len(fetch_all()))"


┌──────────────────────────────────────────────────────────────────────┐
│ FINDING RSS FEEDS                                                    │
└──────────────────────────────────────────────────────────────────────┘

💡 Tips to find RSS feeds:

1. Add /rss or /feed to website URL:
   • https://moneycontrol.com/rss/
   • https://business-standard.com/rss/

2. Look in website footer for RSS icon

3. Use RSS discovery tools:
   • RSS.app
   • FetchRSS.com

4. Popular Indian Financial RSS Feeds:
   • Money Control
   • Business Standard
   • The Hindu Business Line
   • Zee Business


═══════════════════════════════════════════════════════════════════════
PART D: MONITORING & ALERTS
═══════════════════════════════════════════════════════════════════════

🎯 CONCEPT: Get notified about important news

┌──────────────────────────────────────────────────────────────────────┐
│ REAL-TIME WEBSOCKET ALERTS                                           │
└──────────────────────────────────────────────────────────────────────┘

Your system has WebSocket support for real-time alerts!

Endpoint: ws://127.0.0.1:8000/ws/alerts

Alert Types:
📉 HIGH_RISK      - Negative sentiment > 0.90
📈 BULLISH        - Positive sentiment > 0.90
⚖️ REGULATORY     - Mentions RBI, SEBI, policy
💰 EARNINGS       - Mentions profit, revenue, growth

┌──────────────────────────────────────────────────────────────────────┐
│ CONNECTING TO WEBSOCKET (JavaScript)                                │
└──────────────────────────────────────────────────────────────────────┘

const socket = new WebSocket('ws://127.0.0.1:8000/ws/alerts');

socket.onmessage = (event) => {
    const alert = JSON.parse(event.data);
    console.log('Alert:', alert);
    
    // Show notification
    if (alert.type === 'HIGH_RISK') {
        showNotification('⚠️ High Risk Alert', alert.text);
    }
};

Alert structure:
{
    "type": "BULLISH",
    "article_id": 123,
    "text": "HDFC Bank announces record profit...",
    "sentiment": {
        "label": "positive",
        "score": 0.95
    },
    "entities": {
        "companies": ["HDFC Bank"],
        "sectors": ["Banking"]
    },
    "timestamp": "2025-12-05T08:30:00"
}


┌──────────────────────────────────────────────────────────────────────┐
│ DATABASE MONITORING                                                  │
└──────────────────────────────────────────────────────────────────────┘

Check system stats:

GET http://127.0.0.1:8000/stats

PowerShell:
Invoke-RestMethod -Uri "http://127.0.0.1:8000/stats"

Response:
{
    "articles": {
        "total": 639,
        "with_entities": 169,
        "with_sentiment": 703
    },
    "entities": {
        "companies": 465,
        "sectors": 469,
        "regulators": 129
    },
    "sources": {
        "Google News": 394,
        "Economic Times": 150,
        "LiveMint": 70,
        "Financial Times": 25
    }
}


═══════════════════════════════════════════════════════════════════════
PART E: PRODUCTION DEPLOYMENT
═══════════════════════════════════════════════════════════════════════

🎯 CONCEPT: Deploy your system 24/7

┌──────────────────────────────────────────────────────────────────────┐
│ OPTION 1: SIMPLE BACKGROUND RUN (Windows)                           │
└──────────────────────────────────────────────────────────────────────┘

1. Create run_server.bat:

@echo off
cd C:\\Users\\T MOHAMED AMMAR\\Desktop\\Tradl\\finnews-ai
call .venv\\Scripts\\activate
uvicorn main:app --host 0.0.0.0 --port 8000
pause

2. Double-click to run
3. Start scheduler via API
4. Leave running 24/7


┌──────────────────────────────────────────────────────────────────────┐
│ OPTION 2: WINDOWS SERVICE (nssm)                                    │
└──────────────────────────────────────────────────────────────────────┘

1. Download NSSM: https://nssm.cc/download

2. Install as service:

nssm install FinNewsAI "C:\\path\\to\\venv\\python.exe"
nssm set FinNewsAI AppParameters "-m uvicorn main:app --host 0.0.0.0 --port 8000"
nssm set FinNewsAI AppDirectory "C:\\Users\\T MOHAMED AMMAR\\Desktop\\Tradl\\finnews-ai"
nssm start FinNewsAI

3. Auto-starts on Windows boot!


┌──────────────────────────────────────────────────────────────────────┐
│ OPTION 3: DOCKER CONTAINER                                          │
└──────────────────────────────────────────────────────────────────────┘

Create Dockerfile:

FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
RUN python -m spacy download en_core_web_sm
COPY . .
EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]

Build and run:

docker build -t finnews-ai .
docker run -d -p 8000:8000 --name finnews finnews-ai


┌──────────────────────────────────────────────────────────────────────┐
│ OPTION 4: CLOUD DEPLOYMENT (Railway/Render/Heroku)                  │
└──────────────────────────────────────────────────────────────────────┘

1. Push to GitHub (already done!)

2. Connect to Railway.app:
   • Sign up at railway.app
   • New Project → Deploy from GitHub
   • Select: Yaser-123/finnews-ai
   • Add PostgreSQL database
   • Set environment variables
   • Deploy!

3. Your API will be live at:
   https://finnews-ai.railway.app


┌──────────────────────────────────────────────────────────────────────┐
│ RECOMMENDED SCHEDULE                                                 │
└──────────────────────────────────────────────────────────────────────┘

📅 For Development:
   • Fetch news: Every 30 minutes
   • Process pipeline: After each fetch

📅 For Production:
   • Market hours (9 AM - 5 PM): Every 15 minutes
   • Off hours: Every 60 minutes
   • Weekend: Every 2 hours (low activity)

Example schedule setup:

# Market hours (more frequent)
if is_market_hours():
    interval = 15  # minutes
else:
    interval = 60  # minutes

# Start scheduler
POST /scheduler/start
Body: {"interval_minutes": interval}


═══════════════════════════════════════════════════════════════════════
                            🎓 STEP 5 COMPLETE!
═══════════════════════════════════════════════════════════════════════

You now know how to:
✅ Fetch news manually or automatically
✅ Schedule background jobs (APScheduler)
✅ Manage RSS feeds (add/remove sources)
✅ Monitor system with WebSocket alerts
✅ Deploy for 24/7 operation

📝 PRACTICAL EXERCISES:

1. Start the scheduler:
   Invoke-RestMethod -Uri "http://127.0.0.1:8000/scheduler/start" \\
     -Method POST -Body '{"interval_minutes": 5}' \\
     -ContentType "application/json"

2. Check status after 5 minutes:
   Invoke-RestMethod -Uri "http://127.0.0.1:8000/scheduler/status"

3. Trigger manual run:
   Invoke-RestMethod -Uri "http://127.0.0.1:8000/scheduler/run-now" \\
     -Method POST

4. Check database for new articles:
   python demo/check_db_count.py

═══════════════════════════════════════════════════════════════════════

🚀 NEXT STEP: Advanced Features
   • Custom entity extraction
   • Multi-language support
   • Advanced analytics dashboard
   • Trading signal generation

═══════════════════════════════════════════════════════════════════════
""")
