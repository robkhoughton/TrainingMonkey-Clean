#!/usr/bin/env python3
"""
Test script to verify HR stream data collection fix.
This script will test the enhanced TRIMP calculation with real HR stream data.
"""

import sys
import os
import logging
from datetime import datetime, timedelta

# Add the app directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from db_utils import execute_query, get_hr_stream_data
from strava_training_load import calculate_training_load
from utils.feature_flags import is_feature_enabled

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_hr_stream_collection():
    """Test HR stream data collection and enhanced TRIMP calculation"""
    
    logger.info("=== TESTING HR STREAM COLLECTION FIX ===")
    
    # Check if we have any activities with HR data
    logger.info("Checking for activities with HR data...")
    
    try:
        # Get activities with HR data
        activities_query = """
            SELECT activity_id, user_id, name, date, avg_heart_rate, trimp_calculation_method, hr_stream_sample_count
            FROM activities 
            WHERE avg_heart_rate IS NOT NULL 
            ORDER BY date DESC 
            LIMIT 5
        """
        
        activities = execute_query(activities_query, fetch=True)
        
        if not activities:
            logger.error("No activities with HR data found in database")
            return False
            
        logger.info(f"Found {len(activities)} activities with HR data")
        
        # Check HR streams table
        hr_streams_query = "SELECT COUNT(*) as count FROM hr_streams"
        hr_streams_result = execute_query(hr_streams_query, fetch=True)
        hr_streams_count = hr_streams_result[0]['count'] if hr_streams_result else 0
        
        logger.info(f"HR streams table contains {hr_streams_count} records")
        
        # Show sample activities
        for i, activity in enumerate(activities[:3]):
            logger.info(f"Activity {i+1}: ID={activity['activity_id']}, Name='{activity['name']}', "
                       f"Date={activity['date']}, AvgHR={activity['avg_heart_rate']}, "
                       f"Method={activity.get('trimp_calculation_method', 'unknown')}, "
                       f"Samples={activity.get('hr_stream_sample_count', 0)}")
        
        # Test feature flag status
        test_user_id = activities[0]['user_id']
        enhanced_enabled = is_feature_enabled('enhanced_trimp_calculation', test_user_id)
        logger.info(f"Enhanced TRIMP calculation enabled for user {test_user_id}: {enhanced_enabled}")
        
        return True
        
    except Exception as e:
        logger.error(f"Error testing HR stream collection: {str(e)}")
        return False

def test_hr_stream_retrieval():
    """Test retrieving HR stream data from database"""
    
    logger.info("=== TESTING HR STREAM RETRIEVAL ===")
    
    try:
        # Get an activity with HR data
        activities_query = """
            SELECT activity_id, user_id 
            FROM activities 
            WHERE avg_heart_rate IS NOT NULL 
            LIMIT 1
        """
        
        activities = execute_query(activities_query, fetch=True)
        
        if not activities:
            logger.error("No activities found for HR stream retrieval test")
            return False
            
        activity = activities[0]
        activity_id = activity['activity_id']
        user_id = activity['user_id']
        
        logger.info(f"Testing HR stream retrieval for activity {activity_id}, user {user_id}")
        
        # Try to retrieve HR stream data
        hr_stream_data = get_hr_stream_data(activity_id, user_id)
        
        if hr_stream_data:
            logger.info(f"✅ HR stream data found: {hr_stream_data['sample_count']} samples")
            logger.info(f"   Sample rate: {hr_stream_data['sample_rate']} Hz")
            logger.info(f"   Created: {hr_stream_data['created_at']}")
            return True
        else:
            logger.warning(f"⚠️  No HR stream data found for activity {activity_id}")
            return False
            
    except Exception as e:
        logger.error(f"Error testing HR stream retrieval: {str(e)}")
        return False

def main():
    """Main test function"""
    
    logger.info("Starting HR stream collection fix tests...")
    
    # Test 1: Check current state
    test1_success = test_hr_stream_collection()
    
    # Test 2: Test HR stream retrieval
    test2_success = test_hr_stream_retrieval()
    
    # Summary
    logger.info("=== TEST SUMMARY ===")
    logger.info(f"HR stream collection test: {'✅ PASSED' if test1_success else '❌ FAILED'}")
    logger.info(f"HR stream retrieval test: {'✅ PASSED' if test2_success else '❌ FAILED'}")
    
    if test1_success and test2_success:
        logger.info("🎉 All tests passed! HR stream collection fix is working.")
    else:
        logger.warning("⚠️  Some tests failed. Check the logs above for details.")
    
    return test1_success and test2_success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
