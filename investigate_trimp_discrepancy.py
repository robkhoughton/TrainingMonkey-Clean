#!/usr/bin/env python3
"""
Deep Investigation of TRIMP Calculation Discrepancy
Analyzes why database TRIMP values differ from calculated values
"""

import sys
import os
import json
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from db_utils import get_db_connection
from strava_training_load import calculate_banister_trimp, _calculate_trimp_from_stream, _calculate_trimp_from_average
from utils.feature_flags import is_feature_enabled

def investigate_discrepancy():
    """Deep investigation of TRIMP calculation discrepancy"""
    print("🔍 Deep TRIMP Discrepancy Investigation")
    print("=" * 60)
    
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                # Get detailed data for one specific activity
                cursor.execute("""
                    SELECT a.activity_id, a.name, a.date, a.duration_minutes, a.avg_heart_rate,
                           a.max_heart_rate, a.trimp, a.trimp_calculation_method, a.hr_stream_sample_count,
                           a.trimp_processed_at, a.user_id,
                           h.hr_data, h.sample_rate, h.created_at as hr_stream_created
                    FROM activities a
                    LEFT JOIN hr_streams h ON a.activity_id = h.activity_id
                    WHERE h.hr_data IS NOT NULL
                    ORDER BY a.date DESC
                    LIMIT 1
                """)
                activity = cursor.fetchone()
                
                if not activity:
                    print("❌ No activities with HR stream data found")
                    return False
                
                print(f"\n📊 Detailed Analysis for Activity: {activity['name']} ({activity['date']})")
                print(f"Activity ID: {activity['activity_id']}")
                print(f"User ID: {activity['user_id']}")
                print(f"Duration: {activity['duration_minutes']} minutes")
                print(f"Avg HR: {activity['avg_heart_rate']} bpm")
                print(f"Max HR: {activity['max_heart_rate']} bpm")
                print(f"Current DB TRIMP: {activity['trimp']}")
                print(f"Calculation Method: {activity['trimp_calculation_method']}")
                print(f"HR Stream Samples: {activity['hr_stream_sample_count']}")
                print(f"TRIMP Processed At: {activity['trimp_processed_at']}")
                print(f"HR Stream Created: {activity['hr_stream_created']}")
                
                # Get user's HR configuration
                cursor.execute("""
                    SELECT resting_hr, max_hr, gender
                    FROM user_settings
                    WHERE id = %s
                """, (activity['user_id'],))
                user_config = cursor.fetchone()
                
                if user_config:
                    print(f"\n👤 User HR Configuration:")
                    print(f"Resting HR: {user_config['resting_hr']} bpm")
                    print(f"Max HR: {user_config['max_hr']} bpm")
                    print(f"Gender: {user_config['gender']}")
                    resting_hr = user_config['resting_hr']
                    max_hr = user_config['max_hr']
                    gender = user_config['gender']
                else:
                    print(f"\n⚠️  No user HR configuration found, using defaults")
                    resting_hr = 50
                    max_hr = 180
                    gender = 'male'
                
                # Check feature flag for this user
                feature_enabled = is_feature_enabled('enhanced_trimp_calculation', activity['user_id'])
                print(f"\n🚩 Feature Flag Status:")
                print(f"Enhanced TRIMP enabled for user {activity['user_id']}: {'✅ Yes' if feature_enabled else '❌ No'}")
                
                # Get HR stream data
                hr_stream = activity['hr_data']
                if isinstance(hr_stream, str):
                    hr_stream = json.loads(hr_stream)
                
                print(f"\n📈 HR Stream Data Analysis:")
                print(f"Sample Rate: {activity['sample_rate']} Hz")
                print(f"Total Samples: {len(hr_stream)}")
                print(f"Expected Duration: {len(hr_stream) / activity['sample_rate'] / 60:.2f} minutes")
                print(f"Actual Duration: {activity['duration_minutes']} minutes")
                
                # Analyze HR data quality
                valid_hr_samples = [hr for hr in hr_stream if hr > 0]
                print(f"Valid HR Samples: {len(valid_hr_samples)}")
                print(f"Invalid HR Samples: {len(hr_stream) - len(valid_hr_samples)}")
                
                if valid_hr_samples:
                    print(f"HR Range: {min(valid_hr_samples)} - {max(valid_hr_samples)} bpm")
                    print(f"HR Average: {sum(valid_hr_samples) / len(valid_hr_samples):.1f} bpm")
                    print(f"DB Avg HR: {activity['avg_heart_rate']} bpm")
                    print(f"HR Difference: {abs(sum(valid_hr_samples) / len(valid_hr_samples) - activity['avg_heart_rate']):.1f} bpm")
                
                # Test different calculation methods
                print(f"\n🧮 TRIMP Calculation Tests:")
                
                # Test 1: Current function with stream data
                trimp_with_stream = calculate_banister_trimp(
                    duration_minutes=activity['duration_minutes'],
                    avg_hr=activity['avg_heart_rate'],
                    resting_hr=resting_hr,
                    max_hr=max_hr,
                    gender=gender,
                    hr_stream=hr_stream
                )
                print(f"1. Enhanced function with stream: {trimp_with_stream:.2f}")
                
                # Test 2: Current function without stream data
                trimp_without_stream = calculate_banister_trimp(
                    duration_minutes=activity['duration_minutes'],
                    avg_hr=activity['avg_heart_rate'],
                    resting_hr=resting_hr,
                    max_hr=max_hr,
                    gender=gender
                )
                print(f"2. Enhanced function without stream: {trimp_without_stream:.2f}")
                
                # Test 3: Direct stream calculation
                k = 1.92 if gender.lower() == 'male' else 1.67
                trimp_direct_stream = _calculate_trimp_from_stream(
                    activity['duration_minutes'], hr_stream, resting_hr, max_hr, k
                )
                print(f"3. Direct stream calculation: {trimp_direct_stream:.2f}")
                
                # Test 4: Direct average calculation
                trimp_direct_average = _calculate_trimp_from_average(
                    activity['duration_minutes'], activity['avg_heart_rate'], resting_hr, max_hr, k
                )
                print(f"4. Direct average calculation: {trimp_direct_average:.2f}")
                
                # Test 5: Calculate with stream-derived average HR
                if valid_hr_samples:
                    stream_avg_hr = sum(valid_hr_samples) / len(valid_hr_samples)
                    trimp_stream_avg = calculate_banister_trimp(
                        duration_minutes=activity['duration_minutes'],
                        avg_hr=stream_avg_hr,
                        resting_hr=resting_hr,
                        max_hr=max_hr,
                        gender=gender
                    )
                    print(f"5. Average calculation with stream-derived HR: {trimp_stream_avg:.2f}")
                
                print(f"\n📊 Comparison with Database Value:")
                print(f"Database TRIMP: {activity['trimp']}")
                print(f"Differences from DB value:")
                print(f"  - Enhanced with stream: {abs(trimp_with_stream - activity['trimp']):.2f}")
                print(f"  - Enhanced without stream: {abs(trimp_without_stream - activity['trimp']):.2f}")
                print(f"  - Direct stream: {abs(trimp_direct_stream - activity['trimp']):.2f}")
                print(f"  - Direct average: {abs(trimp_direct_average - activity['trimp']):.2f}")
                
                # Check if this activity was processed recently
                print(f"\n⏰ Timing Analysis:")
                if activity['trimp_processed_at']:
                    print(f"TRIMP was processed at: {activity['trimp_processed_at']}")
                if activity['hr_stream_created']:
                    print(f"HR stream was created at: {activity['hr_stream_created']}")
                
                # Check for other activities with same ID (duplicates)
                cursor.execute("""
                    SELECT COUNT(*) as count
                    FROM activities
                    WHERE activity_id = %s
                """, (activity['activity_id'],))
                duplicate_count = cursor.fetchone()['count']
                print(f"Duplicate activities with same ID: {duplicate_count}")
                
                return True
                
    except Exception as e:
        print(f"❌ Error during investigation: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    investigate_discrepancy()
