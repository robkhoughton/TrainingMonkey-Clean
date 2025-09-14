#!/usr/bin/env python3
"""
Test script for ACWR Migration Integrity and Rollback System
Tests data integrity validation and rollback capabilities
"""

import sys
import os
import logging
import unittest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
import time
import json

# Add the app directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Mock database dependencies before importing
with patch.dict('sys.modules', {
    'db_utils': Mock(),
    'psycopg2': Mock(),
    'psycopg2.extras': Mock()
}):
    from acwr_migration_integrity import (
        ACWRMigrationIntegrityValidator, ValidationLevel, ValidationResult,
        IntegrityCheckpoint, RollbackScope
    )
    from acwr_migration_rollback import (
        ACWRMigrationRollbackManager, RollbackImpact, RollbackPlan, RollbackOperation
    )

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class TestACWRMigrationIntegrityValidator(unittest.TestCase):
    """Test cases for ACWR Migration Integrity Validator"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.validator = ACWRMigrationIntegrityValidator()
        
        # Mock database connections
        self.mock_conn = Mock()
        self.mock_cursor = Mock()
        
        # Create a proper context manager mock
        cursor_context = Mock()
        cursor_context.__enter__ = Mock(return_value=self.mock_cursor)
        cursor_context.__exit__ = Mock(return_value=None)
        self.mock_conn.cursor.return_value = cursor_context
        
    def test_validator_initialization(self):
        """Test validator initialization"""
        logger.info("Testing validator initialization...")
        
        # Test validation rules
        self.assertIn(ValidationLevel.BASIC, self.validator.validation_rules)
        self.assertIn(ValidationLevel.STANDARD, self.validator.validation_rules)
        self.assertIn(ValidationLevel.STRICT, self.validator.validation_rules)
        self.assertIn(ValidationLevel.PARANOID, self.validator.validation_rules)
        
        # Test validation functions exist
        self.assertIsNotNone(self.validator.validation_rules[ValidationLevel.BASIC])
        self.assertIsNotNone(self.validator.validation_rules[ValidationLevel.STANDARD])
        self.assertIsNotNone(self.validator.validation_rules[ValidationLevel.STRICT])
        self.assertIsNotNone(self.validator.validation_rules[ValidationLevel.PARANOID])
        
        logger.info("✅ Validator initialization test passed")
    
    def test_basic_validation(self):
        """Test basic validation functionality"""
        logger.info("Testing basic validation...")
        
        # Mock database responses
        self.mock_cursor.fetchone.side_effect = [
            {'count': 1000},  # Enhanced calculations count
            {'count': 0},     # Null values count
            {'count': 5},     # Invalid ACWR ratios
            {'count': 0}      # Negative loads
        ]
        
        # Mock db_utils.get_db_connection
        with patch('acwr_migration_integrity.db_utils.get_db_connection') as mock_get_conn:
            mock_get_conn.return_value.__enter__.return_value = self.mock_conn
            mock_get_conn.return_value.__exit__.return_value = None
            
            result = self.validator._basic_validation("test_migration", 1)
        
        # Verify results
        self.assertIn('errors', result)
        self.assertIn('warnings', result)
        self.assertIn('validated_count', result)
        self.assertIn('failed_count', result)
        
        # Should have warnings for invalid ACWR ratios
        self.assertEqual(len(result['warnings']), 1)
        self.assertIn('invalid ACWR ratios', result['warnings'][0])
        
        logger.info("✅ Basic validation test passed")
    
    def test_standard_validation(self):
        """Test standard validation functionality"""
        logger.info("Testing standard validation...")
        
        # Mock database responses for standard validation
        self.mock_cursor.fetchone.side_effect = [
            {'count': 1000},  # Enhanced calculations count (from basic)
            {'count': 0},     # Null values count (from basic)
            {'count': 5},     # Invalid ACWR ratios (from basic)
            {'count': 0},     # Negative loads (from basic)
            None,             # No duplicates
            {'count': 0},     # No orphaned records
            {'count': 1}      # Configuration exists
        ]
        self.mock_cursor.fetchall.side_effect = [
            [],  # No duplicates
            [{'configuration_id': 1}],  # Configurations
            []   # Recent calculations
        ]
        
        with patch('acwr_migration_integrity.db_utils.get_db_connection') as mock_get_conn:
            mock_get_conn.return_value.__enter__.return_value = self.mock_conn
            mock_get_conn.return_value.__exit__.return_value = None
            
            result = self.validator._standard_validation("test_migration", 1)
        
        # Verify results
        self.assertIn('errors', result)
        self.assertIn('warnings', result)
        self.assertIn('validated_count', result)
        self.assertIn('failed_count', result)
        
        logger.info("✅ Standard validation test passed")
    
    def test_validation_result_creation(self):
        """Test validation result creation"""
        logger.info("Testing validation result creation...")
        
        # Create a validation result
        result = ValidationResult(
            is_valid=True,
            validation_level=ValidationLevel.STANDARD,
            errors=[],
            warnings=['Test warning'],
            validated_count=1000,
            failed_count=0,
            validation_time=1.5,
            checksum='test_checksum_123'
        )
        
        # Verify result structure
        self.assertTrue(result.is_valid)
        self.assertEqual(result.validation_level, ValidationLevel.STANDARD)
        self.assertEqual(len(result.errors), 0)
        self.assertEqual(len(result.warnings), 1)
        self.assertEqual(result.validated_count, 1000)
        self.assertEqual(result.failed_count, 0)
        self.assertEqual(result.validation_time, 1.5)
        self.assertEqual(result.checksum, 'test_checksum_123')
        
        logger.info("✅ Validation result creation test passed")
    
    def test_checksum_calculation(self):
        """Test checksum calculation"""
        logger.info("Testing checksum calculation...")
        
        # Mock database response
        self.mock_cursor.fetchall.return_value = [
            {'activity_id': 1, 'configuration_id': 1, 'acwr_ratio': 1.2, 
             'acute_load': 80.5, 'chronic_load': 67.1, 'calculation_date': datetime.now()},
            {'activity_id': 2, 'configuration_id': 1, 'acwr_ratio': 1.1, 
             'acute_load': 75.0, 'chronic_load': 68.2, 'calculation_date': datetime.now()}
        ]
        
        with patch('acwr_migration_integrity.db_utils.get_db_connection') as mock_get_conn:
            mock_get_conn.return_value.__enter__.return_value = self.mock_conn
            mock_get_conn.return_value.__exit__.return_value = None
            
            checksum = self.validator._calculate_data_checksum("test_migration", 1)
        
        # Verify checksum is generated
        self.assertIsNotNone(checksum)
        self.assertIsInstance(checksum, str)
        self.assertEqual(len(checksum), 64)  # SHA256 hex length
        
        logger.info("✅ Checksum calculation test passed")

class TestACWRMigrationRollbackManager(unittest.TestCase):
    """Test cases for ACWR Migration Rollback Manager"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.rollback_manager = ACWRMigrationRollbackManager()
        
        # Mock database connections
        self.mock_conn = Mock()
        self.mock_cursor = Mock()
        
        # Create a proper context manager mock
        cursor_context = Mock()
        cursor_context.__enter__ = Mock(return_value=self.mock_cursor)
        cursor_context.__exit__ = Mock(return_value=None)
        self.mock_conn.cursor.return_value = cursor_context
        
    def test_rollback_manager_initialization(self):
        """Test rollback manager initialization"""
        logger.info("Testing rollback manager initialization...")
        
        # Test initial state
        self.assertIsNotNone(self.rollback_manager.integrity_validator)
        self.assertIsInstance(self.rollback_manager.active_rollbacks, dict)
        self.assertIsInstance(self.rollback_manager.rollback_history, list)
        
        # Test initial counts
        self.assertEqual(len(self.rollback_manager.active_rollbacks), 0)
        self.assertEqual(len(self.rollback_manager.rollback_history), 0)
        
        logger.info("✅ Rollback manager initialization test passed")
    
    def test_rollback_impact_analysis(self):
        """Test rollback impact analysis"""
        logger.info("Testing rollback impact analysis...")
        
        # Mock database responses
        self.mock_cursor.fetchone.side_effect = [
            {'users': 1, 'activities': 1000, 'configurations': 1}  # Affected counts
        ]
        
        with patch('acwr_migration_rollback.db_utils.get_db_connection') as mock_get_conn:
            mock_get_conn.return_value.__enter__.return_value = self.mock_conn
            mock_get_conn.return_value.__exit__.return_value = None
            
            impact = self.rollback_manager.analyze_rollback_impact(
                "test_migration", 1, RollbackScope.USER_MIGRATION
            )
        
        # Verify impact analysis
        self.assertIsInstance(impact, RollbackImpact)
        self.assertEqual(impact.affected_users, 1)
        self.assertEqual(impact.affected_activities, 1000)
        self.assertEqual(impact.affected_configurations, 1)
        self.assertIn(impact.data_loss_risk, ['low', 'medium', 'high', 'critical'])
        self.assertIn(impact.rollback_complexity, ['simple', 'moderate', 'complex', 'extreme'])
        self.assertIsInstance(impact.estimated_downtime, int)
        self.assertIsInstance(impact.backup_available, bool)
        
        logger.info("✅ Rollback impact analysis test passed")
    
    def test_rollback_plan_creation(self):
        """Test rollback plan creation"""
        logger.info("Testing rollback plan creation...")
        
        # Mock database responses for impact analysis
        self.mock_cursor.fetchone.side_effect = [
            {'users': 1, 'activities': 1000, 'configurations': 1},  # Affected counts
            {'count': 1}  # Backup available
        ]
        
        with patch('acwr_migration_rollback.db_utils.get_db_connection') as mock_get_conn:
            mock_get_conn.return_value.__enter__.return_value = self.mock_conn
            mock_get_conn.return_value.__exit__.return_value = None
            
            plan = self.rollback_manager.create_rollback_plan(
                "test_migration", 1, RollbackScope.USER_MIGRATION, 
                "Test rollback", 1
            )
        
        # Verify rollback plan
        self.assertIsInstance(plan, RollbackPlan)
        self.assertIsNotNone(plan.plan_id)
        self.assertEqual(plan.rollback_scope, RollbackScope.USER_MIGRATION)
        self.assertEqual(plan.target_migration_id, "test_migration")
        self.assertEqual(plan.target_user_id, 1)
        self.assertIsInstance(plan.steps, list)
        self.assertGreater(len(plan.steps), 0)
        self.assertIsInstance(plan.estimated_duration, int)
        self.assertIn(plan.risk_level, ['low', 'medium', 'high', 'critical'])
        self.assertIsInstance(plan.prerequisites, list)
        self.assertIsInstance(plan.rollback_data, dict)
        
        logger.info("✅ Rollback plan creation test passed")
    
    def test_rollback_operation_creation(self):
        """Test rollback operation creation"""
        logger.info("Testing rollback operation creation...")
        
        # Create a rollback operation
        rollback_op = RollbackOperation(
            rollback_id="test_rollback_123",
            migration_id="test_migration",
            user_id=1,
            scope=RollbackScope.USER_MIGRATION,
            reason="Test rollback operation",
            initiated_by=1,
            timestamp=datetime.now(),
            status='pending',
            affected_records=0,
            rollback_data={'test': 'data'},
            error_log=[]
        )
        
        # Verify rollback operation structure
        self.assertEqual(rollback_op.rollback_id, "test_rollback_123")
        self.assertEqual(rollback_op.migration_id, "test_migration")
        self.assertEqual(rollback_op.user_id, 1)
        self.assertEqual(rollback_op.scope, RollbackScope.USER_MIGRATION)
        self.assertEqual(rollback_op.reason, "Test rollback operation")
        self.assertEqual(rollback_op.initiated_by, 1)
        self.assertEqual(rollback_op.status, 'pending')
        self.assertEqual(rollback_op.affected_records, 0)
        self.assertIsInstance(rollback_op.rollback_data, dict)
        self.assertIsInstance(rollback_op.error_log, list)
        
        logger.info("✅ Rollback operation creation test passed")
    
    def test_rollback_scope_assessment(self):
        """Test rollback scope assessment"""
        logger.info("Testing rollback scope assessment...")
        
        # Test different rollback scopes
        scopes = [
            RollbackScope.SINGLE_BATCH,
            RollbackScope.USER_MIGRATION,
            RollbackScope.CONFIGURATION,
            RollbackScope.FULL_SYSTEM
        ]
        
        for scope in scopes:
            # Mock database responses
            if scope == RollbackScope.SINGLE_BATCH:
                affected_users, affected_activities, affected_configurations = 1, 1000, 1
            elif scope == RollbackScope.USER_MIGRATION:
                self.mock_cursor.fetchone.return_value = {'users': 1, 'activities': 1000, 'configurations': 1}
                affected_users, affected_activities, affected_configurations = 1, 1000, 1
            elif scope == RollbackScope.CONFIGURATION:
                self.mock_cursor.fetchone.side_effect = [
                    {'configuration_id': 1},  # Migration config
                    {'users': 5, 'activities': 5000, 'configurations': 1}  # Affected counts
                ]
                affected_users, affected_activities, affected_configurations = 5, 5000, 1
            else:  # FULL_SYSTEM
                self.mock_cursor.fetchone.return_value = {'users': 100, 'activities': 50000, 'configurations': 5}
                affected_users, affected_activities, affected_configurations = 100, 50000, 5
            
            with patch('acwr_migration_rollback.db_utils.get_db_connection') as mock_get_conn:
                mock_get_conn.return_value.__enter__.return_value = self.mock_conn
                mock_get_conn.return_value.__exit__.return_value = None
                
                impact = self.rollback_manager.analyze_rollback_impact(
                    "test_migration", 1, scope
                )
            
            # Verify impact assessment
            self.assertEqual(impact.affected_users, affected_users)
            self.assertEqual(impact.affected_activities, affected_activities)
            self.assertEqual(impact.affected_configurations, affected_configurations)
            
            # Verify risk assessment
            if scope == RollbackScope.FULL_SYSTEM:
                self.assertEqual(impact.data_loss_risk, 'critical')
            elif scope == RollbackScope.CONFIGURATION and affected_activities > 10000:
                self.assertIn(impact.data_loss_risk, ['medium', 'high'])
            else:
                self.assertIn(impact.data_loss_risk, ['low', 'medium'])
        
        logger.info("✅ Rollback scope assessment test passed")
    
    def test_rollback_steps_creation(self):
        """Test rollback steps creation"""
        logger.info("Testing rollback steps creation...")
        
        # Test different rollback scopes
        scopes = [
            RollbackScope.SINGLE_BATCH,
            RollbackScope.USER_MIGRATION,
            RollbackScope.CONFIGURATION,
            RollbackScope.FULL_SYSTEM
        ]
        
        for scope in scopes:
            steps = self.rollback_manager._create_rollback_steps("test_migration", 1, scope)
            
            # Verify steps structure
            self.assertIsInstance(steps, list)
            self.assertGreater(len(steps), 0)
            
            # Verify common steps
            step_ids = [step['step_id'] for step in steps]
            self.assertIn('create_backup', step_ids)
            self.assertIn('validate_current_state', step_ids)
            self.assertIn('validate_rollback_result', step_ids)
            self.assertIn('update_migration_status', step_ids)
            
            # Verify scope-specific steps
            if scope == RollbackScope.SINGLE_BATCH:
                self.assertIn('rollback_single_batch', step_ids)
            elif scope == RollbackScope.USER_MIGRATION:
                self.assertIn('rollback_user_migration', step_ids)
            elif scope == RollbackScope.CONFIGURATION:
                self.assertIn('rollback_configuration', step_ids)
            else:  # FULL_SYSTEM
                self.assertIn('rollback_full_system', step_ids)
            
            # Verify step structure
            for step in steps:
                self.assertIn('step_id', step)
                self.assertIn('description', step)
                self.assertIn('critical', step)
                self.assertIn('estimated_duration', step)
                self.assertIsInstance(step['critical'], bool)
                self.assertIsInstance(step['estimated_duration'], int)
        
        logger.info("✅ Rollback steps creation test passed")

