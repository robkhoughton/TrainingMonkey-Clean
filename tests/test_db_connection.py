#!/usr/bin/env python3
"""
Test database connection and schema verification
"""

from app.db_utils import get_db_connection

def test_database_connection():
    """Test database connection and list tables"""
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                # Get all tables
                cursor.execute("""
                    SELECT table_name 
                    FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    ORDER BY table_name
                """)
                tables = cursor.fetchall()
                
                print("Available tables:")
                table_names = []
                for table in tables:
                    table_name = table['table_name']
                    table_names.append(table_name)
                    print(f"  - {table_name}")
                
                # Check if hr_streams table exists
                hr_streams_exists = 'hr_streams' in table_names
                print(f"\nhr_streams table exists: {hr_streams_exists}")
                
                # Check activities table structure
                cursor.execute("""
                    SELECT column_name, data_type, is_nullable, column_default
                    FROM information_schema.columns 
                    WHERE table_name = 'activities'
                    ORDER BY ordinal_position
                """)
                activities_columns = cursor.fetchall()
                
                print(f"\nActivities table columns ({len(activities_columns)} total):")
                for col in activities_columns:
                    print(f"  - {col['column_name']} ({col['data_type']}) - nullable: {col['is_nullable']}")
                
                # Check for TRIMP-related columns
                trimp_columns = [col for col in activities_columns if 'trimp' in col['column_name'].lower()]
                print(f"\nTRIMP-related columns:")
                for col in trimp_columns:
                    print(f"  - {col['column_name']} ({col['data_type']})")
                
                return True
                
    except Exception as e:
        print(f"Database connection error: {e}")
        return False

if __name__ == "__main__":
    test_database_connection()
