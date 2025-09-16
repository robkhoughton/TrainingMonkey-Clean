# db_connection_manager.py
# Thread-safe connection pool manager for PostgreSQL

import psycopg2.pool
import threading
import logging
from contextlib import contextmanager
import os
import time
from functools import wraps

logger = logging.getLogger(__name__)

class DatabaseConnectionManager:
    """Thread-safe connection pool manager for PostgreSQL"""
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not hasattr(self, 'initialized'):
            self.pool = None
            self.logger = logging.getLogger(__name__)
            self.initialized = True
            self.connection_stats = {
                'total_connections': 0,
                'active_connections': 0,
                'pool_hits': 0,
                'pool_misses': 0,
                'connection_errors': 0
            }
    
    def initialize_pool(self, dsn, minconn=2, maxconn=10):
        """Initialize connection pool with PostgreSQL-specific settings"""
        if self.pool is None:
            try:
                self.pool = psycopg2.pool.ThreadedConnectionPool(
                    minconn=minconn,
                    maxconn=maxconn,
                    dsn=dsn
                )
                self.logger.info(f"Connection pool initialized: {minconn}-{maxconn} connections")
                self.logger.info(f"Database URL: {dsn[:50]}...")
                return True
            except Exception as e:
                self.logger.error(f"Failed to initialize connection pool: {str(e)}")
                self.connection_stats['connection_errors'] += 1
                return False
        return True
    
    @contextmanager
    def get_connection(self):
        """Get connection from pool with enhanced error handling"""
        if self.pool is None:
            raise RuntimeError("Connection pool not initialized")
        
        conn = None
        start_time = time.time()
        
        try:
            conn = self.pool.getconn()
            if conn is None:
                self.connection_stats['pool_misses'] += 1
                raise RuntimeError("Failed to get connection from pool")
            
            self.connection_stats['pool_hits'] += 1
            self.connection_stats['active_connections'] += 1
            
            # Configure connection for optimal performance
            conn.cursor_factory = psycopg2.extras.RealDictCursor
            
            # Set PostgreSQL-specific optimizations
            with conn.cursor() as cursor:
                cursor.execute("SET search_path TO public;")
                cursor.execute("SET statement_timeout = '30s';")
            
            yield conn
            
        except Exception as e:
            if conn:
                try:
                    conn.rollback()
                except:
                    pass
            self.logger.error(f"Database operation failed: {str(e)}")
            self.connection_stats['connection_errors'] += 1
            raise
        finally:
            if conn:
                try:
                    self.pool.putconn(conn)
                    self.connection_stats['active_connections'] -= 1
                except Exception as e:
                    self.logger.error(f"Error returning connection to pool: {str(e)}")
            
            # Log performance metrics
            execution_time = time.time() - start_time
            if execution_time > 1.0:  # Log slow operations
                self.logger.warning(f"Slow database operation: {execution_time:.3f}s")
    
    def execute_query(self, query, params=(), fetch=False):
        """Execute query using connection pool with performance monitoring"""
        start_time = time.time()
        
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Convert ? placeholders to %s for PostgreSQL compatibility
                if '?' in query:
                    param_count = query.count('?')
                    query = query.replace('?', '%s')
                    self.logger.debug(f"Converted {param_count} placeholders for PostgreSQL")
                
                self.logger.debug(f"Executing: {query[:100]}...")
                cursor.execute(query, params)
                
                if fetch:
                    result = cursor.fetchall()
                    self.logger.debug(f"Fetched {len(result)} rows")
                    return result
                
                conn.commit()
                execution_time = time.time() - start_time
                
                if execution_time > 0.5:  # Log slow queries
                    self.logger.warning(f"Slow query ({execution_time:.3f}s): {query[:100]}...")
                
                return cursor.rowcount
                
        except Exception as e:
            execution_time = time.time() - start_time
            self.logger.error(f"Query failed after {execution_time:.3f}s: {str(e)}")
            self.logger.error(f"Query was: {query[:200]}...")
            self.logger.error(f"Params were: {params}")
            raise
    
    def execute_batch_queries(self, queries_with_params):
        """Execute multiple queries in single connection for better performance"""
        start_time = time.time()
        
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                results = []
                
                for i, (query, params) in enumerate(queries_with_params):
                    try:
                        # Convert ? placeholders to %s for PostgreSQL compatibility
                        if '?' in query:
                            param_count = query.count('?')
                            query = query.replace('?', '%s')
                        
                        cursor.execute(query, params)
                        
                        if 'SELECT' in query.upper():
                            results.append(cursor.fetchall())
                        else:
                            results.append(cursor.rowcount)
                            
                    except Exception as e:
                        self.logger.error(f"Batch query {i+1} failed: {str(e)}")
                        self.logger.error(f"Query: {query[:100]}...")
                        raise
                
                conn.commit()
                execution_time = time.time() - start_time
                
                self.logger.info(f"Batch execution completed: {len(queries_with_params)} queries in {execution_time:.3f}s")
                return results
                
        except Exception as e:
            execution_time = time.time() - start_time
            self.logger.error(f"Batch execution failed after {execution_time:.3f}s: {str(e)}")
            raise
    
    def get_pool_status(self):
        """Get current pool status and statistics"""
        if not self.pool:
            return {
                'status': 'not_initialized',
                'pool_size': 0,
                'active_connections': 0,
                'stats': self.connection_stats
            }
        
        try:
            # Get pool statistics
            pool_size = self.pool.minconn + self.pool.maxconn
            active_connections = self.connection_stats['active_connections']
            
            return {
                'status': 'active',
                'pool_size': pool_size,
                'min_connections': self.pool.minconn,
                'max_connections': self.pool.maxconn,
                'active_connections': active_connections,
                'pool_utilization': (active_connections / self.pool.maxconn) * 100,
                'stats': self.connection_stats.copy()
            }
        except Exception as e:
            self.logger.error(f"Error getting pool status: {str(e)}")
            return {
                'status': 'error',
                'error': str(e),
                'stats': self.connection_stats
            }
    
    def close_pool(self):
        """Close all connections in pool"""
        if self.pool:
            try:
                self.pool.closeall()
                self.logger.info("Connection pool closed")
                self.pool = None
                return True
            except Exception as e:
                self.logger.error(f"Error closing connection pool: {str(e)}")
                return False
        return True
    
    def reset_stats(self):
        """Reset connection statistics"""
        self.connection_stats = {
            'total_connections': 0,
            'active_connections': 0,
            'pool_hits': 0,
            'pool_misses': 0,
            'connection_errors': 0
        }
        self.logger.info("Connection statistics reset")

# Global instance
db_manager = DatabaseConnectionManager()

# Performance monitoring decorator
def monitor_performance(func):
    """Decorator to monitor function performance"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        try:
            result = func(*args, **kwargs)
            execution_time = time.time() - start_time
            logger.info(f"{func.__name__} executed in {execution_time:.3f}s")
            return result
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"{func.__name__} failed after {execution_time:.3f}s: {str(e)}")
            raise
    return wrapper

# Utility functions for backward compatibility
def initialize_database_pool(database_url=None):
    """Initialize database connection pool"""
    if database_url is None:
        database_url = os.environ.get('DATABASE_URL')
    
    if not database_url:
        raise ValueError('DATABASE_URL environment variable is required')
    
    return db_manager.initialize_pool(database_url)

def get_database_manager():
    """Get the global database manager instance"""
    return db_manager

def close_database_pool():
    """Close the database connection pool"""
    return db_manager.close_pool()
