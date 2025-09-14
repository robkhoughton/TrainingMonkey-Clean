"""
Tiered Feature Unlock Module

This module implements sophisticated tiered feature unlocking logic for the progressive
onboarding system. It provides advanced feature unlocking capabilities including:

- Conditional feature unlocking based on multiple criteria
- Intelligent progression tracking and recommendations
- Feature dependency management
- Usage-based unlocking triggers
- Performance-based feature access
- Social and engagement-based unlocking
- Time-based feature availability
- Custom unlock conditions and rules
"""

import logging
import json
from typing import Dict, List, Optional, Tuple, Any, Set
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum

from db_utils import get_db_connection, execute_query
from onboarding_manager import OnboardingManager, OnboardingStep, FeatureTier, FeatureUnlock

logger = logging.getLogger(__name__)


class UnlockCondition(Enum):
    """Types of unlock conditions"""
    STEP_COMPLETION = 'step_completion'
    ACTIVITY_COUNT = 'activity_count'
    DAYS_ACTIVE = 'days_active'
    USAGE_FREQUENCY = 'usage_frequency'
    PERFORMANCE_THRESHOLD = 'performance_threshold'
    ENGAGEMENT_LEVEL = 'engagement_level'
    SOCIAL_INTERACTION = 'social_interaction'
    TIME_BASED = 'time_based'
    CUSTOM_RULE = 'custom_rule'


class UnlockTrigger(Enum):
    """Types of unlock triggers"""
    AUTOMATIC = 'automatic'
    MANUAL = 'manual'
    SCHEDULED = 'scheduled'
    EVENT_BASED = 'event_based'
    CONDITIONAL = 'conditional'


@dataclass
class UnlockRequirement:
    """Individual requirement for feature unlocking"""
    condition: UnlockCondition
    value: Any
    operator: str = '>='
    description: str = ''
    weight: float = 1.0


@dataclass
class TieredFeatureDefinition:
    """Enhanced feature definition with tiered unlocking logic"""
    feature_name: str
    tier: FeatureTier
    requirements: List[UnlockRequirement]
    dependencies: List[str]  # Other features that must be unlocked first
    unlock_trigger: UnlockTrigger
    unlock_conditions: Dict[str, Any]  # Additional conditions
    description: str
    tutorial_available: bool
    priority: int = 1
    max_users_per_tier: Optional[int] = None


