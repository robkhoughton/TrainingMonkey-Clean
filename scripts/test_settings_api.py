#!/usr/bin/env python3
"""
Test script for settings API with timezone support
Tests the updated settings endpoints
"""

import requests
import json
import sys
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Test settings API endpoints
BASE_URL = "http://localhost:5000"  # Adjust as needed

def test_get_settings():
    """Test GET /settings endpoint"""
    logger.info("Testing GET /settings endpoint...")
    
    try:
        response = requests.get(f"{BASE_URL}/settings")
        
        if response.status_code == 200:
            data = response.json()
            settings = data.get('settings', {})
            
            logger.info(f"✅ Settings retrieved successfully")
            logger.info(f"  User ID: {settings.get('id')}")
            logger.info(f"  Email: {settings.get('email')}")
            logger.info(f"  Timezone: {settings.get('timezone', 'NOT FOUND')}")
            logger.info(f"  Resting HR: {settings.get('resting_hr')}")
            logger.info(f"  Max HR: {settings.get('max_hr')}")
            
            return settings
        else:
            logger.error(f"❌ Failed to get settings: {response.status_code}")
            logger.error(f"Response: {response.text}")
            return None
            
    except Exception as e:
        logger.error(f"❌ Error testing GET /settings: {str(e)}")
        return None

def test_update_timezone(current_settings):
    """Test updating timezone setting"""
    if not current_settings:
        logger.error("❌ Cannot test timezone update without current settings")
        return False
    
    logger.info("Testing timezone update...")
    
    # Test data - change timezone to Eastern
    update_data = {
        'timezone': 'US/Eastern'
    }
    
    try:
        response = requests.put(
            f"{BASE_URL}/settings",
            json=update_data,
            headers={'Content-Type': 'application/json'}
        )
        
        if response.status_code == 200:
            logger.info("✅ Timezone update successful")
            
            # Verify the change
            updated_settings = test_get_settings()
            if updated_settings and updated_settings.get('timezone') == 'US/Eastern':
                logger.info("✅ Timezone change verified")
                
                # Revert back to original
                revert_data = {'timezone': current_settings.get('timezone', 'US/Pacific')}
                revert_response = requests.put(
                    f"{BASE_URL}/settings",
                    json=revert_data,
                    headers={'Content-Type': 'application/json'}
                )
                
                if revert_response.status_code == 200:
                    logger.info("✅ Timezone reverted successfully")
                    return True
                else:
                    logger.warning("⚠️ Failed to revert timezone")
                    return True  # Still successful test
            else:
                logger.error("❌ Timezone change not reflected")
                return False
        else:
            logger.error(f"❌ Failed to update timezone: {response.status_code}")
            logger.error(f"Response: {response.text}")
            return False
            
    except Exception as e:
        logger.error(f"❌ Error testing timezone update: {str(e)}")
        return False

def test_invalid_timezone():
    """Test invalid timezone validation"""
    logger.info("Testing invalid timezone validation...")
    
    invalid_data = {
        'timezone': 'Invalid/Timezone'
    }
    
    try:
        response = requests.put(
            f"{BASE_URL}/settings",
            json=invalid_data,
            headers={'Content-Type': 'application/json'}
        )
        
        if response.status_code == 400:
            logger.info("✅ Invalid timezone correctly rejected")
            return True
        else:
            logger.error(f"❌ Invalid timezone not rejected: {response.status_code}")
            return False
            
    except Exception as e:
        logger.error(f"❌ Error testing invalid timezone: {str(e)}")
        return False

def main():
    """Run all settings API tests"""
    logger.info("🧪 Testing Settings API with Timezone Support")
    logger.info("=" * 60)
    
    # Test GET settings
    current_settings = test_get_settings()
    if not current_settings:
        logger.error("❌ Cannot continue without current settings")
        return False
    
    # Test timezone update
    timezone_test = test_update_timezone(current_settings)
    
    # Test invalid timezone
    invalid_test = test_invalid_timezone()
    
    # Summary
    all_passed = all([current_settings, timezone_test, invalid_test])
    
    if all_passed:
        logger.info("🎉 All settings API tests passed!")
    else:
        logger.error("❌ Some settings API tests failed")
    
    return all_passed

if __name__ == "__main__":
    logger.info("Note: This test requires the Flask app to be running")
    logger.info("Start the app and ensure you're logged in before running this test")
    
    success = main()
    sys.exit(0 if success else 1)

























