#!/usr/bin/env python3
"""
Test script to check database structure and data
"""

import db_utils
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_database_structure():
    """Test database structure and data"""
    try:
        logger.info("Testing database structure...")
        
        # Test user_settings table
        logger.info("1. Testing user_settings table...")
        query = "SELECT id, email FROM user_settings LIMIT 5"
        result = db_utils.execute_query(query, fetch=True)
        if result:
            logger.info(f"Found {len(result)} users in user_settings:")
            for row in result:
                logger.info(f"  - ID: {row['id']}, Email: {row['email']}")
        else:
            logger.warning("No users found in user_settings table")
        
        # Test activities table
        logger.info("2. Testing activities table...")
        query = "SELECT COUNT(*) as total FROM activities"
        result = db_utils.execute_query(query, fetch=True)
        if result:
            total_activities = result[0]['total']
            logger.info(f"Total activities: {total_activities}")
            
            if total_activities > 0:
                # Get sample activities
                query = "SELECT user_id, activity_date, trimp_score FROM activities LIMIT 5"
                result = db_utils.execute_query(query, fetch=True)
                logger.info("Sample activities:")
                for row in result:
                    logger.info(f"  - User: {row['user_id']}, Date: {row['activity_date']}, TRIMP: {row['trimp_score']}")
        else:
            logger.warning("No activities found")
        
        # Test acwr_configurations table
        logger.info("3. Testing acwr_configurations table...")
        query = "SELECT id, name, chronic_period_days, decay_rate FROM acwr_configurations"
        result = db_utils.execute_query(query, fetch=True)
        if result:
            logger.info(f"Found {len(result)} configurations:")
            for row in result:
                logger.info(f"  - ID: {row['id']}, Name: {row['name']}, Period: {row['chronic_period_days']}, Decay: {row['decay_rate']}")
        else:
            logger.warning("No configurations found")
        
        # Test user_acwr_configurations table
        logger.info("4. Testing user_acwr_configurations table...")
        query = "SELECT user_id, configuration_id, is_active FROM user_acwr_configurations"
        result = db_utils.execute_query(query, fetch=True)
        if result:
            logger.info(f"Found {len(result)} user configurations:")
            for row in result:
                logger.info(f"  - User: {row['user_id']}, Config: {row['configuration_id']}, Active: {row['is_active']}")
        else:
            logger.warning("No user configurations found")
        
        logger.info("Database structure test completed successfully!")
        
    except Exception as e:
        logger.error(f"Error testing database structure: {str(e)}")
        raise

if __name__ == "__main__":
    test_database_structure()