def run_integrity_rollback_tests():
    """Run all integrity and rollback tests"""
    logger.info("=" * 60)
    logger.info("ACWR Migration Integrity and Rollback Test Suite")
    logger.info("=" * 60)
    
    # Create test suite
    test_suite = unittest.TestLoader().loadTestsFromTestCase(TestACWRMigrationIntegrityValidator)
    test_suite.addTests(unittest.TestLoader().loadTestsFromTestCase(TestACWRMigrationRollbackManager))
    
    # Run tests
    test_runner = unittest.TextTestRunner(verbosity=2)
    result = test_runner.run(test_suite)
    
    # Log results
    logger.info("=" * 60)
    logger.info(f"Test Results: {result.testsRun} tests run")
    logger.info(f"Failures: {len(result.failures)}")
    logger.info(f"Errors: {len(result.errors)}")
    logger.info("=" * 60)
    
    if result.wasSuccessful():
        logger.info("🎉 All integrity and rollback tests passed!")
        return True
    else:
        logger.error("⚠️  Some integrity and rollback tests failed.")
        for failure in result.failures:
            logger.error(f"FAILURE: {failure[0]}")
            logger.error(f"Details: {failure[1]}")
        for error in result.errors:
            logger.error(f"ERROR: {error[0]}")
            logger.error(f"Details: {error[1]}")
        return False

def main():
    """Run the test suite"""
    success = run_integrity_rollback_tests()
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
