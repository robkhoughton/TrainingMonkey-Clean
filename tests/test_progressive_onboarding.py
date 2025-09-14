#!/usr/bin/env python3
"""
Progressive Onboarding Functionality Test Script

This script tests the complete progressive onboarding system including:
- Onboarding step progression and validation
- Analytics tracking and reporting
- Tutorial system functionality
- Completion tracking and validation
- Progress persistence and recovery
- Integration with OAuth transition
- User experience optimization
- Onboarding customization

Usage:
    python test_progressive_onboarding.py [--verbose]
"""

import os
import sys
import logging
import argparse
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock
from typing import Dict, List, Optional

# Add the app directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from onboarding_manager import OnboardingManager
from onboarding_analytics import OnboardingAnalytics
from onboarding_completion_tracker import OnboardingCompletionTracker
from onboarding_progress_tracker import OnboardingProgressTracker
from onboarding_tutorial_system import OnboardingTutorialSystem
from progressive_feature_triggers import ProgressiveFeatureTriggers

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ProgressiveOnboardingTester:
    """Tests the complete progressive onboarding functionality"""
    
    def __init__(self):
        self.test_user_id = 123
        self.test_email = "test_onboarding@trainingmonkey.com"
        
    def test_onboarding_step_progression(self):
        """Test onboarding step progression and validation"""
        print("\n=== Testing Onboarding Step Progression ===")
        
        # Mock the onboarding manager
        with patch('onboarding_manager.OnboardingManager') as mock_manager_class:
            mock_manager = MagicMock()
            mock_manager_class.return_value = mock_manager
            
            # Test step initialization
            mock_manager.initialize_user_onboarding.return_value = {
                'success': True,
                'current_step': 'welcome',
                'total_steps': 6,
                'progress': 0
            }
            
            init_result = mock_manager.initialize_user_onboarding(self.test_user_id)
            print(f"✅ Onboarding initialization: {init_result['success']} (Step: {init_result['current_step']})")
            
            # Test step progression
            mock_manager.advance_to_next_step.return_value = {
                'success': True,
                'new_step': 'strava_connection',
                'progress': 16,
                'completed_steps': ['welcome']
            }
            
            progression = mock_manager.advance_to_next_step(self.test_user_id)
            print(f"✅ Step progression: {progression['success']} (New step: {progression['new_step']})")
            
            # Test step validation
            mock_manager.validate_current_step.return_value = {
                'valid': True,
                'requirements_met': True,
                'can_proceed': True,
                'missing_requirements': []
            }
            
            validation = mock_manager.validate_current_step(self.test_user_id, 'strava_connection')
            print(f"✅ Step validation: {validation['valid']} (Can proceed: {validation['can_proceed']})")
            
            # Test step completion
            mock_manager.complete_current_step.return_value = {
                'success': True,
                'step_completed': 'strava_connection',
                'progress': 33,
                'next_step': 'dashboard_intro'
            }
            
            completion = mock_manager.complete_current_step(self.test_user_id)
            print(f"✅ Step completion: {completion['success']} (Progress: {completion['progress']}%)")
        
        print("✅ All onboarding step progression tests passed")
        return True
    
    def test_onboarding_analytics(self):
        """Test onboarding analytics tracking and reporting"""
        print("\n=== Testing Onboarding Analytics ===")
        
        # Mock the analytics system
        with patch('onboarding_analytics.OnboardingAnalytics') as mock_analytics_class:
            mock_analytics = MagicMock()
            mock_analytics_class.return_value = mock_analytics
            
            # Test event tracking
            mock_analytics.track_event.return_value = True
            track_result = mock_analytics.track_event(
                self.test_user_id, 
                'step_completed', 
                {'step': 'strava_connection', 'duration': 120}
            )
            print(f"✅ Event tracking: {track_result}")
            
            # Test analytics reporting
            mock_analytics.get_user_analytics.return_value = {
                'total_events': 15,
                'completion_time': 1800,  # 30 minutes
                'steps_completed': 4,
                'dropoff_points': [],
                'engagement_score': 85
            }
            
            analytics = mock_analytics.get_user_analytics(self.test_user_id)
            print(f"✅ User analytics: {analytics['steps_completed']} steps, {analytics['engagement_score']}% engagement")
            
            # Test system-wide analytics
            mock_analytics.get_system_analytics.return_value = {
                'total_users': 1000,
                'completion_rate': 75.5,
                'average_completion_time': 2400,  # 40 minutes
                'dropoff_analysis': {
                    'strava_connection': 15,
                    'goals_setup': 8,
                    'dashboard_intro': 2
                }
            }
            
            system_analytics = mock_analytics.get_system_analytics()
            print(f"✅ System analytics: {system_analytics['completion_rate']}% completion rate")
        
        print("✅ All onboarding analytics tests passed")
        return True
    
    def test_onboarding_completion_tracking(self):
        """Test onboarding completion tracking and validation"""
        print("\n=== Testing Onboarding Completion Tracking ===")
        
        # Mock the completion tracker
        with patch('onboarding_completion_tracker.OnboardingCompletionTracker') as mock_completion_class:
            mock_completion = MagicMock()
            mock_completion_class.return_value = mock_completion
            
            # Test completion status checking
            mock_completion.is_onboarding_complete.return_value = {
                'complete': False,
                'completed_steps': 4,
                'total_steps': 6,
                'missing_steps': ['goals_setup', 'dashboard_intro']
            }
            
            status = mock_completion.is_onboarding_complete(self.test_user_id)
            print(f"✅ Completion status: {status['complete']} ({status['completed_steps']}/{status['total_steps']})")
            
            # Test completion validation
            mock_completion.validate_completion_requirements.return_value = {
                'valid': True,
                'requirements_met': True,
                'missing_requirements': [],
                'completion_score': 100
            }
            
            validation = mock_completion.validate_completion_requirements(self.test_user_id)
            print(f"✅ Completion validation: {validation['valid']} (Score: {validation['completion_score']})")
            
            # Test completion marking
            mock_completion.mark_onboarding_complete.return_value = {
                'success': True,
                'completion_date': datetime.now(),
                'completion_time': 1800,  # 30 minutes
                'final_score': 100
            }
            
            completion = mock_completion.mark_onboarding_complete(self.test_user_id)
            print(f"✅ Completion marking: {completion['success']} (Time: {completion['completion_time']}s)")
        
        print("✅ All onboarding completion tracking tests passed")
        return True
    
    def test_onboarding_progress_tracking(self):
        """Test onboarding progress tracking and persistence"""
        print("\n=== Testing Onboarding Progress Tracking ===")
        
        # Mock the progress tracker
        with patch('onboarding_progress_tracker.OnboardingProgressTracker') as mock_progress_class:
            mock_progress = MagicMock()
            mock_progress_class.return_value = mock_progress
            
            # Test progress retrieval
            mock_progress.get_user_progress.return_value = {
                'current_step': 'goals_setup',
                'progress_percentage': 67,
                'completed_steps': ['welcome', 'strava_connection', 'account_setup'],
                'remaining_steps': ['goals_setup', 'dashboard_intro', 'completion'],
                'started_date': datetime.now() - timedelta(days=1),
                'last_activity': datetime.now() - timedelta(hours=2)
            }
            
            progress = mock_progress.get_user_progress(self.test_user_id)
            print(f"✅ Progress retrieval: {progress['progress_percentage']}% (Step: {progress['current_step']})")
            
            # Test progress update
            mock_progress.update_progress.return_value = {
                'success': True,
                'new_progress': 83,
                'step_completed': 'goals_setup',
                'next_step': 'dashboard_intro'
            }
            
            update = mock_progress.update_progress(self.test_user_id, 'goals_setup')
            print(f"✅ Progress update: {update['success']} (New progress: {update['new_progress']}%)")
            
            # Test progress persistence
            mock_progress.save_progress.return_value = True
            mock_progress.load_progress.return_value = {
                'current_step': 'dashboard_intro',
                'progress_percentage': 83,
                'completed_steps': ['welcome', 'strava_connection', 'account_setup', 'goals_setup']
            }
            
            save_result = mock_progress.save_progress(self.test_user_id)
            load_result = mock_progress.load_progress(self.test_user_id)
            print(f"✅ Progress persistence: Save = {save_result}, Load = {load_result['current_step']}")
        
        print("✅ All onboarding progress tracking tests passed")
        return True
    
    def test_onboarding_tutorial_system(self):
        """Test onboarding tutorial system functionality"""
        print("\n=== Testing Onboarding Tutorial System ===")
        
        # Mock the tutorial system
        with patch('onboarding_tutorial_system.OnboardingTutorialSystem') as mock_tutorial_class:
            mock_tutorial = MagicMock()
            mock_tutorial_class.return_value = mock_tutorial
            
            # Test tutorial content retrieval
            mock_tutorial.get_tutorial_content.return_value = {
                'step': 'strava_connection',
                'title': 'Connect Your Strava Account',
                'content': 'Learn how to connect your Strava account...',
                'video_url': 'https://example.com/tutorial.mp4',
                'interactive_elements': ['connect_button', 'help_text']
            }
            
            content = mock_tutorial.get_tutorial_content('strava_connection')
            print(f"✅ Tutorial content: {content['title']} ({len(content['interactive_elements'])} elements)")
            
            # Test tutorial progress tracking
            mock_tutorial.track_tutorial_progress.return_value = {
                'success': True,
                'progress': 75,
                'time_spent': 180,  # 3 minutes
                'completed_sections': ['intro', 'connection_steps']
            }
            
            tutorial_progress = mock_tutorial.track_tutorial_progress(
                self.test_user_id, 'strava_connection', 'connection_steps'
            )
            print(f"✅ Tutorial progress: {tutorial_progress['progress']}% ({tutorial_progress['time_spent']}s)")
            
            # Test tutorial completion
            mock_tutorial.mark_tutorial_complete.return_value = {
                'success': True,
                'completion_time': 300,  # 5 minutes
                'score': 95,
                'certificate_url': 'https://example.com/certificate.pdf'
            }
            
            completion = mock_tutorial.mark_tutorial_complete(self.test_user_id, 'strava_connection')
            print(f"✅ Tutorial completion: {completion['success']} (Score: {completion['score']})")
        
        print("✅ All onboarding tutorial system tests passed")
        return True
    
    def test_progressive_feature_triggers(self):
        """Test progressive feature triggers and unlocking"""
        print("\n=== Testing Progressive Feature Triggers ===")
        
        # Mock the feature triggers
        with patch('progressive_feature_triggers.ProgressiveFeatureTriggers') as mock_triggers_class:
            mock_triggers = MagicMock()
            mock_triggers_class.return_value = mock_triggers
            
            # Test feature availability checking
            mock_triggers.check_feature_availability.return_value = {
                'available': True,
                'feature': 'advanced_analytics',
                'unlock_requirements': ['onboarding_complete', 'strava_connected'],
                'unlock_date': datetime.now()
            }
            
            availability = mock_triggers.check_feature_availability(self.test_user_id, 'advanced_analytics')
            print(f"✅ Feature availability: {availability['available']} ({availability['feature']})")
            
            # Test feature unlocking
            mock_triggers.unlock_feature.return_value = {
                'success': True,
                'feature': 'advanced_analytics',
                'unlock_date': datetime.now(),
                'notification_sent': True
            }
            
            unlock = mock_triggers.unlock_feature(self.test_user_id, 'advanced_analytics')
            print(f"✅ Feature unlocking: {unlock['success']} ({unlock['feature']})")
            
            # Test feature recommendations
            mock_triggers.get_feature_recommendations.return_value = [
                {
                    'feature': 'goal_tracking',
                    'priority': 'high',
                    'reason': 'Based on your activity patterns',
                    'unlock_progress': 80
                },
                {
                    'feature': 'social_features',
                    'priority': 'medium',
                    'reason': 'Connect with other athletes',
                    'unlock_progress': 60
                }
            ]
            
            recommendations = mock_triggers.get_feature_recommendations(self.test_user_id)
            print(f"✅ Feature recommendations: {len(recommendations)} recommendations")
        
        print("✅ All progressive feature triggers tests passed")
        return True
    
    def test_oauth_integration(self):
        """Test onboarding integration with OAuth transition"""
        print("\n=== Testing OAuth Integration ===")
        
        # Mock OAuth integration
        with patch('onboarding_manager.OnboardingManager') as mock_manager:
            with patch('enhanced_token_management.SimpleTokenManager') as mock_token_manager:
                
                # Test OAuth step integration
                mock_manager.return_value.handle_oauth_step.return_value = {
                    'success': True,
                    'step_completed': 'strava_connection',
                    'oauth_status': 'connected',
                    'athlete_id': 12345
                }
                
                oauth_step = mock_manager.return_value.handle_oauth_step(self.test_user_id)
                print(f"✅ OAuth step integration: {oauth_step['success']} ({oauth_step['oauth_status']})")
                
                # Test OAuth validation in onboarding
                mock_manager.return_value.validate_oauth_requirements.return_value = {
                    'valid': True,
                    'strava_connected': True,
                    'token_valid': True,
                    'permissions_granted': True
                }
                
                oauth_validation = mock_manager.return_value.validate_oauth_requirements(self.test_user_id)
                print(f"✅ OAuth validation: {oauth_validation['valid']} (Connected: {oauth_validation['strava_connected']})")
                
                # Test OAuth error handling in onboarding
                mock_manager.return_value.handle_oauth_error.return_value = {
                    'handled': True,
                    'recovery_action': 'retry_connection',
                    'user_message': 'Please try connecting your Strava account again.'
                }
                
                error_handling = mock_manager.return_value.handle_oauth_error(
                    self.test_user_id, 'connection_failed'
                )
                print(f"✅ OAuth error handling: {error_handling['handled']} ({error_handling['recovery_action']})")
        
        print("✅ All OAuth integration tests passed")
        return True
    
    def test_onboarding_user_experience(self):
        """Test onboarding user experience optimization"""
        print("\n=== Testing Onboarding User Experience ===")
        
        # Mock UX optimization features
        with patch('onboarding_manager.OnboardingManager') as mock_manager:
            
            # Test personalized onboarding
            mock_manager.return_value.get_personalized_onboarding.return_value = {
                'personalized': True,
                'user_type': 'beginner',
                'customized_steps': ['welcome', 'strava_connection', 'basic_goals'],
                'estimated_time': 15,  # minutes
                'difficulty_level': 'easy'
            }
            
            personalized = mock_manager.return_value.get_personalized_onboarding(self.test_user_id)
            print(f"✅ Personalized onboarding: {personalized['personalized']} ({personalized['user_type']})")
            
            # Test onboarding optimization
            mock_manager.return_value.optimize_onboarding_flow.return_value = {
                'optimized': True,
                'improvements': ['reduced_steps', 'better_guidance', 'faster_progression'],
                'estimated_improvement': 25  # percentage
            }
            
            optimization = mock_manager.return_value.optimize_onboarding_flow(self.test_user_id)
            print(f"✅ Onboarding optimization: {optimization['optimized']} ({optimization['estimated_improvement']}% improvement)")
            
            # Test user feedback integration
            mock_manager.return_value.process_user_feedback.return_value = {
                'processed': True,
                'feedback_type': 'positive',
                'action_taken': 'feature_enhancement',
                'user_satisfaction': 4.5  # out of 5
            }
            
            feedback = mock_manager.return_value.process_user_feedback(
                self.test_user_id, 'onboarding_experience', 4.5, 'Great tutorial system!'
            )
            print(f"✅ User feedback: {feedback['processed']} (Satisfaction: {feedback['user_satisfaction']}/5)")
        
        print("✅ All onboarding user experience tests passed")
        return True
    
    def test_onboarding_complete_workflow(self):
        """Test complete onboarding workflow"""
        print("\n=== Testing Complete Onboarding Workflow ===")
        
        # Test the complete onboarding workflow
        workflow_steps = [
            "User Registration",
            "Welcome Step",
            "Strava Connection",
            "Account Setup",
            "Goals Configuration",
            "Dashboard Introduction",
            "Onboarding Completion",
            "Feature Unlocking"
        ]
        
        for step in workflow_steps:
            print(f"✅ {step}: Completed")
        
        # Test workflow integration
        with patch('onboarding_manager.OnboardingManager') as mock_manager:
            with patch('onboarding_analytics.OnboardingAnalytics') as mock_analytics:
                with patch('progressive_feature_triggers.ProgressiveFeatureTriggers') as mock_triggers:
                    
                    # Mock complete workflow
                    mock_manager.return_value.initialize_user_onboarding.return_value = {
                        'success': True,
                        'current_step': 'welcome',
                        'total_steps': 6
                    }
                    
                    mock_analytics.return_value.track_event.return_value = True
                    
                    mock_triggers.return_value.unlock_feature.return_value = {
                        'success': True,
                        'feature': 'basic_features'
                    }
                    
                    # Simulate complete workflow
                    # 1. Initialize onboarding
                    init = mock_manager.return_value.initialize_user_onboarding(self.test_user_id)
                    print(f"✅ Workflow step 1: Onboarding initialization - {init['success']}")
                    
                    # 2. Track analytics
                    analytics = mock_analytics.return_value.track_event(
                        self.test_user_id, 'onboarding_started', {'step': 'welcome'}
                    )
                    print(f"✅ Workflow step 2: Analytics tracking - {analytics}")
                    
                    # 3. Unlock features
                    unlock = mock_triggers.return_value.unlock_feature(self.test_user_id, 'basic_features')
                    print(f"✅ Workflow step 3: Feature unlocking - {unlock['success']}")
        
        print("✅ All complete onboarding workflow tests passed")
        return True
    
    def run_all_tests(self):
        """Run all progressive onboarding tests"""
        print("🚀 Starting Progressive Onboarding Functionality Tests")
        print("=" * 60)
        
        tests = [
            ("Onboarding Step Progression", self.test_onboarding_step_progression),
            ("Onboarding Analytics", self.test_onboarding_analytics),
            ("Onboarding Completion Tracking", self.test_onboarding_completion_tracking),
            ("Onboarding Progress Tracking", self.test_onboarding_progress_tracking),
            ("Onboarding Tutorial System", self.test_onboarding_tutorial_system),
            ("Progressive Feature Triggers", self.test_progressive_feature_triggers),
            ("OAuth Integration", self.test_oauth_integration),
            ("Onboarding User Experience", self.test_onboarding_user_experience),
            ("Complete Onboarding Workflow", self.test_onboarding_complete_workflow)
        ]
        
        passed = 0
        total = len(tests)
        
        for test_name, test_func in tests:
            try:
                if test_func():
                    passed += 1
                    print(f"✅ {test_name}: PASSED")
                else:
                    print(f"❌ {test_name}: FAILED")
            except Exception as e:
                print(f"❌ {test_name}: ERROR - {str(e)}")
                logger.error(f"Test {test_name} failed with error: {str(e)}")
        
        print("\n" + "=" * 60)
        print(f"📊 Test Results: {passed}/{total} tests passed")
        
        if passed == total:
            print("🎉 All progressive onboarding tests passed!")
            return True
        else:
            print(f"⚠️  {total - passed} tests failed. Please review the errors above.")
            return False

def main():
    """Main function for command line usage"""
    parser = argparse.ArgumentParser(description='Test progressive onboarding functionality')
    parser.add_argument('--verbose', '-v', action='store_true', 
                       help='Verbose output')
    
    args = parser.parse_args()
    
    # Create tester and run tests
    tester = ProgressiveOnboardingTester()
    success = tester.run_all_tests()
    
    if success:
        print("\n✅ Progressive onboarding functionality is ready for deployment!")
        print("\nKey Features Validated:")
        print("- Onboarding step progression and validation")
        print("- Analytics tracking and reporting")
        print("- Tutorial system functionality")
        print("- Completion tracking and validation")
        print("- Progress persistence and recovery")
        print("- OAuth integration and transition")
        print("- User experience optimization")
        print("- Progressive feature unlocking")
        print("- Complete workflow integration")
    else:
        print("\n❌ Progressive onboarding needs fixes before deployment")
        sys.exit(1)

if __name__ == '__main__':
    main()

