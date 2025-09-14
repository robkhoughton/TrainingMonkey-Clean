#!/usr/bin/env python3
"""
Test script for ACWR database connectivity and table access
Tests PostgreSQL connection and ACWR configuration service functionality
"""

import sys
import os
import logging
from datetime import datetime, date

# Add the app directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import db_utils
from acwr_configuration_service import ACWRConfigurationService

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_database_connection():
    """Test basic PostgreSQL database connection"""
    logger.info("Testing PostgreSQL database connection...")
    
    try:
        with db_utils.get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT version();")
            version = cursor.fetchone()
            logger.info(f"✅ Database connection successful!")
            logger.info(f"PostgreSQL version: {version['version']}")
            return True
    except Exception as e:
        logger.error(f"❌ Database connection failed: {str(e)}")
        return False

def test_acwr_tables_exist():
    """Test that ACWR tables exist and are accessible"""
    logger.info("Testing ACWR tables existence...")
    
    tables_to_check = [
        'acwr_configurations',
        'user_acwr_configurations', 
        'enhanced_acwr_calculations'
    ]
    
    try:
        for table in tables_to_check:
            query = """
                SELECT COUNT(*) as count 
                FROM information_schema.tables 
                WHERE table_name = %s
            """
            result = db_utils.execute_query(query, (table,), fetch=True)
            
            if result and result[0]['count'] > 0:
                logger.info(f"✅ Table '{table}' exists")
            else:
                logger.error(f"❌ Table '{table}' does not exist")
                return False
        
        return True
    except Exception as e:
        logger.error(f"❌ Error checking table existence: {str(e)}")
        return False

def test_acwr_table_structure():
    """Test ACWR table structure and constraints"""
    logger.info("Testing ACWR table structure...")
    
    try:
        # Test acwr_configurations table structure
        query = """
            SELECT column_name, data_type, is_nullable, column_default
            FROM information_schema.columns 
            WHERE table_name = 'acwr_configurations'
            ORDER BY ordinal_position
        """
        result = db_utils.execute_query(query, fetch=True)
        
        logger.info("✅ acwr_configurations table structure:")
        for row in result:
            logger.info(f"  - {row['column_name']}: {row['data_type']} (nullable: {row['is_nullable']})")
        
        # Test foreign key constraints
        fk_query = """
            SELECT 
                tc.table_name, 
                kcu.column_name,
                ccu.table_name AS foreign_table_name,
                ccu.column_name AS foreign_column_name
            FROM information_schema.table_constraints tc
            JOIN information_schema.key_column_usage kcu 
                ON tc.constraint_name = kcu.constraint_name
            JOIN information_schema.constraint_column_usage ccu 
                ON ccu.constraint_name = tc.constraint_name
            WHERE tc.table_name IN ('user_acwr_configurations', 'enhanced_acwr_calculations')
                AND tc.constraint_type = 'FOREIGN KEY'
        """
        fk_result = db_utils.execute_query(fk_query, fetch=True)
        
        logger.info("✅ Foreign key constraints:")
        for row in fk_result:
            logger.info(f"  - {row['table_name']}.{row['column_name']} -> {row['foreign_table_name']}.{row['foreign_column_name']}")
        
        return True
    except Exception as e:
        logger.error(f"❌ Error testing table structure: {str(e)}")
        return False

def test_default_configuration():
    """Test that default configuration exists and is accessible"""
    logger.info("Testing default configuration...")
    
    try:
        query = """
            SELECT id, name, description, chronic_period_days, decay_rate, is_active
            FROM acwr_configurations 
            WHERE name = 'default_enhanced'
        """
        result = db_utils.execute_query(query, fetch=True)
        
        if result:
            config = result[0]
            logger.info("✅ Default configuration found:")
            logger.info(f"  - ID: {config['id']}")
            logger.info(f"  - Name: {config['name']}")
            logger.info(f"  - Chronic Period: {config['chronic_period_days']} days")
            logger.info(f"  - Decay Rate: {config['decay_rate']}")
            logger.info(f"  - Active: {config['is_active']}")
            
            # Verify expected values
            if config['chronic_period_days'] == 42 and config['decay_rate'] == 0.05:
                logger.info("✅ Default configuration has correct values")
                return True
            else:
                logger.error(f"❌ Default configuration has incorrect values")
                return False
        else:
            logger.error("❌ Default configuration not found")
            return False
    except Exception as e:
        logger.error(f"❌ Error testing default configuration: {str(e)}")
        return False

