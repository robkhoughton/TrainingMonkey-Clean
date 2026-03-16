#!/usr/bin/env python3
"""
User Activity Report Generator
Generates a report showing users, email addresses, first activity, and last activity dates
"""

import sys
import os
from datetime import datetime
from pathlib import Path

# Add app directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

# Load database credentials BEFORE importing db_utils (which requires DATABASE_URL)
from db_credentials_loader import set_database_url
if not set_database_url():
    print("ERROR: Could not load DATABASE_URL from .env file")
    sys.exit(1)

import db_utils


def generate_user_activity_report(output_format='text'):
    """
    Generate a report of users with their email addresses, first activity, and last activity dates.
    
    Args:
        output_format: 'text' for console output, 'csv' for CSV file
    """
    try:
        # Query to get user information with activity dates
        query = """
            SELECT 
                u.id AS user_id,
                u.email,
                MIN(a.date) AS first_activity,
                MAX(a.date) AS last_activity,
                COUNT(a.activity_id) AS total_activities
            FROM user_settings u
            LEFT JOIN activities a ON u.id = a.user_id
            GROUP BY u.id, u.email
            ORDER BY u.id;
        """
        
        results = db_utils.execute_query(query, fetch=True)
        
        if not results:
            print("No users found in database")
            return False
        
        # Generate report based on format
        if output_format == 'csv':
            return generate_csv_report(results)
        else:
            return generate_text_report(results)
            
    except Exception as e:
        print(f"ERROR generating report: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def generate_text_report(results):
    """Generate a formatted text report"""
    print("=" * 100)
    print("USER ACTIVITY REPORT")
    print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 100)
    print()
    
    # Header
    print(f"{'User ID':<10} {'Email':<40} {'First Activity':<15} {'Last Activity':<15} {'Total Activities':<15}")
    print("-" * 100)
    
    # Data rows
    users_with_activities = 0
    users_without_activities = 0
    
    for row in results:
        user_id = row['user_id']
        email = row['email'] or 'N/A'
        first_activity = row['first_activity'] or 'N/A'
        last_activity = row['last_activity'] or 'N/A'
        total_activities = row['total_activities'] or 0
        
        # Format dates if they exist
        if first_activity != 'N/A' and first_activity:
            if isinstance(first_activity, str):
                first_activity = first_activity[:10]  # Take YYYY-MM-DD part
            else:
                first_activity = str(first_activity)[:10]
        
        if last_activity != 'N/A' and last_activity:
            if isinstance(last_activity, str):
                last_activity = last_activity[:10]  # Take YYYY-MM-DD part
            else:
                last_activity = str(last_activity)[:10]
        
        print(f"{user_id:<10} {email:<40} {str(first_activity):<15} {str(last_activity):<15} {total_activities:<15}")
        
        if total_activities > 0:
            users_with_activities += 1
        else:
            users_without_activities += 1
    
    print("-" * 100)
    print()
    print(f"Total Users: {len(results)}")
    print(f"Users with activities: {users_with_activities}")
    print(f"Users without activities: {users_without_activities}")
    print()
    print("=" * 100)
    
    return True


def generate_csv_report(results):
    """Generate a CSV report file"""
    import csv
    
    # Create logs directory if it doesn't exist (root logs directory, not app/logs)
    logs_dir = Path(__file__).parent.parent / 'logs'
    logs_dir.mkdir(exist_ok=True)
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = logs_dir / f"user_activity_report_{timestamp}.csv"
    
    try:
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['user_id', 'email', 'first_activity', 'last_activity', 'total_activities']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            writer.writeheader()
            
            for row in results:
                # Format dates
                first_activity = row['first_activity']
                last_activity = row['last_activity']
                
                if first_activity:
                    if isinstance(first_activity, str):
                        first_activity = first_activity[:10]
                    else:
                        first_activity = str(first_activity)[:10]
                
                if last_activity:
                    if isinstance(last_activity, str):
                        last_activity = last_activity[:10]
                    else:
                        last_activity = str(last_activity)[:10]
                
                writer.writerow({
                    'user_id': row['user_id'],
                    'email': row['email'] or '',
                    'first_activity': first_activity or '',
                    'last_activity': last_activity or '',
                    'total_activities': row['total_activities'] or 0
                })
        
        print(f"CSV report generated successfully: {filename}")
        print(f"Total users: {len(results)}")
        return True
        
    except Exception as e:
        print(f"ERROR generating CSV report: {str(e)}")
        return False


if __name__ == "__main__":
    # Default to text output, but allow CSV via command line argument
    output_format = 'text'
    if len(sys.argv) > 1 and sys.argv[1].lower() == 'csv':
        output_format = 'csv'
    
    success = generate_user_activity_report(output_format)
    sys.exit(0 if success else 1)

