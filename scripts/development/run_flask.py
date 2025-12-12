#!/usr/bin/env python3
"""
Simple script to run the Flask app for local development
"""

from strava_app import app

if __name__ == '__main__':
    print("Starting Flask app...")
    print("Available routes:")
    for rule in app.url_map.iter_rules():
        print(f"  {rule.rule} -> {rule.endpoint}")
    
    print("\nStarting server on http://localhost:5001")
    print("Press Ctrl+C to stop")
    
    app.run(debug=True, host='0.0.0.0', port=5001)
