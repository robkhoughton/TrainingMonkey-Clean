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
                WHERE uac.user_id = ? AND uac.is_active = TRUE AND ac.is_active = TRUE
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
            if chronic_period_days < 28:
                raise ValueError("Chronic period must be at least 28 days")
            if not (0 < decay_rate <= 1.0):
                raise ValueError("Decay rate must be between 0 and 1.0")
            
            query = """
                INSERT INTO acwr_configurations 
                (name, description, chronic_period_days, decay_rate, created_by, notes)
                VALUES (?, ?, ?, ?, ?, ?)
            """
            
            result = db_utils.execute_query(
                query, 
                (name, description, chronic_period_days, decay_rate, created_by, notes)
            )
            
            if result:
                config_id = db_utils.execute_query(
                    "SELECT last_insert_rowid()", fetch=True
                )[0]['last_insert_rowid()']
                
                self.logger.info(f"Created ACWR configuration '{name}' with ID {config_id}")
                return config_id
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error creating configuration: {str(e)}")
            return None
    
    def assign_configuration_to_user(self, user_id: int, configuration_id: int, assigned_by: int) -> bool:
        """Assign a configuration to a user"""
        try:
            # First, deactivate any existing assignments
            db_utils.execute_query(
                "UPDATE user_acwr_configurations SET is_active = FALSE WHERE user_id = ?",
                (user_id,)
            )
            
            # Create new assignment
            query = """
                INSERT INTO user_acwr_configurations (user_id, configuration_id, assigned_by)
                VALUES (?, ?, ?)
            """
            
            result = db_utils.execute_query(query, (user_id, configuration_id, assigned_by))
            
            if result:
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
                              configuration: Dict) -> Dict:
        """
        Calculate enhanced ACWR using exponential decay weighting
        
        Args:
            user_id: User ID
            activity_date: Date string in 'YYYY-MM-DD' format
            configuration: ACWR configuration dictionary
            
        Returns:
            Dictionary with enhanced ACWR calculations
        """
        try:
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
                WHERE user_id = ? AND date BETWEEN ? AND ?
                ORDER BY date
            """
            acute_activities = db_utils.execute_query(
                acute_query, (user_id, seven_days_ago, activity_date), fetch=True
            )
            
            # Get chronic activities (configurable period)
            chronic_query = """
                SELECT date, total_load_miles, trimp
                FROM activities 
                WHERE user_id = ? AND date BETWEEN ? AND ?
                ORDER BY date
            """
            chronic_activities = db_utils.execute_query(
                chronic_query, (user_id, chronic_start, activity_date), fetch=True
            )
            
            # Calculate acute averages (simple average for 7 days)
            acute_load_avg = sum(a.get('total_load_miles', 0) or 0 for a in acute_activities) / 7.0
            acute_trimp_avg = sum(a.get('trimp', 0) or 0 for a in acute_activities) / 7.0
            
            # Calculate chronic averages (exponential weighted)
            chronic_load_avg, chronic_trimp_avg = self.calculate_exponential_weighted_average(
                chronic_activities, decay_rate, date_obj
            )
            
            # Calculate ACWR ratios
            external_acwr = acute_load_avg / chronic_load_avg if chronic_load_avg > 0 else 0
            internal_acwr = acute_trimp_avg / chronic_trimp_avg if chronic_trimp_avg > 0 else 0
            
            # Calculate normalized divergence
            normalized_divergence = self.calculate_normalized_divergence(external_acwr, internal_acwr)
            
            result = {
                'user_id': user_id,
                'activity_date': activity_date,
                'configuration_id': configuration['id'],
                'chronic_period_days': chronic_days,
                'decay_rate': decay_rate,
                'acute_load_avg': round(acute_load_avg, 2),
                'acute_trimp_avg': round(acute_trimp_avg, 2),
                'enhanced_chronic_load': round(chronic_load_avg, 2),
                'enhanced_chronic_trimp': round(chronic_trimp_avg, 2),
                'enhanced_acute_chronic_ratio': round(external_acwr, 2),
                'enhanced_trimp_acute_chronic_ratio': round(internal_acwr, 2),
                'enhanced_normalized_divergence': round(normalized_divergence, 2)
            }
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error calculating enhanced ACWR: {str(e)}")
            return {}
    
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
            query = """
                INSERT INTO enhanced_acwr_calculations
                (user_id, activity_date, configuration_id, chronic_period_days, decay_rate,
                 enhanced_chronic_load, enhanced_chronic_trimp, enhanced_acute_chronic_ratio,
                 enhanced_trimp_acute_chronic_ratio, enhanced_normalized_divergence)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            
            result = db_utils.execute_query(query, (
                calculation_result['user_id'],
                calculation_result['activity_date'],
                calculation_result['configuration_id'],
                calculation_result['chronic_period_days'],
                calculation_result['decay_rate'],
                calculation_result['enhanced_chronic_load'],
                calculation_result['enhanced_chronic_trimp'],
                calculation_result['enhanced_acute_chronic_ratio'],
                calculation_result['enhanced_trimp_acute_chronic_ratio'],
                calculation_result['enhanced_normalized_divergence']
            ))
            
            return result is not None
            
        except Exception as e:
            self.logger.error(f"Error storing enhanced calculation: {str(e)}")
            return False
    
    def get_all_configurations(self) -> List[Dict]:
        """Get all ACWR configurations"""
        try:
            query = """
                SELECT ac.*, 
                       COUNT(uac.user_id) as assigned_users,
                       GROUP_CONCAT(uac.user_id) as user_ids
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
            
            query = f"UPDATE acwr_configurations SET {', '.join(updates)} WHERE id = ?"
            
            result = db_utils.execute_query(query, values)
            return result is not None
            
        except Exception as e:
            self.logger.error(f"Error updating configuration: {str(e)}")
            return False
    
    def deactivate_configuration(self, config_id: int) -> bool:
        """Deactivate a configuration"""
        try:
            query = "UPDATE acwr_configurations SET is_active = FALSE, updated_at = CURRENT_TIMESTAMP WHERE id = ?"
            result = db_utils.execute_query(query, (config_id,))
            return result is not None
            
        except Exception as e:
            self.logger.error(f"Error deactivating configuration: {str(e)}")
            return False
