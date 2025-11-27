# Real-Time News Ingestion System

Automated RSS feed ingestion with scheduled background processing, incremental indexing, and WebSocket alerts.

## ⚠️ IMPORTANT: Database Schema Requirement

**Before using real-time ingestion**, ensure your database has the correct schema:

The `articles.id` column must be **BIGINT** (not INTEGER) to support large hash-based IDs.

### Quick Check
```bash
python database/verify_schema.py
```

### If Migration Needed
See [database/MIGRATION_BIGINT.md](database/MIGRATION_BIGINT.md) for detailed migration instructions.

**Quick fix (fresh installations):**
```bash
python database/drop_tables.py  # Drops all tables (WARNING: deletes data!)
# Tables will be recreated with correct schema on next app startup
```

## 🚀 Overview

The real-time ingestion system continuously monitors RSS feeds, fetches new articles, processes them through the FinNews AI pipeline, and sends alerts for high-confidence signals.

### Key Features

- **📡 RSS Feed Monitoring**: Fetch articles from configurable RSS feeds
- **⏰ Background Scheduler**: Periodic ingestion (default: every 60 seconds)
- **💾 Incremental Storage**: Only saves new articles (deduplication by ID)
- **🔄 Pipeline Integration**: Automatic sentiment analysis and indexing
- **🚨 Real-Time Alerts**: WebSocket broadcasts for high-confidence signals
- **📊 Job Statistics**: Track fetched/new/indexed counts per run
- **🔑 Deterministic IDs**: SHA-1 hash-based IDs prevent duplicates

## 📁 Architecture

```
ingest/
├── realtime.py          # RSS fetching and normalization
└── __init__.py

api/
├── scheduler.py         # Background job scheduler
└── routes/
    └── pipeline.py      # Pipeline processing (enhanced)

database/
└── db.py                # Database helpers (existing_ids, save_new_articles)
```

## 🔧 Configuration

### Environment Variables (.env)

```bash
# RSS Feeds (comma-separated URLs)
RSS_FEEDS="https://news.google.com/rss/search?q=HDFC+Bank&hl=en-IN,https://news.google.com/rss/search?q=Reliance&hl=en-IN"

# Ingestion interval in seconds
INGEST_INTERVAL=60

# Auto-start scheduler on app startup
AUTO_START_SCHEDULER=false

# Maximum article age in hours (filters old articles)
MAX_AGE_HOURS=168
```

### Default RSS Feeds

If `RSS_FEEDS` is not set, these defaults are used:
- HDFC Bank news (Google News)
- Reliance Industries news
- RBI monetary policy news
- Nifty/BSE market news

## 🎯 How It Works

### 1. Ingestion Flow

```
┌─────────────┐
│ RSS Feeds   │
└──────┬──────┘
       │
       ▼
┌─────────────────────────────────┐
│ fetch_all()                     │
│ - Fetches feeds concurrently    │
│ - Parses with feedparser        │
│ - Generates deterministic IDs   │
└──────┬──────────────────────────┘
       │
       ▼
┌─────────────────────────────────┐
│ save_new_articles()             │
│ - Checks existing IDs           │
│ - Inserts only new articles     │
└──────┬──────────────────────────┘
       │
       ▼
┌─────────────────────────────────┐
│ run_pipeline_on_articles()      │
│ - Sentiment analysis            │
│ - ChromaDB indexing             │
│ - WebSocket alerts              │
└─────────────────────────────────┘
```

### 2. Deterministic ID Generation

Articles get unique IDs using SHA-1 hash:

```python
id = sha1(f"{feed_url}|{guid}|{published_at}")[:15]
```

This ensures:
- Same article always gets same ID
- No duplicate entries in database
- Cross-feed deduplication

### 3. Incremental Processing

Only new articles are processed:

```python
# Check which IDs already exist
existing = await existing_ids(incoming_ids)

# Filter to new articles only
new_articles = [a for a in articles if a['id'] not in existing]

# Process only new articles
await save_new_articles(new_articles)
```

## 🎮 Usage

### Starting the Application

```bash
# Install dependencies
pip install feedparser apscheduler

# Start server
uvicorn main:app --reload
```

### Scheduler API Endpoints

#### Start Scheduler

```bash
# Start with default interval (60s)
curl -X POST http://127.0.0.1:8000/scheduler/start

# Start with custom interval
curl -X POST http://127.0.0.1:8000/scheduler/start \
  -H "Content-Type: application/json" \
  -d '{"interval_seconds": 120}'
```

Response:
```json
{
  "status": "started",
  "message": "Scheduler started successfully with 60s interval",
  "interval_seconds": 60,
  "next_run": "2025-11-27T12:01:00"
}
```

#### Stop Scheduler

```bash
curl -X POST http://127.0.0.1:8000/scheduler/stop
```

#### Get Status

```bash
curl http://127.0.0.1:8000/scheduler/status
```

Response:
```json
{
  "running": true,
  "next_run": "2025-11-27T12:02:00",
  "stats": {
    "last_run": "2025-11-27T12:01:00",
    "last_run_time": 3.45,
    "last_fetched": 25,
    "last_new": 5,
    "last_indexed": 5,
    "last_alerts": 2,
    "total_runs": 10,
    "last_error": null
  }
}
```

#### Get Last Run Stats

```bash
curl http://127.0.0.1:8000/scheduler/last_run
```

### Auto-Start on Startup

