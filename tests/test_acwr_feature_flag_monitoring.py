#!/usr/bin/env python3
"""
Test script for ACWR Feature Flag Monitoring functionality
Tests the monitoring and logging system
"""

import sys
import os
import logging
from datetime import datetime, timedelta

# Add the app directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from acwr_feature_flag_monitor import ACWRFeatureFlagMonitor, FeatureFlagEvent

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_feature_flag_event_creation():
    """Test FeatureFlagEvent data class"""
    logger.info("Testing FeatureFlagEvent creation...")
    
    event = FeatureFlagEvent(
        timestamp=datetime.now(),
        event_type='access_granted',
        feature_name='enhanced_acwr_calculation',
        user_id=1,
        admin_user_id=None,
        details={'rollout_phase': 'beta'},
        success=True
    )
    
    assert event.event_type == 'access_granted', "Event type should be correct"
    assert event.feature_name == 'enhanced_acwr_calculation', "Feature name should be correct"
    assert event.user_id == 1, "User ID should be correct"
    assert event.success == True, "Success should be correct"
    
    logger.info("✅ FeatureFlagEvent creation test passed")
    return True

def test_monitor_initialization():
    """Test ACWRFeatureFlagMonitor initialization"""
    logger.info("Testing monitor initialization...")
    
    monitor = ACWRFeatureFlagMonitor()
    
    assert monitor is not None, "Monitor should be initialized"
    assert monitor.events == [], "Events list should be empty initially"
    assert monitor.max_events == 1000, "Max events should be set correctly"
    
    logger.info("✅ Monitor initialization test passed")
    return True

def test_log_feature_access():
    """Test logging feature access"""
    logger.info("Testing feature access logging...")
    
    monitor = ACWRFeatureFlagMonitor()
    
    # Test access granted
    monitor.log_feature_access('enhanced_acwr_calculation', 1, True, {'rollout_phase': 'beta'})
    
    assert len(monitor.events) == 1, "Should have one event"
    event = monitor.events[0]
    assert event.event_type == 'access_granted', "Event type should be access_granted"
    assert event.user_id == 1, "User ID should be correct"
    assert event.success == True, "Success should be True"
    
    # Test access denied
    monitor.log_feature_access('enhanced_acwr_calculation', 4, False, {'rollout_phase': 'beta'})
    
    assert len(monitor.events) == 2, "Should have two events"
    event = monitor.events[1]
    assert event.event_type == 'access_denied', "Event type should be access_denied"
    assert event.user_id == 4, "User ID should be correct"
    assert event.success == False, "Success should be False"
    
    logger.info("✅ Feature access logging test passed")
    return True

def test_log_feature_toggle():
    """Test logging feature toggle"""
    logger.info("Testing feature toggle logging...")
    
    monitor = ACWRFeatureFlagMonitor()
    
    monitor.log_feature_toggle('enhanced_acwr_calculation', 1, True, {'admin_action': 'enable'})
    
    assert len(monitor.events) == 1, "Should have one event"
    event = monitor.events[0]
    assert event.event_type == 'flag_toggled', "Event type should be flag_toggled"
    assert event.admin_user_id == 1, "Admin user ID should be correct"
    assert event.success == True, "Success should be True"
    
    logger.info("✅ Feature toggle logging test passed")
    return True

def test_log_error():
    """Test logging errors"""
    logger.info("Testing error logging...")
    
    monitor = ACWRFeatureFlagMonitor()
    
    monitor.log_error('enhanced_acwr_calculation', 1, 'Database connection failed', {'error_code': 'DB_CONN'})
    
    assert len(monitor.events) == 1, "Should have one event"
    event = monitor.events[0]
    assert event.event_type == 'error', "Event type should be error"
    assert event.user_id == 1, "User ID should be correct"
    assert event.success == False, "Success should be False"
    assert 'Database connection failed' in str(event.details), "Error message should be in details"
    
    logger.info("✅ Error logging test passed")
    return True

def test_get_recent_events():
    """Test getting recent events"""
    logger.info("Testing recent events retrieval...")
    
    monitor = ACWRFeatureFlagMonitor()
    
    # Add some events
    monitor.log_feature_access('enhanced_acwr_calculation', 1, True)
    monitor.log_feature_access('enhanced_acwr_calculation', 2, True)
    monitor.log_feature_access('enhanced_acwr_calculation', 3, False)
    
    # Get recent events
    recent_events = monitor.get_recent_events(hours_back=24)
    
    assert len(recent_events) == 3, "Should have 3 recent events"
    assert all('timestamp' in event for event in recent_events), "All events should have timestamps"
    assert all('event_type' in event for event in recent_events), "All events should have event types"
    
    logger.info("✅ Recent events retrieval test passed")
    return True

