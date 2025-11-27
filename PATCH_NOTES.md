# PATCH BUNDLE - FinNews AI Production Upgrade

**Version:** 2.0  
**Date:** 2025-01-XX  
**Status:** ✅ COMPLETE

## 🎯 Overview

Comprehensive 5-part production upgrade patch to enhance FinNews AI's data quality, coverage, and deduplication capabilities.

---

## 📋 Patch Components

### ✅ Part 1: Standardize Embeddings (768-dim MPNet)

**Status:** Already Complete

All embedding models standardized to `sentence-transformers/all-mpnet-base-v2` (768 dimensions):
- ✅ `graphs/query_graph.py`
- ✅ `graphs/pipeline_graph.py`
- ✅ `agents/query/agent.py`
- ✅ `agents/dedup/agent.py`

**Benefits:**
- Higher quality semantic search
- Better query expansion
- Improved deduplication accuracy

---

### ✅ Part 2: Expand RSS Feeds (6 → 12 Premium Sources)

**Status:** Complete

**Files Modified:**
- `.env.example` - Updated RSS_FEEDS default
- `config.py` - Updated default RSS_FEED_LIST
- `ingest/realtime.py` - Updated DEFAULT_FEEDS

**New Premium Sources:**

| Category | Count | Sources |
|----------|-------|---------|
| **Moneycontrol** | 3 | Latest News, Top News, Market Reports |
| **Economic Times** | 2 | Markets/Stocks, Banking/Finance |
| **Livemint** | 2 | Money, Markets |
| **NDTV Profit** | 1 | Business |
| **Financial Times** | 1 | India Coverage |
| **CNBC TV18** | 1 | Business |
| **Google News** | 2 | Banking Sector, RBI Policy |
| **TOTAL** | **12** | |

**Benefits:**
- 2× increase in news coverage
- More diverse sources (reduce single-source bias)
- Better market sentiment capture
- Enhanced deduplication testing across feeds

---

### ✅ Part 3: RSS Cleanup Utilities

**Status:** Complete

**New File:** `ingest/utils.py` (7 functions)

```python
# Core Functions
clean_html(text: str) -> str
    # Remove HTML tags, decode entities, normalize whitespace
    
normalize_title(text: str) -> str
    # Lowercase, remove punctuation, collapse whitespace
    
compute_hash(text: str) -> str
    # Generate MD5 hash for deduplication
```

**Additional Utilities:**
- `extract_domain()` - URL parsing
- `truncate_text()` - Length limiting

**Test Results:**
```
✅ HTML Cleaning: <p>HDFC &nbsp; Bank</p> → "HDFC Bank"
✅ Normalization: "RBI hikes rates!" → "rbi hikes rates"
✅ Hashing: MD5 deterministic hashes
```

---

### ✅ Part 4: Integration in Real-Time Ingestion

**Status:** Complete

**Files Modified:**
- `ingest/realtime.py`

**Changes:**

1. **Import Cleanup Utilities:**
```python
from ingest.utils import clean_html, normalize_title, compute_hash
```

2. **Updated `normalize_entry()` Function:**
   - Clean HTML from title and description
   - Generate content hash from normalized title
   - Return hash in article dict
   
```python
# Before
text = f"{title}. {summary}".strip()

# After
title_clean = clean_html(title)
summary_clean = clean_html(summary)
text = f"{title_clean}. {summary_clean}".strip()
content_hash = compute_hash(normalize_title(title_clean))
return {..., "hash": content_hash}
```

3. **Enhanced `fetch_all()` Deduplication:**
   - Track `seen_hashes: Set[str]` across all feeds
   - Skip duplicate articles by content hash
   - Log deduplication metrics
   
```python
# Deduplication by both ID and content hash
seen_ids: Set[int] = set()
seen_hashes: Set[str] = set()

for article in all_articles:
    if article['id'] in seen_ids:
        id_duplicates += 1
        continue
    if article['hash'] in seen_hashes:
        hash_duplicates += 1
        continue
    # Add to results
```

**Benefits:**
- Clean text without HTML artifacts
- Content-based deduplication across feeds
- Metrics for monitoring duplicate rates

---

### ✅ Part 5: Database Schema Update

**Status:** Complete (code ready, migration pending)

**Files Modified:**
- `database/schema.py`

**Changes:**

```python
from sqlalchemy import UniqueConstraint, String

class Article(Base):
    __tablename__ = "articles"
    __table_args__ = (
        UniqueConstraint("hash", name="uq_article_hash"),
    )
    
    # ... existing columns ...
    hash = Column(String, nullable=True, index=True)
```

**Schema Features:**
- `hash` column: VARCHAR, nullable (safe for existing data)
- Index on `hash` for fast lookups
- Unique constraint `uq_article_hash` for database-level deduplication

