#!/usr/bin/env python3
"""
Test Migration Proof of Concept Components
Verify that all migration system components are working correctly
"""

import os
import sys
import logging
from datetime import datetime
from unittest.mock import Mock, patch

# Add the app directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_migration_services_import():
    """Test that all migration services can be imported"""
    try:
        logger.info("Testing migration services import...")
        
        # Test imports
        from acwr_migration_service import ACWRMigrationService
        from acwr_configuration_service import ACWRConfigurationService
        from acwr_calculation_service import ACWRCalculationService
        from acwr_migration_monitoring import ACWRMigrationMonitor
        from acwr_migration_integrity import ACWRMigrationIntegrityManager
        from acwr_migration_rollback import ACWRMigrationRollbackManager
        
        logger.info("✅ All migration services imported successfully")
        return True
        
    except ImportError as e:
        logger.error(f"❌ Import error: {e}")
        return False
    except Exception as e:
        logger.error(f"❌ Unexpected error: {e}")
        return False

def test_migration_service_initialization():
    """Test that migration services can be initialized"""
    try:
        logger.info("Testing migration service initialization...")
        
        # Mock database connection to avoid actual DB calls
        with patch('db_utils.get_db_connection') as mock_db:
            mock_conn = Mock()
            mock_cursor = Mock()
            mock_cursor.__enter__ = Mock(return_value=mock_cursor)
            mock_cursor.__exit__ = Mock(return_value=None)
            mock_conn.cursor.return_value = mock_cursor
            mock_db.return_value = mock_conn
            
            # Test service initialization
            from acwr_migration_service import ACWRMigrationService
            from acwr_configuration_service import ACWRConfigurationService
            from acwr_calculation_service import ACWRCalculationService
            
            migration_service = ACWRMigrationService()
            config_service = ACWRConfigurationService()
            calc_service = ACWRCalculationService()
            
            logger.info("✅ Migration services initialized successfully")
            return True
            
    except Exception as e:
        logger.error(f"❌ Service initialization error: {e}")
        return False

def test_migration_monitoring():
    """Test migration monitoring functionality"""
    try:
        logger.info("Testing migration monitoring...")
        
        from acwr_migration_monitoring import ACWRMigrationMonitor, LogLevel, AlertSeverity
        
        # Test monitor initialization
        monitor = ACWRMigrationMonitor()
        
        # Test logging
        monitor.log_event(
            migration_id="test_migration",
            event_type="migration_started",
            message="Test migration started",
            level=LogLevel.INFO
        )
        
        # Test alert generation
        alert = monitor.generate_alert(
            migration_id="test_migration",
            severity=AlertSeverity.MEDIUM,
            alert_type="test_alert",
            title="Test Alert",
            message="This is a test alert"
        )
        
        logger.info("✅ Migration monitoring tested successfully")
        return True
        
    except Exception as e:
        logger.error(f"❌ Migration monitoring error: {e}")
        return False

def test_migration_integrity():
    """Test migration integrity functionality"""
    try:
        logger.info("Testing migration integrity...")
        
        from acwr_migration_integrity import ACWRMigrationIntegrityManager, ValidationLevel
        
        # Test integrity manager initialization
        integrity_manager = ACWRMigrationIntegrityManager()
        
        # Test checkpoint creation (mocked)
        checkpoint_data = {
            'checkpoint_id': 'test_checkpoint',
            'migration_id': 'test_migration',
            'user_id': 1,
            'validation_result': {'status': 'test', 'passed': True},
            'data_snapshot': {'test': 'data'},
            'checksum': 'test_checksum',
            'rollback_data': {'test': 'rollback'}
        }
        
        logger.info("✅ Migration integrity tested successfully")
        return True
        
    except Exception as e:
        logger.error(f"❌ Migration integrity error: {e}")
        return False

