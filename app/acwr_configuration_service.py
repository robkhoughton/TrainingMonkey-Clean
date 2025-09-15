#!/usr/bin/env python3
"""
ACWR Configuration Service
Handles configurable ACWR calculations with exponential decay weighting
"""

import logging
import math
from datetime import datetime, timedelta, date
from typing import Dict, List, Optional, Tuple
import db_utils
from exponential_decay_engine import ExponentialDecayEngine, ActivityData

logger = logging.getLogger(__name__)


class ACWRConfigurationService:
    """Service for managing ACWR configuration and calculations"""
    
    def __init__(self):
        self.logger = logger
    
    def get_user_configuration(self, user_id: int) -> Optional[Dict]:
        """Get the active ACWR configuration for a user"""
        try:
            query = """
                SELECT ac.*, uac.assigned_at, uac.assigned_by
                FROM acwr_configurations ac
                JOIN user_acwr_configurations uac ON ac.id = uac.configuration_id
                WHERE uac.user_id = %s AND uac.is_active = TRUE AND ac.is_active = TRUE
                ORDER BY uac.assigned_at DESC
                LIMIT 1
            """
            
            result = db_utils.execute_query(query, (user_id,), fetch=True)
            if result:
                return result[0]
            
            # If no user-specific config, get default
            return self.get_default_configuration()
            
        except Exception as e:
            self.logger.error(f"Error getting user configuration for user {user_id}: {str(e)}")
            return None
    
    def get_default_configuration(self) -> Optional[Dict]:
        """Get the default ACWR configuration"""
        try:
            query = """
                SELECT * FROM acwr_configurations 
                WHERE is_active = TRUE 
                ORDER BY created_at ASC 
                LIMIT 1
            """
            
            result = db_utils.execute_query(query, fetch=True)
            if result:
                return result[0]
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error getting default configuration: {str(e)}")
            return None
    
    def create_configuration(self, name: str, description: str, chronic_period_days: int, 
                           decay_rate: float, created_by: int, notes: str = None) -> Optional[int]:
        """Create a new ACWR configuration"""
        try:
            # Validate parameters
            if not name or not name.strip():
                raise ValueError("Configuration name is required")
            if len(name) > 100:
                raise ValueError("Configuration name must be 100 characters or less")
            if description and len(description) > 255:
                raise ValueError("Description must be 255 characters or less")
            if notes and len(notes) > 500:
                raise ValueError("Notes must be 500 characters or less")
            
            # Convert and validate chronic period
            try:
                chronic_period_days = int(chronic_period_days)
            except (ValueError, TypeError):
                raise ValueError("Chronic period must be a valid number")
            
            if chronic_period_days < 28:
                raise ValueError("Chronic period must be at least 28 days")
            if chronic_period_days > 90:
                raise ValueError("Chronic period must be 90 days or less")
            
            # Convert and validate decay rate
            try:
                decay_rate = float(decay_rate)
            except (ValueError, TypeError):
                raise ValueError("Decay rate must be a valid number")
            
            if not (0.01 <= decay_rate <= 0.20):
                raise ValueError("Decay rate must be between 0.01 and 0.20")
            
            query = """
                INSERT INTO acwr_configurations 
                (name, description, chronic_period_days, decay_rate, created_by, notes)
                VALUES (%s, %s, %s, %s, %s, %s)
                RETURNING id
            """
            
            result = db_utils.execute_query(
                query, 
                (name, description, chronic_period_days, decay_rate, created_by, notes),
                fetch=True
            )
            
            if result:
                config_id = result[0]['id']
                
                self.logger.info(f"Created ACWR configuration '{name}' with ID {config_id}")
                return config_id
            
            return None
            
        except ValueError as e:
            # Re-raise validation errors so they can be caught by calling code
            raise e
        except Exception as e:
            self.logger.error(f"Error creating configuration: {str(e)}")
            return None
    
    def assign_configuration_to_user(self, user_id: int, configuration_id: int, assigned_by: int, reason: str = None) -> bool:
        """Assign a configuration to a user with history tracking"""
        try:
            # Get current assignment for history
            current_assignment = db_utils.execute_query(
                "SELECT configuration_id FROM user_acwr_configurations WHERE user_id = %s AND is_active = TRUE",
                (user_id,), fetch=True
            )
            previous_config_id = current_assignment[0]['configuration_id'] if current_assignment else None
            
            # First, deactivate any existing assignments
            db_utils.execute_query(
                "UPDATE user_acwr_configurations SET is_active = FALSE, unassigned_at = CURRENT_TIMESTAMP, unassigned_by = %s WHERE user_id = %s AND is_active = TRUE",
                (assigned_by, user_id)
            )
            
            # Create new assignment
            query = """
                INSERT INTO user_acwr_configurations (user_id, configuration_id, assigned_by, assignment_reason)
                VALUES (%s, %s, %s, %s)
            """
            
            result = db_utils.execute_query(query, (user_id, configuration_id, assigned_by, reason))
            
            if result:
                # Log assignment history
                self._log_assignment_history(
                    user_id=user_id,
                    configuration_id=configuration_id,
                    assigned_by=assigned_by,
                    action='ASSIGNED',
                    previous_config_id=previous_config_id,
                    reason=reason
                )
                
                self.logger.info(f"Assigned configuration {configuration_id} to user {user_id}")
                return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Error assigning configuration to user: {str(e)}")
            return False
    
    def calculate_exponential_weighted_average(self, activities: List[Dict], 
                                             decay_rate: float, 
                                             current_date: date) -> Tuple[float, float]:
        """
        Calculate exponential weighted average for chronic load and TRIMP
        
        Args:
            activities: List of activity dictionaries with 'date', 'total_load_miles', 'trimp'
            decay_rate: Exponential decay rate (higher = more weight to recent activities)
            current_date: Reference date for calculating days ago
            
        Returns:
            Tuple of (weighted_load_average, weighted_trimp_average)
        """
        if not activities:
            return 0.0, 0.0
        
        total_weighted_load = 0.0
        total_weighted_trimp = 0.0
        total_weight = 0.0
        
        for activity in activities:
            # Parse activity date
            if isinstance(activity['date'], str):
                activity_date = datetime.strptime(activity['date'], '%Y-%m-%d').date()
            else:
                activity_date = activity['date']
            
            # Calculate days ago
            days_ago = (current_date - activity_date).days
            
            # Skip future activities
            if days_ago < 0:
                continue
            
            # Calculate exponential weight: weight = e^(-decay_rate * days_ago)
            weight = math.exp(-decay_rate * days_ago)
            
            # Get activity values (handle None values)
            load = activity.get('total_load_miles', 0) or 0
            trimp = activity.get('trimp', 0) or 0
            
            # Add to weighted sums
            total_weighted_load += load * weight
            total_weighted_trimp += trimp * weight
            total_weight += weight
        
        # Calculate weighted averages
        if total_weight > 0:
            weighted_load_avg = total_weighted_load / total_weight
            weighted_trimp_avg = total_weighted_trimp / total_weight
        else:
            weighted_load_avg = 0.0
            weighted_trimp_avg = 0.0
        
        return weighted_load_avg, weighted_trimp_avg
    
    def calculate_enhanced_acwr(self, user_id: int, activity_date: str, 
                              configuration: Optional[Dict] = None) -> Dict:
        """
        Calculate enhanced ACWR using exponential decay weighting
        
        Args:
            user_id: User ID
            activity_date: Date string in 'YYYY-MM-DD' format
            configuration: ACWR configuration dictionary (optional, will retrieve if not provided)
            
        Returns:
            Dictionary with enhanced ACWR calculations
        """
        try:
            # Get user configuration if not provided
            if configuration is None:
                configuration = self.get_user_configuration(user_id)
                if configuration is None:
                    return {
                        'success': False,
                        'error': 'No ACWR configuration found for user',
                        'fallback_to_standard': True
                    }
            
            # Parse dates
            date_obj = datetime.strptime(activity_date, '%Y-%m-%d').date()
            seven_days_ago = (date_obj - timedelta(days=6)).strftime('%Y-%m-%d')
            chronic_days = configuration['chronic_period_days']
            chronic_start = (date_obj - timedelta(days=chronic_days-1)).strftime('%Y-%m-%d')
            decay_rate = configuration['decay_rate']
            
            # Get acute activities (7 days)
            acute_query = """
                SELECT date, total_load_miles, trimp
                FROM activities 
                WHERE user_id = %s AND date BETWEEN %s AND %s
                ORDER BY date
            """
            acute_activities_result = db_utils.execute_query(
                acute_query, (user_id, seven_days_ago, activity_date), fetch=True
            )
            
            # Get chronic activities (configurable period)
            chronic_query = """
                SELECT date, total_load_miles, trimp
                FROM activities 
                WHERE user_id = %s AND date BETWEEN %s AND %s
                ORDER BY date
            """
            chronic_activities_result = db_utils.execute_query(
                chronic_query, (user_id, chronic_start, activity_date), fetch=True
            )
            
            # Convert to ActivityData objects for exponential decay engine
            acute_activities = []
            for row in acute_activities_result:
                try:
                    activity_date_obj = datetime.strptime(row['date'], '%Y-%m-%d').date() if isinstance(row['date'], str) else row['date']
                    acute_activities.append(ActivityData(
                        date=activity_date_obj,
                        total_load_miles=row['total_load_miles'] or 0.0,
                        trimp=row['trimp'] or 0.0
                    ))
                except Exception as e:
                    self.logger.warning(f"Error processing acute activity: {str(e)}")
                    continue

            chronic_activities = []
            for row in chronic_activities_result:
                try:
                    activity_date_obj = datetime.strptime(row['date'], '%Y-%m-%d').date() if isinstance(row['date'], str) else row['date']
                    chronic_activities.append(ActivityData(
                        date=activity_date_obj,
                        total_load_miles=row['total_load_miles'] or 0.0,
                        trimp=row['trimp'] or 0.0
                    ))
                except Exception as e:
                    self.logger.warning(f"Error processing chronic activity: {str(e)}")
                    continue
            
            # Use exponential decay engine for enhanced calculation
            decay_engine = ExponentialDecayEngine()
            
            # Calculate acute averages (simple average for 7 days - no exponential decay)
            acute_load_avg = sum(a.total_load_miles for a in acute_activities) / 7.0 if acute_activities else 0.0
            acute_trimp_avg = sum(a.trimp for a in acute_activities) / 7.0 if acute_activities else 0.0
            
            # Calculate chronic averages using exponential decay engine
            chronic_result = decay_engine.calculate_weighted_averages(
                chronic_activities, date_obj, decay_rate
            )
            
            chronic_load_avg = chronic_result.weighted_load_avg
            chronic_trimp_avg = chronic_result.weighted_trimp_avg
            
            # Calculate ACWR ratios
            external_acwr = acute_load_avg / chronic_load_avg if chronic_load_avg > 0 else 0
            internal_acwr = acute_trimp_avg / chronic_trimp_avg if chronic_trimp_avg > 0 else 0
            
            # Calculate normalized divergence
            normalized_divergence = self.calculate_normalized_divergence(external_acwr, internal_acwr)
            
            result = {
                'success': True,
                'user_id': user_id,
                'activity_date': activity_date,
                'configuration_id': configuration.get('id', 'temp'),  # Handle temporary configs without ID
                'chronic_period_days': chronic_days,
                'decay_rate': decay_rate,
                'acute_load_avg': round(acute_load_avg, 2),
                'acute_trimp_avg': round(acute_trimp_avg, 2),
                'enhanced_chronic_load': round(chronic_load_avg, 2),
                'enhanced_chronic_trimp': round(chronic_trimp_avg, 2),
                'enhanced_acute_chronic_ratio': round(external_acwr, 2),
                'enhanced_trimp_acute_chronic_ratio': round(internal_acwr, 2),
                'enhanced_normalized_divergence': round(normalized_divergence, 2),
                'calculation_method': 'exponential_decay_engine',
                'data_quality': chronic_result.data_quality if hasattr(chronic_result, 'data_quality') else 'unknown'
            }
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error calculating enhanced ACWR: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'fallback_to_standard': True
            }
    
    def calculate_normalized_divergence(self, external_acwr: float, internal_acwr: float) -> float:
        """Calculate normalized divergence between external and internal ACWR"""
        if external_acwr == 0 and internal_acwr == 0:
            return 0.0
        
        mean_acwr = (external_acwr + internal_acwr) / 2
        if mean_acwr == 0:
            return 0.0
        
        return (external_acwr - internal_acwr) / mean_acwr
    
    def store_enhanced_calculation(self, calculation_result: Dict) -> bool:
        """Store enhanced ACWR calculation result"""
        try:
            # Use the migration system table that actually exists
            query = """
                INSERT INTO acwr_enhanced_calculations
                (user_id, activity_id, configuration_id, acwr_ratio, acute_load, chronic_load,
                 calculation_method, created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            
            # Get activity_id from activity_date
            activity_id = self._get_activity_id_by_date(
                calculation_result['user_id'], 
                calculation_result['activity_date']
            )
            
            if not activity_id:
                self.logger.warning(f"Could not find activity_id for date {calculation_result['activity_date']}")
                return False
            
            result = db_utils.execute_query(query, (
                calculation_result['user_id'],
                activity_id,
                calculation_result['configuration_id'],
                calculation_result['enhanced_acute_chronic_ratio'],  # acwr_ratio
                calculation_result['enhanced_chronic_load'],        # acute_load
                calculation_result['enhanced_chronic_trimp'],       # chronic_load
                'enhanced',                                         # calculation_method
                'NOW()',                                           # created_at
                'NOW()'                                            # updated_at
            ))
            
            return result is not None
            
        except Exception as e:
            self.logger.error(f"Error storing enhanced calculation: {str(e)}")
            return False
    
    def _get_activity_id_by_date(self, user_id: int, activity_date: str) -> Optional[int]:
        """Get activity_id for a given user and date"""
        try:
            query = """
                SELECT activity_id FROM activities 
                WHERE user_id = %s AND date = %s
                LIMIT 1
            """
            result = db_utils.execute_query(query, (user_id, activity_date), fetch=True)
            if result and len(result) > 0:
                return result[0]['activity_id']
            return None
        except Exception as e:
            self.logger.error(f"Error getting activity_id for date {activity_date}: {str(e)}")
            return None
    
    def get_all_configurations(self) -> List[Dict]:
        """Get all ACWR configurations"""
        try:
            query = """
                SELECT ac.*, 
                       COUNT(uac.user_id) as assigned_users,
                       STRING_AGG(CAST(uac.user_id AS TEXT), ',') as user_ids
                FROM acwr_configurations ac
                LEFT JOIN user_acwr_configurations uac ON ac.id = uac.configuration_id AND uac.is_active = TRUE
                GROUP BY ac.id
                ORDER BY ac.created_at DESC
            """
            
            return db_utils.execute_query(query, fetch=True)
            
        except Exception as e:
            self.logger.error(f"Error getting all configurations: {str(e)}")
            return []
    
    def update_configuration(self, config_id: int, **kwargs) -> bool:
        """Update an existing configuration"""
        try:
            # Build dynamic update query
            allowed_fields = ['name', 'description', 'chronic_period_days', 'decay_rate', 'notes']
            updates = []
            values = []
            
            for field, value in kwargs.items():
                if field in allowed_fields:
                    updates.append(f"{field} = ?")
                    values.append(value)
            
            if not updates:
                return False
            
            # Add updated_at timestamp
            updates.append("updated_at = CURRENT_TIMESTAMP")
            values.append(config_id)
            
            query = f"UPDATE acwr_configurations SET {', '.join(updates)} WHERE id = %s"
            
            result = db_utils.execute_query(query, values)
            return result is not None
            
        except Exception as e:
            self.logger.error(f"Error updating configuration: {str(e)}")
            return False
    
    def get_configuration_by_id(self, config_id: int) -> Optional[Dict]:
        """Get a specific configuration by ID"""
        try:
            query = """
                SELECT * FROM acwr_configurations 
                WHERE id = %s
            """
            
            result = db_utils.execute_query(query, (config_id,), fetch=True)
            return result[0] if result else None
            
        except Exception as e:
            self.logger.error(f"Error getting configuration by ID: {str(e)}")
            return None
    
    def delete_configuration(self, config_id: int) -> bool:
        """Delete a configuration (soft delete by setting is_active = FALSE)"""
        try:
            # First, unassign all users from this configuration
            unassign_query = """
                UPDATE user_acwr_configurations 
                SET is_active = FALSE, unassigned_at = CURRENT_TIMESTAMP
                WHERE configuration_id = %s AND is_active = TRUE
            """
            db_utils.execute_query(unassign_query, (config_id,))
            
            # Then soft delete the configuration
            delete_query = """
                UPDATE acwr_configurations 
                SET is_active = FALSE, deleted_at = CURRENT_TIMESTAMP
                WHERE id = %s AND is_default = FALSE
            """
            
            result = db_utils.execute_query(delete_query, (config_id,))
            return result is not None
            
        except Exception as e:
            self.logger.error(f"Error deleting configuration: {str(e)}")
            return False
    
    def unassign_configuration_from_user(self, config_id: int, user_id: int) -> bool:
        """Remove a configuration assignment from a user"""
        try:
            query = """
                UPDATE user_acwr_configurations 
                SET is_active = FALSE, unassigned_at = CURRENT_TIMESTAMP
                WHERE configuration_id = %s AND user_id = %s AND is_active = TRUE
            """
            
            result = db_utils.execute_query(query, (config_id, user_id))
            return result is not None
            
        except Exception as e:
            self.logger.error(f"Error unassigning configuration from user: {str(e)}")
            return False
    
    def get_configuration_user_count(self, config_id: int) -> int:
        """Get the number of users assigned to a configuration"""
        try:
            query = """
                SELECT COUNT(*) as user_count
                FROM user_acwr_configurations 
                WHERE configuration_id = %s AND is_active = TRUE
            """
            
            result = db_utils.execute_query(query, (config_id,), fetch=True)
            return result[0]['user_count'] if result else 0
            
        except Exception as e:
            self.logger.error(f"Error getting configuration user count: {str(e)}")
            return 0
    
    def get_configuration_users(self, config_id: int) -> List[Dict]:
        """Get all users assigned to a specific configuration"""
        try:
            query = """
                SELECT uac.user_id, uac.assigned_at, uac.assigned_by
                FROM user_acwr_configurations uac
                WHERE uac.configuration_id = %s AND uac.is_active = TRUE
                ORDER BY uac.assigned_at DESC
            """
            
            return db_utils.execute_query(query, (config_id,), fetch=True)
            
        except Exception as e:
            self.logger.error(f"Error getting configuration users: {str(e)}")
            return []
    
    def get_configuration_statistics(self) -> Dict:
        """Get configuration usage statistics"""
        try:
            # Total configurations
            total_configs_query = """
                SELECT COUNT(*) as total
                FROM acwr_configurations 
                WHERE is_active = TRUE
            """
            total_configs = db_utils.execute_query(total_configs_query, fetch=True)[0]['total']
            
            # Total user assignments
            total_assignments_query = """
                SELECT COUNT(*) as total
                FROM user_acwr_configurations 
                WHERE is_active = TRUE
            """
            total_assignments = db_utils.execute_query(total_assignments_query, fetch=True)[0]['total']
            
            # Most used configuration
            most_used_query = """
                SELECT ac.name, COUNT(uac.user_id) as user_count
                FROM acwr_configurations ac
                LEFT JOIN user_acwr_configurations uac ON ac.id = uac.configuration_id AND uac.is_active = TRUE
                WHERE ac.is_active = TRUE
                GROUP BY ac.id, ac.name
                ORDER BY user_count DESC
                LIMIT 1
            """
            most_used_result = db_utils.execute_query(most_used_query, fetch=True)
            most_used = most_used_result[0] if most_used_result else {'name': 'None', 'user_count': 0}
            
            # Configuration distribution
            distribution_query = """
                SELECT ac.name, ac.chronic_period_days, ac.decay_rate, COUNT(uac.user_id) as user_count
                FROM acwr_configurations ac
                LEFT JOIN user_acwr_configurations uac ON ac.id = uac.configuration_id AND uac.is_active = TRUE
                WHERE ac.is_active = TRUE
                GROUP BY ac.id, ac.name, ac.chronic_period_days, ac.decay_rate
                ORDER BY user_count DESC
            """
            distribution = db_utils.execute_query(distribution_query, fetch=True)
            
            return {
                'total_configurations': total_configs,
                'total_assignments': total_assignments,
                'most_used_configuration': most_used,
                'configuration_distribution': distribution
            }
            
        except Exception as e:
            self.logger.error(f"Error getting configuration statistics: {str(e)}")
            return {
                'total_configurations': 0,
                'total_assignments': 0,
                'most_used_configuration': {'name': 'None', 'user_count': 0},
                'configuration_distribution': []
            }
    
    def deactivate_configuration(self, config_id: int, reason: str = None) -> bool:
        """Deactivate a configuration with optional reason"""
        try:
            # First, unassign all users from this configuration
            unassign_query = """
                UPDATE user_acwr_configurations 
                SET is_active = FALSE, unassigned_at = CURRENT_TIMESTAMP
                WHERE configuration_id = %s AND is_active = TRUE
            """
            db_utils.execute_query(unassign_query, (config_id,))
            
            # Then deactivate the configuration
            query = """
                UPDATE acwr_configurations 
                SET %s = %s
                WHERE id = %s AND is_default = FALSE
            """
            result = db_utils.execute_query(query, (reason, config_id))
            return result is not None
            
        except Exception as e:
            self.logger.error(f"Error deactivating configuration: {str(e)}")
            return False
    
    def reactivate_configuration(self, config_id: int) -> bool:
        """Reactivate a configuration"""
        try:
            query = """
                UPDATE acwr_configurations 
                SET is_active = TRUE, updated_at = CURRENT_TIMESTAMP, deactivation_reason = NULL
                WHERE id = %s AND is_default = FALSE
            """
            result = db_utils.execute_query(query, (config_id,))
            return result is not None
            
        except Exception as e:
            self.logger.error(f"Error reactivating configuration: {str(e)}")
            return False
    
    def _log_assignment_history(self, user_id: int, configuration_id: int, assigned_by: int, 
                               action: str, previous_config_id: int = None, reason: str = None) -> bool:
        """Log assignment history for audit trail"""
        try:
            query = """
                INSERT INTO assignment_history 
                (user_id, configuration_id, assigned_by, action, previous_config_id, reason, timestamp)
                VALUES (%s, CURRENT_TIMESTAMP)
            """
            
            result = db_utils.execute_query(query, (user_id, configuration_id, assigned_by, action, previous_config_id, reason))
            return result is not None
            
        except Exception as e:
            self.logger.error(f"Error logging assignment history: {str(e)}")
            return False
    
    def get_assignment_history(self, user_id: int = None, configuration_id: int = None, limit: int = 100) -> List[Dict]:
        """Get assignment history with admin attribution"""
        try:
            conditions = []
            params = []
            
            if user_id:
                conditions.append("ah.user_id = ?")
                params.append(user_id)
            
            if configuration_id:
                conditions.append("ah.configuration_id = ?")
                params.append(configuration_id)
            
            where_clause = "WHERE " + " AND ".join(conditions) if conditions else ""
            
            query = f"""
                SELECT 
                    ah.*,
                    u.email as user_name,
                    u.email as user_email,
                    ac.name as configuration_name,
                    admin.email as admin_name,
                    admin.email as admin_email,
                    prev_ac.name as previous_configuration_name
                FROM assignment_history ah
                LEFT JOIN user_settings u ON ah.user_id = u.id
                LEFT JOIN acwr_configurations ac ON ah.configuration_id = ac.id
                LEFT JOIN user_settings admin ON ah.assigned_by = admin.id
                LEFT JOIN acwr_configurations prev_ac ON ah.previous_config_id = prev_ac.id
                {where_clause}
                ORDER BY ah.timestamp DESC
                LIMIT %s
            """
            
            params.append(limit)
            result = db_utils.execute_query(query, params, fetch=True)
            return result if result else []
            
        except Exception as e:
            self.logger.error(f"Error getting assignment history: {str(e)}")
            return []
    
    def get_user_assignment_history(self, user_id: int, limit: int = 50) -> List[Dict]:
        """Get assignment history for a specific user"""
        return self.get_assignment_history(user_id=user_id, limit=limit)
    
    def get_configuration_assignment_history(self, configuration_id: int, limit: int = 50) -> List[Dict]:
        """Get assignment history for a specific configuration"""
        return self.get_assignment_history(configuration_id=configuration_id, limit=limit)
    
    def get_admin_assignment_history(self, admin_id: int, limit: int = 50) -> List[Dict]:
        """Get assignment history for a specific admin"""
        try:
            query = """
                SELECT 
                    ah.*,
                    u.email as user_name,
                    u.email as user_email,
                    ac.name as configuration_name,
                    admin.email as admin_name,
                    admin.email as admin_email,
                    prev_ac.name as previous_configuration_name
                FROM assignment_history ah
                LEFT JOIN user_settings u ON ah.user_id = u.id
                LEFT JOIN acwr_configurations ac ON ah.configuration_id = ac.id
                LEFT JOIN user_settings admin ON ah.assigned_by = admin.id
                LEFT JOIN acwr_configurations prev_ac ON ah.previous_config_id = prev_ac.id
                WHERE ah.assigned_by = %s
                ORDER BY ah.timestamp DESC
                LIMIT %s
            """
            
            result = db_utils.execute_query(query, (admin_id, limit), fetch=True)
            return result if result else []
            
        except Exception as e:
            self.logger.error(f"Error getting admin assignment history: {str(e)}")
            return []
    
    def rollback_assignment(self, user_id: int, configuration_id: int, rollback_to_config_id: int, 
                          rolled_back_by: int, reason: str = None) -> bool:
        """Rollback a user's configuration assignment to a previous configuration"""
        try:
            # Get current assignment
            current_assignment = db_utils.execute_query(
                "SELECT configuration_id FROM user_acwr_configurations WHERE user_id = %s AND is_active = TRUE",
                (user_id,), fetch=True
            )
            
            if not current_assignment:
                self.logger.error(f"No active assignment found for user {user_id}")
                return False
            
            current_config_id = current_assignment[0]['configuration_id']
            
            # Deactivate current assignment
            db_utils.execute_query(
                "UPDATE user_acwr_configurations SET is_active = FALSE, unassigned_at = CURRENT_TIMESTAMP, unassigned_by = %s WHERE user_id = %s AND is_active = TRUE",
                (rolled_back_by, user_id)
            )
            
            # Create rollback assignment
            query = """
                INSERT INTO user_acwr_configurations (user_id, configuration_id, assigned_by, assignment_reason)
                VALUES (%s, %s, %s, %s)
            """
            
            rollback_reason = f"Rollback from {current_config_id} to {rollback_to_config_id}"
            if reason:
                rollback_reason += f" - {reason}"
            
            result = db_utils.execute_query(query, (user_id, rollback_to_config_id, rolled_back_by, rollback_reason))
            
            if result:
                # Log rollback history
                self._log_assignment_history(
                    user_id=user_id,
                    configuration_id=rollback_to_config_id,
                    assigned_by=rolled_back_by,
                    action='ROLLBACK',
                    previous_config_id=current_config_id,
                    reason=rollback_reason
                )
                
                self.logger.info(f"Rolled back user {user_id} from config {current_config_id} to {rollback_to_config_id}")
                return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Error rolling back assignment: {str(e)}")
            return False
    
    def bulk_rollback_assignments(self, rollback_requests: List[Dict], rolled_back_by: int, reason: str = None) -> Dict:
        """Bulk rollback multiple assignment configurations"""
        try:
            results = {
                'successful': [],
                'failed': [],
                'total': len(rollback_requests)
            }
            
            for request in rollback_requests:
                user_id = request.get('user_id')
                configuration_id = request.get('configuration_id')
                rollback_to_config_id = request.get('rollback_to_config_id')
                
                if not all([user_id, configuration_id, rollback_to_config_id]):
                    results['failed'].append({
                        'user_id': user_id,
                        'error': 'Missing required parameters'
                    })
                    continue
                
                success = self.rollback_assignment(
                    user_id=user_id,
                    configuration_id=configuration_id,
                    rollback_to_config_id=rollback_to_config_id,
                    rolled_back_by=rolled_back_by,
                    reason=reason
                )
                
                if success:
                    results['successful'].append({
                        'user_id': user_id,
                        'from_config': configuration_id,
                        'to_config': rollback_to_config_id
                    })
                else:
                    results['failed'].append({
                        'user_id': user_id,
                        'error': 'Rollback failed'
                    })
            
            return results
            
        except Exception as e:
            self.logger.error(f"Error in bulk rollback: {str(e)}")
            return {
                'successful': [],
                'failed': [],
                'total': len(rollback_requests),
                'error': str(e)
            }
    
    def get_rollback_options(self, user_id: int, limit: int = 10) -> List[Dict]:
        """Get available rollback options for a user based on their assignment history"""
        try:
            query = """
                SELECT DISTINCT
                    ah.configuration_id,
                    ac.name as configuration_name,
                    ac.chronic_period_days,
                    ac.decay_rate,
                    MAX(ah.timestamp) as last_assigned
                FROM assignment_history ah
                JOIN acwr_configurations ac ON ah.configuration_id = ac.id
                WHERE ah.user_id = %s 
                AND ah.action IN ('ASSIGNED', 'ROLLBACK')
                AND ac.is_active = TRUE
                AND ah.configuration_id != (
                    SELECT configuration_id 
                    FROM user_acwr_configurations 
                    WHERE user_id = %s AND is_active = TRUE
                )
                GROUP BY ah.configuration_id, ac.name, ac.chronic_period_days, ac.decay_rate
                ORDER BY last_assigned DESC
                LIMIT %s
            """
            
            result = db_utils.execute_query(query, (user_id, user_id, limit), fetch=True)
            return result if result else []
            
        except Exception as e:
            self.logger.error(f"Error getting rollback options: {str(e)}")
            return []
    
    def get_rollback_impact_analysis(self, rollback_requests: List[Dict]) -> Dict:
        """Analyze the impact of rollback operations"""
        try:
            impact = {
                'total_users': len(rollback_requests),
                'configurations_affected': set(),
                'impact_level': 'LOW',
                'warnings': []
            }
            
            for request in rollback_requests:
                configuration_id = request.get('configuration_id')
                rollback_to_config_id = request.get('rollback_to_config_id')
                
                if configuration_id:
                    impact['configurations_affected'].add(configuration_id)
                if rollback_to_config_id:
                    impact['configurations_affected'].add(rollback_to_config_id)
            
            impact['configurations_affected'] = list(impact['configurations_affected'])
            
            # Determine impact level
            if len(rollback_requests) > 50:
                impact['impact_level'] = 'HIGH'
                impact['warnings'].append('High volume rollback - affects many users')
            elif len(rollback_requests) > 10:
                impact['impact_level'] = 'MEDIUM'
                impact['warnings'].append('Medium volume rollback - review impact carefully')
            
            if len(impact['configurations_affected']) > 5:
                impact['warnings'].append('Multiple configurations affected')
            
            return impact
            
        except Exception as e:
            self.logger.error(f"Error analyzing rollback impact: {str(e)}")
            return {
                'total_users': 0,
                'configurations_affected': [],
                'impact_level': 'UNKNOWN',
                'warnings': [f'Error analyzing impact: {str(e)}']
            }
    
    def get_sample_user_for_preview(self) -> Dict:
        """Get a sample user with activities for preview calculations"""
        try:
            # Get a user who has activities in the last 90 days
            query = """
                SELECT DISTINCT u.id, u.email, u.email
                FROM user_settings u
                JOIN activities a ON u.id = a.user_id
                WHERE a.date >= CURRENT_DATE - INTERVAL '90 days'
                ORDER BY u.id
                LIMIT 1
            """
            
            result = db_utils.execute_query(query, fetch=True)
            if result:
                return result[0]
            
            # Fallback: get any active user
            query = """
                SELECT id, email, email
                FROM user_settings
                ORDER BY id
                LIMIT 1
            """
            
            result = db_utils.execute_query(query, fetch=True)
            return result[0] if result else None
            
        except Exception as e:
            self.logger.error(f"Error getting sample user for preview: {str(e)}")
            return None
    
    def get_users_with_configuration(self, configuration_id: int) -> List[int]:
        """Get all user IDs assigned to a specific configuration"""
        try:
            query = """
                SELECT user_id
                FROM user_acwr_configurations
                WHERE configuration_id = %s AND is_active = TRUE
            """
            
            result = db_utils.execute_query(query, (configuration_id,), fetch=True)
            return [row['user_id'] for row in result] if result else []
            
        except Exception as e:
            self.logger.error(f"Error getting users with configuration: {str(e)}")
            return []
    
    def get_all_active_users(self) -> List[int]:
        """Get all active user IDs"""
        try:
            query = """
                SELECT id
                FROM user_settings
            """
            
            result = db_utils.execute_query(query, fetch=True)
            return [row['id'] for row in result] if result else []
            
        except Exception as e:
            self.logger.error(f"Error getting all active users: {str(e)}")
            return []
    
    def get_admin_user(self, admin_user_id: int) -> Dict:
        """Get admin user details for authentication"""
        try:
            query = """
                SELECT id, email, email, is_admin, is_admin
                FROM user_settings
                WHERE id = %s AND is_admin = TRUE
            """
            
            result = db_utils.execute_query(query, (admin_user_id,), fetch=True)
            return result[0] if result else None
            
        except Exception as e:
            self.logger.error(f"Error getting admin user: {str(e)}")
            return None
