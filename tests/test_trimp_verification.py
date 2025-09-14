#!/usr/bin/env python3
"""
TRIMP Enhancement Verification Script
Tests the current TRIMP implementation with real database data
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from db_utils import get_db_connection
from strava_training_load import calculate_banister_trimp
from utils.feature_flags import is_feature_enabled

def test_trimp_implementation():
    """Test the current TRIMP implementation with real data"""
    print("🔍 TRIMP Enhancement Verification")
    print("=" * 50)
    
    try:
        # Test 1: Check feature flag status
        print("\n1. Feature Flag Status:")
        admin_enabled = is_feature_enabled('enhanced_trimp_calculation', 1)
        beta_enabled = is_feature_enabled('enhanced_trimp_calculation', 2)
        regular_enabled = is_feature_enabled('enhanced_trimp_calculation', 4)
        
        print(f"   - Admin (User 1): {'✅ Enabled' if admin_enabled else '❌ Disabled'}")
        print(f"   - Beta (User 2): {'✅ Enabled' if beta_enabled else '❌ Disabled'}")
        print(f"   - Regular (User 4): {'✅ Enabled' if regular_enabled else '❌ Disabled'}")
        
        # Test 2: Get real activity data with HR streams
        print("\n2. Real Activity Data Analysis:")
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                # Get activities with HR stream data
                cursor.execute("""
                    SELECT a.activity_id, a.name, a.date, a.duration_minutes, a.avg_heart_rate,
                           a.trimp, a.trimp_calculation_method, a.hr_stream_sample_count,
                           h.hr_data, h.sample_rate
                    FROM activities a
                    LEFT JOIN hr_streams h ON a.activity_id = h.activity_id
                    WHERE h.hr_data IS NOT NULL
                    ORDER BY a.date DESC
                    LIMIT 3
                """)
                activities = cursor.fetchall()
                
                print(f"   Found {len(activities)} activities with HR stream data")
                
                for i, activity in enumerate(activities, 1):
                    print(f"\n   Activity {i}: {activity['name']} ({activity['date']})")
                    print(f"   - Duration: {activity['duration_minutes']} minutes")
                    print(f"   - Avg HR: {activity['avg_heart_rate']} bpm")
                    print(f"   - Current TRIMP: {activity['trimp']}")
                    print(f"   - Calculation Method: {activity['trimp_calculation_method']}")
                    print(f"   - HR Stream Samples: {activity['hr_stream_sample_count']}")
                    print(f"   - Sample Rate: {activity['sample_rate']} Hz")
                    
                    # Test 3: Recalculate TRIMP with both methods
                    if activity['hr_data'] and activity['avg_heart_rate']:
                        print(f"\n   🔬 Testing TRIMP Calculations:")
                        
                        # Get HR stream data
                        hr_stream = activity['hr_data']
                        if isinstance(hr_stream, str):
                            import json
                            hr_stream = json.loads(hr_stream)
                        
                        # Test average HR calculation
                        avg_trimp = calculate_banister_trimp(
                            duration_minutes=activity['duration_minutes'],
                            avg_hr=activity['avg_heart_rate'],
                            resting_hr=50,  # Default values
                            max_hr=180,
                            gender='male'
                        )
                        
                        # Test stream HR calculation
                        stream_trimp = calculate_banister_trimp(
                            duration_minutes=activity['duration_minutes'],
                            avg_hr=activity['avg_heart_rate'],
                            resting_hr=50,
                            max_hr=180,
                            gender='male',
                            hr_stream=hr_stream
                        )
                        
                        print(f"   - Average HR TRIMP: {avg_trimp:.2f}")
                        print(f"   - Stream HR TRIMP: {stream_trimp:.2f}")
                        print(f"   - Difference: {abs(stream_trimp - avg_trimp):.2f} ({((stream_trimp - avg_trimp) / avg_trimp * 100):+.1f}%)")
                        print(f"   - Current DB TRIMP: {activity['trimp']}")
                        
                        # Check if current DB value matches expected method
                        if activity['trimp_calculation_method'] == 'stream':
                            expected_trimp = stream_trimp
                            method_name = "stream"
                        else:
                            expected_trimp = avg_trimp
                            method_name = "average"
                        
                        diff = abs(activity['trimp'] - expected_trimp)
                        if diff < 0.1:  # Within 0.1 TRIMP units
                            print(f"   ✅ Current DB TRIMP matches {method_name} calculation")
                        else:
                            print(f"   ⚠️  Current DB TRIMP differs from {method_name} calculation by {diff:.2f}")
        
        # Test 4: Check TRIMP calculation statistics
        print(f"\n3. TRIMP Calculation Statistics:")
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    SELECT 
                        COUNT(*) as total_activities,
                        COUNT(CASE WHEN trimp > 0 THEN 1 END) as activities_with_trimp,
                        COUNT(CASE WHEN trimp_calculation_method = 'stream' THEN 1 END) as stream_calculations,
                        COUNT(CASE WHEN trimp_calculation_method = 'average' THEN 1 END) as average_calculations,
                        COUNT(CASE WHEN hr_stream_sample_count > 0 THEN 1 END) as activities_with_hr_streams,
                        AVG(CASE WHEN trimp > 0 THEN trimp END) as avg_trimp_value
                    FROM activities
                """)
                stats = cursor.fetchone()
                
                print(f"   - Total Activities: {stats['total_activities']}")
                print(f"   - Activities with TRIMP: {stats['activities_with_trimp']}")
                print(f"   - Stream Calculations: {stats['stream_calculations']}")
                print(f"   - Average Calculations: {stats['average_calculations']}")
                print(f"   - Activities with HR Streams: {stats['activities_with_hr_streams']}")
                print(f"   - Average TRIMP Value: {stats['avg_trimp_value']:.2f}")
        
        print(f"\n✅ TRIMP Enhancement Verification Complete!")
        return True
        
    except Exception as e:
        print(f"❌ Error during verification: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_trimp_implementation()