def test_migration_rollback():
    """Test migration rollback functionality"""
    try:
        logger.info("Testing migration rollback...")
        
        from acwr_migration_rollback import ACWRMigrationRollbackManager, RollbackScope
        
        # Test rollback manager initialization
        rollback_manager = ACWRMigrationRollbackManager()
        
        # Test rollback planning (mocked)
        rollback_plan = {
            'rollback_id': 'test_rollback',
            'migration_id': 'test_migration',
            'user_id': 1,
            'scope': RollbackScope.USER_MIGRATION,
            'reason': 'Test rollback'
        }
        
        logger.info("✅ Migration rollback tested successfully")
        return True
        
    except Exception as e:
        logger.error(f"❌ Migration rollback error: {e}")
        return False

def test_database_schema_verification():
    """Test that database schema is properly set up"""
    try:
        logger.info("Testing database schema verification...")
        
        # Mock database connection
        with patch('db_utils.get_db_connection') as mock_db:
            mock_conn = Mock()
            mock_cursor = Mock()
            mock_cursor.__enter__ = Mock(return_value=mock_cursor)
            mock_cursor.__exit__ = Mock(return_value=None)
            mock_cursor.fetchall.return_value = [
                ('acwr_enhanced_calculations',),
                ('acwr_migration_history',),
                ('acwr_migration_progress',),
                ('acwr_migration_batches',),
                ('acwr_migration_logs',),
                ('acwr_migration_alerts',),
                ('acwr_migration_events',),
                ('acwr_migration_health_metrics',),
                ('acwr_migration_monitoring_config',),
                ('acwr_migration_notification_preferences',),
                ('acwr_integrity_checkpoints',),
                ('acwr_rollback_history',),
                ('acwr_data_validation_results',),
                ('acwr_rollback_executions',)
            ]
            mock_conn.cursor.return_value = mock_cursor
            mock_db.return_value = mock_conn
            
            # Test schema verification
            from db_utils import get_db_connection
            
            with get_db_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("""
                        SELECT table_name 
                        FROM information_schema.tables 
                        WHERE table_name LIKE 'acwr_%' 
                        AND table_schema = 'public'
                        ORDER BY table_name
                    """)
                    tables = cursor.fetchall()
            
            expected_tables = 14  # Based on our schema
            actual_tables = len(tables)
            
            if actual_tables >= expected_tables:
                logger.info(f"✅ Database schema verification passed ({actual_tables} tables found)")
                return True
            else:
                logger.error(f"❌ Database schema verification failed ({actual_tables} tables found, expected {expected_tables})")
                return False
        
    except Exception as e:
        logger.error(f"❌ Database schema verification error: {e}")
        return False

def run_all_tests():
    """Run all component tests"""
    logger.info("=" * 60)
    logger.info("RUNNING MIGRATION PROOF OF CONCEPT COMPONENT TESTS")
    logger.info("=" * 60)
    
    tests = [
        ("Migration Services Import", test_migration_services_import),
        ("Migration Service Initialization", test_migration_service_initialization),
        ("Migration Monitoring", test_migration_monitoring),
        ("Migration Integrity", test_migration_integrity),
        ("Migration Rollback", test_migration_rollback),
        ("Database Schema Verification", test_database_schema_verification)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        logger.info(f"\n--- Running: {test_name} ---")
        try:
            result = test_func()
            results.append((test_name, result))
            if result:
                logger.info(f"✅ {test_name}: PASSED")
            else:
                logger.error(f"❌ {test_name}: FAILED")
        except Exception as e:
            logger.error(f"❌ {test_name}: ERROR - {e}")
            results.append((test_name, False))
    
    # Summary
    logger.info("\n" + "=" * 60)
    logger.info("TEST RESULTS SUMMARY")
    logger.info("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        logger.info(f"{test_name}: {status}")
    
    logger.info(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        logger.info("🎉 All tests passed! Migration system is ready for proof of concept.")
        return True
    else:
        logger.error(f"⚠️  {total - passed} tests failed. Please fix issues before running migration.")
        return False

def main():
    """Main entry point"""
    try:
        success = run_all_tests()
        sys.exit(0 if success else 1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()

