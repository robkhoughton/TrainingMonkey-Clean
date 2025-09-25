# optimized_token_management.py
# Batch-optimized token management for improved database performance

import logging
import time
from datetime import datetime
from typing import List, Dict, Any, Optional
import db_utils

logger = logging.getLogger(__name__)

class OptimizedTokenManager:
    """Batch-optimized token management for improved database performance"""
    
    def __init__(self):
        self.audit_queue = []
        self.batch_size = 10
        self.max_batch_wait = 5.0  # seconds
    
    def batch_save_tokens(self, token_operations: List[Dict[str, Any]]) -> List[Any]:
        """Save multiple token operations in single transaction"""
        try:
            queries = []
            
            for operation in token_operations:
                user_id = operation['user_id']
                tokens = operation['tokens']
                athlete_id = operation.get('athlete_id')
                context = operation.get('context', {})
                
                # Token save query
                queries.append((
                    """UPDATE user_settings 
                       SET strava_access_token = %s, strava_refresh_token = %s,
                           strava_token_expires_at = %s, strava_athlete_id = %s,
                           strava_token_created_at = NOW()
                       WHERE id = %s""",
                    (tokens['access_token'], tokens.get('refresh_token'),
                     tokens.get('expires_at'), athlete_id, user_id)
                ))
                
                # Audit log query (if audit logging is enabled)
                if context.get('audit_enabled', True):
                    queries.append((
                        """INSERT INTO token_audit_log 
                           (user_id, operation, success, timestamp, ip_address, user_agent, details)
                           VALUES (%s, %s, %s, %s, %s, %s, %s)""",
                        (user_id, 'save_tokens', True, 
                         context.get('timestamp', datetime.now()),
                         context.get('ip_address'), 
                         context.get('user_agent'), 
                         context.get('details', 'Batch token save'))
                    ))
            
            # Execute all queries in single transaction
            results = db_utils.execute_batch_queries(queries)
            
            logger.info(f"Batch saved tokens for {len(token_operations)} users")
            return results
            
        except Exception as e:
            logger.error(f"Batch token save failed: {str(e)}")
            raise
    
    def batch_load_tokens(self, user_ids: List[int]) -> List[Dict[str, Any]]:
        """Load tokens for multiple users in single query"""
        try:
            if not user_ids:
                return []
            
            placeholders = ','.join(['%s'] * len(user_ids))
            query = f"""
                SELECT id as user_id, strava_access_token, strava_refresh_token, 
                       strava_token_expires_at, strava_athlete_id
                FROM user_settings 
                WHERE id IN ({placeholders})
                AND strava_access_token IS NOT NULL
            """
            
            results = db_utils.execute_query(query, tuple(user_ids), fetch=True)
            
            # Convert to token format
            tokens_by_user = {}
            for row in results:
                user_id = row['user_id']
                tokens_by_user[user_id] = {
                    'access_token': row['strava_access_token'],
                    'refresh_token': row['strava_refresh_token'],
                    'expires_at': row['strava_token_expires_at'],
                    'athlete_id': row['strava_athlete_id']
                }
            
            logger.info(f"Batch loaded tokens for {len(tokens_by_user)} users")
            return tokens_by_user
            
        except Exception as e:
            logger.error(f"Batch token load failed: {str(e)}")
            raise
    
    def batch_refresh_tokens(self, user_tokens: Dict[int, Dict[str, Any]]) -> Dict[int, Any]:
        """Refresh tokens for multiple users in batch"""
        try:
            refresh_results = {}
            successful_refreshes = []
            failed_refreshes = []
            
            # Process each user's token refresh
            for user_id, tokens in user_tokens.items():
                try:
                    # Import here to avoid circular imports
                    from enhanced_token_management import SimpleTokenManager
                    
                    token_manager = SimpleTokenManager(user_id)
                    refresh_result = token_manager.refresh_strava_tokens()
                    
                    if refresh_result:
                        refresh_results[user_id] = {
                            'success': True,
                            'tokens': refresh_result,
                            'refreshed_at': datetime.now()
                        }
                        successful_refreshes.append(user_id)
                    else:
                        refresh_results[user_id] = {
                            'success': False,
                            'error': 'Token refresh failed',
                            'refreshed_at': datetime.now()
                        }
                        failed_refreshes.append(user_id)
                        
                except Exception as e:
                    refresh_results[user_id] = {
                        'success': False,
                        'error': str(e),
                        'refreshed_at': datetime.now()
                    }
                    failed_refreshes.append(user_id)
            
            # Batch save successful refreshes
            if successful_refreshes:
                save_operations = []
                for user_id in successful_refreshes:
                    save_operations.append({
                        'user_id': user_id,
                        'tokens': refresh_results[user_id]['tokens'],
                        'context': {
                            'operation': 'batch_refresh',
                            'timestamp': datetime.now(),
                            'audit_enabled': True
                        }
                    })
                
                self.batch_save_tokens(save_operations)
            
            logger.info(f"Batch token refresh completed: {len(successful_refreshes)} successful, {len(failed_refreshes)} failed")
            return refresh_results
            
        except Exception as e:
            logger.error(f"Batch token refresh failed: {str(e)}")
            raise
    
    def batch_validate_tokens(self, user_tokens: Dict[int, Dict[str, Any]]) -> Dict[int, bool]:
        """Validate tokens for multiple users in batch"""
        try:
            validation_results = {}
            
            # Get all users who need validation
            user_ids = list(user_tokens.keys())
            if not user_ids:
                return {}
            
            # Batch check token expiration
            placeholders = ','.join(['%s'] * len(user_ids))
            query = f"""
                SELECT id as user_id, strava_token_expires_at
                FROM user_settings 
                WHERE id IN ({placeholders})
                AND strava_token_expires_at IS NOT NULL
            """
            
            results = db_utils.execute_query(query, tuple(user_ids), fetch=True)
            
            current_time = int(time.time())
            buffer_seconds = 30 * 60  # 30 minutes buffer
            
            for row in results:
                user_id = row['user_id']
                expires_at = row['strava_token_expires_at']
                
                if expires_at and expires_at > current_time + buffer_seconds:
                    validation_results[user_id] = True
                else:
                    validation_results[user_id] = False
            
            # Mark users not found in database as invalid
            for user_id in user_ids:
                if user_id not in validation_results:
                    validation_results[user_id] = False
            
            logger.info(f"Batch validated tokens for {len(validation_results)} users")
            return validation_results
            
        except Exception as e:
            logger.error(f"Batch token validation failed: {str(e)}")
            raise
    
    def get_users_needing_token_refresh(self, buffer_minutes: int = 30) -> List[Dict[str, Any]]:
        """Get all users who need token refresh in single query"""
        try:
            current_time = int(time.time())
            buffer_seconds = buffer_minutes * 60
            
            query = """
                SELECT id, email, strava_access_token, strava_refresh_token, 
                       strava_token_expires_at, strava_athlete_id
                FROM user_settings 
                WHERE strava_access_token IS NOT NULL 
                  AND strava_refresh_token IS NOT NULL
                  AND strava_token_expires_at IS NOT NULL
                  AND strava_token_expires_at <= %s
                ORDER BY strava_token_expires_at ASC
            """
            
            results = db_utils.execute_query(query, (current_time + buffer_seconds,), fetch=True)
            
            users_needing_refresh = []
            for row in results:
                time_until_expiry = row['strava_token_expires_at'] - current_time
                users_needing_refresh.append({
                    'user_id': row['id'],
                    'email': row['email'],
                    'expires_in_minutes': round(time_until_expiry / 60, 1),
                    'athlete_id': row['strava_athlete_id'],
                    'tokens': {
                        'access_token': row['strava_access_token'],
                        'refresh_token': row['strava_refresh_token'],
                        'expires_at': row['strava_token_expires_at']
                    }
                })
            
            logger.info(f"Found {len(users_needing_refresh)} users needing token refresh")
            return users_needing_refresh
            
        except Exception as e:
            logger.error(f"Error getting users needing token refresh: {str(e)}")
            return []
    
    def batch_cleanup_expired_tokens(self, expired_days: int = 7) -> int:
        """Clean up expired tokens older than specified days"""
        try:
            cutoff_time = int(time.time()) - (expired_days * 24 * 60 * 60)
            
            query = """
                UPDATE user_settings 
                SET strava_access_token = NULL, strava_refresh_token = NULL,
                    strava_token_expires_at = NULL, strava_athlete_id = NULL
                WHERE strava_token_expires_at IS NOT NULL 
                  AND strava_token_expires_at < %s
            """
            
            result = db_utils.execute_query(query, (cutoff_time,))
            
            logger.info(f"Cleaned up expired tokens for {result} users")
            return result
            
        except Exception as e:
            logger.error(f"Error cleaning up expired tokens: {str(e)}")
            return 0

    def get_token_health_summary(self):
        """Get comprehensive token health summary for monitoring"""
        try:
            # Get users needing refresh
            users_needing_refresh = self.get_users_needing_token_refresh()
            
            # Get total users with tokens
            total_users_query = """
                SELECT COUNT(*) as total_users
                FROM user_settings 
                WHERE strava_access_token IS NOT NULL
            """
            total_result = db_utils.execute_query(total_users_query, fetch=True)
            total_users = total_result[0]['total_users'] if total_result else 0
            
            # Calculate health metrics
            users_needing_refresh_count = len(users_needing_refresh)
            healthy_users = total_users - users_needing_refresh_count
            
            if total_users > 0:
                health_percentage = (healthy_users / total_users) * 100
            else:
                health_percentage = 100
            
            # Determine overall health status
            if health_percentage >= 90:
                overall_health = 'healthy'
            elif health_percentage >= 70:
                overall_health = 'warning'
            else:
                overall_health = 'critical'
            
            return {
                'overall_health': overall_health,
                'health_percentage': round(health_percentage, 1),
                'total_users': total_users,
                'healthy_users': healthy_users,
                'users_needing_refresh': users_needing_refresh_count,
                'needs_attention': overall_health in ['warning', 'critical'],
                'last_checked': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting token health summary: {str(e)}")
            return {
                'overall_health': 'error',
                'error': str(e),
                'needs_attention': True,
                'last_checked': datetime.now().isoformat()
            }

# Utility functions for backward compatibility
def batch_refresh_all_tokens(buffer_minutes: int = 30) -> Dict[str, Any]:
    """Refresh tokens for all users who need it"""
    try:
        token_manager = OptimizedTokenManager()
        
        # Get users needing refresh
        users_needing_refresh = token_manager.get_users_needing_token_refresh(buffer_minutes)
        
        if not users_needing_refresh:
            return {
                'success': True,
                'message': 'No users need token refresh',
                'users_checked': 0,
                'users_refreshed': 0,
                'users_failed': 0
            }
        
        # Prepare token data for batch refresh
        user_tokens = {}
        for user_info in users_needing_refresh:
            user_tokens[user_info['user_id']] = user_info['tokens']
        
        # Perform batch refresh
        refresh_results = token_manager.batch_refresh_tokens(user_tokens)
        
        # Count results
        successful = sum(1 for result in refresh_results.values() if result['success'])
        failed = len(refresh_results) - successful
        
        return {
            'success': True,
            'message': f'Batch refresh completed: {successful} successful, {failed} failed',
            'users_checked': len(users_needing_refresh),
            'users_refreshed': successful,
            'users_failed': failed,
            'results': refresh_results
        }
        
    except Exception as e:
        logger.error(f"Error in batch token refresh: {str(e)}")
        return {
            'success': False,
            'message': f'Batch refresh error: {str(e)}',
            'users_checked': 0,
            'users_refreshed': 0,
            'users_failed': 0
        }

def get_token_health_summary() -> Dict[str, Any]:
    """Get comprehensive token health summary for monitoring"""
    try:
        token_manager = OptimizedTokenManager()
        
        # Get users needing refresh
        users_needing_refresh = token_manager.get_users_needing_token_refresh()
        
        # Get total users with tokens
        total_users_query = """
            SELECT COUNT(*) as total_users
            FROM user_settings 
            WHERE strava_access_token IS NOT NULL
        """
        total_result = db_utils.execute_query(total_users_query, fetch=True)
        total_users = total_result[0]['total_users'] if total_result else 0
        
        # Calculate health metrics
        users_needing_refresh_count = len(users_needing_refresh)
        healthy_users = total_users - users_needing_refresh_count
        
        if total_users > 0:
            health_percentage = (healthy_users / total_users) * 100
        else:
            health_percentage = 100
        
        # Determine overall health status
        if health_percentage >= 90:
            overall_health = 'healthy'
        elif health_percentage >= 70:
            overall_health = 'warning'
        else:
            overall_health = 'critical'
        
        return {
            'overall_health': overall_health,
            'health_percentage': round(health_percentage, 1),
            'total_users': total_users,
            'healthy_users': healthy_users,
            'users_needing_refresh': users_needing_refresh_count,
            'needs_attention': overall_health in ['warning', 'critical'],
            'last_checked': datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting token health summary: {str(e)}")
        return {
            'overall_health': 'error',
            'error': str(e),
            'needs_attention': True,
            'last_checked': datetime.now().isoformat()
        }