def test_get_event_statistics():
    """Test getting event statistics"""
    logger.info("Testing event statistics...")
    
    monitor = ACWRFeatureFlagMonitor()
    
    # Clear any existing events first
    monitor.events = []
    
    # Add some events
    monitor.log_feature_access('enhanced_acwr_calculation', 1, True)
    monitor.log_feature_access('enhanced_acwr_calculation', 2, True)
    monitor.log_feature_access('enhanced_acwr_calculation', 3, False)
    monitor.log_feature_toggle('enhanced_acwr_calculation', 1, True)
    
    # Get statistics
    stats = monitor.get_event_statistics(hours_back=24)
    
    assert stats['total_events'] == 4, "Should have 4 total events"
    assert stats['access_granted'] == 2, "Should have 2 access granted events"
    assert stats['access_denied'] == 1, "Should have 1 access denied event"
    assert stats['flags_toggled'] == 1, "Should have 1 flag toggled event"
    assert stats['unique_users'] >= 2, "Should have at least 2 unique users"
    assert stats['success_rate'] == 75.0, "Success rate should be 75%"
    
    logger.info("✅ Event statistics test passed")
    return True

def test_get_user_access_summary():
    """Test getting user access summary"""
    logger.info("Testing user access summary...")
    
    monitor = ACWRFeatureFlagMonitor()
    
    # Add some events for different users
    monitor.log_feature_access('enhanced_acwr_calculation', 1, True)
    monitor.log_feature_access('enhanced_acwr_calculation', 1, True)
    monitor.log_feature_access('enhanced_acwr_calculation', 2, True)
    monitor.log_feature_access('enhanced_acwr_calculation', 2, False)
    
    # Get user summary
    user_summary = monitor.get_user_access_summary(hours_back=24)
    
    assert len(user_summary) == 2, "Should have 2 users in summary"
    assert 1 in user_summary, "User 1 should be in summary"
    assert 2 in user_summary, "User 2 should be in summary"
    
    # Check user 1 stats
    user1_stats = user_summary[1]
    assert user1_stats['access_granted'] == 2, "User 1 should have 2 access granted"
    assert user1_stats['access_denied'] == 0, "User 1 should have 0 access denied"
    assert user1_stats['success_rate'] == 100.0, "User 1 success rate should be 100%"
    
    # Check user 2 stats
    user2_stats = user_summary[2]
    assert user2_stats['access_granted'] == 1, "User 2 should have 1 access granted"
    assert user2_stats['access_denied'] == 1, "User 2 should have 1 access denied"
    assert user2_stats['success_rate'] == 50.0, "User 2 success rate should be 50%"
    
    logger.info("✅ User access summary test passed")
    return True

def test_export_events():
    """Test exporting events as JSON"""
    logger.info("Testing event export...")
    
    monitor = ACWRFeatureFlagMonitor()
    
    # Add some events
    monitor.log_feature_access('enhanced_acwr_calculation', 1, True)
    monitor.log_feature_access('enhanced_acwr_calculation', 2, False)
    
    # Export events
    events_json = monitor.export_events(hours_back=24)
    
    assert events_json != "[]", "Export should not be empty"
    assert 'enhanced_acwr_calculation' in events_json, "Export should contain feature name"
    assert 'access_granted' in events_json, "Export should contain access granted event"
    assert 'access_denied' in events_json, "Export should contain access denied event"
    
    logger.info("✅ Event export test passed")
    return True

def test_max_events_limit():
    """Test that max events limit is enforced"""
    logger.info("Testing max events limit...")
    
    monitor = ACWRFeatureFlagMonitor()
    monitor.max_events = 5  # Set small limit for testing
    
    # Add more events than the limit
    for i in range(10):
        monitor.log_feature_access('enhanced_acwr_calculation', i, True)
    
    assert len(monitor.events) == 5, "Should only keep 5 events"
    
    # Check that the most recent events are kept
    user_ids = [event.user_id for event in monitor.events]
    assert user_ids == [5, 6, 7, 8, 9], "Should keep the most recent 5 events"
    
    logger.info("✅ Max events limit test passed")
    return True

def run_all_tests():
    """Run all monitoring tests"""
    logger.info("=" * 60)
    logger.info("ACWR Feature Flag Monitoring Test Suite")
    logger.info("=" * 60)
    
    tests = [
        ("FeatureFlagEvent Creation", test_feature_flag_event_creation),
        ("Monitor Initialization", test_monitor_initialization),
        ("Feature Access Logging", test_log_feature_access),
        ("Feature Toggle Logging", test_log_feature_toggle),
        ("Error Logging", test_log_error),
        ("Recent Events Retrieval", test_get_recent_events),
        ("Event Statistics", test_get_event_statistics),
        ("User Access Summary", test_get_user_access_summary),
        ("Event Export", test_export_events),
        ("Max Events Limit", test_max_events_limit)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        logger.info(f"\n--- {test_name} ---")
        try:
            if test_func():
                passed += 1
                logger.info(f"✅ {test_name} PASSED")
            else:
                logger.error(f"❌ {test_name} FAILED")
        except Exception as e:
            logger.error(f"❌ {test_name} FAILED with exception: {str(e)}")
    
    logger.info("\n" + "=" * 60)
    logger.info(f"Test Results: {passed}/{total} tests passed")
    logger.info("=" * 60)
    
    if passed == total:
        logger.info("🎉 All tests passed! ACWR Feature Flag Monitoring is working correctly.")
        return True
    else:
        logger.error(f"⚠️  {total - passed} tests failed. Please check the errors above.")
        return False

def main():
    """Run the test suite"""
    success = run_all_tests()
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
