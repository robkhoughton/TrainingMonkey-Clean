#!/usr/bin/env python3
"""
Test script with proper request context
"""

from strava_app import app
from flask import request

# Create a test client
client = app.test_client()

print("Testing Flask app with proper context...")

# Test the landing route with proper context
with app.test_request_context('/landing'):
    print("\n1. Testing /landing route with request context:")
    response = client.get('/landing')
    print(f"Status Code: {response.status_code}")
    if response.status_code == 200:
        print("✅ Landing page loads successfully!")
        print(f"Response length: {len(response.data)} characters")
        print("First 300 characters:")
        print(response.data[:300].decode('utf-8'))
    else:
        print(f"❌ Error: {response.status_code}")
        print(response.data.decode('utf-8'))

# Test the root route
with app.test_request_context('/'):
    print("\n2. Testing / route with request context:")
    response = client.get('/')
    print(f"Status Code: {response.status_code}")
    if response.status_code == 200:
        print("✅ Root page loads successfully!")
    else:
        print(f"❌ Error: {response.status_code}")

print("\n3. Flask app is ready for browser testing!")
print("Open your browser and go to: http://localhost:5000/landing")
