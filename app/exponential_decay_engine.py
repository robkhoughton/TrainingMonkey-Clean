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
                                 decay_rate: float,
                                 period_days: int) -> DecayCalculationResult:
        """
        Calculate per-calendar-day weighted averages using exponential decay

        The average is per DAY, not per activity row: the weighted sums run over the
        activities, but the denominator is the sum of weights over all period_days
        calendar days. A day with no activity counts as a zero-load day, and multiple
        activities on one day add to that day's load rather than adding weight. This
        keeps the chronic average in the same units as the 7-day acute average
        (7-day sum / 7).

        Args:
            activities: List of activity data, all within the period ending reference_date
            reference_date: Reference date for calculating days_ago
            decay_rate: Decay rate parameter
            period_days: Number of calendar days in the averaging period

        Returns:
            DecayCalculationResult with weighted calculations
        """
        try:
            weighted_load_sum = 0.0
            weighted_trimp_sum = 0.0
            total_weight = sum(self.calculate_exponential_weight(i, decay_rate) for i in range(period_days))
            
            # Process each activity
            for activity in activities:
                # Calculate days ago from reference date
                days_ago = (reference_date - activity.date).days
                if days_ago >= period_days:
                    raise ValueError(f"activity on {activity.date} is outside the {period_days}-day period ending {reference_date}")
                
                # Calculate exponential weight
                weight = self.calculate_exponential_weight(days_ago, decay_rate)
                
                # Update weighted sums
                weighted_load_sum += activity.total_load_miles * weight
                weighted_trimp_sum += activity.trimp * weight
                
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
