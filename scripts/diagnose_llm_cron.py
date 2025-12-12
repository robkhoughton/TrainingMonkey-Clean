#!/usr/bin/env python3
"""
Diagnostic script to investigate LLM recommendations auto-generation issues.
Checks Cloud Scheduler, database records, and application logs.
"""

import sys
import os
from datetime import datetime, timedelta
import pytz

# Add parent directory to path to import db_utils
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'app'))

from db_utils import execute_query

def print_section(title):
    """Print formatted section header"""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print('='*60)

def check_recent_recommendations():
    """Check recent LLM recommendations in database"""
    print_section("RECENT LLM RECOMMENDATIONS (Last 7 Days)")
    
    try:
        results = execute_query("""
            SELECT 
                user_id,
                target_date,
                generation_date,
                generated_at,
                is_autopsy_informed,
                autopsy_count,
                CASE 
                    WHEN daily_recommendation IS NOT NULL THEN 'Yes'
                    ELSE 'No'
                END as has_daily,
                CASE 
                    WHEN weekly_recommendation IS NOT NULL THEN 'Yes'
                    ELSE 'No'
                END as has_weekly
            FROM llm_recommendations
            WHERE generated_at >= NOW() - INTERVAL '7 days'
            ORDER BY generated_at DESC
            LIMIT 20
        """, fetch=True)
        
        if results:
            print(f"\nFound {len(results)} recommendations in last 7 days:\n")
            print(f"{'User':<6} {'Target Date':<12} {'Gen Date':<12} {'Generated At (UTC)':<20} {'Autopsy':<8} {'Daily':<6} {'Weekly'}")
            print("-" * 95)
            
            for row in results:
                data = dict(row)
                user_id = data['user_id']
                target = data['target_date']
                gen_date = data['generation_date']
                gen_at = data['generated_at'].strftime('%Y-%m-%d %H:%M:%S') if data['generated_at'] else 'N/A'
                autopsy = 'Yes' if data['is_autopsy_informed'] else 'No'
                has_daily = data['has_daily']
                has_weekly = data['has_weekly']
                
                print(f"{user_id:<6} {target:<12} {gen_date:<12} {gen_at:<20} {autopsy:<8} {has_daily:<6} {has_weekly}")
        else:
            print("\n⚠️  NO RECOMMENDATIONS FOUND IN LAST 7 DAYS")
            
    except Exception as e:
        print(f"\n❌ Error querying recommendations: {str(e)}")


