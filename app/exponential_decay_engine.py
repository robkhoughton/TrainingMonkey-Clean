#!/usr/bin/env python3
"""
Exponential Decay Calculation Engine
Implements the core mathematical engine for ACWR calculations with exponential decay weighting
"""

import math
import logging
from datetime import datetime, date, timedelta
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class ActivityData:
    """Data class for activity information"""
    date: date
    total_load_miles: float
    trimp: float
    days_ago: int = 0
    weight: float = 1.0

@dataclass
class DecayCalculationResult:
    """Result of exponential decay calculation"""
    weighted_load_sum: float
    weighted_trimp_sum: float
    total_weight: float
    weighted_load_avg: float
    weighted_trimp_avg: float
    activity_count: int
    decay_rate: float
    calculation_method: str

class ExponentialDecayEngine:
    """Core engine for exponential decay calculations"""
    
    def __init__(self):
        self.logger = logger
    
    def calculate_exponential_weight(self, days_ago: int, decay_rate: float) -> float:
        """
        Calculate exponential decay weight for an activity
        
        Formula: Weight = e^(-decay_rate × days_ago)
        
        Args:
            days_ago: Number of days ago the activity occurred
            decay_rate: Decay rate parameter (0 < decay_rate <= 1.0)
            
        Returns:
            Weight value between 0 and 1
        """
        try:
            if days_ago < 0:
                raise ValueError(f"days_ago must be non-negative, got {days_ago}")
            
            if decay_rate <= 0 or decay_rate > 1.0:
                raise ValueError(f"decay_rate must be between 0 and 1, got {decay_rate}")
            
            # Calculate exponential decay weight
            weight = math.exp(-decay_rate * days_ago)
            
            # Ensure weight is within valid range
            weight = max(0.0, min(1.0, weight))
            
            self.logger.debug(f"Calculated weight for {days_ago} days ago with decay_rate {decay_rate}: {weight:.6f}")
            
            return weight
            
        except Exception as e:
            self.logger.error(f"Error calculating exponential weight: {str(e)}")
            raise
    
    def calculate_weighted_averages(self, activities: List[ActivityData], 
                                 reference_date: date,
                                 decay_rate: float) -> DecayCalculationResult:
        """
        Calculate weighted averages using exponential decay
        
        Args:
            activities: List of activity data
            decay_rate: Decay rate parameter
            reference_date: Reference date for calculating days_ago
            
        Returns:
            DecayCalculationResult with weighted calculations
        """
        try:
            if not activities:
                return DecayCalculationResult(
                    weighted_load_sum=0.0,
                    weighted_trimp_sum=0.0,
                    total_weight=0.0,
                    weighted_load_avg=0.0,
                    weighted_trimp_avg=0.0,
                    activity_count=0,
                    decay_rate=decay_rate,
                    calculation_method='exponential_decay'
                )
            
            weighted_load_sum = 0.0
            weighted_trimp_sum = 0.0
            total_weight = 0.0
            
            # Process each activity
            for activity in activities:
                # Calculate days ago from reference date
                days_ago = (reference_date - activity.date).days
                
                # Calculate exponential weight
                weight = self.calculate_exponential_weight(days_ago, decay_rate)
                
                # Update weighted sums
                weighted_load_sum += activity.total_load_miles * weight
                weighted_trimp_sum += activity.trimp * weight
                total_weight += weight
                
                # Update activity data
                activity.days_ago = days_ago
                activity.weight = weight
                
                self.logger.debug(f"Activity {activity.date}: load={activity.total_load_miles}, "
                                f"trimp={activity.trimp}, days_ago={days_ago}, weight={weight:.6f}")
            
            # Calculate weighted averages
            weighted_load_avg = round(weighted_load_sum / total_weight, 3) if total_weight > 0 else 0.0
            weighted_trimp_avg = round(weighted_trimp_sum / total_weight, 3) if total_weight > 0 else 0.0
            
            result = DecayCalculationResult(
                weighted_load_sum=round(weighted_load_sum, 3),
                weighted_trimp_sum=round(weighted_trimp_sum, 3),
                total_weight=round(total_weight, 3),
                weighted_load_avg=weighted_load_avg,
                weighted_trimp_avg=weighted_trimp_avg,
                activity_count=len(activities),
                decay_rate=decay_rate,
                calculation_method='exponential_decay'
            )
            
            self.logger.info(f"Calculated weighted averages: load_avg={weighted_load_avg:.3f}, "
                           f"trimp_avg={weighted_trimp_avg:.3f}, total_weight={total_weight:.3f}, "
                           f"activities={len(activities)}")
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error calculating weighted averages: {str(e)}")
            raise
    
    def calculate_enhanced_acwr(self, acute_activities: List[ActivityData],
                              chronic_activities: List[ActivityData],
                              decay_rate: float,
                              reference_date: date) -> Dict:
        """
        Calculate enhanced ACWR using exponential decay weighting
        
        Args:
            acute_activities: Activities for acute period (typically 7 days)
            chronic_activities: Activities for chronic period (configurable, typically 28-90 days)
            decay_rate: Decay rate parameter
            reference_date: Reference date for calculations
            
        Returns:
            Dictionary with enhanced ACWR calculations
        """
        try:
            # Validate inputs
            if not self.validate_decay_rate(decay_rate):
                raise ValueError(f"Invalid decay rate: {decay_rate}")
            
            # Handle edge cases
            edge_case_result = self._handle_edge_cases(acute_activities, chronic_activities, reference_date)
            if edge_case_result:
                return edge_case_result
            
            # Calculate acute averages (simple average for 7-day period)
            acute_load_avg = sum(a.total_load_miles for a in acute_activities) / len(acute_activities) if acute_activities else 0.0
            acute_trimp_avg = sum(a.trimp for a in acute_activities) / len(acute_activities) if acute_activities else 0.0
            
            # Calculate chronic averages using exponential decay
            chronic_result = self.calculate_weighted_averages(chronic_activities, reference_date, decay_rate)
            
            # Calculate ACWR ratios
            acute_chronic_ratio = 0.0
            if chronic_result.weighted_load_avg > 0:
                acute_chronic_ratio = acute_load_avg / chronic_result.weighted_load_avg
            
            trimp_acute_chronic_ratio = 0.0
            if chronic_result.weighted_trimp_avg > 0:
                trimp_acute_chronic_ratio = acute_trimp_avg / chronic_result.weighted_trimp_avg
            
            # Calculate normalized divergence
            normalized_divergence = abs(acute_chronic_ratio - trimp_acute_chronic_ratio)
            
            result = {
                'acute_load_avg': round(acute_load_avg, 3),
                'acute_trimp_avg': round(acute_trimp_avg, 3),
                'enhanced_chronic_load': round(chronic_result.weighted_load_avg, 3),
                'enhanced_chronic_trimp': round(chronic_result.weighted_trimp_avg, 3),
                'enhanced_acute_chronic_ratio': round(acute_chronic_ratio, 3),
                'enhanced_trimp_acute_chronic_ratio': round(trimp_acute_chronic_ratio, 3),
                'enhanced_normalized_divergence': round(normalized_divergence, 3),
                'chronic_total_weight': round(chronic_result.total_weight, 3),
                'chronic_activity_count': chronic_result.activity_count,
                'decay_rate': decay_rate,
                'calculation_method': 'exponential_decay',
                'reference_date': reference_date.isoformat(),
                'data_quality': self._assess_data_quality(acute_activities, chronic_activities, reference_date)
            }
            
            self.logger.info(f"Enhanced ACWR calculated: acute_ratio={acute_chronic_ratio:.3f}, "
                           f"trimp_ratio={trimp_acute_chronic_ratio:.3f}, "
                           f"divergence={normalized_divergence:.3f}")
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error calculating enhanced ACWR: {str(e)}")
            raise
    
    def _handle_edge_cases(self, acute_activities: List[ActivityData],
                          chronic_activities: List[ActivityData],
                          reference_date: date) -> Optional[Dict]:
        """
        Handle edge cases for ACWR calculation
        
        Args:
            acute_activities: Activities for acute period
            chronic_activities: Activities for chronic period
            reference_date: Reference date for calculations
            
        Returns:
            Dictionary with edge case result or None if no edge case
        """
        try:
            # Check for insufficient data
            if not acute_activities and not chronic_activities:
                self.logger.warning("No activity data available for ACWR calculation")
                return self._create_edge_case_result("no_data", "No activity data available")
            
            if not acute_activities:
                self.logger.warning("No acute period data available")
                return self._create_edge_case_result("no_acute_data", "No acute period data available")
            
            if not chronic_activities:
                self.logger.warning("No chronic period data available")
                return self._create_edge_case_result("no_chronic_data", "No chronic period data available")
            
            # Check for future dates
            future_acute = [a for a in acute_activities if a.date > reference_date]
            future_chronic = [a for a in chronic_activities if a.date > reference_date]
            
            if future_acute or future_chronic:
                self.logger.warning(f"Found {len(future_acute)} acute and {len(future_chronic)} chronic activities with future dates")
                return self._create_edge_case_result("future_dates", 
                    f"Found activities with future dates: {len(future_acute)} acute, {len(future_chronic)} chronic")
            
            # Check for insufficient chronic period data
            if len(chronic_activities) < 7:  # Minimum 7 days of data
                self.logger.warning(f"Insufficient chronic period data: {len(chronic_activities)} activities")
                return self._create_edge_case_result("insufficient_chronic_data", 
                    f"Insufficient chronic period data: {len(chronic_activities)} activities (minimum 7 required)")
            
            # Check for data gaps
            data_gaps = self._detect_data_gaps(chronic_activities, reference_date)
            if data_gaps['gap_count'] > len(chronic_activities) * 0.5:  # More than 50% gaps
                self.logger.warning(f"Significant data gaps detected: {data_gaps['gap_count']} gaps")
                return self._create_edge_case_result("significant_data_gaps", 
                    f"Significant data gaps detected: {data_gaps['gap_count']} gaps")
            
            # Check for missing values
            missing_values = self._detect_missing_values(acute_activities, chronic_activities)
            if missing_values['missing_count'] > 0:
                self.logger.warning(f"Missing values detected: {missing_values['missing_count']} missing values")
                # Don't return edge case for missing values, just log warning
            
            return None  # No edge case detected
            
        except Exception as e:
            self.logger.error(f"Error handling edge cases: {str(e)}")
            return self._create_edge_case_result("edge_case_error", f"Error handling edge cases: {str(e)}")
    
    def _create_edge_case_result(self, case_type: str, message: str) -> Dict:
        """
        Create result dictionary for edge cases
        
        Args:
            case_type: Type of edge case
            message: Description of the edge case
            
        Returns:
            Dictionary with edge case result
        """
        return {
            'acute_load_avg': 0.0,
            'acute_trimp_avg': 0.0,
            'enhanced_chronic_load': 0.0,
            'enhanced_chronic_trimp': 0.0,
            'enhanced_acute_chronic_ratio': 0.0,
            'enhanced_trimp_acute_chronic_ratio': 0.0,
            'enhanced_normalized_divergence': 0.0,
            'chronic_total_weight': 0.0,
            'chronic_activity_count': 0,
            'decay_rate': 0.0,
            'calculation_method': 'edge_case',
            'edge_case_type': case_type,
            'edge_case_message': message,
            'data_quality': 'poor',
            'timestamp': datetime.now().isoformat()
        }
    
    def _assess_data_quality(self, acute_activities: List[ActivityData],
                           chronic_activities: List[ActivityData],
                           reference_date: date) -> str:
        """
        Assess data quality for ACWR calculation
        
        Args:
            acute_activities: Activities for acute period
            chronic_activities: Activities for chronic period
            reference_date: Reference date for calculations
            
        Returns:
            Data quality assessment: 'excellent', 'good', 'fair', 'poor'
        """
        try:
            quality_score = 0
            
            # Check acute period completeness (7 days)
            if len(acute_activities) >= 7:
                quality_score += 2
            elif len(acute_activities) >= 5:
                quality_score += 1
            
            # Check chronic period completeness (28+ days)
            if len(chronic_activities) >= 28:
                quality_score += 2
            elif len(chronic_activities) >= 14:
                quality_score += 1
            
            # Check for data gaps
            data_gaps = self._detect_data_gaps(chronic_activities, reference_date)
            gap_ratio = data_gaps['gap_count'] / max(len(chronic_activities), 1)
            if gap_ratio < 0.1:  # Less than 10% gaps
                quality_score += 2
            elif gap_ratio < 0.3:  # Less than 30% gaps
                quality_score += 1
            
            # Check for missing values
            missing_values = self._detect_missing_values(acute_activities, chronic_activities)
            missing_ratio = missing_values['missing_count'] / max(len(acute_activities) + len(chronic_activities), 1)
            if missing_ratio < 0.05:  # Less than 5% missing
                quality_score += 2
            elif missing_ratio < 0.2:  # Less than 20% missing
                quality_score += 1
            
            # Determine quality level
            if quality_score >= 7:
                return 'excellent'
            elif quality_score >= 5:
                return 'good'
            elif quality_score >= 3:
                return 'fair'
            else:
                return 'poor'
                
        except Exception as e:
            self.logger.error(f"Error assessing data quality: {str(e)}")
            return 'poor'
    
    def _detect_data_gaps(self, activities: List[ActivityData], reference_date: date) -> Dict:
        """
        Detect data gaps in activity data
        
        Args:
            activities: List of activities
            reference_date: Reference date for calculations
            
        Returns:
            Dictionary with gap information
        """
        try:
            if not activities:
                return {'gap_count': 0, 'gaps': []}
            
            # Sort activities by date
            sorted_activities = sorted(activities, key=lambda x: x.date)
            
            gaps = []
            gap_count = 0
            
            # Check for gaps between consecutive activities
            for i in range(len(sorted_activities) - 1):
                current_date = sorted_activities[i].date
                next_date = sorted_activities[i + 1].date
                days_diff = (next_date - current_date).days
                
                if days_diff > 1:  # Gap of more than 1 day
                    gap_count += days_diff - 1
                    gaps.append({
                        'start_date': current_date,
                        'end_date': next_date,
                        'gap_days': days_diff - 1
                    })
            
            return {
                'gap_count': gap_count,
                'gaps': gaps,
                'total_activities': len(activities)
            }
            
        except Exception as e:
            self.logger.error(f"Error detecting data gaps: {str(e)}")
            return {'gap_count': 0, 'gaps': []}
    
    def _detect_missing_values(self, acute_activities: List[ActivityData],
                             chronic_activities: List[ActivityData]) -> Dict:
        """
        Detect missing values in activity data
        
        Args:
            acute_activities: Activities for acute period
            chronic_activities: Activities for chronic period
            
        Returns:
            Dictionary with missing value information
        """
        try:
            missing_count = 0
            missing_details = []
            
            all_activities = acute_activities + chronic_activities
            
            for activity in all_activities:
                activity_missing = []
                
                if activity.total_load_miles is None or activity.total_load_miles < 0:
                    activity_missing.append('total_load_miles')
                    missing_count += 1
                
                if activity.trimp is None or activity.trimp < 0:
                    activity_missing.append('trimp')
                    missing_count += 1
                
                if activity_missing:
                    missing_details.append({
                        'date': activity.date,
                        'missing_fields': activity_missing
                    })
            
            return {
                'missing_count': missing_count,
                'missing_details': missing_details,
                'total_activities': len(all_activities)
            }
            
        except Exception as e:
            self.logger.error(f"Error detecting missing values: {str(e)}")
            return {'missing_count': 0, 'missing_details': []}
    
    def compare_with_standard_calculation(self, activities: List[ActivityData],
                                        decay_rate: float,
                                        reference_date: date) -> Dict:
        """
        Compare exponential decay calculation with standard simple average
        
        Args:
            activities: List of activity data
            decay_rate: Decay rate parameter
            reference_date: Reference date for calculations
            
        Returns:
            Dictionary with comparison results
        """
        try:
            # Calculate exponential decay weighted average
            decay_result = self.calculate_weighted_averages(activities, reference_date, decay_rate)
            
            # Calculate standard simple average
            standard_load_avg = sum(a.total_load_miles for a in activities) / len(activities) if activities else 0.0
            standard_trimp_avg = sum(a.trimp for a in activities) / len(activities) if activities else 0.0
            
            # Calculate differences
            load_difference = decay_result.weighted_load_avg - standard_load_avg
            trimp_difference = decay_result.weighted_trimp_avg - standard_trimp_avg
            
            load_percentage_diff = (load_difference / standard_load_avg * 100) if standard_load_avg > 0 else 0.0
            trimp_percentage_diff = (trimp_difference / standard_trimp_avg * 100) if standard_trimp_avg > 0 else 0.0
            
            comparison = {
                'exponential_decay': {
                    'weighted_load_avg': decay_result.weighted_load_avg,
                    'weighted_trimp_avg': decay_result.weighted_trimp_avg,
                    'total_weight': decay_result.total_weight,
                    'activity_count': decay_result.activity_count
                },
                'standard_average': {
                    'load_avg': standard_load_avg,
                    'trimp_avg': standard_trimp_avg,
                    'activity_count': len(activities)
                },
                'differences': {
                    'load_difference': load_difference,
                    'trimp_difference': trimp_difference,
                    'load_percentage_diff': load_percentage_diff,
                    'trimp_percentage_diff': trimp_percentage_diff
                },
                'decay_rate': decay_rate,
                'reference_date': reference_date.isoformat()
            }
            
            self.logger.info(f"Comparison completed: load_diff={load_difference:.3f} ({load_percentage_diff:.1f}%), "
                           f"trimp_diff={trimp_difference:.3f} ({trimp_percentage_diff:.1f}%)")
            
            return comparison
            
        except Exception as e:
            self.logger.error(f"Error comparing calculations: {str(e)}")
            raise
    
    def validate_decay_rate(self, decay_rate: float) -> bool:
        """
        Validate decay rate parameter
        
        Args:
            decay_rate: Decay rate to validate
            
        Returns:
            True if valid, False otherwise
        """
        try:
            if not isinstance(decay_rate, (int, float)):
                self.logger.error(f"Decay rate must be numeric, got {type(decay_rate)}")
                return False
            
            if decay_rate <= 0:
                self.logger.error(f"Decay rate must be positive, got {decay_rate}")
                return False
            
            if decay_rate > 1.0:
                self.logger.error(f"Decay rate must be <= 1.0, got {decay_rate}")
                return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error validating decay rate: {str(e)}")
            return False
    
    def validate_chronic_period(self, chronic_period_days: int) -> bool:
        """
        Validate chronic period parameter
        
        Args:
            chronic_period_days: Chronic period in days to validate
            
        Returns:
            True if valid, False otherwise
        """
        try:
            if not isinstance(chronic_period_days, int):
                self.logger.error(f"Chronic period must be an integer, got {type(chronic_period_days)}")
                return False
            
            if chronic_period_days < 28:
                self.logger.error(f"Chronic period must be >= 28 days, got {chronic_period_days}")
                return False
            
            if chronic_period_days > 90:
                self.logger.error(f"Chronic period must be <= 90 days, got {chronic_period_days}")
                return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error validating chronic period: {str(e)}")
            return False
    
    def validate_activity_data(self, activities: List[ActivityData]) -> bool:
        """
        Validate activity data
        
        Args:
            activities: List of activity data to validate
            
        Returns:
            True if valid, False otherwise
        """
        try:
            if not isinstance(activities, list):
                self.logger.error(f"Activities must be a list, got {type(activities)}")
                return False
            
            for i, activity in enumerate(activities):
                if not isinstance(activity, ActivityData):
                    self.logger.error(f"Activity {i} must be ActivityData instance, got {type(activity)}")
                    return False
                
                if not isinstance(activity.date, date):
                    self.logger.error(f"Activity {i} date must be date instance, got {type(activity.date)}")
                    return False
                
                if not isinstance(activity.total_load_miles, (int, float)):
                    self.logger.error(f"Activity {i} total_load_miles must be numeric, got {type(activity.total_load_miles)}")
                    return False
                
                if activity.total_load_miles < 0:
                    self.logger.error(f"Activity {i} total_load_miles must be non-negative, got {activity.total_load_miles}")
                    return False
                
                if not isinstance(activity.trimp, (int, float)):
                    self.logger.error(f"Activity {i} trimp must be numeric, got {type(activity.trimp)}")
                    return False
                
                if activity.trimp < 0:
                    self.logger.error(f"Activity {i} trimp must be non-negative, got {activity.trimp}")
                    return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error validating activity data: {str(e)}")
            return False
    
    def get_weight_distribution(self, days_range: int, decay_rate: float) -> List[Dict]:
        """
        Get weight distribution for a range of days
        
        Args:
            days_range: Number of days to calculate weights for
            decay_rate: Decay rate parameter
            
        Returns:
            List of dictionaries with day and weight information
        """
        try:
            if not self.validate_decay_rate(decay_rate):
                raise ValueError(f"Invalid decay rate: {decay_rate}")
            
            distribution = []
            for days_ago in range(days_range):
                weight = self.calculate_exponential_weight(days_ago, decay_rate)
                distribution.append({
                    'days_ago': days_ago,
                    'weight': weight,
                    'weight_percentage': weight * 100
                })
            
            return distribution
            
        except Exception as e:
            self.logger.error(f"Error getting weight distribution: {str(e)}")
            raise
    
    def detect_data_availability(self, activities: List[ActivityData], 
                               reference_date: date, 
                               chronic_period_days: int = 28,
                               minimum_required_days: int = 7) -> Dict:
        """
        Detect data availability for minimum chronic period
        
        Args:
            activities: List of activity data
            reference_date: Reference date for calculations
            chronic_period_days: Desired chronic period in days
            minimum_required_days: Minimum days required for valid calculation
            
        Returns:
            Dictionary with data availability information
        """
        try:
            if not activities:
                return self._create_data_availability_result(
                    available=False, 
                    reason="no_data",
                    message="No activity data available",
                    days_available=0,
                    chronic_period_days=chronic_period_days,
                    minimum_required_days=minimum_required_days
                )
            
            # Filter activities within chronic period
            chronic_start_date = reference_date - timedelta(days=chronic_period_days - 1)
            chronic_activities = [
                activity for activity in activities 
                if chronic_start_date <= activity.date <= reference_date
            ]
            
            # Sort activities by date
            chronic_activities.sort(key=lambda x: x.date)
            
            # Count unique days with activities
            unique_days = set(activity.date for activity in chronic_activities)
            days_available = len(unique_days)
            
            # Check if minimum requirement is met
            if days_available < minimum_required_days:
                return self._create_data_availability_result(
                    available=False,
                    reason="insufficient_data",
                    message=f"Only {days_available} days of data available, need at least {minimum_required_days}",
                    days_available=days_available,
                    chronic_period_days=chronic_period_days,
                    minimum_required_days=minimum_required_days,
                    chronic_activities=chronic_activities
                )
            
            # Analyze data gaps
            gap_analysis = self._analyze_data_gaps(chronic_activities, reference_date)
            
            # Calculate data coverage percentage
            coverage_percentage = (days_available / chronic_period_days) * 100
            
            # Determine data quality
            data_quality = self._assess_data_availability_quality(
                days_available, chronic_period_days, gap_analysis, coverage_percentage
            )
            
            return self._create_data_availability_result(
                available=True,
                reason="sufficient_data",
                message=f"Sufficient data available: {days_available} days ({coverage_percentage:.1f}% coverage)",
                days_available=days_available,
                chronic_period_days=chronic_period_days,
                minimum_required_days=minimum_required_days,
                chronic_activities=chronic_activities,
                gap_analysis=gap_analysis,
                coverage_percentage=coverage_percentage,
                data_quality=data_quality
            )
            
        except Exception as e:
            self.logger.error(f"Error detecting data availability: {str(e)}")
            return self._create_data_availability_result(
                available=False,
                reason="error",
                message=f"Error analyzing data availability: {str(e)}",
                days_available=0,
                chronic_period_days=chronic_period_days,
                minimum_required_days=minimum_required_days
            )
    
    def _create_data_availability_result(self, available: bool, reason: str, message: str,
                                       days_available: int, chronic_period_days: int,
                                       minimum_required_days: int, **kwargs) -> Dict:
        """
        Create standardized data availability result
        
        Args:
            available: Whether sufficient data is available
            reason: Reason code for availability status
            message: Human-readable message
            days_available: Number of days with data
            chronic_period_days: Desired chronic period
            minimum_required_days: Minimum required days
            **kwargs: Additional data to include
            
        Returns:
            Dictionary with data availability result
        """
        result = {
            'available': available,
            'reason': reason,
            'message': message,
            'days_available': days_available,
            'chronic_period_days': chronic_period_days,
            'minimum_required_days': minimum_required_days,
            'timestamp': datetime.now().isoformat()
        }
        
        # Add additional data if provided
        for key, value in kwargs.items():
            result[key] = value
        
        return result
    
    def _analyze_data_gaps(self, activities: List[ActivityData], reference_date: date) -> Dict:
        """
        Analyze data gaps in activity data
        
        Args:
            activities: List of activities (should be sorted by date)
            reference_date: Reference date for calculations
            
        Returns:
            Dictionary with gap analysis
        """
        try:
            if not activities:
                return {
                    'total_gaps': 0,
                    'gap_days': 0,
                    'largest_gap': 0,
                    'gap_percentage': 0.0,
                    'gaps': []
                }
            
            gaps = []
            total_gap_days = 0
            largest_gap = 0
            
            # Check for gaps between consecutive activities
            for i in range(len(activities) - 1):
                current_date = activities[i].date
                next_date = activities[i + 1].date
                days_diff = (next_date - current_date).days
                
                if days_diff > 1:  # Gap of more than 1 day
                    gap_days = days_diff - 1
                    total_gap_days += gap_days
                    largest_gap = max(largest_gap, gap_days)
                    
                    gaps.append({
                        'start_date': current_date,
                        'end_date': next_date,
                        'gap_days': gap_days
                    })
            
            # Calculate gap percentage
            total_days = len(activities)
            gap_percentage = (total_gap_days / total_days * 100) if total_days > 0 else 0.0
            
            return {
                'total_gaps': len(gaps),
                'gap_days': total_gap_days,
                'largest_gap': largest_gap,
                'gap_percentage': gap_percentage,
                'gaps': gaps
            }
            
        except Exception as e:
            self.logger.error(f"Error analyzing data gaps: {str(e)}")
            return {
                'total_gaps': 0,
                'gap_days': 0,
                'largest_gap': 0,
                'gap_percentage': 0.0,
                'gaps': []
            }
    
    def _assess_data_availability_quality(self, days_available: int, chronic_period_days: int,
                                        gap_analysis: Dict, coverage_percentage: float) -> str:
        """
        Assess data availability quality
        
        Args:
            days_available: Number of days with data
            chronic_period_days: Desired chronic period
            gap_analysis: Gap analysis results
            coverage_percentage: Data coverage percentage
            
        Returns:
            Quality assessment: 'excellent', 'good', 'fair', 'poor'
        """
        try:
            quality_score = 0
            
            # Coverage score (0-3 points)
            if coverage_percentage >= 90:
                quality_score += 3
            elif coverage_percentage >= 75:
                quality_score += 2
            elif coverage_percentage >= 50:
                quality_score += 1
            
            # Gap score (0-2 points)
            gap_percentage = gap_analysis.get('gap_percentage', 0)
            if gap_percentage < 10:
                quality_score += 2
            elif gap_percentage < 25:
                quality_score += 1
            
            # Days available score (0-2 points)
            if days_available >= chronic_period_days * 0.8:
                quality_score += 2
            elif days_available >= chronic_period_days * 0.6:
                quality_score += 1
            
            # Determine quality level
            if quality_score >= 6:
                return 'excellent'
            elif quality_score >= 4:
                return 'good'
            elif quality_score >= 2:
                return 'fair'
            else:
                return 'poor'
                
        except Exception as e:
            self.logger.error(f"Error assessing data availability quality: {str(e)}")
            return 'poor'
    
    def get_optimal_chronic_period(self, activities: List[ActivityData], 
                                 reference_date: date,
                                 preferred_period: int = 28,
                                 max_period: int = 90) -> Dict:
        """
        Determine optimal chronic period based on available data
        
        Args:
            activities: List of activity data
            reference_date: Reference date for calculations
            preferred_period: Preferred chronic period
            max_period: Maximum allowed chronic period
            
        Returns:
            Dictionary with optimal period recommendation
        """
        try:
            if not activities:
                return {
                    'optimal_period': 0,
                    'available_periods': [],
                    'recommendation': 'no_data',
                    'message': 'No activity data available'
                }
            
            # Test different chronic periods
            available_periods = []
            
            for period in range(7, max_period + 1, 7):  # Test every 7 days
                availability = self.detect_data_availability(
                    activities, reference_date, period, minimum_required_days=7
                )
                
                if availability['available']:
                    available_periods.append({
                        'period': period,
                        'days_available': availability['days_available'],
                        'coverage_percentage': availability.get('coverage_percentage', 0),
                        'data_quality': availability.get('data_quality', 'poor')
                    })
            
            if not available_periods:
                return {
                    'optimal_period': 0,
                    'available_periods': [],
                    'recommendation': 'insufficient_data',
                    'message': 'No chronic period has sufficient data (minimum 7 days)'
                }
            
            # Find optimal period
            # Prefer periods close to preferred_period with good quality
            best_period = None
            best_score = -1
            
            for period_info in available_periods:
                period = period_info['period']
                quality = period_info['data_quality']
                coverage = period_info['coverage_percentage']
                
                # Calculate score (closer to preferred period = higher score)
                period_score = 100 - abs(period - preferred_period)
                
                # Quality multiplier
                quality_multiplier = {
                    'excellent': 1.2,
                    'good': 1.1,
                    'fair': 1.0,
                    'poor': 0.8
                }.get(quality, 0.8)
                
                # Coverage multiplier
                coverage_multiplier = coverage / 100
                
                total_score = period_score * quality_multiplier * coverage_multiplier
                
                if total_score > best_score:
                    best_score = total_score
                    best_period = period_info
            
            return {
                'optimal_period': best_period['period'],
                'available_periods': available_periods,
                'recommendation': 'optimal_found',
                'message': f"Optimal chronic period: {best_period['period']} days "
                          f"({best_period['data_quality']} quality, "
                          f"{best_period['coverage_percentage']:.1f}% coverage)",
                'optimal_period_info': best_period
            }
            
        except Exception as e:
            self.logger.error(f"Error determining optimal chronic period: {str(e)}")
            return {
                'optimal_period': 0,
                'available_periods': [],
                'recommendation': 'error',
                'message': f"Error determining optimal period: {str(e)}"
            }
    
    def calculate_enhanced_acwr_optimized(self, acute_activities: List[ActivityData],
                                        chronic_activities: List[ActivityData],
                                        reference_date: date,
                                        decay_rate: float = 0.05,
                                        chronic_period_days: int = 28,
                                        use_caching: bool = True,
                                        batch_size: int = 1000) -> Dict:
        """
        Optimized enhanced ACWR calculation for large datasets
        
        Args:
            acute_activities: List of activities for acute load (7 days)
            chronic_activities: List of activities for chronic load
            reference_date: Reference date for calculations
            decay_rate: Decay rate parameter
            chronic_period_days: Chronic period in days
            use_caching: Whether to use weight caching for performance
            batch_size: Batch size for processing large datasets
            
        Returns:
            Dictionary with enhanced ACWR calculation results
        """
        try:
            start_time = datetime.now()
            
            # Validate inputs
            if not self.validate_decay_rate(decay_rate):
                raise ValueError(f"Invalid decay rate: {decay_rate}")
            
            if not self.validate_chronic_period(chronic_period_days):
                raise ValueError(f"Invalid chronic period: {chronic_period_days}")
            
            # Handle edge cases first
            edge_case_result = self._handle_edge_cases(acute_activities, chronic_activities, reference_date)
            if edge_case_result:
                edge_case_result['calculation_time_ms'] = (datetime.now() - start_time).total_seconds() * 1000
                return edge_case_result
            
            # Optimize data processing for large datasets
            if len(chronic_activities) > batch_size:
                self.logger.info(f"Processing large dataset: {len(chronic_activities)} activities, using batch size {batch_size}")
                return self._calculate_enhanced_acwr_batched(
                    acute_activities, chronic_activities, reference_date, 
                    decay_rate, chronic_period_days, batch_size, start_time
                )
            
            # Use caching for repeated weight calculations
            if use_caching:
                return self._calculate_enhanced_acwr_cached(
                    acute_activities, chronic_activities, reference_date, 
                    decay_rate, chronic_period_days, start_time
                )
            
            # Standard calculation for smaller datasets
            return self._calculate_enhanced_acwr_standard(
                acute_activities, chronic_activities, reference_date, 
                decay_rate, chronic_period_days, start_time
            )
            
        except Exception as e:
            self.logger.error(f"Error in optimized enhanced ACWR calculation: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'calculation_time_ms': (datetime.now() - start_time).total_seconds() * 1000
            }
    
    def _calculate_enhanced_acwr_batched(self, acute_activities: List[ActivityData],
                                       chronic_activities: List[ActivityData],
                                       reference_date: date,
                                       decay_rate: float,
                                       chronic_period_days: int,
                                       batch_size: int,
                                       start_time: datetime) -> Dict:
        """
        Calculate enhanced ACWR using batched processing for large datasets
        """
        try:
            # Process chronic activities in batches
            chronic_batches = [chronic_activities[i:i + batch_size] 
                             for i in range(0, len(chronic_activities), batch_size)]
            
            total_weighted_load = 0.0
            total_weighted_trimp = 0.0
            total_weight = 0.0
            total_activities = 0
            
            # Process each batch
            for batch_idx, batch in enumerate(chronic_batches):
                batch_result = self.calculate_weighted_averages(
                    batch, reference_date, decay_rate
                )
                
                total_weighted_load += batch_result.weighted_load_sum
                total_weighted_trimp += batch_result.weighted_trimp_sum
                total_weight += batch_result.total_weight
                total_activities += batch_result.activity_count
                
                self.logger.debug(f"Processed batch {batch_idx + 1}/{len(chronic_batches)}: "
                                f"{batch_result.activity_count} activities")
            
            # Calculate chronic averages
            chronic_load_avg = total_weighted_load / total_weight if total_weight > 0 else 0.0
            chronic_trimp_avg = total_weighted_trimp / total_weight if total_weight > 0 else 0.0
            
            # Calculate acute averages (should be smaller, no batching needed)
            acute_result = self.calculate_weighted_averages(
                acute_activities, reference_date, decay_rate
            )
            
            acute_load_avg = acute_result.weighted_load_avg
            acute_trimp_avg = acute_result.weighted_trimp_avg
            
            # Calculate ACWR ratios
            acute_chronic_ratio = acute_load_avg / chronic_load_avg if chronic_load_avg > 0 else 0.0
            trimp_acute_chronic_ratio = acute_trimp_avg / chronic_trimp_avg if chronic_trimp_avg > 0 else 0.0
            
            calculation_time = (datetime.now() - start_time).total_seconds() * 1000
            
            return {
                'success': True,
                'acute_load_avg': round(acute_load_avg, 2),
                'chronic_load_avg': round(chronic_load_avg, 2),
                'acute_chronic_ratio': round(acute_chronic_ratio, 2),
                'enhanced_chronic_load': round(chronic_load_avg, 2),
                'enhanced_chronic_trimp': round(chronic_trimp_avg, 2),
                'enhanced_trimp_acute_chronic_ratio': round(trimp_acute_chronic_ratio, 2),
                'calculation_method': 'exponential_decay_batched',
                'total_activities_processed': total_activities + acute_result.activity_count,
                'batches_processed': len(chronic_batches),
                'calculation_time_ms': round(calculation_time, 2),
                'performance_optimization': 'batched_processing'
            }
            
        except Exception as e:
            self.logger.error(f"Error in batched ACWR calculation: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'calculation_time_ms': (datetime.now() - start_time).total_seconds() * 1000
            }
    
    def _calculate_enhanced_acwr_cached(self, acute_activities: List[ActivityData],
                                      chronic_activities: List[ActivityData],
                                      reference_date: date,
                                      decay_rate: float,
                                      chronic_period_days: int,
                                      start_time: datetime) -> Dict:
        """
        Calculate enhanced ACWR using weight caching for performance
        """
        try:
            # Create weight cache for common days_ago values
            weight_cache = {}
            max_days = max(
                (reference_date - activity.date).days 
                for activity in chronic_activities + acute_activities
            )
            
            # Pre-calculate weights for all possible days_ago values
            for days_ago in range(max_days + 1):
                weight_cache[days_ago] = self.calculate_exponential_weight(days_ago, decay_rate)
            
            # Calculate chronic averages using cached weights
            chronic_weighted_load = 0.0
            chronic_weighted_trimp = 0.0
            chronic_total_weight = 0.0
            
            for activity in chronic_activities:
                days_ago = (reference_date - activity.date).days
                weight = weight_cache.get(days_ago, 0.0)
                
                if activity.total_load_miles is not None:
                    chronic_weighted_load += activity.total_load_miles * weight
                if activity.trimp is not None:
                    chronic_weighted_trimp += activity.trimp * weight
                chronic_total_weight += weight
            
            chronic_load_avg = chronic_weighted_load / chronic_total_weight if chronic_total_weight > 0 else 0.0
            chronic_trimp_avg = chronic_weighted_trimp / chronic_total_weight if chronic_total_weight > 0 else 0.0
            
            # Calculate acute averages using cached weights
            acute_weighted_load = 0.0
            acute_weighted_trimp = 0.0
            acute_total_weight = 0.0
            
            for activity in acute_activities:
                days_ago = (reference_date - activity.date).days
                weight = weight_cache.get(days_ago, 0.0)
                
                if activity.total_load_miles is not None:
                    acute_weighted_load += activity.total_load_miles * weight
                if activity.trimp is not None:
                    acute_weighted_trimp += activity.trimp * weight
                acute_total_weight += weight
            
            acute_load_avg = acute_weighted_load / acute_total_weight if acute_total_weight > 0 else 0.0
            acute_trimp_avg = acute_weighted_trimp / acute_total_weight if acute_total_weight > 0 else 0.0
            
            # Calculate ACWR ratios
            acute_chronic_ratio = acute_load_avg / chronic_load_avg if chronic_load_avg > 0 else 0.0
            trimp_acute_chronic_ratio = acute_trimp_avg / chronic_trimp_avg if chronic_trimp_avg > 0 else 0.0
            
            calculation_time = (datetime.now() - start_time).total_seconds() * 1000
            
            return {
                'success': True,
                'acute_load_avg': round(acute_load_avg, 2),
                'chronic_load_avg': round(chronic_load_avg, 2),
                'acute_chronic_ratio': round(acute_chronic_ratio, 2),
                'enhanced_chronic_load': round(chronic_load_avg, 2),
                'enhanced_chronic_trimp': round(chronic_trimp_avg, 2),
                'enhanced_trimp_acute_chronic_ratio': round(trimp_acute_chronic_ratio, 2),
                'calculation_method': 'exponential_decay_cached',
                'total_activities_processed': len(chronic_activities) + len(acute_activities),
                'weight_cache_size': len(weight_cache),
                'calculation_time_ms': round(calculation_time, 2),
                'performance_optimization': 'weight_caching'
            }
            
        except Exception as e:
            self.logger.error(f"Error in cached ACWR calculation: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'calculation_time_ms': (datetime.now() - start_time).total_seconds() * 1000
            }
    
    def _calculate_enhanced_acwr_standard(self, acute_activities: List[ActivityData],
                                        chronic_activities: List[ActivityData],
                                        reference_date: date,
                                        decay_rate: float,
                                        chronic_period_days: int,
                                        start_time: datetime) -> Dict:
        """
        Standard enhanced ACWR calculation for smaller datasets
        """
        try:
            # Calculate chronic averages
            chronic_result = self.calculate_weighted_averages(
                chronic_activities, reference_date, decay_rate
            )
            
            # Calculate acute averages
            acute_result = self.calculate_weighted_averages(
                acute_activities, reference_date, decay_rate
            )
            
            # Calculate ACWR ratios
            acute_chronic_ratio = (acute_result.weighted_load_avg / chronic_result.weighted_load_avg 
                                 if chronic_result.weighted_load_avg > 0 else 0.0)
            trimp_acute_chronic_ratio = (acute_result.weighted_trimp_avg / chronic_result.weighted_trimp_avg 
                                       if chronic_result.weighted_trimp_avg > 0 else 0.0)
            
            calculation_time = (datetime.now() - start_time).total_seconds() * 1000
            
            return {
                'success': True,
                'acute_load_avg': round(acute_result.weighted_load_avg, 2),
                'chronic_load_avg': round(chronic_result.weighted_load_avg, 2),
                'acute_chronic_ratio': round(acute_chronic_ratio, 2),
                'enhanced_chronic_load': round(chronic_result.weighted_load_avg, 2),
                'enhanced_chronic_trimp': round(chronic_result.weighted_trimp_avg, 2),
                'enhanced_trimp_acute_chronic_ratio': round(trimp_acute_chronic_ratio, 2),
                'calculation_method': 'exponential_decay_standard',
                'total_activities_processed': chronic_result.activity_count + acute_result.activity_count,
                'calculation_time_ms': round(calculation_time, 2),
                'performance_optimization': 'standard_processing'
            }
            
        except Exception as e:
            self.logger.error(f"Error in standard ACWR calculation: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'calculation_time_ms': (datetime.now() - start_time).total_seconds() * 1000
            }
    
    def get_performance_metrics(self, activities: List[ActivityData], 
                              reference_date: date,
                              decay_rate: float = 0.05) -> Dict:
        """
        Get performance metrics for dataset processing
        
        Args:
            activities: List of activity data
            reference_date: Reference date for calculations
            decay_rate: Decay rate parameter
            
        Returns:
            Dictionary with performance metrics
        """
        try:
            if not activities:
                return {
                    'dataset_size': 0,
                    'recommended_optimization': 'none',
                    'estimated_processing_time_ms': 0,
                    'memory_usage_estimate_mb': 0
                }
            
            dataset_size = len(activities)
            
            # Determine recommended optimization based on dataset size
            if dataset_size > 10000:
                recommended_optimization = 'batched_processing'
                estimated_time = dataset_size * 0.001  # 0.001ms per activity
                memory_usage = dataset_size * 0.0001  # 0.0001MB per activity
            elif dataset_size > 1000:
                recommended_optimization = 'weight_caching'
                estimated_time = dataset_size * 0.0005  # 0.0005ms per activity
                memory_usage = dataset_size * 0.00005  # 0.00005MB per activity
            else:
                recommended_optimization = 'standard_processing'
                estimated_time = dataset_size * 0.0001  # 0.0001ms per activity
                memory_usage = dataset_size * 0.00001  # 0.00001MB per activity
            
            return {
                'dataset_size': dataset_size,
                'recommended_optimization': recommended_optimization,
                'estimated_processing_time_ms': round(estimated_time, 2),
                'memory_usage_estimate_mb': round(memory_usage, 4),
                'optimization_thresholds': {
                    'batched_processing': 10000,
                    'weight_caching': 1000,
                    'standard_processing': 0
                }
            }
            
        except Exception as e:
            self.logger.error(f"Error getting performance metrics: {str(e)}")
            return {
                'dataset_size': len(activities) if activities else 0,
                'recommended_optimization': 'error',
                'estimated_processing_time_ms': 0,
                'memory_usage_estimate_mb': 0,
                'error': str(e)
            }

# Global engine instance
exponential_decay_engine = ExponentialDecayEngine()

def calculate_exponential_weight(days_ago: int, decay_rate: float) -> float:
    """Convenience function to calculate exponential weight"""
    return exponential_decay_engine.calculate_exponential_weight(days_ago, decay_rate)

def calculate_weighted_averages(activities: List[ActivityData], reference_date: date, decay_rate: float) -> DecayCalculationResult:
    """Convenience function to calculate weighted averages"""
    return exponential_decay_engine.calculate_weighted_averages(activities, reference_date, decay_rate)

def calculate_enhanced_acwr(acute_activities: List[ActivityData], chronic_activities: List[ActivityData], 
                          decay_rate: float, reference_date: date) -> Dict:
    """Convenience function to calculate enhanced ACWR"""
    return exponential_decay_engine.calculate_enhanced_acwr(acute_activities, chronic_activities, decay_rate, reference_date)
