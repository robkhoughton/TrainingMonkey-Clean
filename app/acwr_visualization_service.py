#!/usr/bin/env python3
"""
ACWR Visualization Data Generation Service
Generates comprehensive visualization data for ACWR analysis and comparison
"""

import logging
import math
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass
from acwr_configuration_service import ACWRConfigurationService
from acwr_calculation_service import ACWRCalculationService
import db_utils

logger = logging.getLogger(__name__)

@dataclass
class VisualizationDataPoint:
    """Data point for visualization"""
    x: float
    y: float
    z: float
    value: float
    label: str
    metadata: Dict[str, Any]

@dataclass
class ParameterCombination:
    """Parameter combination for analysis"""
    chronic_period_days: int
    decay_rate: float
    configuration_id: Optional[int] = None
    configuration_name: Optional[str] = None

@dataclass
class TimeSeriesPoint:
    """Time series data point"""
    date: datetime
    value: float
    metadata: Dict[str, Any]

class ACWRVisualizationService:
    """Service for generating ACWR visualization data"""
    
    def __init__(self):
        self.config_service = ACWRConfigurationService()
        self.calc_service = ACWRCalculationService()
        self.logger = logging.getLogger(__name__)
        
        # Default parameter ranges
        self.default_chronic_periods = [28, 35, 42, 49, 56, 63, 70, 77, 84, 90]
        self.default_decay_rates = [0.01, 0.02, 0.03, 0.04, 0.05, 0.06, 0.07, 0.08, 0.09, 0.10, 0.12, 0.15, 0.18, 0.20]
        
        # Risk zone thresholds
        self.risk_zones = {
            'low': {'min': 0.0, 'max': 0.8, 'color': '#28a745'},
            'moderate': {'min': 0.8, 'max': 1.3, 'color': '#ffc107'},
            'high': {'min': 1.3, 'max': 1.5, 'color': '#fd7e14'},
            'very_high': {'min': 1.5, 'max': float('inf'), 'color': '#dc3545'}
        }
    
    def generate_parameter_matrix(self, 
                                chronic_periods: Optional[List[int]] = None,
                                decay_rates: Optional[List[float]] = None) -> List[ParameterCombination]:
        """Generate parameter matrix for analysis"""
        try:
            if chronic_periods is None:
                chronic_periods = self.default_chronic_periods
            if decay_rates is None:
                decay_rates = self.default_decay_rates
            
            combinations = []
            for chronic_period in chronic_periods:
                for decay_rate in decay_rates:
                    combinations.append(ParameterCombination(
                        chronic_period_days=chronic_period,
                        decay_rate=decay_rate
                    ))
            
            self.logger.info(f"Generated {len(combinations)} parameter combinations")
            return combinations
            
        except Exception as e:
            self.logger.error(f"Error generating parameter matrix: {str(e)}")
            return []
    
    def calculate_chronic_load_surface(self, 
                                     user_id: int,
                                     parameter_combinations: List[ParameterCombination]) -> List[VisualizationDataPoint]:
        """Calculate chronic load values for 3D surface plot"""
        try:
            data_points = []
            
            for i, combination in enumerate(parameter_combinations):
                try:
                    # Calculate chronic load for this parameter combination
                    acwr_result = self.calc_service.calculate_acwr_for_user(
                        user_id=user_id,
                        activity_date=datetime.now().date().strftime('%Y-%m-%d')
                    )
                    
                    chronic_load = acwr_result.get('chronic_load', 0)
                    
                    data_point = VisualizationDataPoint(
                        x=combination.chronic_period_days,
                        y=combination.decay_rate,
                        z=chronic_load,
                        value=chronic_load,
                        label=f"Chronic: {combination.chronic_period_days}d, Decay: {combination.decay_rate}",
                        metadata={
                            'chronic_period_days': combination.chronic_period_days,
                            'decay_rate': combination.decay_rate,
                            'acute_load': acwr_result.get('acute_load', 0),
                            'acwr_ratio': acwr_result.get('acwr_ratio', 0),
                            'risk_level': acwr_result.get('risk_level', 'Unknown'),
                            'data_quality': acwr_result.get('data_quality', 'Unknown')
                        }
                    )
                    
                    data_points.append(data_point)
                    
                except Exception as e:
                    self.logger.warning(f"Error calculating chronic load for combination {i}: {str(e)}")
                    continue
            
            self.logger.info(f"Generated {len(data_points)} chronic load data points")
            return data_points
            
        except Exception as e:
            self.logger.error(f"Error calculating chronic load surface: {str(e)}")
            return []
    
    def generate_heatmap_data(self, 
                            user_id: int,
                            parameter_combinations: List[ParameterCombination]) -> Dict[str, Any]:
        """Generate 2D heatmap data with color-coded chronic load values"""
        try:
            # Calculate chronic load values
            data_points = self.calculate_chronic_load_surface(user_id, parameter_combinations)
            
            if not data_points:
                return {'error': 'No data points generated'}
            
            # Extract unique values for axes
            chronic_periods = sorted(list(set([dp.x for dp in data_points])))
            decay_rates = sorted(list(set([dp.y for dp in data_points])))
            
            # Create matrix for heatmap
            matrix = []
            for decay_rate in decay_rates:
                row = []
                for chronic_period in chronic_periods:
                    # Find matching data point
                    matching_point = next(
                        (dp for dp in data_points if dp.x == chronic_period and dp.y == decay_rate),
                        None
                    )
                    
                    if matching_point:
                        row.append(matching_point.value)
                    else:
                        row.append(0)  # Default value for missing data
                
                matrix.append(row)
            
            # Generate color mapping
            all_values = [dp.value for dp in data_points if dp.value > 0]
            if all_values:
                min_value = min(all_values)
                max_value = max(all_values)
            else:
                min_value = max_value = 0
            
            heatmap_data = {
                'matrix': matrix,
                'x_labels': chronic_periods,
                'y_labels': decay_rates,
                'color_scale': {
                    'min': min_value,
                    'max': max_value,
                    'colors': ['#0066cc', '#00cc66', '#ffcc00', '#ff6600', '#cc0000']
                },
                'data_points': [
                    {
                        'x': dp.x,
                        'y': dp.y,
                        'value': dp.value,
                        'label': dp.label,
                        'metadata': dp.metadata
                    }
                    for dp in data_points
                ]
            }
            
            self.logger.info(f"Generated heatmap data with {len(data_points)} points")
            return heatmap_data
            
        except Exception as e:
            self.logger.error(f"Error generating heatmap data: {str(e)}")
            return {'error': str(e)}
    
    def generate_time_series_data(self, 
                                user_id: int,
                                configuration_id: int,
                                days_back: int = 90) -> List[TimeSeriesPoint]:
        """Generate time series data for parameter comparison"""
        try:
            # Get configuration details
            config = self.config_service.get_configuration_by_id(configuration_id)
            if not config:
                self.logger.error(f"Configuration {configuration_id} not found")
                return []
            
            # Get user's activities for the time period
            end_date = datetime.now().date()
            start_date = end_date - timedelta(days=days_back)
            
            # Query activities
            query = """
                SELECT start_date, trimp_score, duration_seconds
                FROM activities
                WHERE user_id = %s AND start_date >= %s AND start_date <= %s
                ORDER BY start_date
            """
            
            activities = db_utils.execute_query(
                query, 
                (user_id, start_date, end_date), 
                fetch=True
            )
            
            if not activities:
                self.logger.warning(f"No activities found for user {user_id} in the specified period")
                return []
            
            # Calculate ACWR for each day
            time_series_points = []
            current_date = start_date
            
            while current_date <= end_date:
                try:
                    # Calculate ACWR for this date
                    acwr_result = self.calc_service.calculate_acwr_for_user(
                        user_id=user_id,
                        activity_date=current_date.strftime('%Y-%m-%d')
                    )
                    
                    time_series_point = TimeSeriesPoint(
                        date=current_date,
                        value=acwr_result.get('acwr_ratio', 0),
                        metadata={
                            'acute_load': acwr_result.get('acute_load', 0),
                            'chronic_load': acwr_result.get('chronic_load', 0),
                            'risk_level': acwr_result.get('risk_level', 'Unknown'),
                            'data_quality': acwr_result.get('data_quality', 'Unknown'),
                            'configuration_id': configuration_id,
                            'configuration_name': config['name']
                        }
                    )
                    
                    time_series_points.append(time_series_point)
                    
                except Exception as e:
                    self.logger.warning(f"Error calculating ACWR for date {current_date}: {str(e)}")
                
                current_date += timedelta(days=1)
            
            self.logger.info(f"Generated {len(time_series_points)} time series points")
            return time_series_points
            
        except Exception as e:
            self.logger.error(f"Error generating time series data: {str(e)}")
            return []
    
    def generate_acwr_ratio_visualization(self, 
                                        user_id: int,
                                        configuration_id: int,
                                        days_back: int = 30) -> Dict[str, Any]:
        """Generate ACWR ratio visualization with risk zone indicators"""
        try:
            # Get time series data
            time_series_data = self.generate_time_series_data(user_id, configuration_id, days_back)
            
            if not time_series_data:
                return {'error': 'No time series data available'}
            
            # Categorize points by risk zones
            risk_zone_data = {
                'low': [],
                'moderate': [],
                'high': [],
                'very_high': []
            }
            
            for point in time_series_data:
                acwr_ratio = point.value
                
                if acwr_ratio < 0.8:
                    risk_zone_data['low'].append(point)
                elif acwr_ratio < 1.3:
                    risk_zone_data['moderate'].append(point)
                elif acwr_ratio < 1.5:
                    risk_zone_data['high'].append(point)
                else:
                    risk_zone_data['very_high'].append(point)
            
            # Calculate statistics
            all_ratios = [point.value for point in time_series_data]
            statistics = {
                'mean': np.mean(all_ratios) if all_ratios else 0,
                'median': np.median(all_ratios) if all_ratios else 0,
                'std': np.std(all_ratios) if all_ratios else 0,
                'min': min(all_ratios) if all_ratios else 0,
                'max': max(all_ratios) if all_ratios else 0
            }
            
            # Risk zone summary
            risk_summary = {}
            for zone, points in risk_zone_data.items():
                risk_summary[zone] = {
                    'count': len(points),
                    'percentage': (len(points) / len(time_series_data)) * 100 if time_series_data else 0,
                    'color': self.risk_zones[zone]['color'],
                    'threshold': self.risk_zones[zone]
                }
            
            visualization_data = {
                'time_series': [
                    {
                        'date': point.date.isoformat(),
                        'value': point.value,
                        'risk_zone': self._get_risk_zone(point.value),
                        'metadata': point.metadata
                    }
                    for point in time_series_data
                ],
                'risk_zones': risk_zone_data,
                'risk_summary': risk_summary,
                'statistics': statistics,
                'risk_zone_thresholds': self.risk_zones
            }
            
            self.logger.info(f"Generated ACWR ratio visualization with {len(time_series_data)} points")
            return visualization_data
            
        except Exception as e:
            self.logger.error(f"Error generating ACWR ratio visualization: {str(e)}")
            return {'error': str(e)}
    
    def perform_sensitivity_analysis(self, 
                                   user_id: int,
                                   base_chronic_period: int = 42,
                                   base_decay_rate: float = 0.05,
                                   analysis_date: Optional[str] = None) -> Dict[str, Any]:
        """Perform sensitivity analysis for parameter combinations on a specific date"""
        try:
            # Use provided date or default to today
            if analysis_date is None:
                analysis_date = datetime.now().date().strftime('%Y-%m-%d')
            
            # Define parameter variations
            chronic_variations = [28, 42, 56, 70, 84]
            decay_variations = [base_decay_rate - 0.02, base_decay_rate, base_decay_rate + 0.02, 0.09]
            
            # Generate parameter combinations
            parameter_combinations = []
            for chronic_period in chronic_variations:
                for decay_rate in decay_variations:
                    if 28 <= chronic_period <= 90 and 0.01 <= decay_rate <= 0.20:
                        parameter_combinations.append(ParameterCombination(
                            chronic_period_days=chronic_period,
                            decay_rate=decay_rate
                        ))
            
            # Calculate results for each combination
            sensitivity_results = []
            base_result = None
            
            for combination in parameter_combinations:
                try:
                    # Create a temporary configuration for this parameter combination
                    temp_config = {
                        'chronic_period_days': combination.chronic_period_days,
                        'decay_rate': combination.decay_rate
                    }
                    
                    # Calculate ACWR with the specific parameters
                    acwr_result = self.config_service.calculate_enhanced_acwr(
                        user_id=user_id,
                        activity_date=analysis_date,
                        configuration=temp_config
                    )
                    
                    result = {
                        'chronic_period_days': combination.chronic_period_days,
                        'decay_rate': combination.decay_rate,
                        'external_acwr': acwr_result.get('enhanced_acute_chronic_ratio', 0),  # External ACWR (based on distance/load)
                        'internal_acwr': acwr_result.get('enhanced_trimp_acute_chronic_ratio', 0),  # Internal ACWR (based on TRIMP)
                        'external_work': acwr_result.get('acute_load_avg', 0),  # External Work (7-day avg load)
                        'internal_load': acwr_result.get('acute_trimp_avg', 0),  # Internal Load (7-day avg TRIMP)
                        'normalized_divergence': acwr_result.get('enhanced_normalized_divergence', 0),  # Normalized divergence
                        'chronic_load': acwr_result.get('enhanced_chronic_load', 0),
                        'risk_level': 'Unknown',  # This would need to be calculated based on ACWR values
                        'data_quality': acwr_result.get('data_quality', 'Unknown')
                    }
                    
                    sensitivity_results.append(result)
                    
                    # Store base result for comparison
                    if (combination.chronic_period_days == base_chronic_period and 
                        combination.decay_rate == base_decay_rate):
                        base_result = result
                        
                except Exception as e:
                    self.logger.warning(f"Error in sensitivity analysis for combination {combination.chronic_period_days}d/{combination.decay_rate}: {str(e)}")
                    # Add a default result to avoid breaking the analysis
                    result = {
                        'chronic_period_days': combination.chronic_period_days,
                        'decay_rate': combination.decay_rate,
                        'external_acwr': 0,
                        'internal_acwr': 0,
                        'external_work': 0,
                        'internal_load': 0,
                        'normalized_divergence': 0,
                        'chronic_load': 0,
                        'risk_level': 'Error',
                        'data_quality': 'Error'
                    }
                    sensitivity_results.append(result)
                    continue
            
            # Calculate sensitivity metrics
            if base_result and sensitivity_results:
                sensitivity_metrics = self._calculate_sensitivity_metrics(base_result, sensitivity_results)
            else:
                sensitivity_metrics = {}
            
            analysis_result = {
                'base_parameters': {
                    'chronic_period_days': base_chronic_period,
                    'decay_rate': base_decay_rate
                },
                'base_result': base_result,
                'sensitivity_results': sensitivity_results,
                'sensitivity_metrics': sensitivity_metrics,
                'parameter_combinations': len(parameter_combinations)
            }
            
            self.logger.info(f"Completed sensitivity analysis with {len(sensitivity_results)} results")
            return analysis_result
            
        except Exception as e:
            self.logger.error(f"Error performing sensitivity analysis: {str(e)}")
            return {'error': str(e)}
    
    def generate_data_quality_indicators(self, 
                                       user_id: int,
                                       configuration_id: int,
                                       days_back: int = 90) -> Dict[str, Any]:
        """Generate data quality indicators and confidence metrics"""
        try:
            # Get configuration details
            config = self.config_service.get_configuration_by_id(configuration_id)
            if not config:
                return {'error': 'Configuration not found'}
            
            # Get user's activities for the time period
            end_date = datetime.now().date()
            start_date = end_date - timedelta(days=days_back)
            
            # Query activities with detailed information
            query = """
                SELECT 
                    start_date,
                    trimp_score,
                    duration_seconds,
                    distance_meters,
                    average_heart_rate,
                    max_heart_rate
                FROM activities
                WHERE user_id = %s AND start_date >= %s AND start_date <= %s
                ORDER BY start_date
            """
            
            activities = db_utils.execute_query(
                query, 
                (user_id, start_date, end_date), 
                fetch=True
            )
            
            if not activities:
                return {'error': 'No activities found'}
            
            # Calculate data quality metrics
            total_activities = len(activities)
            activities_with_trimp = len([a for a in activities if a.get('trimp_score') and a['trimp_score'] > 0])
            activities_with_hr = len([a for a in activities if a.get('average_heart_rate') and a['average_heart_rate'] > 0])
            activities_with_distance = len([a for a in activities if a.get('distance_meters') and a['distance_meters'] > 0])
            
            # Calculate data completeness
            trimp_completeness = (activities_with_trimp / total_activities) * 100 if total_activities > 0 else 0
            hr_completeness = (activities_with_hr / total_activities) * 100 if total_activities > 0 else 0
            distance_completeness = (activities_with_distance / total_activities) * 100 if total_activities > 0 else 0
            
            # Calculate data consistency
            trimp_scores = [a['trimp_score'] for a in activities if a.get('trimp_score') and a['trimp_score'] > 0]
            trimp_consistency = self._calculate_data_consistency(trimp_scores)
            
            # Calculate temporal distribution
            temporal_distribution = self._calculate_temporal_distribution(activities, start_date, end_date)
            
            # Calculate confidence score
            confidence_score = self._calculate_confidence_score(
                trimp_completeness, hr_completeness, temporal_distribution, trimp_consistency
            )
            
            # Generate quality indicators
            quality_indicators = {
                'data_completeness': {
                    'trimp_scores': trimp_completeness,
                    'heart_rate': hr_completeness,
                    'distance': distance_completeness,
                    'overall': (trimp_completeness + hr_completeness + distance_completeness) / 3
                },
                'data_consistency': {
                    'trimp_scores': trimp_consistency,
                    'coefficient_of_variation': trimp_consistency.get('coefficient_of_variation', 0)
                },
                'temporal_distribution': temporal_distribution,
                'confidence_score': confidence_score,
                'total_activities': total_activities,
                'analysis_period': {
                    'start_date': start_date.isoformat(),
                    'end_date': end_date.isoformat(),
                    'days': days_back
                },
                'quality_assessment': self._assess_data_quality(confidence_score)
            }
            
            self.logger.info(f"Generated data quality indicators for {total_activities} activities")
            return quality_indicators
            
        except Exception as e:
            self.logger.error(f"Error generating data quality indicators: {str(e)}")
            return {'error': str(e)}
    
    def _get_risk_zone(self, acwr_ratio: float) -> str:
        """Get risk zone for ACWR ratio"""
        if acwr_ratio < 0.8:
            return 'low'
        elif acwr_ratio < 1.3:
            return 'moderate'
        elif acwr_ratio < 1.5:
            return 'high'
        else:
            return 'very_high'
    
    def _calculate_sensitivity_metrics(self, base_result: Dict, sensitivity_results: List[Dict]) -> Dict[str, Any]:
        """Calculate sensitivity metrics for parameter variations"""
        try:
            base_acwr = base_result.get('acwr_ratio', 0)
            base_chronic = base_result.get('chronic_load', 0)
            
            # Calculate variations
            acwr_variations = []
            chronic_variations = []
            
            for result in sensitivity_results:
                if result['chronic_period_days'] != base_result['chronic_period_days'] or \
                   result['decay_rate'] != base_result['decay_rate']:
                    acwr_variations.append(abs(result['acwr_ratio'] - base_acwr))
                    chronic_variations.append(abs(result['chronic_load'] - base_chronic))
            
            # Calculate sensitivity metrics
            metrics = {
                'acwr_sensitivity': {
                    'mean_variation': np.mean(acwr_variations) if acwr_variations else 0,
                    'max_variation': max(acwr_variations) if acwr_variations else 0,
                    'coefficient_of_variation': (np.std(acwr_variations) / np.mean(acwr_variations)) * 100 if acwr_variations and np.mean(acwr_variations) > 0 else 0
                },
                'chronic_sensitivity': {
                    'mean_variation': np.mean(chronic_variations) if chronic_variations else 0,
                    'max_variation': max(chronic_variations) if chronic_variations else 0,
                    'coefficient_of_variation': (np.std(chronic_variations) / np.mean(chronic_variations)) * 100 if chronic_variations and np.mean(chronic_variations) > 0 else 0
                }
            }
            
            return metrics
            
        except Exception as e:
            self.logger.error(f"Error calculating sensitivity metrics: {str(e)}")
            return {}
    
    def _calculate_data_consistency(self, values: List[float]) -> Dict[str, float]:
        """Calculate data consistency metrics"""
        if not values:
            return {'coefficient_of_variation': 0, 'std': 0, 'mean': 0}
        
        mean_val = np.mean(values)
        std_val = np.std(values)
        cv = (std_val / mean_val) * 100 if mean_val > 0 else 0
        
        return {
            'coefficient_of_variation': cv,
            'std': std_val,
            'mean': mean_val,
            'min': min(values),
            'max': max(values)
        }
    
    def _calculate_temporal_distribution(self, activities: List[Dict], start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Calculate temporal distribution of activities"""
        try:
            # Group activities by week
            weekly_counts = {}
            current_date = start_date
            
            while current_date <= end_date:
                week_start = current_date - timedelta(days=current_date.weekday())
                week_key = week_start.strftime('%Y-%W')
                
                if week_key not in weekly_counts:
                    weekly_counts[week_key] = 0
                
                # Count activities in this week
                week_activities = [
                    a for a in activities 
                    if week_start <= a['start_date'] < week_start + timedelta(days=7)
                ]
                weekly_counts[week_key] = len(week_activities)
                
                current_date += timedelta(days=7)
            
            # Calculate distribution metrics
            activity_counts = list(weekly_counts.values())
            if activity_counts:
                mean_activities = np.mean(activity_counts)
                std_activities = np.std(activity_counts)
                cv = (std_activities / mean_activities) * 100 if mean_activities > 0 else 0
            else:
                mean_activities = std_activities = cv = 0
            
            return {
                'weekly_distribution': weekly_counts,
                'mean_activities_per_week': mean_activities,
                'std_activities_per_week': std_activities,
                'coefficient_of_variation': cv,
                'total_weeks': len(weekly_counts)
            }
            
        except Exception as e:
            self.logger.error(f"Error calculating temporal distribution: {str(e)}")
            return {}
    
    def _calculate_confidence_score(self, trimp_completeness: float, hr_completeness: float, 
                                  temporal_distribution: Dict, trimp_consistency: Dict) -> float:
        """Calculate overall confidence score"""
        try:
            # Weight different factors
            completeness_weight = 0.4
            consistency_weight = 0.3
            temporal_weight = 0.3
            
            # Completeness score (0-100)
            completeness_score = (trimp_completeness + hr_completeness) / 2
            
            # Consistency score (0-100, lower CV is better)
            cv = trimp_consistency.get('coefficient_of_variation', 100)
            consistency_score = max(0, 100 - cv)
            
            # Temporal distribution score (0-100, lower CV is better)
            temporal_cv = temporal_distribution.get('coefficient_of_variation', 100)
            temporal_score = max(0, 100 - temporal_cv)
            
            # Calculate weighted confidence score
            confidence_score = (
                completeness_score * completeness_weight +
                consistency_score * consistency_weight +
                temporal_score * temporal_weight
            )
            
            return min(100, max(0, confidence_score))
            
        except Exception as e:
            self.logger.error(f"Error calculating confidence score: {str(e)}")
            return 0
    
    def _assess_data_quality(self, confidence_score: float) -> Dict[str, Any]:
        """Assess data quality based on confidence score"""
        if confidence_score >= 80:
            quality_level = 'excellent'
            color = '#28a745'
        elif confidence_score >= 60:
            quality_level = 'good'
            color = '#17a2b8'
        elif confidence_score >= 40:
            quality_level = 'fair'
            color = '#ffc107'
        else:
            quality_level = 'poor'
            color = '#dc3545'
        
        return {
            'level': quality_level,
            'color': color,
            'score': confidence_score,
            'description': f"Data quality is {quality_level} with a confidence score of {confidence_score:.1f}%"
        }
