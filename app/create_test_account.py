#!/usr/bin/env python3
"""
Test Account Creation Script for Beta Testing

This script creates a fabricated test account with comprehensive data for beta testing
the OAuth transition and onboarding system. It includes:
- User account with realistic data
- Complete onboarding progress
- Goals setup data
- Analytics tracking data
- Legal compliance records
- Test activities and training data

Usage:
    python create_test_account.py [--email test@example.com] [--password testpass123]
"""

import os
import sys
import logging
import argparse
from datetime import datetime, timedelta, date
from typing import Dict, List, Optional
import random

# Add the app directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from db_utils import execute_query, get_db_connection
from user_account_manager import UserAccountManager
from onboarding_analytics import OnboardingAnalytics
from legal_compliance import get_legal_compliance_tracker
from legal_document_versioning import get_current_legal_versions
from werkzeug.security import generate_password_hash

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class TestAccountCreator:
    """Creates comprehensive test accounts for beta testing"""
    
    def __init__(self):
        self.account_manager = UserAccountManager()
        self.analytics = OnboardingAnalytics()
        self.compliance_tracker = get_legal_compliance_tracker()
        self.legal_versions = get_current_legal_versions()
        
    def create_test_account(self, email: str = "test@trainingmonkey.com", 
                           password: str = "TestPass123!") -> Dict:
        """
        Create a comprehensive test account for beta testing
        
        Args:
            email: Test account email
            password: Test account password
            
        Returns:
            Dictionary with account creation results
        """
        try:
            logger.info(f"Creating test account: {email}")
            
            # Check if test account already exists
            existing_user = self._get_user_by_email(email)
            if existing_user:
                logger.warning(f"Test account already exists: {email}")
                return {
                    'success': False,
                    'error': 'Test account already exists',
                    'user_id': existing_user['id']
                }
            
            # Create the user account
            success, user_id, error = self.account_manager.create_new_user_account(
                email, password, {
                    'terms': True,
                    'privacy': True,
                    'disclaimer': True
                }
            )
            
            if not success:
                return {
                    'success': False,
                    'error': error,
                    'user_id': None
                }
            
            logger.info(f"Created test account with ID: {user_id}")
            
            # Set up comprehensive test data
            self._setup_test_onboarding_progress(user_id)
            self._setup_test_goals(user_id)
            self._setup_test_analytics(user_id)
            self._setup_test_activities(user_id)
            self._setup_test_training_data(user_id)
            
            # Activate the account
            self.account_manager.activate_user_account(user_id)
            
            logger.info(f"Test account setup complete: {email} (ID: {user_id})")
            
            return {
                'success': True,
                'user_id': user_id,
                'email': email,
                'password': password,
                'message': 'Test account created successfully'
            }
            
        except Exception as e:
            logger.error(f"Error creating test account: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'user_id': None
            }
    
    def _get_user_by_email(self, email: str) -> Optional[Dict]:
        """Get user by email address"""
        try:
            query = "SELECT * FROM user_settings WHERE email = ?"
            result = execute_query(query, (email,), fetch=True)
            return result[0] if result else None
        except Exception as e:
            logger.error(f"Error getting user by email: {str(e)}")
            return None
    
    def _setup_test_onboarding_progress(self, user_id: int):
        """Set up realistic onboarding progress for test account"""
        try:
            # Set onboarding to 80% complete (step 5 of 6)
            onboarding_data = {
                'onboarding_step': 'goals_setup',
                'onboarding_progress': 80,
                'onboarding_started_date': datetime.now() - timedelta(days=2),
                'onboarding_completed_date': None,
                'last_onboarding_activity': datetime.now() - timedelta(hours=3)
            }
            
            query = """
                UPDATE user_settings 
                SET onboarding_step = ?, onboarding_progress = ?, 
                    onboarding_started_date = ?, onboarding_completed_date = ?,
                    last_onboarding_activity = ?, updated_at = ?
                WHERE id = ?
            """
            
            execute_query(query, (
                onboarding_data['onboarding_step'],
                onboarding_data['onboarding_progress'],
                onboarding_data['onboarding_started_date'],
                onboarding_data['onboarding_completed_date'],
                onboarding_data['last_onboarding_activity'],
                datetime.now(),
                user_id
            ))
            
            logger.info(f"Set up onboarding progress for user {user_id}")
            
        except Exception as e:
            logger.error(f"Error setting up onboarding progress: {str(e)}")
    
    def _setup_test_goals(self, user_id: int):
        """Set up realistic goals for test account"""
        try:
            goals_data = {
                'goals_configured': True,
                'goal_type': 'distance',
                'goal_target': '100',
                'goal_timeframe': 'monthly',
                'goals_setup_date': datetime.now() - timedelta(days=1)
            }
            
            query = """
                UPDATE user_settings 
                SET goals_configured = ?, goal_type = ?, goal_target = ?,
                    goal_timeframe = ?, goals_setup_date = ?, updated_at = ?
                WHERE id = ?
            """
            
            execute_query(query, (
                goals_data['goals_configured'],
                goals_data['goal_type'],
                goals_data['goal_target'],
                goals_data['goal_timeframe'],
                goals_data['goals_setup_date'],
                datetime.now(),
                user_id
            ))
            
            logger.info(f"Set up goals for user {user_id}")
            
        except Exception as e:
            logger.error(f"Error setting up goals: {str(e)}")
    
    def _setup_test_analytics(self, user_id: int):
        """Set up realistic analytics data for test account"""
        try:
            # Create analytics events for the onboarding journey
            events = [
                {
                    'event_name': 'onboarding_started',
                    'event_data': {'step': 'welcome', 'timestamp': datetime.now() - timedelta(days=2)}
                },
                {
                    'event_name': 'strava_connected',
                    'event_data': {'provider': 'strava', 'timestamp': datetime.now() - timedelta(days=2, hours=1)}
                },
                {
                    'event_name': 'first_activity_synced',
                    'event_data': {'activity_type': 'run', 'distance': 5.2, 'timestamp': datetime.now() - timedelta(days=1)}
                },
                {
                    'event_name': 'dashboard_intro_completed',
                    'event_data': {'step': 'dashboard_intro', 'timestamp': datetime.now() - timedelta(days=1, hours=2)}
                },
                {
                    'event_name': 'goals_setup_started',
                    'event_data': {'step': 'goals_setup', 'timestamp': datetime.now() - timedelta(hours=4)}
                },
                {
                    'event_name': 'page_view',
                    'event_data': {'page': 'goals_setup', 'timestamp': datetime.now() - timedelta(hours=3)}
                }
            ]
            
            for event in events:
                self.analytics.track_event(
                    user_id, 
                    event['event_name'], 
                    event['event_data']
                )
            
            logger.info(f"Set up analytics data for user {user_id}")
            
        except Exception as e:
            logger.error(f"Error setting up analytics: {str(e)}")
    
    def _setup_test_activities(self, user_id: int):
        """Set up realistic activity data for test account"""
        try:
            # Create some test activities
            activities = [
                {
                    'activity_type': 'run',
                    'distance': 5.2,
                    'duration': 1800,  # 30 minutes
                    'date': date.today() - timedelta(days=1),
                    'strava_id': f"test_activity_{random.randint(1000000, 9999999)}"
                },
                {
                    'activity_type': 'run',
                    'distance': 3.1,
                    'duration': 1200,  # 20 minutes
                    'date': date.today() - timedelta(days=3),
                    'strava_id': f"test_activity_{random.randint(1000000, 9999999)}"
                },
                {
                    'activity_type': 'bike',
                    'distance': 25.0,
                    'duration': 3600,  # 1 hour
                    'date': date.today() - timedelta(days=5),
                    'strava_id': f"test_activity_{random.randint(1000000, 9999999)}"
                }
            ]
            
            for activity in activities:
                query = """
                    INSERT INTO activities (
                        user_id, activity_type, distance, duration, date, strava_id, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """
                
                execute_query(query, (
                    user_id,
                    activity['activity_type'],
                    activity['distance'],
                    activity['duration'],
                    activity['date'],
                    activity['strava_id'],
                    datetime.now()
                ))
            
            logger.info(f"Set up test activities for user {user_id}")
            
        except Exception as e:
            logger.error(f"Error setting up activities: {str(e)}")
    
    def _setup_test_training_data(self, user_id: int):
        """Set up realistic training load data for test account"""
        try:
            # Create training load records for the past week
            for i in range(7):
                training_date = date.today() - timedelta(days=i)
                training_load = random.randint(20, 80)
                
                query = """
                    INSERT INTO training_load (
                        user_id, date, training_load, created_at
                    ) VALUES (?, ?, ?, ?)
                    ON CONFLICT (user_id, date) DO UPDATE SET
                        training_load = EXCLUDED.training_load,
                        updated_at = ?
                """
                
                execute_query(query, (
                    user_id,
                    training_date,
                    training_load,
                    datetime.now(),
                    datetime.now()
                ))
            
            logger.info(f"Set up training load data for user {user_id}")
            
        except Exception as e:
            logger.error(f"Error setting up training data: {str(e)}")
    
    def list_test_accounts(self) -> List[Dict]:
        """List all test accounts in the system"""
        try:
            query = """
                SELECT id, email, account_status, onboarding_step, onboarding_progress,
                       goals_configured, created_at, updated_at
                FROM user_settings 
                WHERE email LIKE '%test%' OR email LIKE '%@trainingmonkey.com'
                ORDER BY created_at DESC
            """
            
            result = execute_query(query, fetch=True)
            return result if result else []
            
        except Exception as e:
            logger.error(f"Error listing test accounts: {str(e)}")
            return []
    
    def delete_test_account(self, user_id: int) -> bool:
        """Delete a test account and all associated data"""
        try:
            # Delete associated data first
            tables_to_clean = [
                'onboarding_analytics',
                'activities', 
                'training_load',
                'legal_compliance'
            ]
            
            for table in tables_to_clean:
                try:
                    query = f"DELETE FROM {table} WHERE user_id = ?"
                    execute_query(query, (user_id,))
                except Exception as e:
                    logger.warning(f"Could not clean {table} for user {user_id}: {str(e)}")
            
            # Delete the user account
            query = "DELETE FROM user_settings WHERE id = ?"
            execute_query(query, (user_id,))
            
            logger.info(f"Deleted test account: {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting test account: {str(e)}")
            return False