Set in `.env`:
```bash
AUTO_START_SCHEDULER=true
INGEST_INTERVAL=60
```

Scheduler will start automatically when the app launches.

## 🧪 Testing

Run the test suite:

```bash
python demo/test_realtime.py
```

Tests include:
1. **RSS Feed Fetching**: Fetches from 2 sample feeds
2. **Incremental Storage**: Tests duplicate detection
3. **Pipeline Processing**: Processes articles through sentiment analysis
4. **Scheduler API**: Displays endpoint usage

Expected output:
```
==================================================================
🧪 REAL-TIME INGESTION TEST SUITE
==================================================================

TEST 1: RSS Feed Fetching
==================================================================
✅ Successfully fetched 25 articles

TEST 2: Incremental Database Storage
==================================================================
✅ First save: 25 new articles inserted
✅ Second save: 0 new articles (expected 0)
✅ Incremental storage working correctly

TEST 3: Pipeline Processing
==================================================================
✅ Pipeline processing complete
   Indexed: 5 articles
   Alerts sent: 2

✅ TEST SUITE COMPLETE
```

## 📊 Job Statistics

The scheduler tracks detailed statistics:

| Metric | Description |
|--------|-------------|
| `last_run` | ISO timestamp of last execution |
| `last_run_time` | Duration in seconds |
| `last_fetched` | Articles fetched from feeds |
| `last_new` | New articles saved to DB |
| `last_indexed` | Articles indexed into ChromaDB |
| `last_alerts` | WebSocket alerts sent |
| `total_runs` | Total number of job executions |
| `last_error` | Last error message (null if success) |

## 🚨 Alert Integration

Articles trigger WebSocket alerts when:

- **BULLISH**: Positive sentiment > 0.90
- **HIGH_RISK**: Negative sentiment > 0.90

Alerts broadcast to all connected WebSocket clients at `/ws/alerts`.

## 🔍 Monitoring

### Logs

The scheduler logs detailed information:

```
==============================================================
Starting real-time ingestion job...
==============================================================
📥 Fetched 25 articles from 4 feeds
💾 Saved 5 new articles to database
🔍 Indexed 5 articles
🚨 Sent 2 alerts
==============================================================
✅ Ingestion job complete in 3.45s
==============================================================
```

### Health Check

Check if scheduler is running:

```bash
curl http://127.0.0.1:8000/scheduler/status
```

## 🛠️ Advanced Configuration

### Custom Feeds

Add your own RSS feeds in `.env`:

```bash
RSS_FEEDS="https://example.com/feed1.xml,https://example.com/feed2.xml"
```

### Rate Limiting

Adjust interval to respect feed rate limits:

```bash
INGEST_INTERVAL=300  # 5 minutes
```

### Age Filtering

Only ingest recent articles:

```bash
MAX_AGE_HOURS=24  # Last 24 hours only
```

## 🐛 Troubleshooting

### Issue: No articles fetched

**Solution**: Check feed URLs are accessible
```bash
curl -I "https://news.google.com/rss/..."
```

### Issue: Scheduler not starting

**Solution**: Check logs for initialization errors
```bash
uvicorn main:app --reload --log-level debug
```

### Issue: Duplicate articles

**Solution**: Verify deterministic ID generation
```python
# Check article IDs
articles = await fetch_all()
print([a['id'] for a in articles[:5]])
```

## 🔐 Security Considerations

1. **Rate Limiting**: Default 60s interval respects RSS etiquette
2. **Timeout**: 10s timeout prevents hanging on slow feeds
3. **Error Isolation**: Feed failures don't stop other feeds
4. **Transaction Safety**: DB operations are atomic

## 📈 Performance

- **Concurrent Fetching**: All feeds fetched in parallel
- **Incremental Processing**: Only new articles processed
- **Batch Indexing**: ChromaDB batch operations
- **Async Operations**: Non-blocking I/O throughout

Typical performance:
- 4 feeds: ~2-3 seconds
- 25 articles: ~1-2 seconds processing
- Memory: ~50MB per job

## 🎓 Best Practices

1. **Start with longer intervals** during testing (300s)
2. **Monitor job statistics** for performance
3. **Set MAX_AGE_HOURS** to avoid old articles
4. **Use AUTO_START_SCHEDULER=false** for manual control
5. **Check logs regularly** for feed errors

## 🔄 Integration with Existing Pipeline

The real-time system integrates seamlessly:

- Uses existing `db.save_articles()` with smart reset
- Calls `SentimentAgent.run()` for analysis
- Indexes via `get_or_create_collection()`
- Broadcasts via `alert_manager.send_alert()`

No changes needed to existing pipeline code!

## 📚 API Reference

### `ingest.realtime`

```python
# Fetch all configured feeds
articles = await fetch_all(feeds=None)

# Fetch single feed
articles = await fetch_feed(session, feed_url)

# Normalize feed entry
article = normalize_entry(feed_url, entry)

# Get configured feeds
feeds = get_configured_feeds()
```

### `database.db`

```python
# Check existing article IDs
existing = await existing_ids([1, 2, 3])

# Save only new articles
new_ids = await save_new_articles(articles)
```

### `api.scheduler`

```python
# Initialize scheduler (called on startup)
init_scheduler()

# Shutdown scheduler (called on shutdown)
shutdown_scheduler()

# Job function (runs periodically)
await realtime_ingest_job()
```

---

For questions or issues, see the main project documentation or check the logs.
