#!/usr/bin/env python3
"""
ACWR Calculation Service
Handles both enhanced and standard ACWR calculations with feature flag integration
"""

import logging
from datetime import datetime, timedelta, date
from typing import Dict, Optional, Tuple
from utils.feature_flags import is_feature_enabled
from acwr_configuration_service import ACWRConfigurationService
from acwr_feature_flag_monitor import log_acwr_feature_access, log_acwr_feature_error

# Import db_utils with fallback for testing
try:
    import db_utils
except ImportError:
    # Mock db_utils for testing
    class MockDBUtils:
        @staticmethod
        def execute_query(query, params=None, fetch=False):
            if fetch:
                return [{'sum_load': 0, 'sum_trimp': 0}]
            return None
    db_utils = MockDBUtils()

logger = logging.getLogger(__name__)

class ACWRCalculationService:
    """Service for ACWR calculations with feature flag integration"""
    
    def __init__(self):
        self.acwr_config_service = ACWRConfigurationService()
    
    def calculate_acwr(self, acute_activities, chronic_activities, reference_date, user_id):
        """
        Calculate ACWR using the provided activity data
        This method is called by strava_training_load.py
        
        Args:
            acute_activities: List of ActivityData objects for acute period (7 days)
            chronic_activities: List of ActivityData objects for chronic period
            reference_date: Reference date for calculations
            user_id: User ID
            
        Returns:
            Dictionary with ACWR calculation results
        """
        try:
            # Check if enhanced ACWR is enabled for this user
            enhanced_enabled = is_feature_enabled('enhanced_acwr_calculation', user_id)
            
            if enhanced_enabled:
                # Use enhanced calculation with user-specific configuration
                activity_date_str = reference_date.strftime('%Y-%m-%d')
                result = self.acwr_config_service.calculate_enhanced_acwr(user_id, activity_date_str)
                
                if result.get('success', False):
                    # Convert to format expected by strava_training_load.py
                    return {
                        'success': True,
                        'acute_load_avg': result.get('acute_load_avg', 0.0),
                        'chronic_load_avg': result.get('enhanced_chronic_load', 0.0),
                        'acute_trimp_avg': result.get('acute_trimp_avg', 0.0),
                        'chronic_trimp_avg': result.get('enhanced_chronic_trimp', 0.0),
                        'acute_chronic_ratio': result.get('enhanced_acute_chronic_ratio', 0.0),
                        'trimp_acute_chronic_ratio': result.get('enhanced_trimp_acute_chronic_ratio', 0.0),
                        'normalized_divergence': result.get('enhanced_normalized_divergence', 0.0),
                        'calculation_method': result.get('calculation_method', 'enhanced'),
                        'data_quality': result.get('data_quality', 'unknown')
                    }
                else:
                    # Enhanced calculation failed, fall back to standard
                    return self._calculate_standard_acwr_from_activities(
                        acute_activities, chronic_activities, reference_date, user_id
                    )
            else:
                # Use standard calculation
                return self._calculate_standard_acwr_from_activities(
                    acute_activities, chronic_activities, reference_date, user_id
                )
                
        except Exception as e:
            logger.error(f"Error in calculate_acwr: {str(e)}")
            # Fall back to standard calculation
            return self._calculate_standard_acwr_from_activities(
                acute_activities, chronic_activities, reference_date, user_id
            )
    
    def _calculate_standard_acwr_from_activities(self, acute_activities, chronic_activities, reference_date, user_id):
        """
        Calculate standard ACWR from provided activity data
        """
        try:
            # Calculate acute averages (7 days)
            acute_load_avg = sum(a.total_load_miles for a in acute_activities) / 7.0 if acute_activities else 0.0
            acute_trimp_avg = sum(a.trimp for a in acute_activities) / 7.0 if acute_activities else 0.0
            
            # Calculate chronic averages (28 days)
            chronic_load_avg = sum(a.total_load_miles for a in chronic_activities) / 28.0 if chronic_activities else 0.0
            chronic_trimp_avg = sum(a.trimp for a in chronic_activities) / 28.0 if chronic_activities else 0.0
            
            # Calculate ACWR ratios
            acute_chronic_ratio = acute_load_avg / chronic_load_avg if chronic_load_avg > 0 else 0
            trimp_acute_chronic_ratio = acute_trimp_avg / chronic_trimp_avg if chronic_trimp_avg > 0 else 0
            
            # Calculate normalized divergence
            normalized_divergence = self._calculate_normalized_divergence(acute_chronic_ratio, trimp_acute_chronic_ratio)
            
            return {
                'success': True,
                'acute_load_avg': round(acute_load_avg, 2),
                'chronic_load_avg': round(chronic_load_avg, 2),
                'acute_trimp_avg': round(acute_trimp_avg, 2),
                'chronic_trimp_avg': round(chronic_trimp_avg, 2),
                'acute_chronic_ratio': round(acute_chronic_ratio, 2),
                'trimp_acute_chronic_ratio': round(trimp_acute_chronic_ratio, 2),
                'normalized_divergence': round(normalized_divergence, 2),
                'calculation_method': 'standard'
            }
            
        except Exception as e:
            logger.error(f"Error in standard ACWR calculation: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'calculation_method': 'standard'
            }
    
    def _calculate_normalized_divergence(self, external_acwr, internal_acwr):
        """Calculate normalized divergence between external and internal ACWR"""
        if external_acwr == 0 and internal_acwr == 0:
            return 0.0
        
        avg_acwr = (external_acwr + internal_acwr) / 2
        if avg_acwr == 0:
            return 0.0
        
        return round((external_acwr - internal_acwr) / avg_acwr, 3)
    
    def calculate_acwr_for_user(self, user_id: int, activity_date: str) -> Dict:
        """
        Calculate ACWR for a user based on feature flag status
        
        Args:
            user_id: User ID
            activity_date: Date string in 'YYYY-MM-DD' format
            
        Returns:
            Dictionary with ACWR calculation results
        """
        try:
            # Check if enhanced ACWR is enabled for this user
            enhanced_enabled = is_feature_enabled('enhanced_acwr_calculation', user_id)
            
            if enhanced_enabled:
                logger.info(f"🎉 Using enhanced ACWR calculation for user {user_id}")
                return self._calculate_enhanced_acwr(user_id, activity_date)
            else:
                logger.info(f"📊 Using standard 28-day ACWR calculation for user {user_id}")
                return self._calculate_standard_acwr(user_id, activity_date)
                
        except Exception as e:
            error_msg = f"Error calculating ACWR for user {user_id}: {str(e)}"
            logger.error(error_msg)
            log_acwr_feature_error('enhanced_acwr_calculation', user_id, error_msg)
            
            # Fallback to standard calculation on error
            logger.info(f"🔄 Falling back to standard ACWR calculation for user {user_id}")
            return self._calculate_standard_acwr(user_id, activity_date)
    
    def _calculate_enhanced_acwr(self, user_id: int, activity_date: str) -> Dict:
        """Calculate enhanced ACWR using exponential decay"""
        try:
            # Get user's ACWR configuration
            config = self.acwr_config_service.get_user_configuration(user_id)
            if not config:
                logger.warning(f"No ACWR configuration found for user {user_id}, using default")
                config = self.acwr_config_service.get_default_configuration()
            
            # Calculate enhanced ACWR
            result = self.acwr_config_service.calculate_enhanced_acwr(
                user_id, activity_date, config
            )
            
            # Add metadata
            result['calculation_type'] = 'enhanced'
            result['configuration_used'] = config['name']
            result['chronic_period_days'] = config['chronic_period_days']
            result['decay_rate'] = config['decay_rate']
            
            return result
            
        except Exception as e:
            error_msg = f"Enhanced ACWR calculation failed for user {user_id}: {str(e)}"
            logger.error(error_msg)
            log_acwr_feature_error('enhanced_acwr_calculation', user_id, error_msg)
            raise
    
    def _calculate_standard_acwr(self, user_id: int, activity_date: str) -> Dict:
        """Calculate standard 28-day ACWR (fallback method)"""
        try:
            # Import the existing calculation function
            from strava_training_load import update_moving_averages
            
            # Parse the date
            date_obj = datetime.strptime(activity_date, '%Y-%m-%d').date()
            
            # Calculate date ranges
            seven_days_ago = (date_obj - timedelta(days=6)).strftime('%Y-%m-%d')
            twentyeight_days_ago = (date_obj - timedelta(days=27)).strftime('%Y-%m-%d')
            
            # Get activities for acute period (7 days)
            acute_query = """
                SELECT COALESCE(SUM(total_load_miles), 0) as sum_load, 
                       COALESCE(SUM(trimp), 0) as sum_trimp
                FROM activities 
                WHERE user_id = %s AND date BETWEEN %s AND %s
            """
            acute_result = db_utils.execute_query(
                acute_query, (user_id, seven_days_ago, activity_date), fetch=True
            )
            
            # Get activities for chronic period (28 days)
            chronic_query = """
                SELECT COALESCE(SUM(total_load_miles), 0) as sum_load, 
                       COALESCE(SUM(trimp), 0) as sum_trimp
                FROM activities 
                WHERE user_id = %s AND date BETWEEN %s AND %s
            """
            chronic_result = db_utils.execute_query(
                chronic_query, (user_id, twentyeight_days_ago, activity_date), fetch=True
            )
            
            # Calculate averages
            acute_load_avg = acute_result[0]['sum_load'] / 7.0 if acute_result else 0.0
            acute_trimp_avg = acute_result[0]['sum_trimp'] / 7.0 if acute_result else 0.0
            chronic_load_avg = chronic_result[0]['sum_load'] / 28.0 if chronic_result else 0.0
            chronic_trimp_avg = chronic_result[0]['sum_trimp'] / 28.0 if chronic_result else 0.0
            
            # Calculate ACWR ratios
            acute_chronic_ratio = 0.0
            if chronic_load_avg > 0:
                acute_chronic_ratio = acute_load_avg / chronic_load_avg
            
            trimp_acute_chronic_ratio = 0.0
            if chronic_trimp_avg > 0:
                trimp_acute_chronic_ratio = acute_trimp_avg / chronic_trimp_avg
            
            # Calculate normalized divergence (simplified version)
            normalized_divergence = abs(acute_chronic_ratio - trimp_acute_chronic_ratio)
            
            result = {
                'calculation_type': 'standard',
                'configuration_used': 'standard_28day',
                'chronic_period_days': 28,
                'decay_rate': 0.0,  # No decay in standard calculation
                'enhanced_chronic_load': chronic_load_avg,
                'enhanced_chronic_trimp': chronic_trimp_avg,
                'enhanced_acute_chronic_ratio': acute_chronic_ratio,
                'enhanced_trimp_acute_chronic_ratio': trimp_acute_chronic_ratio,
                'enhanced_normalized_divergence': normalized_divergence,
                'calculation_timestamp': datetime.now().isoformat(),
                'fallback_reason': 'feature_disabled'
            }
            
            return result
            
        except Exception as e:
            error_msg = f"Standard ACWR calculation failed for user {user_id}: {str(e)}"
            logger.error(error_msg)
            log_acwr_feature_error('enhanced_acwr_calculation', user_id, error_msg)
            raise
    
    def get_acwr_calculation_summary(self, user_id: int, activity_date: str) -> Dict:
        """
        Get a summary of ACWR calculation for a user
        
        Args:
            user_id: User ID
            activity_date: Date string in 'YYYY-MM-DD' format
            
        Returns:
            Dictionary with calculation summary
        """
        try:
            # Check feature flag status
            enhanced_enabled = is_feature_enabled('enhanced_acwr_calculation', user_id)
            
            # Get user configuration if enhanced is enabled
            config_info = None
            if enhanced_enabled:
                config = self.acwr_config_service.get_user_configuration(user_id)
                if config:
                    config_info = {
                        'name': config['name'],
                        'chronic_period_days': config['chronic_period_days'],
                        'decay_rate': config['decay_rate']
                    }
            
            summary = {
                'user_id': user_id,
                'activity_date': activity_date,
                'enhanced_enabled': enhanced_enabled,
                'calculation_type': 'enhanced' if enhanced_enabled else 'standard',
                'configuration': config_info,
                'timestamp': datetime.now().isoformat()
            }
            
            return summary
            
        except Exception as e:
            error_msg = f"Error getting ACWR calculation summary for user {user_id}: {str(e)}"
            logger.error(error_msg)
            log_acwr_feature_error('enhanced_acwr_calculation', user_id, error_msg)
            return {
                'user_id': user_id,
                'activity_date': activity_date,
                'enhanced_enabled': False,
                'calculation_type': 'standard',
                'configuration': None,
                'error': error_msg,
                'timestamp': datetime.now().isoformat()
            }
    
    def compare_calculation_methods(self, user_id: int, activity_date: str) -> Dict:
        """
        Compare enhanced vs standard ACWR calculations for analysis
        
        Args:
            user_id: User ID
            activity_date: Date string in 'YYYY-MM-DD' format
            
        Returns:
            Dictionary with comparison results
        """
        try:
            # Get enhanced calculation
            enhanced_result = self._calculate_enhanced_acwr(user_id, activity_date)
            
            # Get standard calculation
            standard_result = self._calculate_standard_acwr(user_id, activity_date)
            
            # Calculate differences
            load_diff = enhanced_result['enhanced_chronic_load'] - standard_result['enhanced_chronic_load']
            trimp_diff = enhanced_result['enhanced_chronic_trimp'] - standard_result['enhanced_chronic_trimp']
            ratio_diff = enhanced_result['enhanced_acute_chronic_ratio'] - standard_result['enhanced_acute_chronic_ratio']
            
            comparison = {
                'user_id': user_id,
                'activity_date': activity_date,
                'enhanced': enhanced_result,
                'standard': standard_result,
                'differences': {
                    'chronic_load_difference': load_diff,
                    'chronic_trimp_difference': trimp_diff,
                    'acute_chronic_ratio_difference': ratio_diff,
                    'chronic_load_percentage_diff': (load_diff / standard_result['enhanced_chronic_load'] * 100) if standard_result['enhanced_chronic_load'] > 0 else 0,
                    'chronic_trimp_percentage_diff': (trimp_diff / standard_result['enhanced_chronic_trimp'] * 100) if standard_result['enhanced_chronic_trimp'] > 0 else 0
                },
                'timestamp': datetime.now().isoformat()
            }
            
            return comparison
            
        except Exception as e:
            error_msg = f"Error comparing ACWR calculation methods for user {user_id}: {str(e)}"
            logger.error(error_msg)
            log_acwr_feature_error('enhanced_acwr_calculation', user_id, error_msg)
            return {
                'user_id': user_id,
                'activity_date': activity_date,
                'error': error_msg,
                'timestamp': datetime.now().isoformat()
            }

# Global service instance
acwr_calculation_service = ACWRCalculationService()

def calculate_acwr_for_user(user_id: int, activity_date: str) -> Dict:
    """Convenience function to calculate ACWR for a user"""
    return acwr_calculation_service.calculate_acwr_for_user(user_id, activity_date)

def get_acwr_calculation_summary(user_id: int, activity_date: str) -> Dict:
    """Convenience function to get ACWR calculation summary"""
    return acwr_calculation_service.get_acwr_calculation_summary(user_id, activity_date)
