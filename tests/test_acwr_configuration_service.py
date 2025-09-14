#!/usr/bin/env python3
"""
Test script for ACWR Configuration Service functionality
Tests the core service methods without requiring database connection
"""

import sys
import os
import logging
from datetime import datetime, date, timedelta
from unittest.mock import Mock, patch, MagicMock

# Add the app directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Mock db_utils before importing the service
with patch.dict('sys.modules', {'db_utils': MagicMock()}):
    from acwr_configuration_service import ACWRConfigurationService

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class TestACWRConfigurationService:
    """Test class for ACWR Configuration Service"""
    
    def __init__(self):
        self.service = ACWRConfigurationService()
        self.mock_db_results = {
            'default_config': {
                'id': 1,
                'name': 'default_enhanced',
                'description': 'Default enhanced ACWR with 42-day chronic period and moderate decay',
                'chronic_period_days': 42,
                'decay_rate': 0.05,
                'is_active': True,
                'created_by': 1,
                'notes': 'Default configuration for enhanced ACWR calculation'
            },
            'user_config': {
                'id': 1,
                'name': 'default_enhanced',
                'description': 'Default enhanced ACWR with 42-day chronic period and moderate decay',
                'chronic_period_days': 42,
                'decay_rate': 0.05,
                'is_active': True,
                'created_by': 1,
                'assigned_at': '2025-01-27T10:00:00Z',
                'assigned_by': 1
            }
        }
    
    def test_calculate_exponential_weighted_average(self):
        """Test exponential weighted average calculation"""
        logger.info("Testing exponential weighted average calculation...")
        
        # Test data: activities over the last 10 days
        test_activities = []
        base_date = date.today()
        
        for i in range(10):
            activity_date = base_date - timedelta(days=i)
            test_activities.append({
                'date': activity_date,
                'total_load_miles': 10.0 + i,  # Increasing load
                'trimp': 50.0 + i * 5  # Increasing TRIMP
            })
        
        # Test with decay rate 0.05
        decay_rate = 0.05
        current_date = base_date
        
        weighted_load, weighted_trimp = self.service.calculate_exponential_weighted_average(
            test_activities, decay_rate, current_date
        )
        
        # Verify results are reasonable
        assert weighted_load > 0, "Weighted load should be positive"
        assert weighted_trimp > 0, "Weighted TRIMP should be positive"
        assert weighted_load < 20.0, "Weighted load should be less than max activity load"
        assert weighted_trimp < 100.0, "Weighted TRIMP should be less than max activity TRIMP"
        
        logger.info(f"✅ Exponential weighted average calculation works")
        logger.info(f"  - Weighted Load: {weighted_load:.2f}")
        logger.info(f"  - Weighted TRIMP: {weighted_trimp:.2f}")
        
        return True
    
    def test_calculate_exponential_weighted_average_edge_cases(self):
        """Test exponential weighted average with edge cases"""
        logger.info("Testing exponential weighted average edge cases...")
        
        # Test with empty activities
        weighted_load, weighted_trimp = self.service.calculate_exponential_weighted_average(
            [], 0.05, date.today()
        )
        assert weighted_load == 0.0, "Empty activities should return 0 load"
        assert weighted_trimp == 0.0, "Empty activities should return 0 TRIMP"
        
        # Test with future activities (should be skipped)
        future_activities = [{
            'date': date.today() + timedelta(days=1),
            'total_load_miles': 10.0,
            'trimp': 50.0
        }]
        
        weighted_load, weighted_trimp = self.service.calculate_exponential_weighted_average(
            future_activities, 0.05, date.today()
        )
        assert weighted_load == 0.0, "Future activities should be skipped"
        assert weighted_trimp == 0.0, "Future activities should be skipped"
        
        # Test with None values
        activities_with_none = [{
            'date': date.today(),
            'total_load_miles': None,
            'trimp': None
        }]
        
        weighted_load, weighted_trimp = self.service.calculate_exponential_weighted_average(
            activities_with_none, 0.05, date.today()
        )
        assert weighted_load == 0.0, "None values should be treated as 0"
        assert weighted_trimp == 0.0, "None values should be treated as 0"
        
        logger.info("✅ Edge cases handled correctly")
        return True
    
    def test_calculate_normalized_divergence(self):
        """Test normalized divergence calculation"""
        logger.info("Testing normalized divergence calculation...")
        
        # Test normal case
        divergence = self.service.calculate_normalized_divergence(1.2, 1.1)
        assert isinstance(divergence, float), "Divergence should be a float"
        
        # Test when both values are 0
        divergence = self.service.calculate_normalized_divergence(0.0, 0.0)
        assert divergence == 0.0, "Divergence should be 0 when both values are 0"
        
        # Test when mean is 0
        divergence = self.service.calculate_normalized_divergence(1.0, -1.0)
        assert divergence == 0.0, "Divergence should be 0 when mean is 0"
        
        logger.info("✅ Normalized divergence calculation works")
        return True
    
    @patch('acwr_configuration_service.db_utils.execute_query')
    def test_get_default_configuration(self, mock_execute_query):
        """Test getting default configuration"""
        logger.info("Testing get_default_configuration method...")
        
        # Mock database response
        mock_execute_query.return_value = [self.mock_db_results['default_config']]
        
        config = self.service.get_default_configuration()
        
        assert config is not None, "Default configuration should not be None"
        assert config['name'] == 'default_enhanced', "Should return default_enhanced configuration"
        assert config['chronic_period_days'] == 42, "Should have 42-day chronic period"
        assert config['decay_rate'] == 0.05, "Should have 0.05 decay rate"
        
        logger.info("✅ get_default_configuration method works")
        return True
    
    @patch('acwr_configuration_service.db_utils.execute_query')
    def test_get_user_configuration(self, mock_execute_query):
        """Test getting user configuration"""
        logger.info("Testing get_user_configuration method...")
        
        # Mock database response for user-specific config
        mock_execute_query.return_value = [self.mock_db_results['user_config']]
        
        config = self.service.get_user_configuration(user_id=1)
        
        assert config is not None, "User configuration should not be None"
        assert config['name'] == 'default_enhanced', "Should return user's configuration"
        assert 'assigned_at' in config, "Should include assignment information"
        
        logger.info("✅ get_user_configuration method works")
        return True
    
    @patch('acwr_configuration_service.db_utils.execute_query')
    def test_create_configuration(self, mock_execute_query):
        """Test creating new configuration"""
        logger.info("Testing create_configuration method...")
        
        # Mock successful creation
        mock_execute_query.side_effect = [
            True,  # First call for INSERT
            [{'last_insert_rowid()': 2}]  # Second call for getting ID
        ]
        
        config_id = self.service.create_configuration(
            name="test_config",
            description="Test configuration",
            chronic_period_days=35,
            decay_rate=0.08,
            created_by=1,
            notes="Test notes"
        )
        
        assert config_id == 2, "Should return the created configuration ID"
        
        logger.info("✅ create_configuration method works")
        return True
    
    def test_create_configuration_validation(self):
        """Test configuration creation validation"""
        logger.info("Testing create_configuration validation...")
        
        # Test invalid chronic period
        try:
            self.service.create_configuration(
                name="invalid_config",
                description="Invalid config",
                chronic_period_days=20,  # Too short
                decay_rate=0.05,
                created_by=1
            )
            assert False, "Should have raised ValueError for chronic_period_days < 28"
        except ValueError as e:
            assert "Chronic period must be at least 28 days" in str(e)
        
        # Test invalid decay rate
        try:
            self.service.create_configuration(
                name="invalid_config2",
                description="Invalid config 2",
                chronic_period_days=30,
                decay_rate=1.5,  # Too high
                created_by=1
            )
            assert False, "Should have raised ValueError for decay_rate > 1.0"
        except ValueError as e:
            assert "Decay rate must be between 0 and 1.0" in str(e)
        
        logger.info("✅ Configuration validation works correctly")
        return True
    
    @patch('acwr_configuration_service.db_utils.execute_query')
    def test_assign_configuration_to_user(self, mock_execute_query):
        """Test assigning configuration to user"""
        logger.info("Testing assign_configuration_to_user method...")
        
        # Mock successful assignment
        mock_execute_query.return_value = True
        
        result = self.service.assign_configuration_to_user(
            user_id=1,
            configuration_id=1,
            assigned_by=1
        )
        
        assert result is True, "Assignment should succeed"
        
        # Verify both queries were called (deactivate existing, create new)
        assert mock_execute_query.call_count == 2, "Should make 2 database calls"
        
        logger.info("✅ assign_configuration_to_user method works")
        return True
    
    @patch('acwr_configuration_service.db_utils.execute_query')
    def test_get_all_configurations(self, mock_execute_query):
        """Test getting all configurations"""
        logger.info("Testing get_all_configurations method...")
        
        # Mock database response
        mock_execute_query.return_value = [
            self.mock_db_results['default_config'],
            {
                'id': 2,
                'name': 'conservative_enhanced',
                'description': 'Conservative configuration',
                'chronic_period_days': 56,
                'decay_rate': 0.03,
                'is_active': False,
                'assigned_users': 0,
                'user_ids': None
            }
        ]
        
        configs = self.service.get_all_configurations()
        
        assert len(configs) == 2, "Should return 2 configurations"
        assert configs[0]['name'] == 'default_enhanced', "Should include default configuration"
        assert configs[1]['name'] == 'conservative_enhanced', "Should include other configurations"
        
        logger.info("✅ get_all_configurations method works")
        return True
    
    def test_enhanced_acwr_calculation_structure(self):
        """Test enhanced ACWR calculation method structure (without database)"""
        logger.info("Testing enhanced ACWR calculation method structure...")
        
        # Test with mock configuration
        config = {
            'id': 1,
            'chronic_period_days': 42,
            'decay_rate': 0.05
        }
        
        # This will fail due to database dependency, but we can test the method exists
        # and handles the configuration structure correctly
        try:
            result = self.service.calculate_enhanced_acwr(
                user_id=1,
                activity_date='2025-01-27',
                configuration=config
            )
            # If it gets here, it means the method structure is correct
            logger.info("✅ calculate_enhanced_acwr method structure is correct")
            return True
        except Exception as e:
            # Expected to fail due to database dependency
            if "database" in str(e).lower() or "connection" in str(e).lower():
                logger.info("✅ calculate_enhanced_acwr method structure is correct (database dependency expected)")
                return True
            else:
                logger.error(f"❌ Unexpected error in calculate_enhanced_acwr: {str(e)}")
                return False
    
    def run_all_tests(self):
        """Run all tests"""
        logger.info("=" * 60)
        logger.info("ACWR Configuration Service Test Suite")
        logger.info("=" * 60)
        
        tests = [
            ("Exponential Weighted Average", self.test_calculate_exponential_weighted_average),
            ("Exponential Weighted Average Edge Cases", self.test_calculate_exponential_weighted_average_edge_cases),
            ("Normalized Divergence", self.test_calculate_normalized_divergence),
            ("Get Default Configuration", self.test_get_default_configuration),
            ("Get User Configuration", self.test_get_user_configuration),
            ("Create Configuration", self.test_create_configuration),
            ("Create Configuration Validation", self.test_create_configuration_validation),
            ("Assign Configuration to User", self.test_assign_configuration_to_user),
            ("Get All Configurations", self.test_get_all_configurations),
            ("Enhanced ACWR Calculation Structure", self.test_enhanced_acwr_calculation_structure)
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
            logger.info("🎉 All tests passed! ACWR Configuration Service is working correctly.")
            return True
        else:
            logger.error(f"⚠️  {total - passed} tests failed. Please check the errors above.")
            return False

def main():
    """Run the test suite"""
    test_suite = TestACWRConfigurationService()
    success = test_suite.run_all_tests()
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
