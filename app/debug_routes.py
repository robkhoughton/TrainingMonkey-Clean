#!/usr/bin/env python3
"""
Debug script to test the landing route
"""

from strava_app import app
from flask import request

# Create a test client
client = app.test_client()

print("Testing Flask app routes...")

# Test the landing route
print("\n1. Testing /landing route:")
response = client.get('/landing')
print(f"Status Code: {response.status_code}")
print(f"Response: {response.data[:200]}...")

# Test the root route
print("\n2. Testing / route:")
response = client.get('/')
print(f"Status Code: {response.status_code}")
print(f"Response: {response.data[:200]}...")

# List all routes
print("\n3. All available routes:")
for rule in app.url_map.iter_rules():
    if 'landing' in rule.rule or rule.rule == '/':
        print(f"  {rule.rule} -> {rule.endpoint} (methods: {rule.methods})")

# Test if the landing_redirect function exists
print("\n4. Testing landing_redirect function:")
try:
    from strava_app import landing_redirect
    print("✅ landing_redirect function exists")
except ImportError as e:
    print(f"❌ Error importing landing_redirect: {e}")
