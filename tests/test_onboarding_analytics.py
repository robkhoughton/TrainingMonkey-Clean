"""
Test Suite for Onboarding Analytics Module

This module tests the onboarding analytics functionality including:
- Analytics engine initialization and configuration
- Funnel analytics generation and calculation
- Engagement and completion metrics calculation
- Tutorial and trigger effectiveness analysis
- Cohort analytics and A/B test results
- Performance benchmarking and predictive insights
- Time series data generation and recommendations
- Report export functionality in multiple formats
- Database integration and data persistence
"""

import unittest
from unittest.mock import patch, MagicMock, Mock
from datetime import datetime, timedelta
import json

from onboarding_analytics import (
    OnboardingAnalyticsEngine,
    AnalyticsMetric,
    AnalyticsPeriod,
    CohortType,
    FunnelStep,
    CohortData,
    ABTestResult,
    PerformanceBenchmark,
    PredictiveInsight,
    OnboardingAnalytics,
    generate_comprehensive_analytics,
    export_analytics_report,
    analytics_engine
)
from onboarding_manager import OnboardingStep, FeatureTier


class TestOnboardingAnalyticsEngine(unittest.TestCase):
    """Test cases for OnboardingAnalyticsEngine class"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.analytics_engine = OnboardingAnalyticsEngine()
        self.date_range = (datetime.now() - timedelta(days=30), datetime.now())
    
    def test_initialization(self):
        """Test analytics engine initialization"""
        self.assertIsNotNone(self.analytics_engine.onboarding_manager)
        self.assertIsNotNone(self.analytics_engine.progress_tracker)
        self.assertIsNotNone(self.analytics_engine.tutorial_system)
        self.assertIsNotNone(self.analytics_engine.tiered_feature_manager)
        self.assertIsNotNone(self.analytics_engine.feature_triggers)
        self.assertIsNotNone(self.analytics_engine.dashboard_manager)
        self.assertIsNotNone(self.analytics_engine.completion_tracker)
    
    def test_generate_comprehensive_analytics(self):
        """Test comprehensive analytics generation"""
        analytics = self.analytics_engine.generate_comprehensive_analytics(self.date_range)
        
        self.assertIsInstance(analytics, OnboardingAnalytics)
        self.assertIsInstance(analytics.funnel_steps, list)
        self.assertIsInstance(analytics.overall_conversion_rate, float)
        self.assertIsInstance(analytics.total_funnel_dropoff, int)
        self.assertIsInstance(analytics.average_engagement_score, float)
        self.assertIsInstance(analytics.active_users_count, int)
        self.assertIsInstance(analytics.session_duration_minutes, float)
        self.assertIsInstance(analytics.feature_usage_distribution, dict)
        self.assertIsInstance(analytics.completion_rate, float)
        self.assertIsInstance(analytics.average_completion_time_minutes, float)
        self.assertIsInstance(analytics.completion_time_distribution, dict)
        self.assertIsInstance(analytics.dropout_points, list)
        self.assertIsInstance(analytics.tutorial_completion_rates, dict)
        self.assertIsInstance(analytics.tutorial_effectiveness_scores, dict)
        self.assertIsInstance(analytics.tutorial_dropout_points, list)
        self.assertIsInstance(analytics.trigger_success_rates, dict)
        self.assertIsInstance(analytics.trigger_effectiveness_scores, dict)
        self.assertIsInstance(analytics.feature_unlock_distribution, dict)
        self.assertIsInstance(analytics.cohorts, list)
        self.assertIsInstance(analytics.ab_tests, list)
        self.assertIsInstance(analytics.benchmarks, list)
        self.assertIsInstance(analytics.insights, list)
        self.assertIsInstance(analytics.time_series_data, dict)
        self.assertIsInstance(analytics.recommendations, list)
        self.assertIsInstance(analytics.generated_at, datetime)
    
    def test_generate_funnel_analytics(self):
        """Test funnel analytics generation"""
        funnel_steps = self.analytics_engine._generate_funnel_analytics(self.date_range)
        
        self.assertIsInstance(funnel_steps, list)
        self.assertGreater(len(funnel_steps), 0)
        
        for step in funnel_steps:
            self.assertIsInstance(step, FunnelStep)
            self.assertIsInstance(step.step_id, str)
            self.assertIsInstance(step.name, str)
            self.assertIsInstance(step.description, str)
            self.assertIsInstance(step.step_type, OnboardingStep)
            self.assertIsInstance(step.order, int)
            self.assertIsInstance(step.conversion_rate, float)
            self.assertIsInstance(step.dropoff_count, int)
            self.assertIsInstance(step.completion_count, int)
            self.assertIsInstance(step.average_time_minutes, float)
            self.assertIsInstance(step.optimization_score, float)
    
    def test_calculate_step_conversion_rate(self):
        """Test step conversion rate calculation"""
        conversion_rate = self.analytics_engine._calculate_step_conversion_rate(
            OnboardingStep.WELCOME, self.date_range
        )
        
        self.assertIsInstance(conversion_rate, float)
        self.assertGreaterEqual(conversion_rate, 0.0)
        self.assertLessEqual(conversion_rate, 1.0)
    
    def test_calculate_step_dropoff_count(self):
        """Test step dropoff count calculation"""
        dropoff_count = self.analytics_engine._calculate_step_dropoff_count(
            OnboardingStep.STRAVA_CONNECTED, self.date_range
        )
        
        self.assertIsInstance(dropoff_count, int)
        self.assertGreaterEqual(dropoff_count, 0)
    
    def test_calculate_step_completion_count(self):
        """Test step completion count calculation"""
        completion_count = self.analytics_engine._calculate_step_completion_count(
            OnboardingStep.FIRST_ACTIVITY, self.date_range
        )
        
        self.assertIsInstance(completion_count, int)
        self.assertGreaterEqual(completion_count, 0)
    
    def test_calculate_step_average_time(self):
        """Test step average time calculation"""
        average_time = self.analytics_engine._calculate_step_average_time(
            OnboardingStep.GOALS_SETUP, self.date_range
        )
        
        self.assertIsInstance(average_time, float)
        self.assertGreaterEqual(average_time, 0.0)
    
    def test_calculate_step_optimization_score(self):
        """Test step optimization score calculation"""
        optimization_score = self.analytics_engine._calculate_step_optimization_score(
            OnboardingStep.DASHBOARD_INTRO, 0.75, 8.0
        )
        
        self.assertIsInstance(optimization_score, float)
        self.assertGreaterEqual(optimization_score, 0.0)
        self.assertLessEqual(optimization_score, 1.0)
    
    def test_calculate_overall_conversion_rate(self):
        """Test overall conversion rate calculation"""
        funnel_steps = [
            FunnelStep(
                step_id='welcome',
                name='Welcome',
                description='Welcome step',
                step_type=OnboardingStep.WELCOME,
                order=1,
                conversion_rate=0.95
            ),
            FunnelStep(
                step_id='strava',
                name='Strava',
                description='Strava step',
                step_type=OnboardingStep.STRAVA_CONNECTED,
                order=2,
                conversion_rate=0.85
            )
        ]
        
        overall_rate = self.analytics_engine._calculate_overall_conversion_rate(funnel_steps)
        
        self.assertIsInstance(overall_rate, float)
        self.assertGreaterEqual(overall_rate, 0.0)
        self.assertLessEqual(overall_rate, 1.0)
        self.assertEqual(overall_rate, 0.95 * 0.85)
    
    def test_calculate_total_funnel_dropoff(self):
        """Test total funnel dropoff calculation"""
        funnel_steps = [
            FunnelStep(
                step_id='welcome',
                name='Welcome',
                description='Welcome step',
                step_type=OnboardingStep.WELCOME,
                order=1,
                dropoff_count=50
            ),
            FunnelStep(
                step_id='strava',
                name='Strava',
                description='Strava step',
                step_type=OnboardingStep.STRAVA_CONNECTED,
                order=2,
                dropoff_count=150
            )
        ]
        
        total_dropoff = self.analytics_engine._calculate_total_funnel_dropoff(funnel_steps)
        
        self.assertIsInstance(total_dropoff, int)
        self.assertEqual(total_dropoff, 200)
    
    def test_calculate_average_engagement_score(self):
        """Test average engagement score calculation"""
        engagement_score = self.analytics_engine._calculate_average_engagement_score(self.date_range)
        
        self.assertIsInstance(engagement_score, float)
        self.assertGreaterEqual(engagement_score, 0.0)
        self.assertLessEqual(engagement_score, 1.0)
    
    def test_get_active_users_count(self):
        """Test active users count retrieval"""
        active_users = self.analytics_engine._get_active_users_count(self.date_range)
        
        self.assertIsInstance(active_users, int)
        self.assertGreaterEqual(active_users, 0)
    
    def test_calculate_average_session_duration(self):
        """Test average session duration calculation"""
        session_duration = self.analytics_engine._calculate_average_session_duration(self.date_range)
        
        self.assertIsInstance(session_duration, float)
        self.assertGreaterEqual(session_duration, 0.0)
    
    def test_get_feature_usage_distribution(self):
        """Test feature usage distribution retrieval"""
        usage_distribution = self.analytics_engine._get_feature_usage_distribution(self.date_range)
        
        self.assertIsInstance(usage_distribution, dict)
        self.assertGreater(len(usage_distribution), 0)
        
        for feature, usage_rate in usage_distribution.items():
            self.assertIsInstance(feature, str)
            self.assertIsInstance(usage_rate, float)
            self.assertGreaterEqual(usage_rate, 0.0)
            self.assertLessEqual(usage_rate, 1.0)
    
    def test_calculate_completion_rate(self):
        """Test completion rate calculation"""
        completion_rate = self.analytics_engine._calculate_completion_rate(self.date_range)
        
        self.assertIsInstance(completion_rate, float)
        self.assertGreaterEqual(completion_rate, 0.0)
        self.assertLessEqual(completion_rate, 1.0)
    
    def test_calculate_average_completion_time(self):
        """Test average completion time calculation"""
        completion_time = self.analytics_engine._calculate_average_completion_time(self.date_range)
        
        self.assertIsInstance(completion_time, float)
        self.assertGreaterEqual(completion_time, 0.0)
    
    def test_get_completion_time_distribution(self):
        """Test completion time distribution retrieval"""
        time_distribution = self.analytics_engine._get_completion_time_distribution(self.date_range)
        
        self.assertIsInstance(time_distribution, dict)
        self.assertGreater(len(time_distribution), 0)
        
        for time_range, count in time_distribution.items():
            self.assertIsInstance(time_range, str)
            self.assertIsInstance(count, int)
            self.assertGreaterEqual(count, 0)
    
    def test_identify_dropout_points(self):
        """Test dropout points identification"""
        dropout_points = self.analytics_engine._identify_dropout_points(self.date_range)
        
        self.assertIsInstance(dropout_points, list)
        
        for dropout_point in dropout_points:
            self.assertIsInstance(dropout_point, dict)
            self.assertIn('step', dropout_point)
            self.assertIn('dropout_rate', dropout_point)
            self.assertIn('users_affected', dropout_point)
            self.assertIn('common_reasons', dropout_point)
            self.assertIn('recommendations', dropout_point)
    
    def test_get_tutorial_completion_rates(self):
        """Test tutorial completion rates retrieval"""
        completion_rates = self.analytics_engine._get_tutorial_completion_rates(self.date_range)
        
        self.assertIsInstance(completion_rates, dict)
        self.assertGreater(len(completion_rates), 0)
        
        for tutorial, rate in completion_rates.items():
            self.assertIsInstance(tutorial, str)
            self.assertIsInstance(rate, float)
            self.assertGreaterEqual(rate, 0.0)
            self.assertLessEqual(rate, 1.0)
    
    def test_calculate_tutorial_effectiveness(self):
        """Test tutorial effectiveness calculation"""
        effectiveness_scores = self.analytics_engine._calculate_tutorial_effectiveness(self.date_range)
        
        self.assertIsInstance(effectiveness_scores, dict)
        self.assertGreater(len(effectiveness_scores), 0)
        
        for tutorial, score in effectiveness_scores.items():
            self.assertIsInstance(tutorial, str)
            self.assertIsInstance(score, float)
            self.assertGreaterEqual(score, 0.0)
            self.assertLessEqual(score, 1.0)
    
    def test_identify_tutorial_dropout_points(self):
        """Test tutorial dropout points identification"""
        dropout_points = self.analytics_engine._identify_tutorial_dropout_points(self.date_range)
        
        self.assertIsInstance(dropout_points, list)
        
        for dropout_point in dropout_points:
            self.assertIsInstance(dropout_point, dict)
            self.assertIn('tutorial', dropout_point)
            self.assertIn('dropout_step', dropout_point)
            self.assertIn('dropout_rate', dropout_point)
            self.assertIn('common_reasons', dropout_point)
            self.assertIn('recommendations', dropout_point)
    
    def test_get_trigger_success_rates(self):
        """Test trigger success rates retrieval"""
        success_rates = self.analytics_engine._get_trigger_success_rates(self.date_range)
        
        self.assertIsInstance(success_rates, dict)
        self.assertGreater(len(success_rates), 0)
        
        for trigger, rate in success_rates.items():
            self.assertIsInstance(trigger, str)
            self.assertIsInstance(rate, float)
            self.assertGreaterEqual(rate, 0.0)
            self.assertLessEqual(rate, 1.0)
    
    def test_calculate_trigger_effectiveness(self):
        """Test trigger effectiveness calculation"""
        effectiveness_scores = self.analytics_engine._calculate_trigger_effectiveness(self.date_range)
        
        self.assertIsInstance(effectiveness_scores, dict)
        self.assertGreater(len(effectiveness_scores), 0)
        
        for trigger, score in effectiveness_scores.items():
            self.assertIsInstance(trigger, str)
            self.assertIsInstance(score, float)
            self.assertGreaterEqual(score, 0.0)
            self.assertLessEqual(score, 1.0)
    
    def test_get_feature_unlock_distribution(self):
        """Test feature unlock distribution retrieval"""
        unlock_distribution = self.analytics_engine._get_feature_unlock_distribution(self.date_range)
        
        self.assertIsInstance(unlock_distribution, dict)
        self.assertGreater(len(unlock_distribution), 0)
        
        for feature, count in unlock_distribution.items():
            self.assertIsInstance(feature, str)
            self.assertIsInstance(count, int)
            self.assertGreaterEqual(count, 0)
    
    def test_generate_cohort_analytics(self):
        """Test cohort analytics generation"""
        cohorts = self.analytics_engine._generate_cohort_analytics(self.date_range)
        
        self.assertIsInstance(cohorts, list)
        self.assertGreater(len(cohorts), 0)
        
        for cohort in cohorts:
            self.assertIsInstance(cohort, CohortData)
            self.assertIsInstance(cohort.cohort_id, str)
            self.assertIsInstance(cohort.cohort_type, CohortType)
            self.assertIsInstance(cohort.cohort_date, datetime)
            self.assertIsInstance(cohort.cohort_size, int)
            self.assertIsInstance(cohort.retention_data, dict)
            self.assertIsInstance(cohort.engagement_metrics, dict)
            self.assertIsInstance(cohort.conversion_rates, dict)
    
    def test_get_ab_test_results(self):
        """Test A/B test results retrieval"""
        ab_tests = self.analytics_engine._get_ab_test_results(self.date_range)
        
        self.assertIsInstance(ab_tests, list)
        self.assertGreater(len(ab_tests), 0)
        
        for ab_test in ab_tests:
            self.assertIsInstance(ab_test, ABTestResult)
            self.assertIsInstance(ab_test.test_id, str)
            self.assertIsInstance(ab_test.test_name, str)
            self.assertIsInstance(ab_test.variant_a, str)
            self.assertIsInstance(ab_test.variant_b, str)
            self.assertIsInstance(ab_test.metric, AnalyticsMetric)
            self.assertIsInstance(ab_test.variant_a_results, dict)
            self.assertIsInstance(ab_test.variant_b_results, dict)
            self.assertIsInstance(ab_test.statistical_significance, float)
            self.assertIsInstance(ab_test.confidence_level, float)
            self.assertIsInstance(ab_test.sample_size, int)
    
    def test_generate_performance_benchmarks(self):
        """Test performance benchmarks generation"""
        analytics = OnboardingAnalytics()
        analytics.completion_rate = 0.75
        analytics.average_engagement_score = 0.75
        analytics.average_completion_time_minutes = 45.0
        
        benchmarks = self.analytics_engine._generate_performance_benchmarks(analytics)
        
        self.assertIsInstance(benchmarks, list)
        self.assertGreater(len(benchmarks), 0)
        
        for benchmark in benchmarks:
            self.assertIsInstance(benchmark, PerformanceBenchmark)
            self.assertIsInstance(benchmark.benchmark_id, str)
            self.assertIsInstance(benchmark.metric, AnalyticsMetric)
            self.assertIsInstance(benchmark.current_value, float)
            self.assertIsInstance(benchmark.benchmark_value, float)
            self.assertIsInstance(benchmark.industry_average, float)
            self.assertIsInstance(benchmark.percentile_rank, float)
            self.assertIsInstance(benchmark.trend_direction, str)
            self.assertIsInstance(benchmark.improvement_potential, float)
    
    def test_generate_predictive_insights(self):
        """Test predictive insights generation"""
        analytics = OnboardingAnalytics()
        analytics.completion_rate = 0.75
        analytics.average_engagement_score = 0.75
        analytics.average_completion_time_minutes = 45.0
        
        insights = self.analytics_engine._generate_predictive_insights(analytics)
        
        self.assertIsInstance(insights, list)
        self.assertGreater(len(insights), 0)
        
        for insight in insights:
            self.assertIsInstance(insight, PredictiveInsight)
            self.assertIsInstance(insight.insight_id, str)
            self.assertIsInstance(insight.insight_type, str)
            self.assertIsInstance(insight.description, str)
            self.assertIsInstance(insight.confidence_score, float)
            self.assertIsInstance(insight.predicted_value, float)
            self.assertIsInstance(insight.timeframe, str)
            self.assertIsInstance(insight.factors, list)
            self.assertIsInstance(insight.recommendations, list)
            self.assertIsInstance(insight.impact_score, float)
    
    def test_generate_time_series_data(self):
        """Test time series data generation"""
        time_series_data = self.analytics_engine._generate_time_series_data(self.date_range)
        
        self.assertIsInstance(time_series_data, dict)
        self.assertGreater(len(time_series_data), 0)
        
        for metric, data_points in time_series_data.items():
            self.assertIsInstance(metric, str)
            self.assertIsInstance(data_points, list)
            self.assertGreater(len(data_points), 0)
            
            for data_point in data_points:
                self.assertIsInstance(data_point, dict)
                self.assertIn('date', data_point)
    
    def test_generate_recommendations(self):
        """Test recommendations generation"""
        analytics = OnboardingAnalytics()
        analytics.overall_conversion_rate = 0.65  # Below target
        analytics.average_completion_time_minutes = 70.0  # High
        analytics.average_engagement_score = 0.65  # Below target
        analytics.dropout_points = [
            {
                'step': 'strava_connection',
                'dropout_rate': 0.15,
                'recommendations': ['Simplify OAuth flow']
            }
        ]
        analytics.tutorial_effectiveness_scores = {
            'advanced_features_tutorial': 0.65  # Below threshold
        }
        analytics.trigger_effectiveness_scores = {
            'tutorial_completion_trigger': 0.65  # Below threshold
        }
        
        recommendations = self.analytics_engine._generate_recommendations(analytics)
        
        self.assertIsInstance(recommendations, list)
        self.assertGreater(len(recommendations), 0)
        
        for recommendation in recommendations:
            self.assertIsInstance(recommendation, str)
            self.assertGreater(len(recommendation), 0)
    
    def test_export_analytics_report_json(self):
        """Test analytics report export in JSON format"""
        analytics = OnboardingAnalytics()
        analytics.overall_conversion_rate = 0.75
        analytics.completion_rate = 0.75
        
        report = self.analytics_engine.export_analytics_report(analytics, 'json')
        
        self.assertIsInstance(report, str)
        self.assertGreater(len(report), 0)
        
        # Verify it's valid JSON
        parsed_report = json.loads(report)
        self.assertIsInstance(parsed_report, dict)
    
    def test_export_analytics_report_csv(self):
        """Test analytics report export in CSV format"""
        analytics = OnboardingAnalytics()
        analytics.funnel_steps = [
            FunnelStep(
                step_id='welcome',
                name='Welcome',
                description='Welcome step',
                step_type=OnboardingStep.WELCOME,
                order=1,
                conversion_rate=0.95,
                dropoff_count=50,
                completion_count=950,
                average_time_minutes=2.0,
                optimization_score=0.85
            )
        ]
        analytics.overall_conversion_rate = 0.75
        analytics.completion_rate = 0.75
        analytics.average_engagement_score = 0.75
        analytics.average_completion_time_minutes = 45.0
        
        report = self.analytics_engine.export_analytics_report(analytics, 'csv')
        
        self.assertIsInstance(report, str)
        self.assertGreater(len(report), 0)
        self.assertIn('Funnel Step,Conversion Rate', report)
        self.assertIn('Welcome,0.95', report)
    
    def test_export_analytics_report_html(self):
        """Test analytics report export in HTML format"""
        analytics = OnboardingAnalytics()
        analytics.overall_conversion_rate = 0.75
        analytics.completion_rate = 0.75
        analytics.average_engagement_score = 0.75
        analytics.average_completion_time_minutes = 45.0
        analytics.funnel_steps = [
            FunnelStep(
                step_id='welcome',
                name='Welcome',
                description='Welcome step',
                step_type=OnboardingStep.WELCOME,
                order=1,
                conversion_rate=0.95
            )
        ]
        analytics.recommendations = ['Test recommendation']
        
        report = self.analytics_engine.export_analytics_report(analytics, 'html')
        
        self.assertIsInstance(report, str)
        self.assertGreater(len(report), 0)
        self.assertIn('<html>', report)
        self.assertIn('<title>Onboarding Analytics Report</title>', report)
        self.assertIn('Overall Conversion Rate', report)
    
    def test_export_analytics_report_invalid_format(self):
        """Test analytics report export with invalid format"""
        analytics = OnboardingAnalytics()
        
        with self.assertRaises(ValueError):
            self.analytics_engine.export_analytics_report(analytics, 'invalid_format')


class TestConvenienceFunctions(unittest.TestCase):
    """Test cases for convenience functions"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.date_range = (datetime.now() - timedelta(days=30), datetime.now())
    
    @patch.object(analytics_engine, 'generate_comprehensive_analytics')
    def test_generate_comprehensive_analytics_function(self, mock_generate):
        """Test convenience function for generating comprehensive analytics"""
        mock_analytics = OnboardingAnalytics()
        mock_generate.return_value = mock_analytics
        
        analytics = generate_comprehensive_analytics(self.date_range)
        
        self.assertEqual(analytics, mock_analytics)
        mock_generate.assert_called_once_with(self.date_range)
    
    @patch.object(analytics_engine, 'export_analytics_report')
    def test_export_analytics_report_function(self, mock_export):
        """Test convenience function for exporting analytics report"""
        analytics = OnboardingAnalytics()
        mock_report = '{"test": "data"}'
        mock_export.return_value = mock_report
        
        report = export_analytics_report(analytics, 'json')
        
        self.assertEqual(report, mock_report)
        mock_export.assert_called_once_with(analytics, 'json')