**Migration Script:**
- `database/migrations/add_hash_column.py`
- Safe migration (nullable column)
- Auto-checks existing columns
- Idempotent (can run multiple times)

**Migration Steps:**
```bash
python database/migrations/add_hash_column.py
```

---

## 🧪 Validation Results

All 5 parts validated with `test_patch.py`:

```
✅ Part 1: Embeddings - Already standardized to MPNet 768-dim
✅ Part 2: RSS Feeds - 12 premium sources configured
✅ Part 3: Cleanup Utilities - All functions working
✅ Part 4: Integration - HTML cleanup and hashing integrated
✅ Part 5: Schema - hash column added with unique constraint
```

---

## 📊 Impact Metrics (Expected)

| Metric | Before | After | Change |
|--------|--------|-------|--------|
| RSS Feeds | 6 | 12 | +100% |
| Embedding Dim | 768 | 768 | ✅ Standard |
| HTML Cleaning | ❌ None | ✅ Yes | +Quality |
| Deduplication | ID only | ID + Hash | +Accuracy |
| DB Constraints | None | Unique hash | +Data integrity |

---

## 🚀 Deployment Checklist

### Pre-Deployment
- [x] Create cleanup utilities (`ingest/utils.py`)
- [x] Update RSS feeds (12 sources)
- [x] Integrate cleanup in ingestion
- [x] Update schema model
- [x] Create migration script
- [x] Validate all changes

### Deployment
- [ ] Commit changes to Git
- [ ] Push to GitHub
- [ ] Run database migration
- [ ] Restart application
- [ ] Monitor ingestion logs

### Post-Deployment Validation
- [ ] Check RSS feed fetching (should see 12 feeds)
- [ ] Verify HTML cleaning in article text
- [ ] Monitor deduplication metrics (id_duplicates, hash_duplicates)
- [ ] Confirm hash values in database
- [ ] Test query performance with new embeddings

---

## 📝 Configuration Updates

### .env File
Update your `.env` file with 12 RSS feeds:

```env
RSS_FEEDS="https://www.moneycontrol.com/rss/latestnews.xml,https://www.moneycontrol.com/rss/MCtopnews.xml,https://www.moneycontrol.com/rss/marketreports.xml,https://economictimes.indiatimes.com/markets/stocks/rssfeeds/2146842.cms,https://economictimes.indiatimes.com/industry/banking/finance/rssfeeds/13358259.cms,https://www.livemint.com/rss/money,https://www.livemint.com/rss/markets,https://www.ndtvprofit.com/rss/business,https://www.ft.com/rss/world/asia-pacific/india,https://www.cnbctv18.com/rss/business.xml,https://news.google.com/rss/search?q=indian+banking+sector&hl=en-IN&gl=IN&ceid=IN:en,https://news.google.com/rss/search?q=RBI+policy+india&hl=en-IN&gl=IN&ceid=IN:en"
```

---

## 🛠️ Rollback Plan

If issues occur:

1. **Code Rollback:**
   ```bash
   git revert HEAD
   ```

2. **Database Rollback:**
   ```sql
   ALTER TABLE articles DROP CONSTRAINT IF EXISTS uq_article_hash;
   DROP INDEX IF EXISTS ix_articles_hash;
   ALTER TABLE articles DROP COLUMN IF EXISTS hash;
   ```

3. **Config Rollback:**
   - Revert to 6 RSS feeds in `.env`
   - Restart application

---

## 📚 Documentation Updates

- [x] `PATCH_NOTES.md` - This file
- [x] `test_patch.py` - Validation script
- [x] `database/migrations/add_hash_column.py` - Migration script
- [x] Inline code comments updated

---

## 🎓 Technical Notes

### Embedding Model Details
- **Model:** `sentence-transformers/all-mpnet-base-v2`
- **Dimensions:** 768
- **Context Window:** 384 tokens
- **Use Cases:** Semantic search, query expansion, deduplication

### Hash Function Details
- **Algorithm:** MD5
- **Input:** Normalized title (lowercase, no punctuation)
- **Output:** 32-character hexadecimal string
- **Collision Rate:** ~0% for news articles

### Deduplication Strategy
1. **ID-based:** SHA-1 of `feed_url|guid|published_at` (15 hex digits)
2. **Hash-based:** MD5 of normalized title content
3. **Database-level:** Unique constraint on hash column

---

## 🤝 Contributors

- Development: GitHub Copilot
- Testing: Automated validation suite
- Review: Code validation passed

---

## 📞 Support

Issues or questions? Check:
1. Validation script: `python test_patch.py`
2. Migration logs: `database/migrations/add_hash_column.py` output
3. Ingestion logs: Look for deduplication metrics
4. Database: Query `articles` table for hash values

---

**End of Patch Notes**