class TieredFeatureUnlockManager:
    """
    Advanced tiered feature unlocking manager with sophisticated logic
    """
    
    def __init__(self):
        """Initialize the tiered feature unlock manager"""
        self.onboarding_manager = OnboardingManager()
        self.feature_definitions = self._initialize_tiered_features()
        self.unlock_rules = self._initialize_unlock_rules()
        self.performance_metrics = self._initialize_performance_metrics()
        
    def _initialize_tiered_features(self) -> Dict[str, TieredFeatureDefinition]:
        """Initialize enhanced feature definitions with tiered unlocking logic"""
        return {
            'dashboard_basic': TieredFeatureDefinition(
                feature_name='Basic Dashboard',
                tier=FeatureTier.BASIC,
                requirements=[
                    UnlockRequirement(UnlockCondition.STEP_COMPLETION, OnboardingStep.WELCOME, '==', 'Complete welcome step', 1.0)
                ],
                dependencies=[],
                unlock_trigger=UnlockTrigger.AUTOMATIC,
                unlock_conditions={'immediate': True},
                description='View basic training metrics and activity summary',
                tutorial_available=True,
                priority=1
            ),
            
            'dashboard_advanced': TieredFeatureDefinition(
                feature_name='Advanced Dashboard',
                tier=FeatureTier.INTERMEDIATE,
                requirements=[
                    UnlockRequirement(UnlockCondition.STEP_COMPLETION, OnboardingStep.DASHBOARD_INTRO, '==', 'Complete dashboard intro', 1.0),
                    UnlockRequirement(UnlockCondition.ACTIVITY_COUNT, 1, '>=', 'Have at least 1 activity', 1.0),
                    UnlockRequirement(UnlockCondition.DAYS_ACTIVE, 1, '>=', 'Be active for at least 1 day', 0.8)
                ],
                dependencies=['dashboard_basic'],
                unlock_trigger=UnlockTrigger.CONDITIONAL,
                unlock_conditions={'engagement_threshold': 0.5},
                description='Access to ACWR, divergence analysis, and trend charts',
                tutorial_available=True,
                priority=2
            ),
            
            'recommendations': TieredFeatureDefinition(
                feature_name='AI Recommendations',
                tier=FeatureTier.INTERMEDIATE,
                requirements=[
                    UnlockRequirement(UnlockCondition.STEP_COMPLETION, OnboardingStep.FIRST_RECOMMENDATION, '==', 'Complete first recommendation step', 1.0),
                    UnlockRequirement(UnlockCondition.ACTIVITY_COUNT, 3, '>=', 'Have at least 3 activities', 1.0),
                    UnlockRequirement(UnlockCondition.DAYS_ACTIVE, 3, '>=', 'Be active for at least 3 days', 1.0),
                    UnlockRequirement(UnlockCondition.USAGE_FREQUENCY, 0.6, '>=', 'Use the app regularly', 0.9)
                ],
                dependencies=['dashboard_basic'],
                unlock_trigger=UnlockTrigger.CONDITIONAL,
                unlock_conditions={'data_quality_threshold': 0.7},
                description='Personalized training recommendations and insights',
                tutorial_available=True,
                priority=3
            ),
            
            'journal': TieredFeatureDefinition(
                feature_name='Training Journal',
                tier=FeatureTier.ADVANCED,
                requirements=[
                    UnlockRequirement(UnlockCondition.STEP_COMPLETION, OnboardingStep.JOURNAL_INTRO, '==', 'Complete journal intro', 1.0),
                    UnlockRequirement(UnlockCondition.ACTIVITY_COUNT, 5, '>=', 'Have at least 5 activities', 1.0),
                    UnlockRequirement(UnlockCondition.DAYS_ACTIVE, 5, '>=', 'Be active for at least 5 days', 1.0),
                    UnlockRequirement(UnlockCondition.ENGAGEMENT_LEVEL, 0.7, '>=', 'Show consistent engagement', 0.8)
                ],
                dependencies=['dashboard_advanced', 'recommendations'],
                unlock_trigger=UnlockTrigger.CONDITIONAL,
                unlock_conditions={'consistency_threshold': 0.6},
                description='Daily training journal with AI analysis and alignment scoring',
                tutorial_available=True,
                priority=4
            ),
            
            'advanced_analytics': TieredFeatureDefinition(
                feature_name='Advanced Analytics',
                tier=FeatureTier.EXPERT,
                requirements=[
                    UnlockRequirement(UnlockCondition.STEP_COMPLETION, OnboardingStep.COMPLETED, '==', 'Complete onboarding', 1.0),
                    UnlockRequirement(UnlockCondition.ACTIVITY_COUNT, 10, '>=', 'Have at least 10 activities', 1.0),
                    UnlockRequirement(UnlockCondition.DAYS_ACTIVE, 7, '>=', 'Be active for at least 7 days', 1.0),
                    UnlockRequirement(UnlockCondition.PERFORMANCE_THRESHOLD, 0.8, '>=', 'Meet performance standards', 1.0),
                    UnlockRequirement(UnlockCondition.USAGE_FREQUENCY, 0.8, '>=', 'High usage frequency', 0.9)
                ],
                dependencies=['journal', 'custom_goals'],
                unlock_trigger=UnlockTrigger.CONDITIONAL,
                unlock_conditions={'expert_threshold': 0.9, 'max_users_per_tier': 100},
                description='Deep analytics, pattern recognition, and predictive insights',
                tutorial_available=False,
                priority=5,
                max_users_per_tier=100
            ),
            
            'custom_goals': TieredFeatureDefinition(
                feature_name='Custom Goals',
                tier=FeatureTier.ADVANCED,
                requirements=[
                    UnlockRequirement(UnlockCondition.STEP_COMPLETION, OnboardingStep.GOALS_SETUP, '==', 'Complete goals setup', 1.0),
                    UnlockRequirement(UnlockCondition.ACTIVITY_COUNT, 3, '>=', 'Have at least 3 activities', 1.0),
                    UnlockRequirement(UnlockCondition.DAYS_ACTIVE, 3, '>=', 'Be active for at least 3 days', 1.0),
                    UnlockRequirement(UnlockCondition.ENGAGEMENT_LEVEL, 0.6, '>=', 'Show engagement', 0.8)
                ],
                dependencies=['dashboard_advanced'],
                unlock_trigger=UnlockTrigger.CONDITIONAL,
                unlock_conditions={'goal_setting_readiness': 0.7},
                description='Set and track custom training goals and milestones',
                tutorial_available=True,
                priority=3
            ),
            
            'social_features': TieredFeatureDefinition(
                feature_name='Social Features',
                tier=FeatureTier.INTERMEDIATE,
                requirements=[
                    UnlockRequirement(UnlockCondition.ACTIVITY_COUNT, 5, '>=', 'Have at least 5 activities', 1.0),
                    UnlockRequirement(UnlockCondition.DAYS_ACTIVE, 5, '>=', 'Be active for at least 5 days', 1.0),
                    UnlockRequirement(UnlockCondition.SOCIAL_INTERACTION, 1, '>=', 'Show social engagement', 0.7)
                ],
                dependencies=['recommendations'],
                unlock_trigger=UnlockTrigger.EVENT_BASED,
                unlock_conditions={'social_ready': True},
                description='Connect with other athletes and share achievements',
                tutorial_available=True,
                priority=4
            ),
            
            'premium_insights': TieredFeatureDefinition(
                feature_name='Premium Insights',
                tier=FeatureTier.EXPERT,
                requirements=[
                    UnlockRequirement(UnlockCondition.ACTIVITY_COUNT, 15, '>=', 'Have at least 15 activities', 1.0),
                    UnlockRequirement(UnlockCondition.DAYS_ACTIVE, 14, '>=', 'Be active for at least 14 days', 1.0),
                    UnlockRequirement(UnlockCondition.PERFORMANCE_THRESHOLD, 0.9, '>=', 'High performance level', 1.0),
                    UnlockRequirement(UnlockCondition.USAGE_FREQUENCY, 0.9, '>=', 'Very high usage frequency', 1.0)
                ],
                dependencies=['advanced_analytics'],
                unlock_trigger=UnlockTrigger.SCHEDULED,
                unlock_conditions={'premium_eligibility': True, 'max_users_per_tier': 50},
                description='Premium insights and advanced analytics features',
                tutorial_available=False,
                priority=6,
                max_users_per_tier=50
            )
        }
    
    def _initialize_unlock_rules(self) -> Dict[str, Any]:
        """Initialize unlock rules and conditions"""
        return {
            'engagement_thresholds': {
                'low': 0.3,
                'medium': 0.6,
                'high': 0.8,
                'expert': 0.9
            },
            'performance_metrics': {
                'consistency': 0.7,
                'improvement': 0.6,
                'goal_achievement': 0.8
            },
            'time_based_rules': {
                'feature_cooldown_hours': 24,
                'tier_progression_days': 7,
                'engagement_window_days': 30
            },
            'social_rules': {
                'min_connections': 1,
                'min_shared_activities': 3,
                'community_engagement': 0.5
            }
        }
    
    def _initialize_performance_metrics(self) -> Dict[str, Any]:
        """Initialize performance tracking metrics"""
        return {
            'usage_frequency': {},
            'engagement_level': {},
            'performance_scores': {},
            'social_metrics': {},
            'goal_achievement': {}
        }
    
    def check_tiered_feature_unlock(self, user_id: int, feature_name: str) -> Tuple[bool, Dict[str, Any]]:
        """
        Check if a user can unlock a specific feature with detailed analysis
        
        Args:
            user_id: User ID to check
            feature_name: Name of feature to check
            
        Returns:
            Tuple of (can_unlock, detailed_analysis)
        """
        try:
            feature_def = self.feature_definitions.get(feature_name)
            if not feature_def:
                return False, {'error': f'Unknown feature: {feature_name}'}
            
            analysis = {
                'feature_name': feature_name,
                'tier': feature_def.tier.value,
                'requirements_met': [],
                'requirements_failed': [],
                'dependencies_met': True,
                'unlock_score': 0.0,
                'can_unlock': False,
                'recommendations': []
            }
            
            # Check dependencies
            for dependency in feature_def.dependencies:
                if not self.onboarding_manager.check_feature_unlock(user_id, dependency):
                    analysis['dependencies_met'] = False
                    analysis['requirements_failed'].append({
                        'type': 'dependency',
                        'feature': dependency,
                        'description': f'Requires {dependency} to be unlocked first'
                    })
            
            if not analysis['dependencies_met']:
                return False, analysis
            
            # Check each requirement
            total_weight = 0
            met_weight = 0
            
            for requirement in feature_def.requirements:
                total_weight += requirement.weight
                requirement_met = self._check_requirement(user_id, requirement)
                
                if requirement_met:
                    met_weight += requirement.weight
                    analysis['requirements_met'].append({
                        'condition': requirement.condition.value,
                        'value': requirement.value,
                        'description': requirement.description,
                        'weight': requirement.weight
                    })
                else:
                    analysis['requirements_failed'].append({
                        'condition': requirement.condition.value,
                        'value': requirement.value,
                        'description': requirement.description,
                        'weight': requirement.weight
                    })
            
            # Calculate unlock score
            if total_weight > 0:
                analysis['unlock_score'] = met_weight / total_weight
            
            # Check additional unlock conditions
            conditions_met = self._check_unlock_conditions(user_id, feature_def)
            analysis['conditions_met'] = conditions_met
            
            # Determine if can unlock
            analysis['can_unlock'] = (
                analysis['dependencies_met'] and
                len(analysis['requirements_failed']) == 0 and
                conditions_met
            )
            
            # Generate recommendations
            analysis['recommendations'] = self._generate_unlock_recommendations(user_id, feature_def, analysis)
            
            return analysis['can_unlock'], analysis
            
        except Exception as e:
            logger.error(f"Error checking tiered feature unlock for user {user_id}, feature {feature_name}: {str(e)}")
            return False, {'error': str(e)}
    
    def _check_requirement(self, user_id: int, requirement: UnlockRequirement) -> bool:
        """Check if a specific requirement is met"""
        try:
            if requirement.condition == UnlockCondition.STEP_COMPLETION:
                progress = self.onboarding_manager.get_onboarding_progress(user_id)
                if not progress:
                    return False
                return requirement.value in progress.completed_steps
            
            elif requirement.condition == UnlockCondition.ACTIVITY_COUNT:
                activity_count = self._get_user_activity_count(user_id)
                return self._compare_values(activity_count, requirement.value, requirement.operator)
            
            elif requirement.condition == UnlockCondition.DAYS_ACTIVE:
                days_active = self._get_user_days_active(user_id)
                return self._compare_values(days_active, requirement.value, requirement.operator)
            
            elif requirement.condition == UnlockCondition.USAGE_FREQUENCY:
                usage_freq = self._get_usage_frequency(user_id)
                return self._compare_values(usage_freq, requirement.value, requirement.operator)
            
            elif requirement.condition == UnlockCondition.PERFORMANCE_THRESHOLD:
                perf_score = self._get_performance_score(user_id)
                return self._compare_values(perf_score, requirement.value, requirement.operator)
            
            elif requirement.condition == UnlockCondition.ENGAGEMENT_LEVEL:
                engagement = self._get_engagement_level(user_id)
                return self._compare_values(engagement, requirement.value, requirement.operator)
            
            elif requirement.condition == UnlockCondition.SOCIAL_INTERACTION:
                social_score = self._get_social_score(user_id)
                return self._compare_values(social_score, requirement.value, requirement.operator)
            
            elif requirement.condition == UnlockCondition.TIME_BASED:
                return self._check_time_based_requirement(user_id, requirement)
            
            elif requirement.condition == UnlockCondition.CUSTOM_RULE:
                return self._check_custom_rule(user_id, requirement)
            
            return False
            
        except Exception as e:
            logger.error(f"Error checking requirement for user {user_id}: {str(e)}")
            return False
    
    def _check_unlock_conditions(self, user_id: int, feature_def: TieredFeatureDefinition) -> bool:
        """Check additional unlock conditions"""
        try:
            conditions = feature_def.unlock_conditions
            
            # Check max users per tier
            if 'max_users_per_tier' in conditions:
                max_users = conditions['max_users_per_tier']
                current_users = self._get_users_in_tier(feature_def.tier)
                if current_users >= max_users:
                    return False
            
            # Check engagement threshold
            if 'engagement_threshold' in conditions:
                engagement = self._get_engagement_level(user_id)
                if engagement < conditions['engagement_threshold']:
                    return False
            
            # Check data quality threshold
            if 'data_quality_threshold' in conditions:
                data_quality = self._get_data_quality_score(user_id)
                if data_quality < conditions['data_quality_threshold']:
                    return False
            
            # Check consistency threshold
            if 'consistency_threshold' in conditions:
                consistency = self._get_consistency_score(user_id)
                if consistency < conditions['consistency_threshold']:
                    return False
            
            # Check goal setting readiness
            if 'goal_setting_readiness' in conditions:
                readiness = self._get_goal_setting_readiness(user_id)
                if readiness < conditions['goal_setting_readiness']:
                    return False
            
            # Check expert threshold
            if 'expert_threshold' in conditions:
                expert_score = self._get_expert_score(user_id)
                if expert_score < conditions['expert_threshold']:
                    return False
            
            # Check premium eligibility
            if 'premium_eligibility' in conditions:
                if not self._check_premium_eligibility(user_id):
                    return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error checking unlock conditions for user {user_id}: {str(e)}")
            return False
    
    def unlock_tiered_feature(self, user_id: int, feature_name: str) -> Tuple[bool, Dict[str, Any]]:
        """
        Unlock a tiered feature for a user with comprehensive validation
        
        Args:
            user_id: User ID
            feature_name: Name of feature to unlock
            
        Returns:
            Tuple of (success, result_details)
        """
        try:
            # Check if can unlock
            can_unlock, analysis = self.check_tiered_feature_unlock(user_id, feature_name)
            
            if not can_unlock:
                return False, {
                    'success': False,
                    'reason': 'Requirements not met',
                    'analysis': analysis
                }
            
            # Use onboarding manager to unlock
            success = self.onboarding_manager.unlock_feature(user_id, feature_name)
            
            if success:
                # Log tiered unlock event
                self._log_tiered_unlock_event(user_id, feature_name, analysis)
                
                # Update performance metrics
                self._update_performance_metrics(user_id, feature_name)
                
                return True, {
                    'success': True,
                    'feature_name': feature_name,
                    'tier': analysis['tier'],
                    'unlock_score': analysis['unlock_score'],
                    'timestamp': datetime.now().isoformat()
                }
            else:
                return False, {
                    'success': False,
                    'reason': 'Failed to unlock feature',
                    'analysis': analysis
                }
                
        except Exception as e:
            logger.error(f"Error unlocking tiered feature {feature_name} for user {user_id}: {str(e)}")
            return False, {'error': str(e)}
    
    def get_tiered_feature_progress(self, user_id: int) -> Dict[str, Any]:
        """
        Get comprehensive progress information for tiered features
        
        Args:
            user_id: User ID
            
        Returns:
            Dictionary with progress information
        """
        try:
            progress = {
                'user_id': user_id,
                'current_tier': self._get_current_tier(user_id),
                'features_by_tier': {},
                'unlock_progress': {},
                'recommendations': [],
                'next_milestones': []
            }
            
            # Group features by tier
            for feature_name, feature_def in self.feature_definitions.items():
                tier = feature_def.tier.value
                if tier not in progress['features_by_tier']:
                    progress['features_by_tier'][tier] = []
                
                can_unlock, analysis = self.check_tiered_feature_unlock(user_id, feature_name)
                feature_info = {
                    'name': feature_name,
                    'description': feature_def.description,
                    'can_unlock': can_unlock,
                    'unlock_score': analysis.get('unlock_score', 0.0),
                    'requirements_met': len(analysis.get('requirements_met', [])),
                    'total_requirements': len(feature_def.requirements),
                    'analysis': analysis
                }
                
                progress['features_by_tier'][tier].append(feature_info)
                
                # Track unlock progress
                if not can_unlock:
                    progress['unlock_progress'][feature_name] = analysis
            
            # Generate recommendations
            progress['recommendations'] = self._generate_user_recommendations(user_id)
            
            # Get next milestones
            progress['next_milestones'] = self._get_next_milestones(user_id)
            
            return progress
            
        except Exception as e:
            logger.error(f"Error getting tiered feature progress for user {user_id}: {str(e)}")
            return {'error': str(e)}
    
    # Helper methods for requirement checking
    def _compare_values(self, actual: Any, expected: Any, operator: str) -> bool:
        """Compare values using specified operator"""
        try:
            if operator == '>=':
                return actual >= expected
            elif operator == '>':
                return actual > expected
            elif operator == '<=':
                return actual <= expected
            elif operator == '<':
                return actual < expected
            elif operator == '==':
                return actual == expected
            elif operator == '!=':
                return actual != expected
            else:
                return False
        except Exception:
            return False
    
    def _get_user_activity_count(self, user_id: int) -> int:
        """Get user's activity count"""
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                # PostgreSQL syntax
                    cursor.execute("SELECT COUNT(*) FROM activities WHERE user_id = %s", (user_id,))
                else:
                    cursor.execute("SELECT COUNT(*) FROM activities WHERE user_id = %s", (user_id,))
                return cursor.fetchone()[0]
        except Exception as e:
            logger.error(f"Error getting activity count for user {user_id}: {str(e)}")
            return 0
    
    def _get_user_days_active(self, user_id: int) -> int:
        """Get number of days user has been active"""
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                # PostgreSQL syntax
                    cursor.execute("""
                        SELECT COUNT(DISTINCT date) 
                        FROM activities 
                        WHERE user_id = %s
                    """, (user_id,))
                else:
                    cursor.execute("""
                        SELECT COUNT(DISTINCT date) 
                        FROM activities 
                        WHERE user_id = %s
                    """, (user_id,))
                return cursor.fetchone()[0]
        except Exception as e:
            logger.error(f"Error getting days active for user {user_id}: {str(e)}")
            return 0
    
    def _get_usage_frequency(self, user_id: int) -> float:
        """Calculate user's usage frequency (0.0 to 1.0)"""
        try:
            # This is a simplified calculation - in practice, you'd track actual usage
            days_active = self._get_user_days_active(user_id)
            if days_active == 0:
                return 0.0
            
            # Assume user has been registered for at least 1 day
            with get_db_connection() as conn:
                cursor = conn.cursor()
                # PostgreSQL syntax
                    cursor.execute("""
                        SELECT created_at FROM user_settings WHERE user_id = %s
                    """, (user_id,))
                else:
                    cursor.execute("""
                        SELECT created_at FROM user_settings WHERE user_id = %s
                    """, (user_id,))
                
                result = cursor.fetchone()
                if not result:
                    return 0.0
                
                created_at = result[0]
                if isinstance(created_at, str):
                    created_at = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                
                days_registered = (datetime.now() - created_at).days
                if days_registered == 0:
                    return 1.0
                
                return min(days_active / days_registered, 1.0)
                
        except Exception as e:
            logger.error(f"Error calculating usage frequency for user {user_id}: {str(e)}")
            return 0.0
    
    def _get_performance_score(self, user_id: int) -> float:
        """Calculate user's performance score (0.0 to 1.0)"""
        try:
            # Simplified performance calculation
            # In practice, this would consider various metrics
            activity_count = self._get_user_activity_count(user_id)
            days_active = self._get_user_days_active(user_id)
            
            if activity_count == 0 or days_active == 0:
                return 0.0
            
            # Basic performance score based on activity consistency
            consistency = min(activity_count / (days_active * 2), 1.0)  # Assume 2 activities per day is excellent
            
            return consistency
            
        except Exception as e:
            logger.error(f"Error calculating performance score for user {user_id}: {str(e)}")
            return 0.0
    
    def _get_engagement_level(self, user_id: int) -> float:
        """Calculate user's engagement level (0.0 to 1.0)"""
        try:
            # Simplified engagement calculation
            usage_freq = self._get_usage_frequency(user_id)
            activity_count = self._get_user_activity_count(user_id)
            
            # Basic engagement score
            if activity_count == 0:
                return 0.0
            
            engagement = (usage_freq * 0.6) + (min(activity_count / 10, 1.0) * 0.4)
            return min(engagement, 1.0)
            
        except Exception as e:
            logger.error(f"Error calculating engagement level for user {user_id}: {str(e)}")
            return 0.0
    
    def _get_social_score(self, user_id: int) -> int:
        """Calculate user's social interaction score"""
        try:
            # Simplified social score - in practice, this would track actual social interactions
            # For now, return a basic score based on activity count
            activity_count = self._get_user_activity_count(user_id)
            if activity_count >= 5:
                return 1
            return 0
            
        except Exception as e:
            logger.error(f"Error calculating social score for user {user_id}: {str(e)}")
            return 0
    
    def _get_current_tier(self, user_id: int) -> str:
        """Get user's current tier"""
        try:
            unlocked_features = self.onboarding_manager._get_unlocked_features(user_id)
            
            # Determine highest tier based on unlocked features
            tiers = [FeatureTier.BASIC, FeatureTier.INTERMEDIATE, FeatureTier.ADVANCED, FeatureTier.EXPERT]
            current_tier = FeatureTier.BASIC
            
            for feature_name in unlocked_features:
                feature_def = self.feature_definitions.get(feature_name)
                if feature_def and feature_def.tier.value > current_tier.value:
                    current_tier = feature_def.tier
            
            return current_tier.value
            
        except Exception as e:
            logger.error(f"Error getting current tier for user {user_id}: {str(e)}")
            return FeatureTier.BASIC.value
    
    def _get_users_in_tier(self, tier: FeatureTier) -> int:
        """Get number of users in a specific tier"""
        try:
            # Simplified implementation - in practice, this would query the database
            # For now, return a reasonable estimate
            return 10  # Placeholder
            
        except Exception as e:
            logger.error(f"Error getting users in tier {tier}: {str(e)}")
            return 0
    
    def _check_time_based_requirement(self, user_id: int, requirement: UnlockRequirement) -> bool:
        """Check time-based requirements"""
        # Placeholder implementation
        return True
    
    def _check_custom_rule(self, user_id: int, requirement: UnlockRequirement) -> bool:
        """Check custom unlock rules"""
        # Placeholder implementation
        return True
    
    def _get_data_quality_score(self, user_id: int) -> float:
        """Calculate data quality score"""
        # Placeholder implementation
        return 0.8
    
    def _get_consistency_score(self, user_id: int) -> float:
        """Calculate consistency score"""
        # Placeholder implementation
        return 0.7
    
    def _get_goal_setting_readiness(self, user_id: int) -> float:
        """Calculate goal setting readiness"""
        # Placeholder implementation
        return 0.8
    
    def _get_expert_score(self, user_id: int) -> float:
        """Calculate expert score"""
        # Placeholder implementation
        return 0.9
    
    def _check_premium_eligibility(self, user_id: int) -> bool:
        """Check premium eligibility"""
        # Placeholder implementation
        return True
    
    def _generate_unlock_recommendations(self, user_id: int, feature_def: TieredFeatureDefinition, analysis: Dict[str, Any]) -> List[str]:
        """Generate recommendations for unlocking a feature"""
        recommendations = []
        
        for failed_req in analysis.get('requirements_failed', []):
            if failed_req['condition'] == 'activity_count':
                recommendations.append(f"Complete {failed_req['value']} more activities to unlock {feature_def.feature_name}")
            elif failed_req['condition'] == 'days_active':
                recommendations.append(f"Stay active for {failed_req['value']} more days to unlock {feature_def.feature_name}")
            elif failed_req['condition'] == 'usage_frequency':
                recommendations.append(f"Increase your app usage to unlock {feature_def.feature_name}")
            elif failed_req['condition'] == 'engagement_level':
                recommendations.append(f"Engage more with the app to unlock {feature_def.feature_name}")
        
        return recommendations
    
    def _generate_user_recommendations(self, user_id: int) -> List[str]:
        """Generate general recommendations for user progress"""
        recommendations = []
        
        activity_count = self._get_user_activity_count(user_id)
        days_active = self._get_user_days_active(user_id)
        
        if activity_count < 3:
            recommendations.append("Complete more activities to unlock advanced features")
        
        if days_active < 3:
            recommendations.append("Stay active for more days to unlock intermediate features")
        
        usage_freq = self._get_usage_frequency(user_id)
        if usage_freq < 0.5:
            recommendations.append("Use the app more regularly to unlock features faster")
        
        return recommendations
    
    def _get_next_milestones(self, user_id: int) -> List[Dict[str, Any]]:
        """Get next milestones for the user"""
        milestones = []
        
        activity_count = self._get_user_activity_count(user_id)
        days_active = self._get_user_days_active(user_id)
        
        if activity_count < 3:
            milestones.append({
                'type': 'activity_count',
                'current': activity_count,
                'target': 3,
                'description': 'Complete 3 activities'
            })
        
        if days_active < 5:
            milestones.append({
                'type': 'days_active',
                'current': days_active,
                'target': 5,
                'description': 'Stay active for 5 days'
            })
        
        return milestones
    
    def _log_tiered_unlock_event(self, user_id: int, feature_name: str, analysis: Dict[str, Any]):
        """Log tiered unlock event"""
        try:
            event_data = {
                'user_id': user_id,
                'feature_name': feature_name,
                'tier': analysis.get('tier'),
                'unlock_score': analysis.get('unlock_score'),
                'timestamp': datetime.now().isoformat(),
                'requirements_met': len(analysis.get('requirements_met', [])),
                'total_requirements': len(analysis.get('requirements_met', [])) + len(analysis.get('requirements_failed', []))
            }
            
            # Log to database or external system
            logger.info(f"Tiered feature unlocked: {event_data}")
            
        except Exception as e:
            logger.error(f"Error logging tiered unlock event: {str(e)}")
    
    def _update_performance_metrics(self, user_id: int, feature_name: str):
        """Update performance metrics after feature unlock"""
        try:
            # Update usage frequency
            usage_freq = self._get_usage_frequency(user_id)
            self.performance_metrics['usage_frequency'][user_id] = usage_freq
            
            # Update engagement level
            engagement = self._get_engagement_level(user_id)
            self.performance_metrics['engagement_level'][user_id] = engagement
            
            # Update performance score
            perf_score = self._get_performance_score(user_id)
            self.performance_metrics['performance_scores'][user_id] = perf_score
            
        except Exception as e:
            logger.error(f"Error updating performance metrics: {str(e)}")


