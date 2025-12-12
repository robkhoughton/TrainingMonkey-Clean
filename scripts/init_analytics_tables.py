#!/usr/bin/env python3
"""
Initialize Analytics Tables Script

This script creates the necessary database tables for analytics tracking.
Run this script to set up the analytics infrastructure.
"""

import sys
import os

# Add the app directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'app'))

from analytics_tracker import analytics_tracker

def main():
    """Initialize analytics tables"""
    print("=" * 60)
    print("TrainingMonkey Analytics Tables Initialization")
    print("=" * 60)
    
    try:
        # Create analytics tables
        print("Creating analytics tables...")
        analytics_tracker.create_analytics_tables()
        print("✅ Analytics tables created successfully!")
        
        print("\nAnalytics infrastructure is now ready!")
        print("The following tables have been created:")
        print("- analytics_events: Stores all analytics events")
        print("- Indexes for optimal query performance")
        
        print("\nYou can now track analytics events and generate reports.")
        print("=" * 60)
        
    except Exception as e:
        print(f"❌ Error initializing analytics tables: {str(e)}")
        print("Please check your database connection and try again.")
        sys.exit(1)

if __name__ == "__main__":
    main()
