#!/usr/bin/env python3
"""
Simple script to run Flask app on port 5001 for local testing
"""
import os
import sys

# Add app directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

# Change to app directory
os.chdir(os.path.join(os.path.dirname(__file__), 'app'))

# Import and run the app
from strava_app import app

if __name__ == '__main__':
    print("Starting Flask on http://localhost:5001")
    print("Navigate to: http://localhost:5001/dashboard?tab=spinner")
    app.run(debug=True, port=5001, host='127.0.0.1')