class TestEnumsAndDataClasses(unittest.TestCase):
    """Test cases for enums and data classes"""
    
    def test_analytics_metric_enum(self):
        """Test AnalyticsMetric enum values"""
        self.assertEqual(AnalyticsMetric.FUNNEL_CONVERSION.value, 'funnel_conversion')
        self.assertEqual(AnalyticsMetric.ENGAGEMENT_RATE.value, 'engagement_rate')
        self.assertEqual(AnalyticsMetric.COMPLETION_RATE.value, 'completion_rate')
        self.assertEqual(AnalyticsMetric.DROPOUT_RATE.value, 'dropout_rate')
        self.assertEqual(AnalyticsMetric.TIME_TO_COMPLETE.value, 'time_to_complete')
        self.assertEqual(AnalyticsMetric.FEATURE_ADOPTION.value, 'feature_adoption')
        self.assertEqual(AnalyticsMetric.TUTORIAL_EFFECTIVENESS.value, 'tutorial_effectiveness')
        self.assertEqual(AnalyticsMetric.TRIGGER_EFFECTIVENESS.value, 'trigger_effectiveness')
        self.assertEqual(AnalyticsMetric.USER_SATISFACTION.value, 'user_satisfaction')
        self.assertEqual(AnalyticsMetric.RETENTION_RATE.value, 'retention_rate')
        self.assertEqual(AnalyticsMetric.REVENUE_IMPACT.value, 'revenue_impact')
        self.assertEqual(AnalyticsMetric.PERFORMANCE_SCORE.value, 'performance_score')
    
    def test_analytics_period_enum(self):
        """Test AnalyticsPeriod enum values"""
        self.assertEqual(AnalyticsPeriod.HOURLY.value, 'hourly')
        self.assertEqual(AnalyticsPeriod.DAILY.value, 'daily')
        self.assertEqual(AnalyticsPeriod.WEEKLY.value, 'weekly')
        self.assertEqual(AnalyticsPeriod.MONTHLY.value, 'monthly')
        self.assertEqual(AnalyticsPeriod.QUARTERLY.value, 'quarterly')
        self.assertEqual(AnalyticsPeriod.YEARLY.value, 'yearly')
    
    def test_cohort_type_enum(self):
        """Test CohortType enum values"""
        self.assertEqual(CohortType.SIGNUP_DATE.value, 'signup_date')
        self.assertEqual(CohortType.ONBOARDING_COMPLETION.value, 'onboarding_completion')
        self.assertEqual(CohortType.FEATURE_ADOPTION.value, 'feature_adoption')
        self.assertEqual(CohortType.ACTIVITY_LEVEL.value, 'activity_level')
        self.assertEqual(CohortType.GEOGRAPHIC.value, 'geographic')
        self.assertEqual(CohortType.DEVICE_TYPE.value, 'device_type')
        self.assertEqual(CohortType.REFERRAL_SOURCE.value, 'referral_source')
    
    def test_funnel_step_dataclass(self):
        """Test FunnelStep dataclass"""
        funnel_step = FunnelStep(
            step_id='welcome',
            name='Welcome',
            description='Welcome step description',
            step_type=OnboardingStep.WELCOME,
            order=1,
            conversion_rate=0.95,
            dropoff_count=50,
            completion_count=950,
            average_time_minutes=2.0,
            optimization_score=0.85
        )
        
        self.assertEqual(funnel_step.step_id, 'welcome')
        self.assertEqual(funnel_step.name, 'Welcome')
        self.assertEqual(funnel_step.description, 'Welcome step description')
        self.assertEqual(funnel_step.step_type, OnboardingStep.WELCOME)
        self.assertEqual(funnel_step.order, 1)
        self.assertEqual(funnel_step.conversion_rate, 0.95)
        self.assertEqual(funnel_step.dropoff_count, 50)
        self.assertEqual(funnel_step.completion_count, 950)
        self.assertEqual(funnel_step.average_time_minutes, 2.0)
        self.assertEqual(funnel_step.optimization_score, 0.85)
    
    def test_cohort_data_dataclass(self):
        """Test CohortData dataclass"""
        cohort_data = CohortData(
            cohort_id='test_cohort',
            cohort_type=CohortType.SIGNUP_DATE,
            cohort_date=datetime.now(),
            cohort_size=1000,
            retention_data={'day_1': 0.85, 'day_7': 0.70},
            engagement_metrics={'avg_session_duration': 25.0},
            conversion_rates={'onboarding_completion': 0.75},
            revenue_data={'total_revenue': 5000.0}
        )
        
        self.assertEqual(cohort_data.cohort_id, 'test_cohort')
        self.assertEqual(cohort_data.cohort_type, CohortType.SIGNUP_DATE)
        self.assertIsInstance(cohort_data.cohort_date, datetime)
        self.assertEqual(cohort_data.cohort_size, 1000)
        self.assertEqual(cohort_data.retention_data['day_1'], 0.85)
        self.assertEqual(cohort_data.engagement_metrics['avg_session_duration'], 25.0)
        self.assertEqual(cohort_data.conversion_rates['onboarding_completion'], 0.75)
        self.assertEqual(cohort_data.revenue_data['total_revenue'], 5000.0)
    
    def test_ab_test_result_dataclass(self):
        """Test ABTestResult dataclass"""
        ab_test = ABTestResult(
            test_id='test_ab',
            test_name='Test A/B Test',
            variant_a='Original',
            variant_b='New',
            metric=AnalyticsMetric.COMPLETION_RATE,
            variant_a_results={'conversion_rate': 0.70},
            variant_b_results={'conversion_rate': 0.80},
            statistical_significance=0.95,
            winner='variant_b',
            confidence_level=0.95,
            sample_size=2000
        )
        
        self.assertEqual(ab_test.test_id, 'test_ab')
        self.assertEqual(ab_test.test_name, 'Test A/B Test')
        self.assertEqual(ab_test.variant_a, 'Original')
        self.assertEqual(ab_test.variant_b, 'New')
        self.assertEqual(ab_test.metric, AnalyticsMetric.COMPLETION_RATE)
        self.assertEqual(ab_test.variant_a_results['conversion_rate'], 0.70)
        self.assertEqual(ab_test.variant_b_results['conversion_rate'], 0.80)
        self.assertEqual(ab_test.statistical_significance, 0.95)
        self.assertEqual(ab_test.winner, 'variant_b')
        self.assertEqual(ab_test.confidence_level, 0.95)
        self.assertEqual(ab_test.sample_size, 2000)
    
    def test_performance_benchmark_dataclass(self):
        """Test PerformanceBenchmark dataclass"""
        benchmark = PerformanceBenchmark(
            benchmark_id='test_benchmark',
            metric=AnalyticsMetric.COMPLETION_RATE,
            current_value=0.75,
            benchmark_value=0.80,
            industry_average=0.65,
            percentile_rank=0.85,
            trend_direction='improving',
            improvement_potential=0.05
        )
        
        self.assertEqual(benchmark.benchmark_id, 'test_benchmark')
        self.assertEqual(benchmark.metric, AnalyticsMetric.COMPLETION_RATE)
        self.assertEqual(benchmark.current_value, 0.75)
        self.assertEqual(benchmark.benchmark_value, 0.80)
        self.assertEqual(benchmark.industry_average, 0.65)
        self.assertEqual(benchmark.percentile_rank, 0.85)
        self.assertEqual(benchmark.trend_direction, 'improving')
        self.assertEqual(benchmark.improvement_potential, 0.05)
        self.assertIsInstance(benchmark.last_updated, datetime)
    
    def test_predictive_insight_dataclass(self):
        """Test PredictiveInsight dataclass"""
        insight = PredictiveInsight(
            insight_id='test_insight',
            insight_type='completion_rate',
            description='Test insight description',
            confidence_score=0.85,
            predicted_value=0.80,
            timeframe='30 days',
            factors=['Factor 1', 'Factor 2'],
            recommendations=['Recommendation 1', 'Recommendation 2'],
            impact_score=0.75
        )
        
        self.assertEqual(insight.insight_id, 'test_insight')
        self.assertEqual(insight.insight_type, 'completion_rate')
        self.assertEqual(insight.description, 'Test insight description')
        self.assertEqual(insight.confidence_score, 0.85)
        self.assertEqual(insight.predicted_value, 0.80)
        self.assertEqual(insight.timeframe, '30 days')
        self.assertEqual(insight.factors, ['Factor 1', 'Factor 2'])
        self.assertEqual(insight.recommendations, ['Recommendation 1', 'Recommendation 2'])
        self.assertEqual(insight.impact_score, 0.75)
    
    def test_onboarding_analytics_dataclass(self):
        """Test OnboardingAnalytics dataclass"""
        analytics = OnboardingAnalytics()
        
        self.assertIsInstance(analytics.funnel_steps, list)
        self.assertEqual(analytics.overall_conversion_rate, 0.0)
        self.assertEqual(analytics.total_funnel_dropoff, 0)
        self.assertEqual(analytics.average_engagement_score, 0.0)
        self.assertEqual(analytics.active_users_count, 0)
        self.assertEqual(analytics.session_duration_minutes, 0.0)
        self.assertIsInstance(analytics.feature_usage_distribution, dict)
        self.assertEqual(analytics.completion_rate, 0.0)
        self.assertEqual(analytics.average_completion_time_minutes, 0.0)
        self.assertIsInstance(analytics.completion_time_distribution, dict)
        self.assertIsInstance(analytics.dropout_points, list)
        self.assertIsInstance(analytics.tutorial_completion_rates, dict)
        self.assertIsInstance(analytics.tutorial_effectiveness_scores, dict)
        self.assertIsInstance(analytics.tutorial_dropout_points, list)
        self.assertIsInstance(analytics.trigger_success_rates, dict)
        self.assertIsInstance(analytics.trigger_effectiveness_scores, dict)
        self.assertIsInstance(analytics.feature_unlock_distribution, dict)
        self.assertIsInstance(analytics.cohorts, list)
        self.assertIsInstance(analytics.ab_tests, list)
        self.assertIsInstance(analytics.benchmarks, list)
        self.assertIsInstance(analytics.insights, list)
        self.assertIsInstance(analytics.time_series_data, dict)
        self.assertIsInstance(analytics.recommendations, list)
        self.assertIsInstance(analytics.generated_at, datetime)


if __name__ == '__main__':
    # Run the tests
    unittest.main(verbosity=2)


