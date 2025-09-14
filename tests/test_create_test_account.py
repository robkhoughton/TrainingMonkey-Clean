#!/usr/bin/env python3
"""
Test Suite for Test Account Creation Script

This module tests the TestAccountCreator class to ensure it properly creates
fabricated test accounts with all necessary data for beta testing.
"""

import os
import sys
import unittest
import tempfile
import shutil
from datetime import datetime, timedelta, date
from unittest.mock import patch, MagicMock

# Add the app directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from create_test_account import TestAccountCreator

class TestTestAccountCreator(unittest.TestCase):
    """Test cases for TestAccountCreator class"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.creator = TestAccountCreator()
        self.test_email = "test_beta@trainingmonkey.com"
        self.test_password = "TestBetaPass123!"
        
        # Mock the database connection and queries
        self.db_patcher = patch('create_test_account.execute_query')
        self.mock_execute_query = self.db_patcher.start()
        
        # Mock the user account manager
        self.account_manager_patcher = patch('create_test_account.UserAccountManager')
        self.mock_account_manager_class = self.account_manager_patcher.start()
        self.mock_account_manager = MagicMock()
        self.mock_account_manager_class.return_value = self.mock_account_manager
        
        # Mock the analytics module
        self.analytics_patcher = patch('create_test_account.OnboardingAnalytics')
        self.mock_analytics_class = self.analytics_patcher.start()
        self.mock_analytics = MagicMock()
        self.mock_analytics_class.return_value = self.mock_analytics
        
        # Mock the compliance tracker
        self.compliance_patcher = patch('create_test_account.get_legal_compliance_tracker')
        self.mock_compliance_tracker = self.compliance_patcher.start()
        
        # Mock the legal versions
        self.legal_versions_patcher = patch('create_test_account.get_current_legal_versions')
        self.mock_legal_versions = self.legal_versions_patcher.start()
        self.mock_legal_versions.return_value = {
            'terms': '2.0',
            'privacy': '2.0',
            'disclaimer': '2.0'
        }
    
    def tearDown(self):
        """Clean up test fixtures"""
        self.db_patcher.stop()
        self.account_manager_patcher.stop()
        self.analytics_patcher.stop()
        self.compliance_patcher.stop()
        self.legal_versions_patcher.stop()
    
    def test_create_test_account_success(self):
        """Test successful test account creation"""
        # Mock existing user check - no existing user
        self.mock_execute_query.return_value = []
        
        # Mock user account creation success
        self.mock_account_manager.create_new_user_account.return_value = (
            True, 123, ""  # success, user_id, error
        )
        
        # Mock account activation success
        self.mock_account_manager.activate_user_account.return_value = True
        
        # Test account creation
        result = self.creator.create_test_account(self.test_email, self.test_password)
        
        # Verify result
        self.assertTrue(result['success'])
        self.assertEqual(result['user_id'], 123)
        self.assertEqual(result['email'], self.test_email)
        self.assertEqual(result['password'], self.test_password)
        self.assertIn('Test account created successfully', result['message'])
        
        # Verify user account manager was called correctly
        self.mock_account_manager.create_new_user_account.assert_called_once_with(
            self.test_email, 
            self.test_password,
            {'terms': True, 'privacy': True, 'disclaimer': True}
        )
        
        # Verify account was activated
        self.mock_account_manager.activate_user_account.assert_called_once_with(123)
    
    def test_create_test_account_existing_user(self):
        """Test test account creation when user already exists"""
        # Mock existing user check - user exists
        self.mock_execute_query.return_value = [{'id': 456, 'email': self.test_email}]
        
        # Test account creation
        result = self.creator.create_test_account(self.test_email, self.test_password)
        
        # Verify result
        self.assertFalse(result['success'])
        self.assertEqual(result['error'], 'Test account already exists')
        self.assertEqual(result['user_id'], 456)
        
        # Verify user account manager was not called
        self.mock_account_manager.create_new_user_account.assert_not_called()
    
    def test_create_test_account_user_creation_failure(self):
        """Test test account creation when user account creation fails"""
        # Mock existing user check - no existing user
        self.mock_execute_query.return_value = []
        
        # Mock user account creation failure
        self.mock_account_manager.create_new_user_account.return_value = (
            False, None, "Database error"
        )
        
        # Test account creation
        result = self.creator.create_test_account(self.test_email, self.test_password)
        
        # Verify result
        self.assertFalse(result['success'])
        self.assertEqual(result['error'], 'Database error')
        self.assertIsNone(result['user_id'])
    
    def test_setup_test_onboarding_progress(self):
        """Test onboarding progress setup"""
        user_id = 123
        
        # Call the method
        self.creator._setup_test_onboarding_progress(user_id)
        
        # Verify the database update was called
        self.mock_execute_query.assert_called()
        
        # Get the last call to verify the query
        last_call = self.mock_execute_query.call_args_list[-1]
        query = last_call[0][0]
        params = last_call[0][1]
        
        # Verify query structure
        self.assertIn('UPDATE user_settings', query)
        self.assertIn('onboarding_step', query)
        self.assertIn('onboarding_progress', query)
        
        # Verify parameters
        self.assertEqual(params[0], 'goals_setup')  # onboarding_step
        self.assertEqual(params[1], 80)  # onboarding_progress
        self.assertEqual(params[-1], user_id)  # user_id
    
    def test_setup_test_goals(self):
        """Test goals setup"""
        user_id = 123
        
        # Call the method
        self.creator._setup_test_goals(user_id)
        
        # Verify the database update was called
        self.mock_execute_query.assert_called()
        
        # Get the last call to verify the query
        last_call = self.mock_execute_query.call_args_list[-1]
        query = last_call[0][0]
        params = last_call[0][1]
        
        # Verify query structure
        self.assertIn('UPDATE user_settings', query)
        self.assertIn('goals_configured', query)
        self.assertIn('goal_type', query)
        
        # Verify parameters
        self.assertTrue(params[0])  # goals_configured
        self.assertEqual(params[1], 'distance')  # goal_type
        self.assertEqual(params[2], '100')  # goal_target
        self.assertEqual(params[3], 'monthly')  # goal_timeframe
        self.assertEqual(params[-1], user_id)  # user_id
    
    def test_setup_test_analytics(self):
        """Test analytics setup"""
        user_id = 123
        
        # Call the method
        self.creator._setup_test_analytics(user_id)
        
        # Verify analytics tracking was called for each event
        expected_events = [
            'onboarding_started',
            'strava_connected', 
            'first_activity_synced',
            'dashboard_intro_completed',
            'goals_setup_started',
            'page_view'
        ]
        
        self.assertEqual(self.mock_analytics.track_event.call_count, len(expected_events))
        
        # Verify each event was tracked
        for call in self.mock_analytics.track_event.call_args_list:
            args = call[0]
            self.assertEqual(args[0], user_id)  # user_id
            self.assertIn(args[1], expected_events)  # event_name
            self.assertIsInstance(args[2], dict)  # event_data
    
    def test_setup_test_activities(self):
        """Test activities setup"""
        user_id = 123
        
        # Call the method
        self.creator._setup_test_activities(user_id)
        
        # Verify database inserts were called for each activity
        # Should be called 3 times (one for each test activity)
        self.assertEqual(self.mock_execute_query.call_count, 3)
        
        # Verify each activity insert
        for call in self.mock_execute_query.call_args_list:
            query = call[0][0]
            params = call[0][1]
            
            # Verify query structure
            self.assertIn('INSERT INTO activities', query)
            self.assertIn('user_id', query)
            self.assertIn('activity_type', query)
            self.assertIn('distance', query)
            
            # Verify parameters
            self.assertEqual(params[0], user_id)  # user_id
            self.assertIn(params[1], ['run', 'bike'])  # activity_type
            self.assertIsInstance(params[2], (int, float))  # distance
            self.assertIsInstance(params[3], int)  # duration
    
    def test_setup_test_training_data(self):
        """Test training data setup"""
        user_id = 123
        
        # Call the method
        self.creator._setup_test_training_data(user_id)
        
        # Verify database inserts were called for each day (7 days)
        self.assertEqual(self.mock_execute_query.call_count, 7)
        
        # Verify each training load insert
        for call in self.mock_execute_query.call_args_list:
            query = call[0][0]
            params = call[0][1]
            
            # Verify query structure
            self.assertIn('INSERT INTO training_load', query)
            self.assertIn('user_id', query)
            self.assertIn('date', query)
            self.assertIn('training_load', query)
            
            # Verify parameters
            self.assertEqual(params[0], user_id)  # user_id
            self.assertIsInstance(params[1], date)  # date
            self.assertIsInstance(params[2], int)  # training_load
            self.assertGreaterEqual(params[2], 20)  # min training load
            self.assertLessEqual(params[2], 80)  # max training load
    
    def test_list_test_accounts(self):
        """Test listing test accounts"""
        # Mock database query result
        mock_accounts = [
            {'id': 123, 'email': 'test1@trainingmonkey.com', 'account_status': 'active'},
            {'id': 456, 'email': 'test2@trainingmonkey.com', 'account_status': 'pending'}
        ]
        self.mock_execute_query.return_value = mock_accounts
        
        # Call the method
        result = self.creator.list_test_accounts()
        
        # Verify result
        self.assertEqual(result, mock_accounts)
        
        # Verify query was called
        self.mock_execute_query.assert_called_once()
        query = self.mock_execute_query.call_args[0][0]
        self.assertIn('SELECT', query)
        self.assertIn('user_settings', query)
        self.assertIn('WHERE', query)
    
    def test_delete_test_account(self):
        """Test deleting test account"""
        user_id = 123
        
        # Call the method
        result = self.creator.delete_test_account(user_id)
        
        # Verify result
        self.assertTrue(result)
        
        # Verify cleanup queries were called
        expected_tables = ['onboarding_analytics', 'activities', 'training_load', 'legal_compliance']
        self.assertEqual(self.mock_execute_query.call_count, len(expected_tables) + 1)  # +1 for user deletion
        
        # Verify user deletion was called last
        last_call = self.mock_execute_query.call_args_list[-1]
        query = last_call[0][0]
        params = last_call[0][1]
        
        self.assertIn('DELETE FROM user_settings', query)
        self.assertEqual(params[0], user_id)
    
    def test_get_user_by_email(self):
        """Test getting user by email"""
        email = "test@example.com"
        mock_user = {'id': 123, 'email': email}
        self.mock_execute_query.return_value = [mock_user]
        
        # Call the method
        result = self.creator._get_user_by_email(email)
        
        # Verify result
        self.assertEqual(result, mock_user)
        
        # Verify query was called
        self.mock_execute_query.assert_called_once()
        query = self.mock_execute_query.call_args[0][0]
        params = self.mock_execute_query.call_args[0][1]
        
        self.assertIn('SELECT * FROM user_settings WHERE email = ?', query)
        self.assertEqual(params[0], email)
    
    def test_get_user_by_email_not_found(self):
        """Test getting user by email when not found"""
        email = "nonexistent@example.com"
        self.mock_execute_query.return_value = []
        
        # Call the method
        result = self.creator._get_user_by_email(email)
        
        # Verify result
        self.assertIsNone(result)

class TestTestAccountCreatorIntegration(unittest.TestCase):
    """Integration tests for TestAccountCreator with real database"""
    
    @classmethod
    def setUpClass(cls):
        """Set up test database"""
        # Create a temporary database for testing
        cls.test_db_path = tempfile.mktemp(suffix='.db')
        
        # Set environment variable to use test database
        os.environ['DB_PATH'] = cls.test_db_path
        
        # Import after setting environment
        from db_utils import execute_query
        
        # Create test tables
        cls.create_test_tables(execute_query)
    
    @classmethod
    def tearDownClass(cls):
        """Clean up test database"""
        if os.path.exists(cls.test_db_path):
            os.remove(cls.test_db_path)
    
    @classmethod
    def create_test_tables(cls, execute_query):
        """Create test database tables"""
        # Create user_settings table
        execute_query("""
            CREATE TABLE IF NOT EXISTS user_settings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                account_status TEXT DEFAULT 'pending',
                onboarding_step TEXT DEFAULT 'not_started',
                onboarding_progress INTEGER DEFAULT 0,
                goals_configured BOOLEAN DEFAULT FALSE,
                goal_type VARCHAR(50),
                goal_target VARCHAR(100),
                goal_timeframe VARCHAR(50),
                goals_setup_date TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create onboarding_analytics table
        execute_query("""
            CREATE TABLE IF NOT EXISTS onboarding_analytics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                event_name VARCHAR(100) NOT NULL,
                event_data TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES user_settings(id)
            )
        """)
        
        # Create activities table
        execute_query("""
            CREATE TABLE IF NOT EXISTS activities (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                activity_type TEXT NOT NULL,
                distance REAL,
                duration INTEGER,
                date DATE,
                strava_id TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES user_settings(id)
            )
        """)
        
        # Create training_load table
        execute_query("""
            CREATE TABLE IF NOT EXISTS training_load (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                date DATE NOT NULL,
                training_load INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(user_id, date)
            )
        """)
        
        # Create legal_compliance table
        execute_query("""
            CREATE TABLE IF NOT EXISTS legal_compliance (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                document_type VARCHAR(50) NOT NULL,
                version VARCHAR(20) NOT NULL,
                accepted BOOLEAN DEFAULT FALSE,
                accepted_date TIMESTAMP,
                ip_address TEXT,
                user_agent TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES user_settings(id)
            )
        """)
    
    def setUp(self):
        """Set up test fixtures"""
        from db_utils import execute_query
        
        # Clear test data
        execute_query("DELETE FROM onboarding_analytics")
        execute_query("DELETE FROM activities")
        execute_query("DELETE FROM training_load")
        execute_query("DELETE FROM legal_compliance")
        execute_query("DELETE FROM user_settings")
        
        # Mock the account manager and analytics
        with patch('create_test_account.UserAccountManager') as mock_account_manager_class:
            with patch('create_test_account.OnboardingAnalytics') as mock_analytics_class:
                with patch('create_test_account.get_legal_compliance_tracker'):
                    with patch('create_test_account.get_current_legal_versions') as mock_legal_versions:
                        
                        self.mock_account_manager = MagicMock()
                        mock_account_manager_class.return_value = self.mock_account_manager
                        
                        self.mock_analytics = MagicMock()
                        mock_analytics_class.return_value = self.mock_analytics
                        
                        mock_legal_versions.return_value = {
                            'terms': '2.0',
                            'privacy': '2.0',
                            'disclaimer': '2.0'
                        }
                        
                        self.creator = TestAccountCreator()
    
    def test_integration_create_test_account(self):
        """Integration test for creating a test account"""
        # Mock user account creation success
        self.mock_account_manager.create_new_user_account.return_value = (True, 1, "")
        self.mock_account_manager.activate_user_account.return_value = True
        
        # Create test account
        result = self.creator.create_test_account("integration@test.com", "TestPass123!")
        
        # Verify result
        self.assertTrue(result['success'])
        self.assertEqual(result['user_id'], 1)
        
        # Verify user was created in database
        from db_utils import execute_query
        user = execute_query("SELECT * FROM user_settings WHERE id = ?", (1,), fetch=True)
        self.assertIsNotNone(user)
        self.assertEqual(user[0]['email'], "integration@test.com")

if __name__ == '__main__':
    unittest.main()

