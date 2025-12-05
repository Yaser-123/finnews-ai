"""
Test Risk Monitoring Endpoint

Tests the new sector risk monitoring feature.
"""

import asyncio
import httpx

async def test_risk_monitor():
    """Test the risk monitoring endpoint."""
    
    async with httpx.AsyncClient() as client:
        print("=" * 80)
        print("RISK MONITORING ENDPOINT TEST")
        print("=" * 80)
        
        # Test 1: Banking sector (default)
        print("\n🏦 Test 1: Banking Sector Risk Monitor")
        print("-" * 80)
        try:
            response = await client.get(
                "http://127.0.0.1:8000/analysis/risk-monitor",
                params={"sector": "Banking", "days_back": 30}
            )
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Status: Success")
                print(f"📊 Sector: {data['sector']}")
                print(f"🚨 Risk Level: {data['risk_level'].upper()}")
                print(f"📉 Negative Articles: {data['negative_count']}")
                print(f"📈 Avg Sentiment Score: {data['avg_sentiment_score']}")
                print(f"🏢 High Risk Companies: {len(data['high_risk_companies'])}")
                print(f"🔔 Recent Alerts: {len(data['recent_alerts'])}")
                
                if data['high_risk_companies']:
                    print("\n🏢 Top 3 High-Risk Companies:")
                    for i, company in enumerate(data['high_risk_companies'][:3], 1):
                        print(f"  {i}. {company['company']}")
                        print(f"     • Negative Articles: {company['negative_count']}")
                        print(f"     • Avg Score: {company['avg_score']:.3f}")
                
                if data['recent_alerts']:
                    print("\n🔔 Most Recent Alert:")
                    alert = data['recent_alerts'][0]
                    print(f"  • Article ID: {alert['article_id']}")
                    print(f"  • Published: {alert['published_at']}")
                    print(f"  • Score: {alert['sentiment_score']}")
                    print(f"  • Companies: {', '.join(alert['companies']) if alert['companies'] else 'None'}")
                    print(f"  • Text: {alert['text'][:150]}...")
            else:
                print(f"❌ Error: {response.status_code}")
                print(f"   {response.text}")
        except Exception as e:
            print(f"❌ Error: {str(e)}")
        
        # Test 2: Technology sector
        print("\n\n💻 Test 2: Technology Sector Risk Monitor")
        print("-" * 80)
        try:
            response = await client.get(
                "http://127.0.0.1:8000/analysis/risk-monitor",
                params={"sector": "Technology", "days_back": 30, "min_sentiment": 0.75}
            )
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Status: Success")
                print(f"📊 Sector: {data['sector']}")
                print(f"🚨 Risk Level: {data['risk_level'].upper()}")
                print(f"📉 Negative Articles: {data['negative_count']}")
                print(f"📈 Avg Sentiment Score: {data['avg_sentiment_score']}")
            else:
                print(f"❌ Error: {response.status_code}")
        except Exception as e:
            print(f"❌ Error: {str(e)}")
        
        # Test 3: Finance sector with strict criteria
        print("\n\n💰 Test 3: Finance Sector (Strict Criteria)")
        print("-" * 80)
        try:
            response = await client.get(
                "http://127.0.0.1:8000/analysis/risk-monitor",
                params={"sector": "Finance", "days_back": 7, "min_sentiment": 0.9}
            )
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Status: Success")
                print(f"📊 Sector: {data['sector']}")
                print(f"🚨 Risk Level: {data['risk_level'].upper()}")
                print(f"📉 Negative Articles: {data['negative_count']}")
            else:
                print(f"❌ Error: {response.status_code}")
        except Exception as e:
            print(f"❌ Error: {str(e)}")
        
        print("\n" + "=" * 80)
        print("✅ Risk Monitoring Test Complete!")
        print("=" * 80)


if __name__ == "__main__":
    asyncio.run(test_risk_monitor())