def test_acwr_service_functionality():
    """Test ACWR configuration service methods"""
    logger.info("Testing ACWR configuration service...")
    
    try:
        service = ACWRConfigurationService()
        
        # Test get_default_configuration
        default_config = service.get_default_configuration()
        if default_config:
            logger.info("✅ get_default_configuration() works")
            logger.info(f"  - Retrieved config: {default_config['name']}")
        else:
            logger.error("❌ get_default_configuration() failed")
            return False
        
        # Test get_all_configurations
        all_configs = service.get_all_configurations()
        if all_configs:
            logger.info(f"✅ get_all_configurations() works - found {len(all_configs)} configurations")
        else:
            logger.error("❌ get_all_configurations() failed")
            return False
        
        # Test create_configuration (with cleanup)
        test_config_id = service.create_configuration(
            name="test_connectivity_config",
            description="Test configuration for connectivity testing",
            chronic_period_days=35,
            decay_rate=0.08,
            created_by=1,
            notes="Temporary test configuration"
        )
        
        if test_config_id:
            logger.info(f"✅ create_configuration() works - created config ID: {test_config_id}")
            
            # Clean up test configuration
            service.deactivate_configuration(test_config_id)
            logger.info("✅ Test configuration cleaned up")
        else:
            logger.error("❌ create_configuration() failed")
            return False
        
        return True
    except Exception as e:
        logger.error(f"❌ Error testing ACWR service: {str(e)}")
        return False

def test_data_integrity_constraints():
    """Test database constraints and data integrity"""
    logger.info("Testing data integrity constraints...")
    
    try:
        service = ACWRConfigurationService()
        
        # Test constraint: chronic_period_days >= 28
        try:
            invalid_config_id = service.create_configuration(
                name="invalid_test_config",
                description="Should fail - chronic period too short",
                chronic_period_days=20,  # Invalid: < 28
                decay_rate=0.05,
                created_by=1
            )
            if invalid_config_id:
                logger.error("❌ Constraint test failed - should have rejected chronic_period_days < 28")
                service.deactivate_configuration(invalid_config_id)
                return False
        except ValueError as e:
            logger.info(f"✅ Constraint validation works: {str(e)}")
        
        # Test constraint: decay_rate > 0 and <= 1.0
        try:
            invalid_config_id = service.create_configuration(
                name="invalid_test_config2",
                description="Should fail - decay rate too high",
                chronic_period_days=30,
                decay_rate=1.5,  # Invalid: > 1.0
                created_by=1
            )
            if invalid_config_id:
                logger.error("❌ Constraint test failed - should have rejected decay_rate > 1.0")
                service.deactivate_configuration(invalid_config_id)
                return False
        except ValueError as e:
            logger.info(f"✅ Constraint validation works: {str(e)}")
        
        return True
    except Exception as e:
        logger.error(f"❌ Error testing constraints: {str(e)}")
        return False

def test_indexes():
    """Test that performance indexes exist"""
    logger.info("Testing database indexes...")
    
    try:
        query = """
            SELECT indexname, tablename, indexdef
            FROM pg_indexes 
            WHERE tablename IN ('acwr_configurations', 'user_acwr_configurations', 'enhanced_acwr_calculations')
            ORDER BY tablename, indexname
        """
        result = db_utils.execute_query(query, fetch=True)
        
        expected_indexes = [
            'idx_acwr_config_active',
            'idx_user_acwr_config_config_id',
            'idx_user_acwr_config_user_id',
            'idx_enhanced_acwr_config_id',
            'idx_enhanced_acwr_user_date'
        ]
        
        found_indexes = [row['indexname'] for row in result]
        logger.info(f"✅ Found {len(result)} indexes:")
        
        for row in result:
            logger.info(f"  - {row['indexname']} on {row['tablename']}")
        
        # Check for expected indexes
        missing_indexes = set(expected_indexes) - set(found_indexes)
        if missing_indexes:
            logger.error(f"❌ Missing expected indexes: {missing_indexes}")
            return False
        else:
            logger.info("✅ All expected indexes found")
            return True
    except Exception as e:
        logger.error(f"❌ Error testing indexes: {str(e)}")
        return False

def main():
    """Run all database connectivity tests"""
    logger.info("=" * 60)
    logger.info("ACWR Database Connectivity Test Suite")
    logger.info("=" * 60)
    
    tests = [
        ("Database Connection", test_database_connection),
        ("ACWR Tables Existence", test_acwr_tables_exist),
        ("Table Structure", test_acwr_table_structure),
        ("Default Configuration", test_default_configuration),
        ("ACWR Service Functionality", test_acwr_service_functionality),
        ("Data Integrity Constraints", test_data_integrity_constraints),
        ("Database Indexes", test_indexes)
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
        logger.info("🎉 All tests passed! Database connectivity is working correctly.")
        return True
    else:
        logger.error(f"⚠️  {total - passed} tests failed. Please check the errors above.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

