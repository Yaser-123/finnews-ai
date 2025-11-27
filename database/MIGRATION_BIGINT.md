# Database Schema Migration - BIGINT Support

## Issue
The real-time ingestion feature generates large hash-based article IDs (using SHA-1) that exceed PostgreSQL's INTEGER range (int32: -2,147,483,648 to 2,147,483,647).

Example error:
```
asyncpg.exceptions.DataError: invalid input for query argument $1: 150152833267162024 (value out of int32 range)
```

## Solution
Changed `articles.id` column from `INTEGER` to `BIGINT` which supports much larger numbers (int64: -9,223,372,036,854,775,808 to 9,223,372,036,854,775,807).

## Migration Steps

### Option 1: Fresh Start (Recommended for new installations)

If you haven't stored important data yet:

1. **Drop existing tables**:
   ```bash
   python database/drop_tables.py
   ```

2. **Tables will be recreated automatically** on next app startup with the correct BIGINT schema.

### Option 2: Preserve Existing Data

If you have existing articles you want to keep:

1. **Run the migration script**:
   ```bash
   python database/migrate_bigint.py
   ```

   This will:
   - Backup your existing articles
   - Drop and recreate tables with BIGINT id
   - Restore article data
   - Recreate dependent tables (dedup_clusters, entities, sentiment)

2. **Verify migration**:
   ```bash
   python database/verify_schema.py
   ```

### Option 3: Manual Migration (Using psql or pgAdmin)

```sql
-- 1. Backup articles
CREATE TABLE articles_backup AS SELECT * FROM articles;

-- 2. Drop dependent tables
DROP TABLE IF EXISTS sentiment CASCADE;
DROP TABLE IF EXISTS entities CASCADE;
DROP TABLE IF EXISTS dedup_clusters CASCADE;

-- 3. Drop and recreate articles with BIGINT
DROP TABLE articles CASCADE;

CREATE TABLE articles (
    id BIGINT PRIMARY KEY,
    text TEXT NOT NULL,
    source TEXT,
    published_at TIMESTAMP,
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

-- 4. Restore data
INSERT INTO articles (id, text, source, published_at, created_at)
SELECT id, text, source, published_at, created_at FROM articles_backup;

-- 5. Recreate dependent tables
CREATE TABLE dedup_clusters (
    id SERIAL PRIMARY KEY,
    article_id INTEGER NOT NULL,
    cluster_main_id INTEGER,
    merged_ids INTEGER[],
    similarity_score FLOAT,
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE entities (
    id SERIAL PRIMARY KEY,
    article_id INTEGER NOT NULL,
    companies TEXT[],
    sectors TEXT[],
    regulators TEXT[],
    people TEXT[],
    events TEXT[],
    stocks JSONB,
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE sentiment (
    id SERIAL PRIMARY KEY,
    article_id INTEGER NOT NULL,
    label TEXT NOT NULL,
    score FLOAT NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

-- 6. Clean up backup
DROP TABLE articles_backup;
```

## Verification

After migration, verify the schema:

```bash
# Check articles.id type
psql $DATABASE_URL -c "SELECT data_type FROM information_schema.columns WHERE table_name = 'articles' AND column_name = 'id';"

# Should return: bigint
```

Or run the verification script:
```bash
python database/verify_schema.py
```

## Testing

After migration, run the test suite to confirm everything works:

```bash
python demo/test_realtime.py
```

You should see:
```
✅ Successfully fetched X articles
✅ First save: X new articles inserted
✅ Second save: 0 new articles (expected 0)
✅ Incremental storage working correctly (no duplicates)
```

## What Changed

**Before:**
```python
id = Column(Integer, primary_key=True, autoincrement=True)  # Max: 2,147,483,647
```

**After:**
```python
id = Column(BigInteger, primary_key=True, autoincrement=False)  # Max: 9,223,372,036,854,775,807
```

## Why BIGINT?

SHA-1 hash generates 160-bit digest. We take first 15 hex digits (60 bits) and convert to integer:
- Max value: int("f" * 15, 16) = 1,152,921,504,606,846,975
- This exceeds int32 range but fits comfortably in int64 (BIGINT)

## Impact

- ✅ Supports hash-based deterministic IDs
- ✅ No ID collisions across feeds
- ✅ Consistent IDs across pipeline runs
- ⚠️ Requires database migration for existing installations
