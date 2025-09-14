#!/usr/bin/env python3
"""
ACWR System Health Verification Script
Checks core functionality after deployment
"""

import os
import sys
import logging
from datetime import datetime

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def check_database_schema():
    """Check if ACWR database schema is properly deployed"""
    try:
        import db_utils
        
        # Check for core ACWR tables
        core_tables = [
            'acwr_configurations',
            'user_acwr_configurations', 
            'acwr_enhanced_calculations',  # Updated to use single table
            'acwr_migration_history',
            'acwr_migration_progress'
        ]
        
        results = {}
        for table in core_tables:
            try:
                query = f"SELECT COUNT(*) as count FROM {table}"
                result = db_utils.execute_query(query, fetch=True)
                results[table] = {
                    'exists': True,
                    'count': result[0]['count'] if result else 0
                }
                logger.info(f"✅ Table {table}: {result[0]['count']} records")
            except Exception as e:
                results[table] = {
                    'exists': False,
                    'error': str(e)
                }
                logger.error(f"❌ Table {table}: {str(e)}")
        
        return results
        
    except Exception as e:
        logger.error(f"Database connection error: {str(e)}")
        return {'error': str(e)}

def check_acwr_services():
    """Check if ACWR services can be imported and initialized"""
    try:
        # Test core service imports
        from acwr_configuration_service import ACWRConfigurationService
        from acwr_calculation_service import ACWRCalculationService
        from exponential_decay_engine import ExponentialDecayEngine
        
        # Initialize services
        config_service = ACWRConfigurationService()
        calc_service = ACWRCalculationService()
        decay_engine = ExponentialDecayEngine()
        
        logger.info("✅ All ACWR services imported and initialized successfully")
        
        return {
            'configuration_service': True,
            'calculation_service': True,
            'exponential_decay_engine': True
        }
        
    except Exception as e:
        logger.error(f"❌ ACWR service import error: {str(e)}")
        return {'error': str(e)}

def check_migration_system():
    """Check if migration system components are available"""
    try:
        from acwr_migration_service import ACWRMigrationService
        from acwr_migration_monitoring import ACWRMigrationMonitor
        from acwr_migration_admin import acwr_migration_admin
        
        logger.info("✅ Migration system components available")
        
        return {
            'migration_service': True,
            'migration_monitoring': True,
            'migration_admin': True
        }
        
    except Exception as e:
        logger.error(f"❌ Migration system error: {str(e)}")
        return {'error': str(e)}

def check_admin_interfaces():
    """Check if admin interfaces are accessible"""
    try:
        # Check if admin routes are registered
        from flask import current_app
        
        # Get all registered routes
        routes = []
        for rule in current_app.url_map.iter_rules():
            if 'acwr' in rule.rule or 'migration' in rule.rule:
                routes.append(rule.rule)
        
        logger.info(f"✅ Found {len(routes)} ACWR/migration routes")
        for route in routes:
            logger.info(f"  - {route}")
        
        return {
            'routes_found': len(routes),
            'routes': routes
        }
        
    except Exception as e:
        logger.error(f"❌ Admin interface check error: {str(e)}")
        return {'error': str(e)}

def check_feature_flags():
    """Check if feature flags are working"""
    try:
        from utils.feature_flags import is_feature_enabled
        
        # Test ACWR feature flags for different users
        admin_acwr = is_feature_enabled('enhanced_acwr_calculation', 1)  # Admin
        beta_user_2_acwr = is_feature_enabled('enhanced_acwr_calculation', 2)  # Beta user 2
        beta_user_3_acwr = is_feature_enabled('enhanced_acwr_calculation', 3)  # Beta user 3
        regular_user_acwr = is_feature_enabled('enhanced_acwr_calculation', 4)  # Regular user
        
        logger.info(f"✅ Admin (user 1) ACWR Enhanced: {'Enabled' if admin_acwr else 'Disabled'}")
        logger.info(f"✅ Beta User 2 ACWR Enhanced: {'Enabled' if beta_user_2_acwr else 'Disabled'}")
        logger.info(f"✅ Beta User 3 ACWR Enhanced: {'Enabled' if beta_user_3_acwr else 'Disabled'}")
        logger.info(f"✅ Regular User ACWR Enhanced: {'Enabled' if regular_user_acwr else 'Disabled'}")
        
        return {
            'admin_acwr_enabled': admin_acwr,
            'beta_user_2_acwr_enabled': beta_user_2_acwr,
            'beta_user_3_acwr_enabled': beta_user_3_acwr,
            'regular_user_acwr_enabled': regular_user_acwr,
            'rollout_status': 'beta_phase' if admin_acwr and beta_user_2_acwr and beta_user_3_acwr else 'incomplete'
        }
        
    except Exception as e:
        logger.error(f"❌ Feature flags error: {str(e)}")
        return {'error': str(e)}

def main():
    """Run all health checks"""
    logger.info("🔍 Starting ACWR System Health Verification")
    logger.info("=" * 50)
    
    results = {}
    
    # Run all checks
    logger.info("\n1. Checking Database Schema...")
    results['database'] = check_database_schema()
    
    logger.info("\n2. Checking ACWR Services...")
    results['services'] = check_acwr_services()
    
    logger.info("\n3. Checking Migration System...")
    results['migration'] = check_migration_system()
    
    logger.info("\n4. Checking Admin Interfaces...")
    results['admin'] = check_admin_interfaces()
    
    logger.info("\n5. Checking Feature Flags...")
    results['feature_flags'] = check_feature_flags()
    
    # Summary
    logger.info("\n" + "=" * 50)
    logger.info("📊 HEALTH CHECK SUMMARY")
    logger.info("=" * 50)
    
    all_good = True
    for category, result in results.items():
        if 'error' in result:
            logger.error(f"❌ {category.upper()}: FAILED - {result['error']}")
            all_good = False
        else:
            logger.info(f"✅ {category.upper()}: PASSED")
    
    if all_good:
        logger.info("\n🎉 ALL CHECKS PASSED - ACWR System is healthy!")
    else:
        logger.info("\n⚠️  SOME CHECKS FAILED - Review errors above")
    
    return results

if __name__ == "__main__":
    main()

