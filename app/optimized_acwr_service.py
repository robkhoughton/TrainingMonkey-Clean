# optimized_acwr_service.py
# Batch-optimized ACWR calculations for improved database performance

import logging
import math
from datetime import datetime, timedelta, date
from typing import List, Dict, Any, Optional, Tuple
import db_utils

logger = logging.getLogger(__name__)

class OptimizedACWRService:
    """Batch-optimized ACWR calculations for improved database performance"""
    
    def __init__(self):
        self.batch_size = 50  # Process activities in batches
        self.cache_size = 1000  # Cache size for activity data
    
    def batch_calculate_acwr(self, user_dates: List[Tuple[int, str]], 
                           chronic_period_days: int = 28, 
                           decay_rate: float = 0.1) -> Dict[str, Any]:
        """Calculate ACWR for multiple users/dates in optimized batches"""
        try:
            if not user_dates:
                return {'success': True, 'processed': 0, 'results': []}
            
            # Group by user for efficient processing
            users_data = {}
            for user_id, date_str in user_dates:
                if user_id not in users_data:
                    users_data[user_id] = []
                users_data[user_id].append(date_str)
            
            results = []
            total_processed = 0
            
            # Process each user's data
            for user_id, dates in users_data.items():
                user_results = self._calculate_user_acwr_batch(
                    user_id, dates, chronic_period_days, decay_rate
                )
                results.extend(user_results)
                total_processed += len(dates)
            
            logger.info(f"Batch ACWR calculation completed: {total_processed} calculations for {len(users_data)} users")
            
            return {
                'success': True,
                'processed': total_processed,
                'users_processed': len(users_data),
                'results': results
            }
            
        except Exception as e:
            logger.error(f"Batch ACWR calculation failed: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'processed': 0,
                'results': []
            }
    
    def _calculate_user_acwr_batch(self, user_id: int, dates: List[str], 
                                 chronic_period_days: int, decay_rate: float) -> List[Dict[str, Any]]:
        """Calculate ACWR for a single user across multiple dates"""
        try:
            if not dates:
                return []
            
            # Get date range for efficient data loading
            min_date = min(dates)
            max_date = max(dates)
            
            # Extend range to include chronic period
            start_date = (datetime.strptime(min_date, '%Y-%m-%d').date() - 
                         timedelta(days=chronic_period_days + 7))
            end_date = datetime.strptime(max_date, '%Y-%m-%d').date()
            
            # Load all activities for the user in the date range
            activities = self._load_user_activities_batch(user_id, start_date, end_date)
            
            if not activities:
                logger.warning(f"No activities found for user {user_id} in date range {start_date} to {end_date}")
                return []
            
            # Create activities lookup by date
            activities_by_date = {}
            for activity in activities:
                date_str = activity['date'].strftime('%Y-%m-%d') if hasattr(activity['date'], 'strftime') else str(activity['date'])
                activities_by_date[date_str] = {
                    'total_load_miles': activity['total_load_miles'] or 0,
                    'trimp': activity['trimp'] or 0
                }
            
            # Calculate ACWR for each requested date
            results = []
            for date_str in dates:
                try:
                    acwr_result = self._calculate_single_acwr(
                        date_str, activities_by_date, chronic_period_days, decay_rate
                    )
                    acwr_result['user_id'] = user_id
                    acwr_result['date'] = date_str
                    results.append(acwr_result)
                except Exception as e:
                    logger.error(f"Error calculating ACWR for user {user_id}, date {date_str}: {str(e)}")
                    results.append({
                        'user_id': user_id,
                        'date': date_str,
                        'error': str(e),
                        'success': False
                    })
            
            return results
            
        except Exception as e:
            logger.error(f"Error in user ACWR batch calculation for user {user_id}: {str(e)}")
            return []
    
    def _load_user_activities_batch(self, user_id: int, start_date: date, end_date: date) -> List[Dict[str, Any]]:
        """Load activities for a user in a date range efficiently"""
        try:
            query = """
                SELECT date, total_load_miles, trimp, activity_id
                FROM activities 
                WHERE user_id = %s 
                AND date >= %s 
                AND date <= %s
                ORDER BY date ASC
            """
            
            results = db_utils.execute_query(query, (
                user_id, 
                start_date.strftime('%Y-%m-%d'), 
                end_date.strftime('%Y-%m-%d')
            ), fetch=True)
            
            return [dict(row) for row in results] if results else []
            
        except Exception as e:
            logger.error(f"Error loading activities for user {user_id}: {str(e)}")
            return []
    
    def _calculate_single_acwr(self, date_str: str, activities_by_date: Dict[str, Dict[str, float]], 
                             chronic_period_days: int, decay_rate: float) -> Dict[str, Any]:
        """Calculate ACWR for a single date"""
        try:
            date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()
            
            # Calculate acute averages (7 days)
            acute_load_sum = 0
            acute_trimp_sum = 0
            acute_count = 0
            
            for i in range(7):
                acute_date = date_obj - timedelta(days=i)
                acute_date_str = acute_date.strftime('%Y-%m-%d')
                if acute_date_str in activities_by_date:
                    acute_load_sum += activities_by_date[acute_date_str]['total_load_miles']
                    acute_trimp_sum += activities_by_date[acute_date_str]['trimp']
                    acute_count += 1
            
            acute_load_avg = acute_load_sum / 7.0 if acute_count > 0 else 0
            acute_trimp_avg = acute_trimp_sum / 7.0 if acute_count > 0 else 0
            
            # Calculate chronic averages with exponential decay
            chronic_load_sum = 0
            chronic_trimp_sum = 0
            total_weight = 0
            
            for i in range(chronic_period_days):
                chronic_date = date_obj - timedelta(days=i)
                chronic_date_str = chronic_date.strftime('%Y-%m-%d')
                if chronic_date_str in activities_by_date:
                    days_ago = i
                    weight = math.exp(-decay_rate * days_ago)
                    total_weight += weight
                    
                    chronic_load_sum += activities_by_date[chronic_date_str]['total_load_miles'] * weight
                    chronic_trimp_sum += activities_by_date[chronic_date_str]['trimp'] * weight
            
            chronic_load_avg = chronic_load_sum / total_weight if total_weight > 0 else 0
            chronic_trimp_avg = chronic_trimp_sum / total_weight if total_weight > 0 else 0
            
            # Calculate ACWR values
            external_acwr = acute_load_avg / chronic_load_avg if chronic_load_avg > 0 else 0
            internal_acwr = acute_trimp_avg / chronic_trimp_avg if chronic_trimp_avg > 0 else 0
            
            # Calculate normalized divergence
            if external_acwr > 0 and internal_acwr > 0:
                avg_acwr = (external_acwr + internal_acwr) / 2
                normalized_divergence = (external_acwr - internal_acwr) / avg_acwr if avg_acwr > 0 else 0
            else:
                normalized_divergence = 0
            
            return {
                'success': True,
                'acute_chronic_ratio': round(external_acwr, 3),
                'trimp_acute_chronic_ratio': round(internal_acwr, 3),
                'normalized_divergence': round(normalized_divergence, 3),
                'seven_day_avg_load': round(acute_load_avg, 2),
                'twentyeight_day_avg_load': round(chronic_load_avg, 2),
                'seven_day_avg_trimp': round(acute_trimp_avg, 1),
                'twentyeight_day_avg_trimp': round(chronic_trimp_avg, 1),
                'acute_count': acute_count,
                'chronic_weight': round(total_weight, 2)
            }
            
        except Exception as e:
            logger.error(f"Error calculating single ACWR for date {date_str}: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def batch_update_acwr_values(self, acwr_results: List[Dict[str, Any]]) -> int:
        """Update ACWR values in database using batch operations"""
        try:
            if not acwr_results:
                return 0
            
            # Prepare batch update queries
            queries = []
            for result in acwr_results:
                if result.get('success', False):
                    query = """
                        UPDATE activities SET 
                            seven_day_avg_load = %s,
                            twentyeight_day_avg_load = %s,
                            seven_day_avg_trimp = %s,
                            twentyeight_day_avg_trimp = %s,
                            acute_chronic_ratio = %s,
                            trimp_acute_chronic_ratio = %s,
                            normalized_divergence = %s
                        WHERE user_id = %s AND date = %s
                    """
                    
                    params = (
                        result['seven_day_avg_load'],
                        result['twentyeight_day_avg_load'],
                        result['seven_day_avg_trimp'],
                        result['twentyeight_day_avg_trimp'],
                        result['acute_chronic_ratio'],
                        result['trimp_acute_chronic_ratio'],
                        result['normalized_divergence'],
                        result['user_id'],
                        result['date']
                    )
                    
                    queries.append((query, params))
            
            if queries:
                # Execute batch update
                results = db_utils.execute_batch_queries(queries)
                total_updated = sum(results) if results else 0
                
                logger.info(f"Batch updated ACWR values for {total_updated} activities")
                return total_updated
            else:
                logger.warning("No valid ACWR results to update")
                return 0
                
        except Exception as e:
            logger.error(f"Error in batch ACWR update: {str(e)}")
            return 0
    
    def get_activities_needing_acwr_recalculation(self, user_id: Optional[int] = None, 
                                                days_back: int = 30) -> List[Dict[str, Any]]:
        """Get activities that need ACWR recalculation in single query"""
        try:
            if user_id:
                query = """
                    SELECT activity_id, user_id, date, name, type, 
                           total_load_miles, trimp, acute_chronic_ratio, 
                           trimp_acute_chronic_ratio, normalized_divergence
                    FROM activities 
                    WHERE user_id = %s 
                    AND date >= CURRENT_DATE - INTERVAL '%s days'
                    AND (
                        acute_chronic_ratio IS NULL 
                        OR trimp_acute_chronic_ratio IS NULL
                        OR normalized_divergence IS NULL
                        OR seven_day_avg_load IS NULL
                        OR twentyeight_day_avg_load IS NULL
                    )
                    ORDER BY date DESC
                """
                params = (user_id, days_back)
            else:
                query = """
                    SELECT activity_id, user_id, date, name, type,
                           total_load_miles, trimp, acute_chronic_ratio,
                           trimp_acute_chronic_ratio, normalized_divergence
                    FROM activities 
                    WHERE date >= CURRENT_DATE - INTERVAL '%s days'
                    AND (
                        acute_chronic_ratio IS NULL 
                        OR trimp_acute_chronic_ratio IS NULL
                        OR normalized_divergence IS NULL
                        OR seven_day_avg_load IS NULL
                        OR twentyeight_day_avg_load IS NULL
                    )
                    ORDER BY user_id, date DESC
                """
                params = (days_back,)
            
            results = db_utils.execute_query(query, params, fetch=True)
            
            activities = [dict(row) for row in results] if results else []
            logger.info(f"Found {len(activities)} activities needing ACWR recalculation")
            
            return activities
            
        except Exception as e:
            logger.error(f"Error getting activities needing ACWR recalculation: {str(e)}")
            return []
    
    def recalculate_user_acwr_range(self, user_id: int, start_date: str, end_date: str,
                                  chronic_period_days: int = 28, decay_rate: float = 0.1) -> Dict[str, Any]:
        """Recalculate ACWR for a user across a date range"""
        try:
            # Generate list of dates in range
            start_dt = datetime.strptime(start_date, '%Y-%m-%d').date()
            end_dt = datetime.strptime(end_date, '%Y-%m-%d').date()
            
            dates = []
            current_date = start_dt
            while current_date <= end_dt:
                dates.append(current_date.strftime('%Y-%m-%d'))
                current_date += timedelta(days=1)
            
            # Calculate ACWR for all dates
            user_dates = [(user_id, date_str) for date_str in dates]
            calculation_result = self.batch_calculate_acwr(user_dates, chronic_period_days, decay_rate)
            
            if calculation_result['success']:
                # Update database with results
                updated_count = self.batch_update_acwr_values(calculation_result['results'])
                
                return {
                    'success': True,
                    'user_id': user_id,
                    'date_range': f"{start_date} to {end_date}",
                    'dates_processed': len(dates),
                    'calculations_successful': len([r for r in calculation_result['results'] if r.get('success', False)]),
                    'database_updates': updated_count
                }
            else:
                return {
                    'success': False,
                    'error': calculation_result.get('error', 'Unknown error'),
                    'user_id': user_id,
                    'date_range': f"{start_date} to {end_date}"
                }
                
        except Exception as e:
            logger.error(f"Error recalculating ACWR range for user {user_id}: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'user_id': user_id,
                'date_range': f"{start_date} to {end_date}"
            }

    def get_acwr_calculation_status(self):
        """Get status of ACWR calculations across all users"""
        try:
            # Get activities needing recalculation
            activities_needing_recalc = self.get_activities_needing_acwr_recalculation()
            
            # Get total activities count
            total_activities_query = "SELECT COUNT(*) as total FROM activities"
            total_result = db_utils.execute_query(total_activities_query, fetch=True)
            total_activities = total_result[0]['total'] if total_result else 0
            
            # Calculate completion percentage
            if total_activities > 0:
                completion_percentage = ((total_activities - len(activities_needing_recalc)) / total_activities) * 100
            else:
                completion_percentage = 100
            
            # Determine status
            if completion_percentage >= 95:
                status = 'complete'
            elif completion_percentage >= 80:
                status = 'mostly_complete'
            else:
                status = 'needs_attention'
            
            return {
                'status': status,
                'completion_percentage': round(completion_percentage, 1),
                'total_activities': total_activities,
                'activities_needing_recalculation': len(activities_needing_recalc),
                'needs_attention': status in ['mostly_complete', 'needs_attention'],
                'last_checked': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting ACWR calculation status: {str(e)}")
            return {
                'status': 'error',
                'error': str(e),
                'needs_attention': True,
                'last_checked': datetime.now().isoformat()
            }

# Utility functions for backward compatibility
def batch_recalculate_all_acwr(days_back: int = 30) -> Dict[str, Any]:
    """Recalculate ACWR for all users who need it"""
    try:
        acwr_service = OptimizedACWRService()
        
        # Get all activities needing recalculation
        activities = acwr_service.get_activities_needing_acwr_recalculation(days_back=days_back)
        
        if not activities:
            return {
                'success': True,
                'message': 'No activities need ACWR recalculation',
                'activities_processed': 0,
                'users_processed': 0
            }
        
        # Group by user and date
        user_dates = {}
        for activity in activities:
            user_id = activity['user_id']
            date_str = activity['date'].strftime('%Y-%m-%d') if hasattr(activity['date'], 'strftime') else str(activity['date'])
            
            if user_id not in user_dates:
                user_dates[user_id] = set()
            user_dates[user_id].add(date_str)
        
        # Convert to list format
        user_date_list = []
        for user_id, dates in user_dates.items():
            for date_str in dates:
                user_date_list.append((user_id, date_str))
        
        # Perform batch calculation
        calculation_result = acwr_service.batch_calculate_acwr(user_date_list)
        
        if calculation_result['success']:
            # Update database
            updated_count = acwr_service.batch_update_acwr_values(calculation_result['results'])
            
            return {
                'success': True,
                'message': f'ACWR recalculation completed: {calculation_result["processed"]} calculations, {updated_count} database updates',
                'activities_processed': len(activities),
                'users_processed': len(user_dates),
                'calculations_successful': calculation_result['processed'],
                'database_updates': updated_count
            }
        else:
            return {
                'success': False,
                'error': calculation_result.get('error', 'Unknown error'),
                'activities_processed': len(activities),
                'users_processed': len(user_dates)
            }
            
    except Exception as e:
        logger.error(f"Error in batch ACWR recalculation: {str(e)}")
        return {
            'success': False,
            'error': str(e),
            'activities_processed': 0,
            'users_processed': 0
        }

def get_acwr_calculation_status() -> Dict[str, Any]:
    """Get status of ACWR calculations across all users"""
    try:
        acwr_service = OptimizedACWRService()
        
        # Get activities needing recalculation
        activities_needing_recalc = acwr_service.get_activities_needing_acwr_recalculation()
        
        # Get total activities count
        total_activities_query = "SELECT COUNT(*) as total FROM activities"
        total_result = db_utils.execute_query(total_activities_query, fetch=True)
        total_activities = total_result[0]['total'] if total_result else 0
        
        # Calculate completion percentage
        if total_activities > 0:
            completion_percentage = ((total_activities - len(activities_needing_recalc)) / total_activities) * 100
        else:
            completion_percentage = 100
        
        # Determine status
        if completion_percentage >= 95:
            status = 'complete'
        elif completion_percentage >= 80:
            status = 'mostly_complete'
        else:
            status = 'needs_attention'
        
        return {
            'status': status,
            'completion_percentage': round(completion_percentage, 1),
            'total_activities': total_activities,
            'activities_needing_recalculation': len(activities_needing_recalc),
            'needs_attention': status in ['mostly_complete', 'needs_attention'],
            'last_checked': datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting ACWR calculation status: {str(e)}")
        return {
            'status': 'error',
            'error': str(e),
            'needs_attention': True,
            'last_checked': datetime.now().isoformat()
        }