def main():
    """Main function for command line usage"""
    parser = argparse.ArgumentParser(description='Create test account for beta testing')
    parser.add_argument('--email', default='test@trainingmonkey.com', 
                       help='Test account email (default: test@trainingmonkey.com)')
    parser.add_argument('--password', default='TestPass123!', 
                       help='Test account password (default: TestPass123!)')
    parser.add_argument('--list', action='store_true', 
                       help='List existing test accounts')
    parser.add_argument('--delete', type=int, 
                       help='Delete test account by user ID')
    
    args = parser.parse_args()
    
    creator = TestAccountCreator()
    
    if args.list:
        print("\n=== Existing Test Accounts ===")
        accounts = creator.list_test_accounts()
        if accounts:
            for account in accounts:
                print(f"ID: {account['id']}, Email: {account['email']}, Status: {account['account_status']}")
        else:
            print("No test accounts found")
        return
    
    if args.delete:
        if creator.delete_test_account(args.delete):
            print(f"Successfully deleted test account {args.delete}")
        else:
            print(f"Failed to delete test account {args.delete}")
        return
    
    # Create test account
    print(f"\n=== Creating Test Account ===")
    print(f"Email: {args.email}")
    print(f"Password: {args.password}")
    
    result = creator.create_test_account(args.email, args.password)
    
    if result['success']:
        print(f"\n✅ Test account created successfully!")
        print(f"User ID: {result['user_id']}")
        print(f"Email: {result['email']}")
        print(f"Password: {result['password']}")
        print(f"\nAccount includes:")
        print("- Complete onboarding progress (80% complete)")
        print("- Goals setup (100km monthly distance goal)")
        print("- Analytics tracking data")
        print("- Test activities (runs and bike rides)")
        print("- Training load data for past week")
        print("- Legal compliance records")
        print(f"\nUse these credentials to test the OAuth transition and onboarding system.")
    else:
        print(f"\n❌ Failed to create test account: {result['error']}")

if __name__ == '__main__':
    main()

