"""
Test suite for user account manager module
"""

import unittest
import sys
import os
from unittest.mock import patch, MagicMock
from datetime import datetime

# Add the app directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from user_account_manager import UserAccountManager


class TestUserAccountManager(unittest.TestCase):
    """Test cases for UserAccountManager class"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.manager = UserAccountManager()
    
    @patch('user_account_manager.execute_query')
    def test_complete_onboarding_success(self, mock_execute):
        """Test successful onboarding completion"""
        mock_execute.return_value = True
        
        success = self.manager.complete_onboarding(123)
        self.assertTrue(success)
    
    @patch('user_account_manager.execute_query')
    def test_complete_onboarding_failure(self, mock_execute):
        """Test onboarding completion failure"""
        mock_execute.side_effect = Exception("Database error")
        
        success = self.manager.complete_onboarding(123)
        self.assertFalse(success)
    
if __name__ == '__main__':
    unittest.main()
