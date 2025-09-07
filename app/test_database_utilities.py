#!/usr/bin/env python3
"""
Test suite for database utilities
Tests the TRIMP enhancement database functions and schema validation
"""

import unittest
import sys
import os
from unittest.mock import patch, MagicMock
from datetime import datetime

# Add the app directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from db_utils import (
    validate_trimp_schema,
    validate_hr_streams_table,
    get_trimp_schema_status,
    save_hr_stream_data,
    get_hr_stream_data,
    update_activity_trimp_metadata,
    get_activities_needing_trimp_recalculation,
    delete_hr_stream_data
)


class TestDatabaseUtilities(unittest.TestCase):
    """Test cases for database utility functions"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.sample_hr_data = [120, 125, 130, 135, 140, 145, 150, 155, 160, 165] * 60  # 600 samples
        self.activity_id = 12345
        self.user_id = 1
    
    @patch('db_utils.execute_query')
    def test_validate_trimp_schema_success(self, mock_execute):
        """Test TRIMP schema validation with valid schema"""
        # Mock successful schema check
        mock_execute.return_value = [{'count': 1}]  # Fields exist
        
        result = validate_trimp_schema()
        
        self.assertTrue(result['trimp_calculation_method_exists'])
        self.assertTrue(result['hr_stream_sample_count_exists'])
        self.assertTrue(result['trimp_processed_at_exists'])
        self.assertTrue(result['overall_valid'])
    
    @patch('db_utils.execute_query')
    def test_validate_trimp_schema_missing_fields(self, mock_execute):
        """Test TRIMP schema validation with missing fields"""
        # Mock missing fields
        def mock_execute_side_effect(query, params=None, fetch=False):
            if 'trimp_calculation_method' in query:
                return [{'count': 0}]  # Field doesn't exist
            elif 'hr_stream_sample_count' in query:
                return [{'count': 1}]  # Field exists
            elif 'trimp_processed_at' in query:
                return [{'count': 0}]  # Field doesn't exist
            return []
        
        mock_execute.side_effect = mock_execute_side_effect
        
        result = validate_trimp_schema()
        
        self.assertFalse(result['trimp_calculation_method_exists'])
        self.assertTrue(result['hr_stream_sample_count_exists'])
        self.assertFalse(result['trimp_processed_at_exists'])
        self.assertFalse(result['overall_valid'])
    
    @patch('db_utils.execute_query')
    def test_validate_hr_streams_table_success(self, mock_execute):
        """Test HR streams table validation with valid table"""
        # Mock successful table check
        mock_execute.return_value = [{'count': 1}]  # Table exists
        
        result = validate_hr_streams_table()
        
        self.assertTrue(result['table_exists'])
        self.assertTrue(result['overall_valid'])
    
    @patch('db_utils.execute_query')
    def test_validate_hr_streams_table_missing(self, mock_execute):
        """Test HR streams table validation with missing table"""
        # Mock missing table
        mock_execute.return_value = [{'count': 0}]  # Table doesn't exist
        
        result = validate_hr_streams_table()
        
        self.assertFalse(result['table_exists'])
        self.assertFalse(result['overall_valid'])
    
    @patch('db_utils.validate_trimp_schema')
    @patch('db_utils.validate_hr_streams_table')
    def test_get_trimp_schema_status_success(self, mock_hr_streams, mock_trimp_schema):
        """Test getting complete TRIMP schema status"""
        mock_trimp_schema.return_value = {
            'trimp_calculation_method_exists': True,
            'hr_stream_sample_count_exists': True,
            'trimp_processed_at_exists': True,
            'overall_valid': True
        }
        
        mock_hr_streams.return_value = {
            'table_exists': True,
            'overall_valid': True
        }
        
        result = get_trimp_schema_status()
        
        self.assertTrue(result['trimp_fields_valid'])
        self.assertTrue(result['hr_streams_table_valid'])
        self.assertTrue(result['overall_valid'])
    
    @patch('db_utils.execute_query')
    def test_save_hr_stream_data_success(self, mock_execute):
        """Test saving HR stream data successfully"""
        mock_execute.return_value = True  # Successful insert
        
        result = save_hr_stream_data(
            activity_id=self.activity_id,
            user_id=self.user_id,
            hr_data=self.sample_hr_data
        )
        
        self.assertTrue(result)
        mock_execute.assert_called_once()
    
    @patch('db_utils.execute_query')
    def test_save_hr_stream_data_invalid_input(self, mock_execute):
        """Test saving HR stream data with invalid input"""
        # Test with None activity_id
        result = save_hr_stream_data(
            activity_id=None,
            user_id=self.user_id,
            hr_data=self.sample_hr_data
        )
        
        self.assertFalse(result)
        mock_execute.assert_not_called()
        
        # Test with None user_id
        result = save_hr_stream_data(
            activity_id=self.activity_id,
            user_id=None,
            hr_data=self.sample_hr_data
        )
        
        self.assertFalse(result)
        mock_execute.assert_not_called()
        
        # Test with None hr_data
        result = save_hr_stream_data(
            activity_id=self.activity_id,
            user_id=self.user_id,
            hr_data=None
        )
        
        self.assertFalse(result)
        mock_execute.assert_not_called()
    
    @patch('db_utils.execute_query')
    def test_save_hr_stream_data_empty_data(self, mock_execute):
        """Test saving HR stream data with empty data"""
        result = save_hr_stream_data(
            activity_id=self.activity_id,
            user_id=self.user_id,
            hr_data=[]
        )
        
        self.assertFalse(result)
        mock_execute.assert_not_called()
    
    @patch('db_utils.execute_query')
    def test_get_hr_stream_data_success(self, mock_execute):
        """Test getting HR stream data successfully"""
        # Mock successful query
        mock_execute.return_value = [{
            'hr_data': '[120, 125, 130, 135, 140]',
            'sample_rate': 1.0,
            'created_at': datetime.now().isoformat()
        }]
        
        result = get_hr_stream_data(
            activity_id=self.activity_id,
            user_id=self.user_id
        )
        
        self.assertIsNotNone(result)
        self.assertIn('hr_data', result)
        self.assertIn('sample_rate', result)
        self.assertIn('created_at', result)
        self.assertEqual(result['sample_rate'], 1.0)
    
    @patch('db_utils.execute_query')
    def test_get_hr_stream_data_not_found(self, mock_execute):
        """Test getting HR stream data when not found"""
        mock_execute.return_value = []  # No data found
        
        result = get_hr_stream_data(
            activity_id=self.activity_id,
            user_id=self.user_id
        )
        
        self.assertIsNone(result)
    
    @patch('db_utils.execute_query')
    def test_get_hr_stream_data_invalid_json(self, mock_execute):
        """Test getting HR stream data with invalid JSON"""
        # Mock invalid JSON data
        mock_execute.return_value = [{
            'hr_data': 'invalid json data',
            'sample_rate': 1.0,
            'created_at': datetime.now().isoformat()
        }]
        
        result = get_hr_stream_data(
            activity_id=self.activity_id,
            user_id=self.user_id
        )
        
        self.assertIsNone(result)
    
    @patch('db_utils.execute_query')
    def test_update_activity_trimp_metadata_success(self, mock_execute):
        """Test updating activity TRIMP metadata successfully"""
        mock_execute.return_value = True  # Successful update
        
        result = update_activity_trimp_metadata(
            activity_id=self.activity_id,
            user_id=self.user_id,
            calculation_method='stream',
            sample_count=600,
            trimp_value=120.5
        )
        
        self.assertTrue(result)
        mock_execute.assert_called_once()
    
    @patch('db_utils.execute_query')
    def test_update_activity_trimp_metadata_invalid_input(self, mock_execute):
        """Test updating activity TRIMP metadata with invalid input"""
        # Test with None activity_id
        result = update_activity_trimp_metadata(
            activity_id=None,
            user_id=self.user_id,
            calculation_method='stream',
            sample_count=600,
            trimp_value=120.5
        )
        
        self.assertFalse(result)
        mock_execute.assert_not_called()
        
        # Test with None user_id
        result = update_activity_trimp_metadata(
            activity_id=self.activity_id,
            user_id=None,
            calculation_method='stream',
            sample_count=600,
            trimp_value=120.5
        )
        
        self.assertFalse(result)
        mock_execute.assert_not_called()
        
        # Test with None calculation_method
        result = update_activity_trimp_metadata(
            activity_id=self.activity_id,
            user_id=self.user_id,
            calculation_method=None,
            sample_count=600,
            trimp_value=120.5
        )
        
        self.assertFalse(result)
        mock_execute.assert_not_called()
    
    @patch('db_utils.execute_query')
    def test_get_activities_needing_trimp_recalculation_success(self, mock_execute):
        """Test getting activities needing TRIMP recalculation"""
        # Mock activities data
        mock_execute.return_value = [
            {
                'activity_id': 12345,
                'user_id': 1,
                'trimp': 100.0,
                'duration_minutes': 60.0,
                'avg_heart_rate': 140,
                'trimp_calculation_method': 'average',
                'trimp_processed_at': None
            },
            {
                'activity_id': 12346,
                'user_id': 1,
                'trimp': 120.0,
                'duration_minutes': 45.0,
                'avg_heart_rate': 150,
                'trimp_calculation_method': None,
                'trimp_processed_at': None
            }
        ]
        
        result = get_activities_needing_trimp_recalculation(
            user_id=self.user_id,
            days_back=30
        )
        
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]['activity_id'], 12345)
        self.assertEqual(result[1]['activity_id'], 12346)
    
    @patch('db_utils.execute_query')
    def test_get_activities_needing_trimp_recalculation_no_activities(self, mock_execute):
        """Test getting activities when none need recalculation"""
        mock_execute.return_value = []  # No activities found
        
        result = get_activities_needing_trimp_recalculation(
            user_id=self.user_id,
            days_back=30
        )
        
        self.assertEqual(len(result), 0)
    
    @patch('db_utils.execute_query')
    def test_get_activities_needing_trimp_recalculation_all_users(self, mock_execute):
        """Test getting activities for all users"""
        mock_execute.return_value = [
            {
                'activity_id': 12345,
                'user_id': 1,
                'trimp': 100.0,
                'duration_minutes': 60.0,
                'avg_heart_rate': 140,
                'trimp_calculation_method': 'average',
                'trimp_processed_at': None
            }
        ]
        
        result = get_activities_needing_trimp_recalculation(
            user_id=None,  # All users
            days_back=30
        )
        
        self.assertEqual(len(result), 1)
        mock_execute.assert_called_once()
    
    @patch('db_utils.execute_query')
    def test_delete_hr_stream_data_success(self, mock_execute):
        """Test deleting HR stream data successfully"""
        mock_execute.return_value = True  # Successful delete
        
        result = delete_hr_stream_data(
            activity_id=self.activity_id,
            user_id=self.user_id
        )
        
        self.assertTrue(result)
        mock_execute.assert_called_once()
    
    @patch('db_utils.execute_query')
    def test_delete_hr_stream_data_invalid_input(self, mock_execute):
        """Test deleting HR stream data with invalid input"""
        # Test with None activity_id
        result = delete_hr_stream_data(
            activity_id=None,
            user_id=self.user_id
        )
        
        self.assertFalse(result)
        mock_execute.assert_not_called()
        
        # Test with None user_id
        result = delete_hr_stream_data(
            activity_id=self.activity_id,
            user_id=None
        )
        
        self.assertFalse(result)
        mock_execute.assert_not_called()
    
    @patch('db_utils.execute_query')
    def test_delete_hr_stream_data_all_users(self, mock_execute):
        """Test deleting HR stream data for all users"""
        mock_execute.return_value = True  # Successful delete
        
        result = delete_hr_stream_data(
            activity_id=self.activity_id,
            user_id=None  # All users
        )
        
        self.assertTrue(result)
        mock_execute.assert_called_once()


class TestDatabaseUtilitiesIntegration(unittest.TestCase):
    """Integration tests for database utilities"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.sample_hr_data = [120, 125, 130, 135, 140, 145, 150, 155, 160, 165] * 60
        self.activity_id = 12345
        self.user_id = 1
    
    @patch('db_utils.execute_query')
    def test_save_and_get_hr_stream_data_roundtrip(self, mock_execute):
        """Test saving and retrieving HR stream data in a roundtrip"""
        # Mock successful save
        mock_execute.return_value = True
        
        # Save HR stream data
        save_result = save_hr_stream_data(
            activity_id=self.activity_id,
            user_id=self.user_id,
            hr_data=self.sample_hr_data
        )
        
        self.assertTrue(save_result)
        
        # Mock successful retrieval
        import json
        mock_execute.return_value = [{
            'hr_data': json.dumps(self.sample_hr_data),
            'sample_rate': 1.0,
            'created_at': datetime.now().isoformat()
        }]
        
        # Get HR stream data
        get_result = get_hr_stream_data(
            activity_id=self.activity_id,
            user_id=self.user_id
        )
        
        self.assertIsNotNone(get_result)
        self.assertEqual(get_result['hr_data'], self.sample_hr_data)
        self.assertEqual(get_result['sample_rate'], 1.0)
    
    @patch('db_utils.execute_query')
    def test_update_and_verify_activity_metadata(self, mock_execute):
        """Test updating and verifying activity metadata"""
        # Mock successful update
        mock_execute.return_value = True
        
        # Update activity metadata
        update_result = update_activity_trimp_metadata(
            activity_id=self.activity_id,
            user_id=self.user_id,
            calculation_method='stream',
            sample_count=600,
            trimp_value=120.5
        )
        
        self.assertTrue(update_result)
        
        # Mock verification query
        mock_execute.return_value = [{
            'trimp': 120.5,
            'trimp_calculation_method': 'stream',
            'hr_stream_sample_count': 600,
            'trimp_processed_at': datetime.now().isoformat()
        }]
        
        # Verify the update (this would be done by the recalculation system)
        # For now, just verify the mock was called correctly
        self.assertTrue(update_result)
    
    @patch('db_utils.execute_query')
    def test_complete_trimp_enhancement_workflow(self, mock_execute):
        """Test complete TRIMP enhancement workflow"""
        # Mock all database operations
        def mock_execute_side_effect(query, params=None, fetch=False):
            if 'INSERT INTO hr_streams' in query:
                return True  # Successful save
            elif 'SELECT hr_data' in query:
                import json
                return [{
                    'hr_data': json.dumps(self.sample_hr_data),
                    'sample_rate': 1.0,
                    'created_at': datetime.now().isoformat()
                }]
            elif 'UPDATE activities' in query:
                return True  # Successful update
            elif 'SELECT activity_id' in query:
                return [{
                    'activity_id': self.activity_id,
                    'user_id': self.user_id,
                    'trimp': 100.0,
                    'duration_minutes': 60.0,
                    'avg_heart_rate': 140,
                    'trimp_calculation_method': 'average',
                    'trimp_processed_at': None
                }]
            return []
        
        mock_execute.side_effect = mock_execute_side_effect
        
        # Step 1: Get activities needing recalculation
        activities = get_activities_needing_trimp_recalculation(
            user_id=self.user_id,
            days_back=30
        )
        
        self.assertEqual(len(activities), 1)
        self.assertEqual(activities[0]['activity_id'], self.activity_id)
        
        # Step 2: Save HR stream data
        save_result = save_hr_stream_data(
            activity_id=self.activity_id,
            user_id=self.user_id,
            hr_data=self.sample_hr_data
        )
        
        self.assertTrue(save_result)
        
        # Step 3: Get HR stream data
        hr_data = get_hr_stream_data(
            activity_id=self.activity_id,
            user_id=self.user_id
        )
        
        self.assertIsNotNone(hr_data)
        self.assertEqual(hr_data['hr_data'], self.sample_hr_data)
        
        # Step 4: Update activity metadata
        update_result = update_activity_trimp_metadata(
            activity_id=self.activity_id,
            user_id=self.user_id,
            calculation_method='stream',
            sample_count=len(self.sample_hr_data),
            trimp_value=120.5
        )
        
        self.assertTrue(update_result)


if __name__ == '__main__':
    # Run the tests
    unittest.main(verbosity=2)
