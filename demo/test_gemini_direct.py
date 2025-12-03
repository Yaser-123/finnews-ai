"""
Direct test of Gemini API to diagnose LLM issues.
"""
import os
from dotenv import load_dotenv
import google.generativeai as genai

# Load environment
load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")
print(f"🔑 API Key loaded: {'Yes' if api_key else 'No'}")
if api_key:
    print(f"   Key starts with: {api_key[:10]}...")

if not api_key:
    print("❌ GEMINI_API_KEY not found in .env")
    exit(1)

# Test 1: Configure API
print("\n📡 Test 1: Configuring Gemini API...")
try:
    genai.configure(api_key=api_key)
    print("✅ API configured successfully")
except Exception as e:
    print(f"❌ Configuration failed: {e}")
    exit(1)

# Test 2: List available models
print("\n📋 Test 2: Listing available models...")
try:
    models = genai.list_models()
    gemini_models = [m.name for m in models if 'gemini' in m.name.lower()]
    print(f"✅ Found {len(gemini_models)} Gemini models:")
    for model_name in gemini_models[:10]:  # Show first 10
        print(f"   - {model_name}")
except Exception as e:
    print(f"❌ Failed to list models: {e}")

# Test 3: Try gemini-2.5-flash
print("\n🧪 Test 3: Testing gemini-2.5-flash...")
try:
    model = genai.GenerativeModel("gemini-2.5-flash")
    response = model.generate_content("Write a one-sentence summary: HDFC Bank reports 20% profit growth.")
    print(f"✅ Response received: {response.text[:100]}...")
except Exception as e:
    print(f"❌ gemini-2.5-flash failed: {type(e).__name__}: {str(e)[:200]}")

# Test 4: Try gemini-1.5-flash (fallback)
print("\n🧪 Test 4: Testing gemini-1.5-flash (fallback)...")
try:
    model = genai.GenerativeModel("gemini-1.5-flash")
    response = model.generate_content("Write a one-sentence summary: HDFC Bank reports 20% profit growth.")
    print(f"✅ Response received: {response.text[:100]}...")
except Exception as e:
    print(f"❌ gemini-1.5-flash failed: {type(e).__name__}: {str(e)[:200]}")

# Test 5: Try gemini-pro (fallback)
print("\n🧪 Test 5: Testing gemini-pro (fallback)...")
try:
    model = genai.GenerativeModel("gemini-pro")
    response = model.generate_content("Write a one-sentence summary: HDFC Bank reports 20% profit growth.")
    print(f"✅ Response received: {response.text[:100]}...")
except Exception as e:
    print(f"❌ gemini-pro failed: {type(e).__name__}: {str(e)[:200]}")

print("\n" + "="*60)
print("🎯 DIAGNOSIS COMPLETE")
print("="*60)