def check_recommendation_gaps():
    """Check for missing daily recommendations"""
    print_section("RECOMMENDATION GAPS ANALYSIS")
    
    try:
        # Get active users
        active_users = execute_query("""
            SELECT DISTINCT user_id
            FROM activities
            WHERE date >= %s
        """, ((datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d'),), fetch=True)
        
        if not active_users:
            print("\n⚠️  No active users found in last 7 days")
            return
            
        print(f"\nActive users in last 7 days: {len(active_users)}")
        
        # Check last 7 days for each user
        for user_row in active_users:
            user_id = dict(user_row)['user_id']
            
            # Get recommendation dates for this user
            rec_dates = execute_query("""
                SELECT target_date, generation_date, generated_at
                FROM llm_recommendations
                WHERE user_id = %s AND target_date >= %s
                ORDER BY target_date DESC
            """, (user_id, (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')), fetch=True)
            
            print(f"\n  User {user_id}:")
            if rec_dates:
                print(f"    Recommendations: {len(rec_dates)} in last 7 days")
                latest = dict(rec_dates[0])
                print(f"    Latest target_date: {latest['target_date']}")
                print(f"    Generated at: {latest['generated_at']}")
            else:
                print(f"    ⚠️  NO RECOMMENDATIONS in last 7 days")
                
    except Exception as e:
        print(f"\n❌ Error checking gaps: {str(e)}")


def check_cron_execution_logs():
    """Check for cron execution in database logs"""
    print_section("CHECKING FOR CRON EXECUTION TRACES")
    
    try:
        # Check if there's a cron_logs table or any trace of cron execution
        results = execute_query("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name LIKE '%cron%' OR table_name LIKE '%log%'
        """, fetch=True)
        
        if results:
            print("\nFound logging tables:")
            for row in results:
                print(f"  - {dict(row)['table_name']}")
        else:
            print("\n⚠️  No logging tables found in database")
            print("    (Application logs would be in Cloud Run logs)")
            
    except Exception as e:
        print(f"\n❌ Error checking logs: {str(e)}")


def check_timezone_settings():
    """Check current time in different zones"""
    print_section("TIMEZONE INFORMATION")
    
    now_utc = datetime.now(pytz.UTC)
    now_pst = now_utc.astimezone(pytz.timezone('America/Los_Angeles'))
    
    print(f"\nCurrent Time:")
    print(f"  UTC:     {now_utc.strftime('%Y-%m-%d %H:%M:%S %Z')}")
    print(f"  Pacific: {now_pst.strftime('%Y-%m-%d %H:%M:%S %Z')}")
    
    print(f"\nCron Schedule (11:00 AM UTC):")
    print(f"  Runs at: 11:00 AM UTC")
    print(f"  Which is: 3:00 AM PST (winter) / 4:00 AM PDT (summer)")
    
    # Next scheduled run
    next_run_utc = now_utc.replace(hour=11, minute=0, second=0, microsecond=0)
    if next_run_utc < now_utc:
        next_run_utc += timedelta(days=1)
    
    next_run_pst = next_run_utc.astimezone(pytz.timezone('America/Los_Angeles'))
    
    print(f"\nNext Scheduled Run:")
    print(f"  UTC:     {next_run_utc.strftime('%Y-%m-%d %H:%M:%S %Z')}")
    print(f"  Pacific: {next_run_pst.strftime('%Y-%m-%d %H:%M:%S %Z')}")
    
    time_until = next_run_utc - now_utc
    hours = int(time_until.total_seconds() // 3600)
    minutes = int((time_until.total_seconds() % 3600) // 60)
    print(f"  In: {hours}h {minutes}m")


def check_user_activity():
    """Check recent user activity to verify active users"""
    print_section("RECENT USER ACTIVITY")
    
    try:
        results = execute_query("""
            SELECT 
                user_id,
                MAX(date) as last_activity_date,
                COUNT(*) as activity_count
            FROM activities
            WHERE date >= %s AND activity_id != 0
            GROUP BY user_id
            ORDER BY MAX(date) DESC
        """, ((datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d'),), fetch=True)
        
        if results:
            print(f"\nActive users in last 7 days: {len(results)}\n")
            print(f"{'User ID':<10} {'Last Activity':<15} {'Activities (7d)'}")
            print("-" * 45)
            
            for row in results:
                data = dict(row)
                print(f"{data['user_id']:<10} {str(data['last_activity_date']):<15} {data['activity_count']}")
        else:
            print("\n⚠️  No user activity found in last 7 days")
            
    except Exception as e:
        print(f"\n❌ Error checking activity: {str(e)}")


def generate_gcloud_commands():
    """Generate gcloud commands for manual checking"""
    print_section("GCLOUD DIAGNOSTIC COMMANDS")
    
    print("\nRun these commands to check Cloud Scheduler:\n")
    
    commands = [
        ("Check if scheduler job exists", 
         "gcloud scheduler jobs list"),
        
        ("Get job details",
         "gcloud scheduler jobs describe daily-recommendations --location=us-central1"),
        
        ("Check recent logs (last 1 hour)",
         'gcloud logging read "resource.type=cloud_run_revision AND (textPayload=~\\"daily recommendations\\" OR textPayload=~\\"cron\\")" --limit 50 --format json --freshness=1h'),
        
        ("Check logs around 11 AM UTC today",
         'gcloud logging read "resource.type=cloud_run_revision AND textPayload=~\\"daily recommendations\\" AND timestamp>=\\"' + 
         datetime.now().strftime('%Y-%m-%d') + 'T10:55:00Z\\" AND timestamp<=\\"' + 
         datetime.now().strftime('%Y-%m-%d') + 'T11:15:00Z\\"" --format json'),
        
        ("Manually trigger the cron job (for testing)",
         "gcloud scheduler jobs run daily-recommendations --location=us-central1"),
    ]
    
    for desc, cmd in commands:
        print(f"\n{desc}:")
        print(f"  {cmd}")


def main():
    """Run all diagnostic checks"""
    print("\n")
    print("╔" + "="*58 + "╗")
    print("║  LLM RECOMMENDATIONS AUTO-GENERATION DIAGNOSTIC TOOL     ║")
    print("╚" + "="*58 + "╝")
    
    # Database checks
    check_timezone_settings()
    check_user_activity()
    check_recent_recommendations()
    check_recommendation_gaps()
    check_cron_execution_logs()
    
    # Cloud infrastructure checks
    generate_gcloud_commands()
    
    print_section("SUMMARY & RECOMMENDATIONS")
    print("""
To complete the investigation:

1. Run the gcloud commands above to check Cloud Scheduler
2. Check application logs around 11:00 AM UTC (3-4 AM Pacific)
3. Verify the scheduler job is enabled and not paused
4. Check for any API key or authentication issues in logs

Common Issues:
- Cloud Scheduler job disabled or deleted
- Authentication header validation failing
- Anthropic API key missing or invalid
- Database connection issues during cron execution
- No active users meeting criteria (activity in last 7 days)

Next Steps:
- Review Cloud Run logs for errors
- Manually trigger cron job for testing
- Verify ANTHROPIC_API_KEY environment variable is set
""")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nDiagnostic cancelled by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n\n❌ Fatal error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)







