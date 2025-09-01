#!/usr/bin/env python3
"""
Test script to check landing page functionality
"""

from strava_app import app
from flask import render_template

# Test the route function directly
with app.app_context():
    try:
        print("Testing landing route...")
        result = render_template('landing.html')
        print("✅ Template rendered successfully!")
        print(f"Length: {len(result)} characters")
        print("First 200 characters:")
        print(result[:200])
    except Exception as e:
        print(f"❌ Error rendering template: {e}")

# Test route registration
print("\nChecking route registration...")
for rule in app.url_map.iter_rules():
    if 'landing' in rule.rule:
        print(f"✅ Found route: {rule.rule} -> {rule.endpoint}")
        print(f"   Methods: {rule.methods}")
