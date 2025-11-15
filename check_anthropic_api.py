#!/usr/bin/env python3
"""
Check Anthropic API connectivity and credits
"""

import requests
import json
import os
from dotenv import load_dotenv

# Load environment
load_dotenv()

# Try to load API key from config
CONFIG_PATH = 'app/config.json'
api_key = None

# Try environment variable first
api_key = os.environ.get('ANTHROPIC_API_KEY')

# Try config file
if not api_key and os.path.exists(CONFIG_PATH):
    with open(CONFIG_PATH, 'r') as f:
        config = json.load(f)
        api_key = config.get('anthropic_api_key')

if not api_key:
    print("ERROR: No API key found")
    print("  - Not in ANTHROPIC_API_KEY environment variable")
    print("  - Not in app/config.json")
    exit(1)

print("=" * 80)
print("ANTHROPIC API DIAGNOSTIC")
print("=" * 80)
print()

# Mask the API key for security
masked_key = api_key[:10] + "..." + api_key[-4:] if len(api_key) > 14 else "***"
print(f"API Key: {masked_key}")
print()

# Test API call with minimal tokens
print("Testing API connectivity...")
print()

headers = {
    "Content-Type": "application/json",
    "X-API-Key": api_key,
    "anthropic-version": "2023-06-01"
}

data = {
    "model": "claude-sonnet-4-20250514",
    "messages": [
        {"role": "user", "content": "Say 'API test successful' and nothing else."}
    ],
    "temperature": 0.3,
    "max_tokens": 50
}

try:
    response = requests.post(
        "https://api.anthropic.com/v1/messages",
        headers=headers,
        json=data,
        timeout=30
    )
    
    print(f"Status Code: {response.status_code}")
    print()
    
    if response.status_code == 200:
        print("✅ SUCCESS - API is accessible and working")
        print()
        response_json = response.json()
        response_text = response_json.get('content', [{}])[0].get('text', '')
        print(f"Response: {response_text}")
        print()
        
        # Check usage
        usage = response_json.get('usage', {})
        print(f"Tokens used: {usage.get('input_tokens', 0)} input + {usage.get('output_tokens', 0)} output")
        
    elif response.status_code == 401:
        print("❌ AUTHENTICATION FAILED")
        print("   The API key is invalid or expired")
        print("   Generate a new key at: https://console.anthropic.com/settings/keys")
        
    elif response.status_code == 429:
        print("❌ RATE LIMIT OR INSUFFICIENT CREDITS")
        print("   Either:")
        print("   1. You've hit the rate limit (wait and try again)")
        print("   2. You're out of API credits")
        print()
        print("   Check your usage at: https://console.anthropic.com/settings/billing")
        print()
        print("   Response:", response.text)
        
    elif response.status_code == 400:
        print("❌ BAD REQUEST")
        print("   The request format is invalid")
        print()
        print("   Response:", response.text)
        
    else:
        print(f"❌ ERROR: Status {response.status_code}")
        print()
        print("Response:", response.text)
        
except requests.exceptions.Timeout:
    print("❌ TIMEOUT - API request took longer than 30 seconds")
    print("   This might indicate network issues or API overload")
    
except Exception as e:
    print(f"❌ ERROR: {str(e)}")
    
print()
print("=" * 80)
print("RECOMMENDATIONS")
print("=" * 80)
print()
print("If you see authentication or credit errors:")
print("1. Check your Anthropic Console: https://console.anthropic.com/")
print("2. Verify your billing status")
print("3. Check if your API key is still valid")
print("4. Generate a new API key if needed")
print()
print("To update the API key:")
print("1. Edit app/config.json")
print("2. Replace 'anthropic_api_key' value")
print("3. Redeploy the application")

