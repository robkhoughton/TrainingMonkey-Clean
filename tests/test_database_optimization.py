#!/usr/bin/env python3
"""
Database Optimization Testing and Validation Script
Tests the new connection pooling and batch operations
"""

import os
import sys
import time
import logging
from datetime import datetime, timedelta
import json

# Add the app directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import optimization modules
from db_connection_manager import db_manager, initialize_database_pool
from optimized_token_management import OptimizedTokenManager, batch_refresh_all_tokens
from optimized_acwr_service import OptimizedACWRService, batch_recalculate_all_acwr
import db_utils

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class DatabaseOptimizationTester:
    """Test suite for database optimization features"""
    
    def __init__(self):
        self.test_results = {
            'connection_pooling': {},
            'batch_operations': {},
            'performance_improvements': {},
            'overall_success': False
        }
    
    def run_all_tests(self):
        """Run all optimization tests"""
        logger.info("🚀 Starting Database Optimization Tests")
        
        try:
            # Test 1: Connection Pool Initialization
            self.test_connection_pool_initialization()
            
            # Test 2: Connection Pool Performance
            self.test_connection_pool_performance()
            
            # Test 3: Batch Query Operations
            self.test_batch_query_operations()
            
            # Test 4: Token Management Optimization
            self.test_token_management_optimization()
            
            # Test 5: ACWR Calculation Optimization
            self.test_acwr_calculation_optimization()
            
            # Test 6: Performance Comparison
            self.test_performance_comparison()
            
            # Generate final report
            self.generate_test_report()
            
        except Exception as e:
            logger.error(f"❌ Test suite failed: {str(e)}")
            self.test_results['overall_success'] = False
    
    def test_connection_pool_initialization(self):
        """Test connection pool initialization"""
        logger.info("🔧 Testing Connection Pool Initialization...")
        
        try:
            # Initialize pool
            database_url = os.environ.get('DATABASE_URL')
            if not database_url:
                raise ValueError("DATABASE_URL environment variable not found")
            
            success = initialize_database_pool(database_url)
            
            if success:
                # Get pool status
                pool_status = db_manager.get_pool_status()
                
                self.test_results['connection_pooling'] = {
                    'initialization': 'PASS',
                    'pool_status': pool_status,
                    'pool_size': pool_status.get('pool_size', 0),
                    'active_connections': pool_status.get('active_connections', 0)
                }
                
                logger.info("✅ Connection pool initialization: PASS")
            else:
                self.test_results['connection_pooling'] = {
                    'initialization': 'FAIL',
                    'error': 'Failed to initialize connection pool'
                }
                logger.error("❌ Connection pool initialization: FAIL")
                
        except Exception as e:
            self.test_results['connection_pooling'] = {
                'initialization': 'FAIL',
                'error': str(e)
            }
            logger.error(f"❌ Connection pool initialization: FAIL - {str(e)}")
    
    def test_connection_pool_performance(self):
        """Test connection pool performance"""
        logger.info("⚡ Testing Connection Pool Performance...")
        
        try:
            # Test multiple concurrent queries
            start_time = time.time()
            
            # Simulate multiple queries
            for i in range(10):
                result = db_utils.execute_query("SELECT 1 as test_query", fetch=True)
                if not result or result[0]['test_query'] != 1:
                    raise ValueError(f"Query {i} returned unexpected result")
            
            end_time = time.time()
            execution_time = end_time - start_time
            
            # Get pool statistics
            pool_status = db_manager.get_pool_status()
            
            self.test_results['connection_pooling']['performance'] = {
                'status': 'PASS',
                'execution_time': round(execution_time, 3),
                'queries_per_second': round(10 / execution_time, 2),
                'pool_utilization': pool_status.get('pool_utilization', 0),
                'pool_hits': pool_status.get('stats', {}).get('pool_hits', 0)
            }
            
            logger.info(f"✅ Connection pool performance: PASS ({execution_time:.3f}s for 10 queries)")
            
        except Exception as e:
            self.test_results['connection_pooling']['performance'] = {
                'status': 'FAIL',
                'error': str(e)
            }
            logger.error(f"❌ Connection pool performance: FAIL - {str(e)}")
    
    def test_batch_query_operations(self):
        """Test batch query operations"""
        logger.info("📦 Testing Batch Query Operations...")
        
        try:
            # Prepare batch queries
            queries = [
                ("SELECT 1 as query_1", ()),
                ("SELECT 2 as query_2", ()),
                ("SELECT 3 as query_3", ()),
                ("SELECT COUNT(*) as user_count FROM user_settings", ()),
                ("SELECT COUNT(*) as activity_count FROM activities", ())
            ]
            
            start_time = time.time()
            results = db_utils.execute_batch_queries(queries)
            end_time = time.time()
            
            execution_time = end_time - start_time
            
            # Validate results
            if len(results) != len(queries):
                raise ValueError(f"Expected {len(queries)} results, got {len(results)}")
            
            self.test_results['batch_operations'] = {
                'batch_queries': 'PASS',
                'execution_time': round(execution_time, 3),
                'queries_processed': len(queries),
                'queries_per_second': round(len(queries) / execution_time, 2),
                'results': [len(str(r)) for r in results]  # Result sizes
            }
            
            logger.info(f"✅ Batch query operations: PASS ({execution_time:.3f}s for {len(queries)} queries)")
            
        except Exception as e:
            self.test_results['batch_operations'] = {
                'batch_queries': 'FAIL',
                'error': str(e)
            }
            logger.error(f"❌ Batch query operations: FAIL - {str(e)}")
    
    def test_token_management_optimization(self):
        """Test token management optimization"""
        logger.info("🔑 Testing Token Management Optimization...")
        
        try:
            # Test batch token operations
            token_manager = OptimizedTokenManager()
            
            # Test getting users needing refresh
            start_time = time.time()
            users_needing_refresh = token_manager.get_users_needing_token_refresh()
            end_time = time.time()
            
            execution_time = end_time - start_time
            
            # Test token health summary
            health_start = time.time()
            health_summary = token_manager.get_token_health_summary()
            health_end = time.time()
            
            health_time = health_end - health_start
            
            self.test_results['batch_operations']['token_management'] = {
                'status': 'PASS',
                'users_needing_refresh': len(users_needing_refresh),
                'query_time': round(execution_time, 3),
                'health_check_time': round(health_time, 3),
                'health_summary': health_summary
            }
            
            logger.info(f"✅ Token management optimization: PASS ({execution_time:.3f}s)")
            
        except Exception as e:
            self.test_results['batch_operations']['token_management'] = {
                'status': 'FAIL',
                'error': str(e)
            }
            logger.error(f"❌ Token management optimization: FAIL - {str(e)}")
    
    def test_acwr_calculation_optimization(self):
        """Test ACWR calculation optimization"""
        logger.info("📊 Testing ACWR Calculation Optimization...")
        
        try:
            acwr_service = OptimizedACWRService()
            
            # Test getting activities needing recalculation
            start_time = time.time()
            activities_needing_recalc = acwr_service.get_activities_needing_acwr_recalculation(days_back=7)
            end_time = time.time()
            
            execution_time = end_time - start_time
            
            # Test ACWR calculation status
            status_start = time.time()
            acwr_status = acwr_service.get_acwr_calculation_status()
            status_end = time.time()
            
            status_time = status_end - status_start
            
            self.test_results['batch_operations']['acwr_calculations'] = {
                'status': 'PASS',
                'activities_needing_recalc': len(activities_needing_recalc),
                'query_time': round(execution_time, 3),
                'status_check_time': round(status_time, 3),
                'acwr_status': acwr_status
            }
            
            logger.info(f"✅ ACWR calculation optimization: PASS ({execution_time:.3f}s)")
            
        except Exception as e:
            self.test_results['batch_operations']['acwr_calculations'] = {
                'status': 'FAIL',
                'error': str(e)
            }
            logger.error(f"❌ ACWR calculation optimization: FAIL - {str(e)}")
    
    def test_performance_comparison(self):
        """Test performance improvements"""
        logger.info("📈 Testing Performance Improvements...")
        
        try:
            # Test single query vs batch query performance
            single_query_times = []
            batch_query_times = []
            
            # Single queries
            for i in range(5):
                start = time.time()
                db_utils.execute_query("SELECT 1", fetch=True)
                single_query_times.append(time.time() - start)
            
            # Batch queries
            queries = [("SELECT 1", ()) for _ in range(5)]
            start = time.time()
            db_utils.execute_batch_queries(queries)
            batch_time = time.time() - start
            
            avg_single_time = sum(single_query_times) / len(single_query_times)
            total_single_time = sum(single_query_times)
            
            improvement = ((total_single_time - batch_time) / total_single_time) * 100
            
            self.test_results['performance_improvements'] = {
                'status': 'PASS',
                'single_query_avg': round(avg_single_time, 3),
                'single_query_total': round(total_single_time, 3),
                'batch_query_time': round(batch_time, 3),
                'improvement_percentage': round(improvement, 1),
                'speedup_factor': round(total_single_time / batch_time, 2)
            }
            
            logger.info(f"✅ Performance improvements: PASS ({improvement:.1f}% improvement)")
            
        except Exception as e:
            self.test_results['performance_improvements'] = {
                'status': 'FAIL',
                'error': str(e)
            }
            logger.error(f"❌ Performance improvements: FAIL - {str(e)}")
    
    def generate_test_report(self):
        """Generate comprehensive test report"""
        logger.info("📋 Generating Test Report...")
        
        # Determine overall success
        all_tests_passed = True
        
        # Check connection pooling
        if self.test_results['connection_pooling'].get('initialization') != 'PASS':
            all_tests_passed = False
        
        # Check batch operations
        batch_ops = self.test_results['batch_operations']
        if (batch_ops.get('batch_queries') != 'PASS' or 
            batch_ops.get('token_management', {}).get('status') != 'PASS' or
            batch_ops.get('acwr_calculations', {}).get('status') != 'PASS'):
            all_tests_passed = False
        
        # Check performance improvements
        if self.test_results['performance_improvements'].get('status') != 'PASS':
            all_tests_passed = False
        
        self.test_results['overall_success'] = all_tests_passed
        
        # Print summary
        print("\n" + "="*80)
        print("🚀 DATABASE OPTIMIZATION TEST RESULTS")
        print("="*80)
        
        print(f"\n📊 Overall Status: {'✅ PASS' if all_tests_passed else '❌ FAIL'}")
        
        print(f"\n🔧 Connection Pooling:")
        cp = self.test_results['connection_pooling']
        print(f"   Initialization: {cp.get('initialization', 'UNKNOWN')}")
        if 'performance' in cp:
            perf = cp['performance']
            print(f"   Performance: {perf.get('status', 'UNKNOWN')}")
            print(f"   Execution Time: {perf.get('execution_time', 0)}s")
            print(f"   Pool Utilization: {perf.get('pool_utilization', 0)}%")
        
        print(f"\n📦 Batch Operations:")
        bo = self.test_results['batch_operations']
        print(f"   Batch Queries: {bo.get('batch_queries', 'UNKNOWN')}")
        if 'token_management' in bo:
            tm = bo['token_management']
            print(f"   Token Management: {tm.get('status', 'UNKNOWN')}")
            print(f"   Users Needing Refresh: {tm.get('users_needing_refresh', 0)}")
        if 'acwr_calculations' in bo:
            ac = bo['acwr_calculations']
            print(f"   ACWR Calculations: {ac.get('status', 'UNKNOWN')}")
            print(f"   Activities Needing Recalc: {ac.get('activities_needing_recalc', 0)}")
        
        print(f"\n📈 Performance Improvements:")
        pi = self.test_results['performance_improvements']
        print(f"   Status: {pi.get('status', 'UNKNOWN')}")
        if 'improvement_percentage' in pi:
            print(f"   Improvement: {pi.get('improvement_percentage', 0)}%")
            print(f"   Speedup Factor: {pi.get('speedup_factor', 1)}x")
        
        print("\n" + "="*80)
        
        # Save detailed report
        report_file = f"database_optimization_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w') as f:
            json.dump(self.test_results, f, indent=2, default=str)
        
        logger.info(f"📄 Detailed report saved to: {report_file}")
        
        return all_tests_passed

def main():
    """Main test execution"""
    print("🚀 Database Optimization Test Suite")
    print("=" * 50)
    
    # Check environment
    if not os.environ.get('DATABASE_URL'):
        print("❌ DATABASE_URL environment variable not found")
        print("Please set DATABASE_URL before running tests")
        print("\nOptions:")
        print("1. Create .env file with: DATABASE_URL=postgresql://user:password@host:port/database")
        print("2. Create .env file with DATABASE_URL")
        print("3. Use production environment with proper configuration")
        return False
    
    # Run tests
    tester = DatabaseOptimizationTester()
    success = tester.run_all_tests()
    
    if success:
        print("\n🎉 All tests passed! Database optimization is working correctly.")
        return True
    else:
        print("\n⚠️  Some tests failed. Please review the results above.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
