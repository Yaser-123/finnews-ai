# Risk Monitoring Endpoint - User Guide

## Overview
The `/analysis/risk-monitor` endpoint tracks negative sentiment articles by sector, helping you identify potential risks in specific industries.

## Endpoint
```
GET /analysis/risk-monitor
```

## Parameters
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `sector` | string | "Banking" | Sector to monitor (e.g., Banking, Technology, Finance, Pharma). Leave empty to monitor all sectors. |
| `days_back` | integer | 30 | Number of days to look back (1-180) |
| `min_sentiment` | float | 0.7 | Minimum negative sentiment score (0.5-1.0). Higher = more negative. |

## Response
```json
{
    "sector": "Banking",
    "risk_level": "low|medium|high|critical",
    "negative_count": 0,
    "avg_sentiment_score": 0.784,
    "high_risk_companies": [
        {
            "company": "HDFC Bank",
            "negative_count": 5,
            "avg_score": 0.856
        }
    ],
    "recent_alerts": [
        {
            "article_id": 123,
            "text": "Article preview...",
            "published_at": "2025-12-05T10:00:00",
            "sentiment_score": 0.906,
            "companies": ["HDFC Bank", "Axis Bank"]
        }
    ],
    "updated_at": "2025-12-05T15:30:00"
}
```

## Risk Levels
- **low**: < 5 negative articles
- **medium**: 5-15 negative articles
- **high**: 16-30 negative articles
- **critical**: > 30 negative articles

## How It Works
1. Searches for articles with negative sentiment labels
2. Filters by sector (searches both in sector tags AND article text)
3. Calculates risk metrics and identifies companies with multiple negative mentions
4. Returns the top high-risk companies and recent alerts

## Example Usage

### Monitor All Sectors (No Filter)
```powershell
curl "http://127.0.0.1:8000/analysis/risk-monitor?sector="
```

### Monitor Banking Sector
```powershell
curl "http://127.0.0.1:8000/analysis/risk-monitor?sector=Banking"
```

### Monitor Technology (Last 7 Days, High Threshold)
```powershell
curl "http://127.0.0.1:8000/analysis/risk-monitor?sector=Technology&days_back=7&min_sentiment=0.9"
```

### Monitor Pharma (Lower Threshold)
```powershell
curl "http://127.0.0.1:8000/analysis/risk-monitor?sector=Pharma&min_sentiment=0.6"
```

## Testing
Based on current database (878 articles):
- **120 negative articles** total
- Most negative articles are about: Biocon, pharma, F&O stocks
- Few banking-specific negative articles currently

### Test Commands
```powershell
# All negative articles
curl "http://127.0.0.1:8000/analysis/risk-monitor?sector=&min_sentiment=0.5"

# Pharma sector
curl "http://127.0.0.1:8000/analysis/risk-monitor?sector=Pharma"

# Banking (may return 0 if no banking negatives)
curl "http://127.0.0.1:8000/analysis/risk-monitor?sector=Banking"
```

## Notes
- Empty `sector` parameter returns ALL negative articles (useful for overview)
- If `high_risk_companies` is empty, it means no company has 2+ negative mentions
- The endpoint searches article TEXT if sector tags are empty (fallback mechanism)
- Sentiment scores: Higher = more negative (0.5-1.0 range)

## Use Cases
1. **Daily Risk Monitoring**: Check critical sectors every morning
2. **Alert System**: Integrate with notifications when risk_level = "critical"
3. **Competitor Tracking**: Monitor negative news about specific companies
4. **Crisis Detection**: Identify emerging risks before they escalate
5. **Trading Signals**: Use high-risk companies as sell signals
