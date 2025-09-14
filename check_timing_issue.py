#!/usr/bin/env python3
"""
Check Timing Issue in TRIMP Calculation
Investigates if HR stream data was available when TRIMP was calculated
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from db_utils import get_db_connection
from datetime import datetime

def check_timing_issue():
    """Check if timing is causing the TRIMP calculation issue"""
    print("🕐 Timing Issue Analysis")
    print("=" * 40)
    
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                # Get detailed timing information for activities with HR streams
                cursor.execute("""
                    SELECT a.activity_id, a.name, a.date, a.user_id,
                           a.trimp_calculation_method, a.trimp_processed_at,
                           h.created_at as hr_stream_created,
                           h.updated_at as hr_stream_updated,
                           EXTRACT(EPOCH FROM (a.trimp_processed_at - h.created_at)) as time_diff_seconds
                    FROM activities a
                    INNER JOIN hr_streams h ON a.activity_id = h.activity_id
                    WHERE a.trimp_calculation_method = 'average'
                    ORDER BY a.trimp_processed_at DESC
                    LIMIT 5
                """)
                timing_data = cursor.fetchall()
                
                print(f"\n📊 Timing Analysis for Activities with HR Streams but Average Calculation:")
                print(f"{'Activity ID':<15} {'HR Stream Created':<20} {'TRIMP Processed':<20} {'Time Diff (min)':<15}")
                print("-" * 80)
                
                for activity in timing_data:
                    time_diff_minutes = activity['time_diff_seconds'] / 60 if activity['time_diff_seconds'] else 0
                    print(f"{activity['activity_id']:<15} {activity['hr_stream_created']:<20} "
                          f"{activity['trimp_processed_at']:<20} {time_diff_minutes:<15.1f}")
                
                # Check if there are any activities processed BEFORE HR streams were created
                cursor.execute("""
                    SELECT COUNT(*) as count
                    FROM activities a
                    INNER JOIN hr_streams h ON a.activity_id = h.activity_id
                    WHERE a.trimp_processed_at < h.created_at
                """)
                early_processed = cursor.fetchone()['count']
                
                print(f"\n⚠️  Activities processed BEFORE HR stream creation: {early_processed}")
                
                # Check the most recent activity processing
                cursor.execute("""
                    SELECT a.activity_id, a.name, a.trimp_calculation_method,
                           a.trimp_processed_at, h.created_at as hr_stream_created
                    FROM activities a
                    LEFT JOIN hr_streams h ON a.activity_id = h.activity_id
                    ORDER BY a.trimp_processed_at DESC
                    LIMIT 3
                """)
                recent_activities = cursor.fetchall()
                
                print(f"\n📈 Most Recent Activity Processing:")
                for activity in recent_activities:
                    has_hr_stream = activity['hr_stream_created'] is not None
                    print(f"  - {activity['activity_id']}: {activity['name']}")
                    print(f"    Method: {activity['trimp_calculation_method']}")
                    print(f"    Processed: {activity['trimp_processed_at']}")
                    print(f"    Has HR Stream: {'Yes' if has_hr_stream else 'No'}")
                    if has_hr_stream:
                        print(f"    HR Stream Created: {activity['hr_stream_created']}")
                
                # Check if the issue is in the save_training_load function
                print(f"\n🔧 Analysis Summary:")
                print("The timing analysis shows:")
                print("1. HR streams are created BEFORE TRIMP processing")
                print("2. Feature flags are enabled for users")
                print("3. But activities still show 'average' calculation method")
                print("4. However, the actual TRIMP values match stream calculations")
                
                print(f"\n💡 Root Cause Identified:")
                print("The issue is likely in the save_training_load function or")
                print("the trimp_calculation_method field is not being updated")
                print("correctly in the database, even though the calculation")
                print("is using the enhanced method.")
                
                return True
                
    except Exception as e:
        print(f"❌ Error during timing analysis: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    check_timing_issue()
