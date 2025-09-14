#!/usr/bin/env python3
"""
Check hr_streams table structure and data
"""

from app.db_utils import get_db_connection

def check_hr_streams():
    """Check hr_streams table structure and data"""
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                # Check hr_streams table structure
                cursor.execute("""
                    SELECT column_name, data_type, is_nullable, column_default
                    FROM information_schema.columns 
                    WHERE table_name = 'hr_streams'
                    ORDER BY ordinal_position
                """)
                hr_streams_columns = cursor.fetchall()
                
                print("hr_streams table structure:")
                for col in hr_streams_columns:
                    print(f"  - {col['column_name']} ({col['data_type']}) - nullable: {col['is_nullable']}")
                
                # Check if there's any data in hr_streams
                cursor.execute("SELECT COUNT(*) FROM hr_streams")
                count = cursor.fetchone()['count']
                print(f"\nTotal hr_streams records: {count}")
                
                if count > 0:
                    # Get sample data
                    cursor.execute("""
                        SELECT id, activity_id, user_id, sample_rate, created_at
                        FROM hr_streams 
                        ORDER BY created_at DESC 
                        LIMIT 5
                    """)
                    sample_data = cursor.fetchall()
                    
                    print("\nSample hr_streams data:")
                    for row in sample_data:
                        print(f"  - ID: {row['id']}, Activity: {row['activity_id']}, User: {row['user_id']}, Sample Rate: {row['sample_rate']}, Created: {row['created_at']}")
                    
                    # Check hr_data structure
                    cursor.execute("""
                        SELECT id, activity_id, 
                               CASE 
                                   WHEN hr_data IS NULL THEN 'NULL'
                                   WHEN jsonb_typeof(hr_data) = 'array' THEN 'Array with ' || jsonb_array_length(hr_data) || ' elements'
                                   ELSE 'Other: ' || jsonb_typeof(hr_data)
                               END as hr_data_info
                        FROM hr_streams 
                        WHERE hr_data IS NOT NULL
                        LIMIT 3
                    """)
                    hr_data_samples = cursor.fetchall()
                    
                    print("\nHR data structure samples:")
                    for row in hr_data_samples:
                        print(f"  - ID: {row['id']}, Activity: {row['activity_id']}, HR Data: {row['hr_data_info']}")
                
                # Check activities with TRIMP data
                cursor.execute("""
                    SELECT COUNT(*) as total_activities,
                           COUNT(CASE WHEN trimp > 0 THEN 1 END) as activities_with_trimp,
                           COUNT(CASE WHEN trimp_calculation_method = 'stream' THEN 1 END) as stream_calculations,
                           COUNT(CASE WHEN trimp_calculation_method = 'average' THEN 1 END) as average_calculations,
                           COUNT(CASE WHEN hr_stream_sample_count > 0 THEN 1 END) as activities_with_hr_streams
                    FROM activities
                """)
                trimp_stats = cursor.fetchone()
                
                print(f"\nTRIMP calculation statistics:")
                print(f"  - Total activities: {trimp_stats['total_activities']}")
                print(f"  - Activities with TRIMP: {trimp_stats['activities_with_trimp']}")
                print(f"  - Stream calculations: {trimp_stats['stream_calculations']}")
                print(f"  - Average calculations: {trimp_stats['average_calculations']}")
                print(f"  - Activities with HR streams: {trimp_stats['activities_with_hr_streams']}")
                
                return True
                
    except Exception as e:
        print(f"Database connection error: {e}")
        return False

if __name__ == "__main__":
    check_hr_streams()
