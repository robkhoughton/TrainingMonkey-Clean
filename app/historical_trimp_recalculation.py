#!/usr/bin/env python3
"""
Historical TRIMP Recalculation System
Handles batch processing of activities to recalculate TRIMP values with enhanced method
"""

import logging
import time
import uuid
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

from db_utils import (
    get_activities_needing_trimp_recalculation,
    update_activity_trimp_metadata,
    save_hr_stream_data,
    get_hr_stream_data,
    execute_query
)
from strava_training_load import calculate_training_load
from utils.feature_flags import is_feature_enabled
from stravalib.client import Client

logger = logging.getLogger(__name__)


class RecalculationStatus(Enum):
    """Status of a recalculation operation"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class RecalculationOperation:
    """Represents a recalculation operation"""
    operation_id: str
    user_id: Optional[int]
    days_back: int
    force_recalculation: bool
    status: RecalculationStatus
    total_activities: int
    processed_count: int
    success_count: int
    error_count: int
    skipped_count: int
    started_at: datetime
    completed_at: Optional[datetime]
    total_processing_time_ms: int
    error_message: Optional[str] = None


@dataclass
class RecalculationResult:
    """Result of a TRIMP recalculation operation"""
    activity_id: int
    user_id: int
    success: bool
    old_trimp: Optional[float]
    new_trimp: Optional[float]
    calculation_method: str
    hr_samples_used: int
    error_message: Optional[str] = None
    processing_time_ms: Optional[int] = None


@dataclass
class BatchRecalculationResult:
    """Result of a batch TRIMP recalculation operation"""
    total_activities: int
    processed_count: int
    success_count: int
    error_count: int
    skipped_count: int
    results: List[RecalculationResult]
    total_processing_time_ms: int
    errors: List[str]


class HistoricalTrimpRecalculator:
    """Handles historical TRIMP recalculation with batch processing"""
    
    def __init__(self, strava_client: Optional[Client] = None):
        self.strava_client = strava_client
        self.batch_size = 10  # Process 10 activities at a time
        self.max_processing_time_ms = 30000  # 30 seconds max per batch
        self._active_operations: Dict[str, RecalculationOperation] = {}
        
    def recalculate_activities_batch(
        self, 
        user_id: Optional[int] = None, 
        days_back: int = 30,
        force_recalculation: bool = False
    ) -> BatchRecalculationResult:
        """
        Recalculate TRIMP values for a batch of activities
        
        Args:
            user_id: Specific user ID, or None for all users
            days_back: Number of days back to look for activities
            force_recalculation: If True, recalculate even if already processed
            
        Returns:
            BatchRecalculationResult with processing details
        """
        # Create operation tracking
        operation_id = str(uuid.uuid4())
        start_time = time.time()
        start_datetime = datetime.now()
        
        logger.info(f"Starting batch TRIMP recalculation (operation_id={operation_id}) for user_id={user_id}, days_back={days_back}")
        
        # Get activities needing recalculation
        activities = get_activities_needing_trimp_recalculation(user_id, days_back)
        
        if not activities:
            logger.info("No activities found needing TRIMP recalculation")
            return BatchRecalculationResult(
                total_activities=0,
                processed_count=0,
                success_count=0,
                error_count=0,
                skipped_count=0,
                results=[],
                total_processing_time_ms=0,
                errors=[]
            )
        
        # Filter activities if force_recalculation is False
        if not force_recalculation:
            activities = [a for a in activities if self._should_recalculate(a)]
        
        logger.info(f"Found {len(activities)} activities for recalculation")
        
        # Create operation tracking object
        operation = RecalculationOperation(
            operation_id=operation_id,
            user_id=user_id,
            days_back=days_back,
            force_recalculation=force_recalculation,
            status=RecalculationStatus.IN_PROGRESS,
            total_activities=len(activities),
            processed_count=0,
            success_count=0,
            error_count=0,
            skipped_count=0,
            started_at=start_datetime,
            completed_at=None,
            total_processing_time_ms=0
        )
        
        # Store operation for tracking
        self._active_operations[operation_id] = operation
        
        try:
            # Process activities in batches
            all_results = []
            errors = []
            processed_count = 0
            success_count = 0
            error_count = 0
            skipped_count = 0
            
            for i in range(0, len(activities), self.batch_size):
                batch = activities[i:i + self.batch_size]
                batch_start_time = time.time()
                
                logger.info(f"Processing batch {i//self.batch_size + 1}: activities {i+1}-{min(i+self.batch_size, len(activities))}")
                
                for activity in batch:
                    try:
                        result = self._recalculate_single_activity(activity)
                        all_results.append(result)
                        processed_count += 1
                        
                        # Update operation progress
                        operation.processed_count = processed_count
                        operation.success_count = success_count
                        operation.error_count = error_count
                        
                        if result.success:
                            success_count += 1
                            operation.success_count = success_count
                            logger.info(f"Successfully recalculated TRIMP for activity {result.activity_id}: "
                                      f"{result.old_trimp} -> {result.new_trimp} ({result.calculation_method})")
                        else:
                            error_count += 1
                            operation.error_count = error_count
                            error_msg = f"Activity {result.activity_id}: {result.error_message}"
                            errors.append(error_msg)
                            logger.error(error_msg)
                            
                    except Exception as e:
                        error_count += 1
                        operation.error_count = error_count
                        error_msg = f"Unexpected error processing activity {activity.get('activity_id', 'unknown')}: {str(e)}"
                        errors.append(error_msg)
                        logger.error(error_msg, exc_info=True)
                        
                        # Create error result
                        all_results.append(RecalculationResult(
                            activity_id=activity.get('activity_id', 0),
                            user_id=activity.get('user_id', 0),
                            success=False,
                            old_trimp=activity.get('trimp'),
                            new_trimp=None,
                            calculation_method='error',
                            hr_samples_used=0,
                            error_message=str(e)
                        ))
                
                # Check if we're taking too long
                batch_time_ms = (time.time() - batch_start_time) * 1000
                if batch_time_ms > self.max_processing_time_ms:
                    logger.warning(f"Batch processing time exceeded limit: {batch_time_ms}ms")
                    break
            
            total_time_ms = int((time.time() - start_time) * 1000)
            
            # Update operation as completed
            operation.status = RecalculationStatus.COMPLETED
            operation.completed_at = datetime.now()
            operation.total_processing_time_ms = total_time_ms
            operation.skipped_count = len(activities) - processed_count
            
            result = BatchRecalculationResult(
                total_activities=len(activities),
                processed_count=processed_count,
                success_count=success_count,
                error_count=error_count,
                skipped_count=len(activities) - processed_count,
                results=all_results,
                total_processing_time_ms=total_time_ms,
                errors=errors
            )
            
            logger.info(f"Batch recalculation completed (operation_id={operation_id}): {success_count} success, {error_count} errors, "
                       f"{skipped_count} skipped in {total_time_ms}ms")
            
            return result
            
        except Exception as e:
            # Update operation as failed
            operation.status = RecalculationStatus.FAILED
            operation.completed_at = datetime.now()
            operation.error_message = str(e)
            operation.total_processing_time_ms = int((time.time() - start_time) * 1000)
            
            logger.error(f"Batch recalculation failed (operation_id={operation_id}): {str(e)}", exc_info=True)
            raise
            
        finally:
            # Clean up operation tracking after 1 hour
            # In a production system, you might want to store this in a database
            pass
    
    def _should_recalculate(self, activity: Dict) -> bool:
        """Determine if an activity should be recalculated"""
        # Skip if already using enhanced method
        if activity.get('trimp_calculation_method') == 'stream':
            return False
            
        # Skip if recently processed (within last 24 hours)
        processed_at = activity.get('trimp_processed_at')
        if processed_at:
            try:
                if isinstance(processed_at, str):
                    processed_time = datetime.fromisoformat(processed_at.replace('Z', '+00:00'))
                else:
                    processed_time = processed_at
                    
                if datetime.now() - processed_time < timedelta(hours=24):
                    return False
            except Exception as e:
                logger.warning(f"Error parsing processed_at timestamp: {e}")
        
        return True
    
    def _recalculate_single_activity(self, activity: Dict) -> RecalculationResult:
        """Recalculate TRIMP for a single activity with data integrity validation"""
        start_time = time.time()
        activity_id = activity['activity_id']
        user_id = activity['user_id']
        old_trimp = activity.get('trimp')
        
        try:
            # Validate input data integrity
            validation_result = self._validate_activity_data(activity)
            if not validation_result['valid']:
                raise ValueError(f"Data validation failed: {validation_result['error']}")
            
            # Check if user has enhanced TRIMP enabled
            enhanced_enabled = is_feature_enabled('enhanced_trimp_calculation', user_id)
            
            if not enhanced_enabled:
                # User doesn't have enhanced TRIMP enabled, skip
                return RecalculationResult(
                    activity_id=activity_id,
                    user_id=user_id,
                    success=True,
                    old_trimp=old_trimp,
                    new_trimp=old_trimp,
                    calculation_method='skipped_no_access',
                    hr_samples_used=0,
                    processing_time_ms=int((time.time() - start_time) * 1000)
                )
            
            # Get HR configuration for user
            hr_config = self._get_user_hr_config(user_id)
            if not hr_config:
                raise ValueError(f"No HR configuration found for user {user_id}")
            
            # Validate HR configuration
            hr_validation = self._validate_hr_config(hr_config)
            if not hr_validation['valid']:
                raise ValueError(f"HR configuration validation failed: {hr_validation['error']}")
            
            # Try to get Strava activity data and client
            strava_activity, strava_client = self._get_strava_activity_and_client(activity_id, user_id)
            if not strava_activity or not strava_client:
                raise ValueError(f"Could not retrieve Strava activity {activity_id}")
            
            # Calculate new TRIMP with enhanced method
            load_data = calculate_training_load(strava_activity, strava_client, hr_config, user_id)
            
            new_trimp = load_data.get('trimp', 0)
            calculation_method = 'stream' if load_data.get('hr_stream_used', False) else 'average'
            hr_samples = load_data.get('hr_stream_sample_count', 0)
            
            # Validate TRIMP calculation result
            trimp_validation = self._validate_trimp_result(old_trimp, new_trimp, activity, load_data)
            if not trimp_validation['valid']:
                logger.warning(f"TRIMP validation warning for activity {activity_id}: {trimp_validation['warning']}")
                # Continue with the calculation but log the warning
            
            # Update database with new TRIMP metadata
            success = update_activity_trimp_metadata(
                activity_id=activity_id,
                user_id=user_id,
                calculation_method=calculation_method,
                sample_count=hr_samples,
                trimp_value=new_trimp
            )
            
            if not success:
                raise ValueError("Failed to update activity TRIMP metadata in database")
            
            # Verify database update
            verification_result = self._verify_database_update(activity_id, user_id, new_trimp, calculation_method)
            if not verification_result['valid']:
                logger.error(f"Database update verification failed for activity {activity_id}: {verification_result['error']}")
            
            processing_time_ms = int((time.time() - start_time) * 1000)
            
            return RecalculationResult(
                activity_id=activity_id,
                user_id=user_id,
                success=True,
                old_trimp=old_trimp,
                new_trimp=new_trimp,
                calculation_method=calculation_method,
                hr_samples_used=hr_samples,
                processing_time_ms=processing_time_ms
            )
            
        except Exception as e:
            processing_time_ms = int((time.time() - start_time) * 1000)
            error_msg = str(e)
            
            return RecalculationResult(
                activity_id=activity_id,
                user_id=user_id,
                success=False,
                old_trimp=old_trimp,
                new_trimp=None,
                calculation_method='error',
                hr_samples_used=0,
                error_message=error_msg,
                processing_time_ms=processing_time_ms
            )
    
    def _get_user_hr_config(self, user_id: int) -> Optional[Dict]:
        """Get HR configuration for a user"""
        try:
            query = """
                SELECT resting_hr, max_hr, gender 
                FROM user_settings 
                WHERE id = ?
            """
            result = execute_query(query, (user_id,), fetch=True)
            
            if result and result[0]:
                row = result[0]
                return {
                    'resting_hr': row['resting_hr'] or 60,
                    'max_hr': row['max_hr'] or 180,
                    'gender': row['gender'] or 'male'
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting HR config for user {user_id}: {e}")
            return None
    
    def _get_strava_activity_and_client(self, activity_id: int, user_id: int) -> Tuple[Optional[object], Optional[Client]]:
        """Get Strava activity data and client for a specific activity and user"""
        try:
            # Use the existing SimpleTokenManager for proper token handling
            from enhanced_token_management import SimpleTokenManager
            
            token_manager = SimpleTokenManager(user_id)
            client = token_manager.get_working_strava_client(auto_refresh=True, validate_connection=False)
            
            if not client:
                logger.warning(f"Could not get working Strava client for user {user_id}")
                return None, None
            
            # Fetch the activity from Strava
            logger.info(f"Fetching Strava activity {activity_id} for user {user_id}")
            activity = client.get_activity(activity_id)
            
            logger.info(f"Successfully retrieved Strava activity {activity_id}")
            return activity, client
            
        except Exception as e:
            logger.error(f"Error retrieving Strava activity {activity_id} for user {user_id}: {str(e)}")
            return None, None
    
    def _validate_activity_data(self, activity: Dict) -> Dict:
        """Validate activity data integrity before recalculation"""
        try:
            # Check required fields
            required_fields = ['activity_id', 'user_id']
            for field in required_fields:
                if field not in activity or activity[field] is None:
                    return {'valid': False, 'error': f'Missing required field: {field}'}
            
            # Validate activity_id
            if not isinstance(activity['activity_id'], int) or activity['activity_id'] <= 0:
                return {'valid': False, 'error': 'Invalid activity_id'}
            
            # Validate user_id
            if not isinstance(activity['user_id'], int) or activity['user_id'] <= 0:
                return {'valid': False, 'error': 'Invalid user_id'}
            
            # Validate duration if present
            duration = activity.get('duration_minutes')
            if duration is not None:
                if not isinstance(duration, (int, float)) or duration <= 0:
                    return {'valid': False, 'error': 'Invalid duration_minutes'}
                if duration > 1440:  # 24 hours
                    return {'valid': False, 'error': 'Duration too long (>24 hours)'}
            
            # Validate heart rate data if present
            avg_hr = activity.get('avg_heart_rate')
            if avg_hr is not None:
                if not isinstance(avg_hr, (int, float)) or avg_hr <= 0:
                    return {'valid': False, 'error': 'Invalid avg_heart_rate'}
                if avg_hr < 30 or avg_hr > 250:
                    return {'valid': False, 'error': 'avg_heart_rate outside physiological range'}
            
            return {'valid': True}
            
        except Exception as e:
            return {'valid': False, 'error': f'Validation error: {str(e)}'}
    
    def _validate_hr_config(self, hr_config: Dict) -> Dict:
        """Validate HR configuration data"""
        try:
            # Check required fields
            required_fields = ['resting_hr', 'max_hr', 'gender']
            for field in required_fields:
                if field not in hr_config or hr_config[field] is None:
                    return {'valid': False, 'error': f'Missing HR config field: {field}'}
            
            # Validate resting HR
            resting_hr = hr_config['resting_hr']
            if not isinstance(resting_hr, (int, float)) or resting_hr <= 0:
                return {'valid': False, 'error': 'Invalid resting_hr'}
            if resting_hr < 30 or resting_hr > 100:
                return {'valid': False, 'error': 'resting_hr outside physiological range'}
            
            # Validate max HR
            max_hr = hr_config['max_hr']
            if not isinstance(max_hr, (int, float)) or max_hr <= 0:
                return {'valid': False, 'error': 'Invalid max_hr'}
            if max_hr < 120 or max_hr > 250:
                return {'valid': False, 'error': 'max_hr outside physiological range'}
            
            # Validate HR range
            if max_hr <= resting_hr:
                return {'valid': False, 'error': 'max_hr must be greater than resting_hr'}
            
            # Validate gender
            gender = hr_config['gender']
            if not isinstance(gender, str) or gender.lower() not in ['male', 'female']:
                return {'valid': False, 'error': 'Invalid gender (must be male or female)'}
            
            return {'valid': True}
            
        except Exception as e:
            return {'valid': False, 'error': f'HR config validation error: {str(e)}'}
    
    def _validate_trimp_result(self, old_trimp: Optional[float], new_trimp: float, activity: Dict, load_data: Dict) -> Dict:
        """Validate TRIMP calculation result for reasonableness"""
        try:
            # Check if new TRIMP is valid
            if not isinstance(new_trimp, (int, float)):
                return {'valid': False, 'warning': 'TRIMP result is not a number'}
            
            if new_trimp < 0:
                return {'valid': False, 'warning': 'TRIMP result is negative'}
            
            if new_trimp > 10000:  # Unreasonably high TRIMP
                return {'valid': False, 'warning': f'TRIMP result seems unreasonably high: {new_trimp}'}
            
            # Compare with old TRIMP if available
            if old_trimp is not None and isinstance(old_trimp, (int, float)):
                # Check for extreme changes (more than 500% increase or 80% decrease)
                if old_trimp > 0:
                    change_ratio = new_trimp / old_trimp
                    if change_ratio > 5.0:  # 500% increase
                        return {'valid': True, 'warning': f'Large TRIMP increase: {old_trimp} -> {new_trimp} ({change_ratio:.1f}x)'}
                    elif change_ratio < 0.2:  # 80% decrease
                        return {'valid': True, 'warning': f'Large TRIMP decrease: {old_trimp} -> {new_trimp} ({change_ratio:.1f}x)'}
            
            # Validate against activity duration
            duration = activity.get('duration_minutes')
            if duration and duration > 0:
                # TRIMP should be roughly proportional to duration
                # Very rough heuristic: TRIMP should be between 0.1 and 50 per minute
                trimp_per_minute = new_trimp / duration
                if trimp_per_minute > 50:
                    return {'valid': True, 'warning': f'High TRIMP per minute: {trimp_per_minute:.2f}'}
                elif trimp_per_minute < 0.1:
                    return {'valid': True, 'warning': f'Low TRIMP per minute: {trimp_per_minute:.2f}'}
            
            return {'valid': True}
            
        except Exception as e:
            return {'valid': False, 'warning': f'TRIMP validation error: {str(e)}'}
    
    def _verify_database_update(self, activity_id: int, user_id: int, expected_trimp: float, expected_method: str) -> Dict:
        """Verify that the database update was successful"""
        try:
            # Query the database to verify the update
            query = """
                SELECT trimp, trimp_calculation_method, hr_stream_sample_count, trimp_processed_at
                FROM activities 
                WHERE activity_id = ? AND user_id = ?
            """
            result = execute_query(query, (activity_id, user_id), fetch=True)
            
            if not result or not result[0]:
                return {'valid': False, 'error': 'Activity not found in database after update'}
            
            row = result[0]
            actual_trimp = row['trimp']
            actual_method = row['trimp_calculation_method']
            actual_samples = row['hr_stream_sample_count']
            processed_at = row['trimp_processed_at']
            
            # Verify TRIMP value
            if abs(actual_trimp - expected_trimp) > 0.01:  # Allow small floating point differences
                return {'valid': False, 'error': f'TRIMP mismatch: expected {expected_trimp}, got {actual_trimp}'}
            
            # Verify calculation method
            if actual_method != expected_method:
                return {'valid': False, 'error': f'Method mismatch: expected {expected_method}, got {actual_method}'}
            
            # Verify processing timestamp was updated
            if not processed_at:
                return {'valid': False, 'error': 'trimp_processed_at was not updated'}
            
            return {'valid': True}
            
        except Exception as e:
            return {'valid': False, 'error': f'Database verification error: {str(e)}'}
    
    def get_recalculation_statistics(self, user_id: Optional[int] = None, days_back: int = 30) -> Dict:
        """Get statistics about activities needing recalculation"""
        try:
            activities = get_activities_needing_trimp_recalculation(user_id, days_back)
            
            if not activities:
                return {
                    'total_activities': 0,
                    'needing_recalculation': 0,
                    'using_enhanced_method': 0,
                    'using_average_method': 0,
                    'no_trimp_data': 0,
                    'recently_processed': 0
                }
            
            stats = {
                'total_activities': len(activities),
                'needing_recalculation': 0,
                'using_enhanced_method': 0,
                'using_average_method': 0,
                'no_trimp_data': 0,
                'recently_processed': 0
            }
            
            for activity in activities:
                method = activity.get('trimp_calculation_method')
                processed_at = activity.get('trimp_processed_at')
                
                if not activity.get('trimp'):
                    stats['no_trimp_data'] += 1
                elif method == 'stream':
                    stats['using_enhanced_method'] += 1
                elif method == 'average':
                    stats['using_average_method'] += 1
                else:
                    stats['needing_recalculation'] += 1
                
                # Check if recently processed
                if processed_at:
                    try:
                        if isinstance(processed_at, str):
                            processed_time = datetime.fromisoformat(processed_at.replace('Z', '+00:00'))
                        else:
                            processed_time = processed_at
                            
                        if datetime.now() - processed_time < timedelta(hours=24):
                            stats['recently_processed'] += 1
                    except Exception:
                        pass
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting recalculation statistics: {e}")
            return {'error': str(e)}
    
    def get_operation_status(self, operation_id: str) -> Optional[RecalculationOperation]:
        """Get the status of a specific recalculation operation"""
        return self._active_operations.get(operation_id)
    
    def get_active_operations(self) -> List[RecalculationOperation]:
        """Get all active recalculation operations"""
        return list(self._active_operations.values())
    
    def get_operation_history(self, limit: int = 50) -> List[RecalculationOperation]:
        """Get recent operation history (placeholder for database implementation)"""
        # In a production system, this would query a database
        # For now, return active operations
        operations = list(self._active_operations.values())
        return sorted(operations, key=lambda x: x.started_at, reverse=True)[:limit]
    
    def cancel_operation(self, operation_id: str) -> bool:
        """Cancel a running recalculation operation"""
        operation = self._active_operations.get(operation_id)
        if operation and operation.status == RecalculationStatus.IN_PROGRESS:
            operation.status = RecalculationStatus.CANCELLED
            operation.completed_at = datetime.now()
            logger.info(f"Cancelled recalculation operation {operation_id}")
            return True
        return False


# Global instance for use in routes
historical_recalculator = HistoricalTrimpRecalculator()