# Convenience functions for easy integration
tiered_feature_manager = TieredFeatureUnlockManager()


def check_tiered_feature_unlock(user_id: int, feature_name: str) -> Tuple[bool, Dict[str, Any]]:
    """Check if a user can unlock a tiered feature"""
    return tiered_feature_manager.check_tiered_feature_unlock(user_id, feature_name)


def unlock_tiered_feature(user_id: int, feature_name: str) -> Tuple[bool, Dict[str, Any]]:
    """Unlock a tiered feature for a user"""
    return tiered_feature_manager.unlock_tiered_feature(user_id, feature_name)


def get_tiered_feature_progress(user_id: int) -> Dict[str, Any]:
    """Get comprehensive progress information for tiered features"""
    return tiered_feature_manager.get_tiered_feature_progress(user_id)


def get_available_tiered_features(user_id: int) -> List[Dict[str, Any]]:
    """Get list of available tiered features for a user"""
    try:
        available_features = []
        
        for feature_name, feature_def in tiered_feature_manager.feature_definitions.items():
            can_unlock, analysis = check_tiered_feature_unlock(user_id, feature_name)
            
            feature_info = {
                'name': feature_name,
                'tier': feature_def.tier.value,
                'description': feature_def.description,
                'can_unlock': can_unlock,
                'unlock_score': analysis.get('unlock_score', 0.0),
                'requirements_met': len(analysis.get('requirements_met', [])),
                'total_requirements': len(feature_def.requirements),
                'tutorial_available': feature_def.tutorial_available,
                'priority': feature_def.priority
            }
            
            available_features.append(feature_info)
        
        # Sort by priority and tier
        available_features.sort(key=lambda x: (x['priority'], x['tier']))
        
        return available_features
        
    except Exception as e:
        logger.error(f"Error getting available tiered features for user {user_id}: {str(e)}")
        return []


if __name__ == "__main__":
    print("=" * 50)
    print("Tiered Feature Unlock Manager")
    print("=" * 50)
    print("Module loaded successfully!")
    print(f"Features defined: {len(tiered_feature_manager.feature_definitions)}")
    print(f"Tiers available: {[tier.value for tier in FeatureTier]}")
    print("=" * 50)


