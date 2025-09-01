#!/usr/bin/env python3
"""
Simple test Flask app to verify landing route works
"""

from flask import Flask, render_template

app = Flask(__name__)

@app.route('/')
def home():
    return "Home page works!"

@app.route('/landing')
def landing():
    return "Landing page works!"

@app.route('/test')
def test():
    return "Test page works!"

if __name__ == '__main__':
    print("Starting simple test Flask app...")
    print("Available routes:")
    for rule in app.url_map.iter_rules():
        print(f"  {rule.rule} -> {rule.endpoint}")
    
    app.run(debug=True, host='0.0.0.0', port=5001)
