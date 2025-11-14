#!/usr/bin/env python3
"""
User Analytics Report Generator for TrainingMonkey
Analyzes user demographics, usage patterns, and feature adoption
"""

import psycopg2
import json
from datetime import datetime, timedelta
from collections import defaultdict

# Connect to database
conn = psycopg2.connect('postgresql://appuser:trainmonk25@35.223.144.85:5432/train-d')
cur = conn.cursor()

print("=" * 80)
print("TRAININGMONKEY USER ANALYTICS REPORT")
print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("=" * 80)

# === SECTION 1: DATABASE SCHEMA OVERVIEW ===
print("\n" + "=" * 80)
print("SECTION 1: DATABASE SCHEMA")
print("=" * 80)

cur.execute("""
    SELECT table_name 
    FROM information_schema.tables 
    WHERE table_schema = 'public'
    ORDER BY table_name;
""")
tables = cur.fetchall()
print(f"\nTotal tables: {len(tables)}")
print("\nAvailable tables:")
for table in tables:
    print(f"  - {table[0]}")

print("\n--- Users Table Schema ---")
cur.execute("""
    SELECT column_name, data_type 
    FROM information_schema.columns 
    WHERE table_name = 'users'
    ORDER BY ordinal_position;
""")
columns = cur.fetchall()
for col in columns:
    print(f"  {col[0]}: {col[1]}")

print("\n--- User Settings Table Schema ---")
cur.execute("""
    SELECT column_name, data_type 
    FROM information_schema.columns 
    WHERE table_name = 'user_settings'
    ORDER BY ordinal_position;
""")
user_settings_cols = cur.fetchall()
if user_settings_cols:
    for col in user_settings_cols:
        print(f"  {col[0]}: {col[1]}")
else:
    print("  (Table not found or empty)")

print("\n--- Activities Table Schema ---")
cur.execute("""
    SELECT column_name, data_type 
    FROM information_schema.columns 
    WHERE table_name = 'activities'
    ORDER BY ordinal_position;
""")
activities_cols = cur.fetchall()
if activities_cols:
    for col in activities_cols:
        print(f"  {col[0]}: {col[1]}")
else:
    print("  (Table not found or empty)")

# Check if activities has user_id or email to link to users
cur.execute("""
    SELECT column_name 
    FROM information_schema.columns 
    WHERE table_name = 'activities' 
    AND column_name IN ('user_id', 'email', 'athlete_id', 'strava_athlete_id');
""")
activity_link_fields = [row[0] for row in cur.fetchall()]
print(f"\n--- Activity-User Link Fields: {activity_link_fields if activity_link_fields else 'None found'} ---")

# === SECTION 2: USER BASE OVERVIEW ===
print("\n" + "=" * 80)
print("SECTION 2: USER BASE OVERVIEW")
print("=" * 80)

# Total users - check both tables
cur.execute("SELECT COUNT(*) FROM users;")
users_table_count = cur.fetchone()[0]
cur.execute("SELECT COUNT(*) FROM user_settings;")
settings_table_count = cur.fetchone()[0]

print(f"\nUsers in 'users' table: {users_table_count}")
print(f"Users in 'user_settings' table: {settings_table_count}")

# Use the table with actual data
total_users = max(users_table_count, settings_table_count)
user_table_name = 'user_settings' if settings_table_count > users_table_count else 'users'
print(f"\n**Using '{user_table_name}' table as primary user source**")
print(f"Total Users: {total_users}")

# Users with account creation date (use registration_date from user_settings if available)
if user_table_name == 'user_settings':
    date_field = 'registration_date'
else:
    date_field = 'created_at'

cur.execute(f"""
    SELECT 
        COUNT(*) as total,
        MIN({date_field}) as first_user,
        MAX({date_field}) as latest_user,
        AVG(EXTRACT(EPOCH FROM (NOW() - {date_field}))/86400) as avg_days_active
    FROM {user_table_name}
    WHERE {date_field} IS NOT NULL;
""")
result = cur.fetchone()
if result[0]:
    print(f"\n  Users with creation date: {result[0]}")
    print(f"  First user signup: {result[1]}")
    print(f"  Latest user signup: {result[2]}")
    print(f"  Average account age: {result[3]:.1f} days")

# User cohorts by signup date
print("\n--- User Cohorts (by signup month) ---")
cur.execute(f"""
    SELECT 
        TO_CHAR({date_field}, 'YYYY-MM') as signup_month,
        COUNT(*) as users
    FROM {user_table_name}
    WHERE {date_field} IS NOT NULL
    GROUP BY signup_month
    ORDER BY signup_month DESC
    LIMIT 12;
""")
cohorts = cur.fetchall()
for cohort in cohorts:
    print(f"  {cohort[0]}: {cohort[1]} users")

# === SECTION 3: USER DEMOGRAPHICS ===
print("\n" + "=" * 80)
print("SECTION 3: USER DEMOGRAPHICS")
print("=" * 80)

# Check users table fields
cur.execute("SELECT COUNT(*) FROM users WHERE email IS NOT NULL AND email != '';")
users_with_email = cur.fetchone()[0]
print(f"\nUsers with email: {users_with_email}")

# Check for gender distribution
cur.execute("""
    SELECT 
        COALESCE(gender, 'Not Set') as gender,
        COUNT(*) as users,
        ROUND(100.0 * COUNT(*) / NULLIF((SELECT COUNT(*) FROM users), 0), 1) as percentage
    FROM users
    GROUP BY gender
    ORDER BY users DESC;
""")
genders = cur.fetchall()
if genders:
    print("\n--- Gender Distribution ---")
    for gender in genders:
        print(f"  {gender[0]}: {gender[1]} users ({gender[2] or 0}%)")

# Check HR metrics
cur.execute("SELECT COUNT(*) FROM users WHERE resting_hr IS NOT NULL;")
users_with_rhr = cur.fetchone()[0]
cur.execute("SELECT COUNT(*) FROM users WHERE max_hr IS NOT NULL;")
users_with_maxhr = cur.fetchone()[0]
print(f"\nUsers with resting HR set: {users_with_rhr}")
print(f"Users with max HR set: {users_with_maxhr}")

# Check user_settings table for additional demographics
cur.execute("""
    SELECT EXISTS (
        SELECT FROM information_schema.tables 
        WHERE table_name = 'user_settings'
    );
""")
has_user_settings = cur.fetchone()[0]

if has_user_settings:
    cur.execute("""
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name = 'user_settings';
    """)
    settings_fields = [row[0] for row in cur.fetchall()]
    
    if 'strava_athlete_id' in settings_fields or 'strava_id' in settings_fields:
        strava_field = 'strava_athlete_id' if 'strava_athlete_id' in settings_fields else 'strava_id'
        cur.execute(f"""
            SELECT COUNT(*) 
            FROM user_settings 
            WHERE {strava_field} IS NOT NULL;
        """)
        print(f"\nUsers with Strava connected: {cur.fetchone()[0]}")
    
    if 'primary_sport' in settings_fields:
        print("\n--- Primary Sport Distribution (from user_settings) ---")
        cur.execute("""
            SELECT 
                COALESCE(primary_sport, 'Not Set') as sport,
                COUNT(*) as users
            FROM user_settings
            GROUP BY primary_sport
            ORDER BY users DESC;
        """)
        sports = cur.fetchall()
        for sport in sports:
            print(f"  {sport[0]}: {sport[1]} users")
    
    if 'timezone' in settings_fields:
        print("\n--- Timezone Distribution (Top 10) ---")
        cur.execute("""
            SELECT 
                COALESCE(timezone, 'Not Set') as tz,
                COUNT(*) as users
            FROM user_settings
            GROUP BY timezone
            ORDER BY users DESC
            LIMIT 10;
        """)
        timezones = cur.fetchall()
        for tz in timezones:
            print(f"  {tz[0]}: {tz[1]} users")

# === SECTION 4: ACTIVITY DATA ANALYSIS ===
print("\n" + "=" * 80)
print("SECTION 4: ACTIVITY DATA ANALYSIS")
print("=" * 80)

# Check for activities table
cur.execute("""
    SELECT EXISTS (
        SELECT FROM information_schema.tables 
        WHERE table_name = 'activities'
    );
""")
has_activities = cur.fetchone()[0]

if has_activities:
    cur.execute("""
        SELECT 
            COUNT(DISTINCT user_id) as active_users,
            COUNT(*) as total_activities,
            MIN(date) as first_activity,
            MAX(date) as latest_activity
        FROM activities;
    """)
    result = cur.fetchone()
    print(f"\nUsers with activities: {result[0]} ({100.0*result[0]/total_users:.1f}%)")
    print(f"Total activities logged: {result[1]}")
    print(f"First activity: {result[2]}")
    print(f"Latest activity: {result[3]}")
    
    # Activities per user
    print("\n--- Activities per User Distribution ---")
    cur.execute(f"""
        SELECT 
            range,
            users
        FROM (
            SELECT 
                CASE 
                    WHEN activity_count = 0 THEN '0 activities'
                    WHEN activity_count BETWEEN 1 AND 5 THEN '1-5 activities'
                    WHEN activity_count BETWEEN 6 AND 20 THEN '6-20 activities'
                    WHEN activity_count BETWEEN 21 AND 50 THEN '21-50 activities'
                    WHEN activity_count BETWEEN 51 AND 100 THEN '51-100 activities'
                    ELSE '100+ activities'
                END as range,
                CASE 
                    WHEN activity_count = 0 THEN 0
                    WHEN activity_count BETWEEN 1 AND 5 THEN 1
                    WHEN activity_count BETWEEN 6 AND 20 THEN 2
                    WHEN activity_count BETWEEN 21 AND 50 THEN 3
                    WHEN activity_count BETWEEN 51 AND 100 THEN 4
                    ELSE 5
                END as sort_order,
                COUNT(*) as users
            FROM (
                SELECT 
                    u.id,
                    COUNT(a.activity_id) as activity_count
                FROM {user_table_name} u
                LEFT JOIN activities a ON u.id = a.user_id
                GROUP BY u.id
            ) user_activities
            GROUP BY range, sort_order
        ) sorted
        ORDER BY sort_order;
    """)
    activity_dist = cur.fetchall()
    for dist in activity_dist:
        print(f"  {dist[0]}: {dist[1]} users")
    
    # Recent activity (last 30 days)
    print("\n--- Recent Activity (Last 30 Days) ---")
    cur.execute("""
        SELECT 
            COUNT(DISTINCT user_id) as active_users,
            COUNT(*) as activities
        FROM activities
        WHERE date >= NOW() - INTERVAL '30 days';
    """)
    result = cur.fetchone()
    print(f"  Active users (30d): {result[0]} ({100.0*result[0]/total_users:.1f}% of total)")
    print(f"  Activities (30d): {result[1]}")
    
    # Sport type distribution in activities
    print("\n--- Activity Types (from activities table) ---")
    cur.execute("""
        SELECT 
            COALESCE(sport_type, 'Unknown') as sport,
            COUNT(*) as activities,
            COUNT(DISTINCT user_id) as users
        FROM activities
        GROUP BY sport_type
        ORDER BY activities DESC
        LIMIT 10;
    """)
    activity_sports = cur.fetchall()
    for sport in activity_sports:
        print(f"  {sport[0]}: {sport[1]} activities from {sport[2]} users")

# === SECTION 5: FEATURE ADOPTION ===
print("\n" + "=" * 80)
print("SECTION 5: FEATURE ADOPTION")
print("=" * 80)

# Check for journal entries
cur.execute("""
    SELECT EXISTS (
        SELECT FROM information_schema.tables 
        WHERE table_name = 'journal_entries'
    );
""")
has_journal = cur.fetchone()[0]

if has_journal:
    cur.execute("""
        SELECT 
            COUNT(DISTINCT user_id) as users_with_journals,
            COUNT(*) as total_entries
        FROM journal_entries;
    """)
    result = cur.fetchone()
    print(f"\nTraining Journal:")
    print(f"  Users with journal entries: {result[0]} ({100.0*result[0]/total_users:.1f}%)")
    print(f"  Total journal entries: {result[1]}")
    
    if result[0] > 0:
        cur.execute("""
            SELECT 
                AVG(entry_count) as avg_entries,
                MAX(entry_count) as max_entries
            FROM (
                SELECT user_id, COUNT(*) as entry_count
                FROM journal_entries
                GROUP BY user_id
            ) user_entries;
        """)
        result = cur.fetchone()
        print(f"  Avg entries per user (who use it): {result[0]:.1f}")
        print(f"  Max entries by a user: {result[1]}")

# Check for planned workouts
cur.execute("""
    SELECT EXISTS (
        SELECT FROM information_schema.tables 
        WHERE table_name = 'planned_workouts'
    );
""")
has_planned = cur.fetchone()[0]

if has_planned:
    cur.execute("""
        SELECT 
            COUNT(DISTINCT user_id) as users_with_plans,
            COUNT(*) as total_plans
        FROM planned_workouts;
    """)
    result = cur.fetchone()
    print(f"\nPlanned Workouts:")
    print(f"  Users with planned workouts: {result[0]} ({100.0*result[0]/total_users:.1f}%)")
    print(f"  Total planned workouts: {result[1]}")

# Check for LLM recommendations
cur.execute("""
    SELECT EXISTS (
        SELECT FROM information_schema.tables 
        WHERE table_name = 'llm_recommendations'
    );
""")
has_llm = cur.fetchone()[0]

if has_llm:
    cur.execute("""
        SELECT 
            COUNT(DISTINCT user_id) as users_with_recs,
            COUNT(*) as total_recs
        FROM llm_recommendations;
    """)
    result = cur.fetchone()
    print(f"\nLLM Recommendations:")
    print(f"  Users with LLM recommendations: {result[0]} ({100.0*result[0]/total_users:.1f}%)")
    print(f"  Total recommendations generated: {result[1]}")

# === SECTION 6: ENGAGEMENT METRICS ===
print("\n" + "=" * 80)
print("SECTION 6: USER ENGAGEMENT SEGMENTATION")
print("=" * 80)

# Segment users by engagement level
if has_activities:
    print("\n--- User Engagement Segments ---")
    date_col = 'registration_date' if user_table_name == 'user_settings' else 'created_at'
    cur.execute(f"""
        WITH user_metrics AS (
            SELECT 
                u.id,
                u.{date_col},
                COUNT(DISTINCT a.activity_id) as total_activities,
                MAX(a.date) as last_date,
                EXTRACT(EPOCH FROM (NOW() - MAX(a.date)))/86400 as days_since_last_activity
            FROM {user_table_name} u
            LEFT JOIN activities a ON u.id = a.user_id
            GROUP BY u.id, u.{date_col}
        )
        SELECT 
            segment,
            users,
            percentage
        FROM (
            SELECT 
                CASE 
                    WHEN total_activities = 0 THEN 'Never Active'
                    WHEN days_since_last_activity <= 7 THEN 'Highly Active (< 7d)'
                    WHEN days_since_last_activity <= 30 THEN 'Active (< 30d)'
                    WHEN days_since_last_activity <= 90 THEN 'At Risk (30-90d)'
                    ELSE 'Churned (> 90d)'
                END as segment,
                CASE 
                    WHEN total_activities = 0 THEN 5
                    WHEN days_since_last_activity <= 7 THEN 1
                    WHEN days_since_last_activity <= 30 THEN 2
                    WHEN days_since_last_activity <= 90 THEN 3
                    ELSE 4
                END as sort_order,
                COUNT(*) as users,
                ROUND(100.0 * COUNT(*) / (SELECT COUNT(*) FROM {user_table_name}), 1) as percentage
            FROM user_metrics
            GROUP BY segment, sort_order
        ) sorted
        ORDER BY sort_order;
    """)
    segments = cur.fetchall()
    for seg in segments:
        print(f"  {seg[0]}: {seg[1]} users ({seg[2]}%)")

# === SECTION 7: FEATURE GAP ANALYSIS ===
print("\n" + "=" * 80)
print("SECTION 7: FEATURE GAP ANALYSIS")
print("=" * 80)
print("\nUsers NOT using key features:")

if has_activities:
    if user_table_name == 'user_settings':
        cur.execute("""
            SELECT COUNT(*) 
            FROM user_settings u
            LEFT JOIN activities a ON u.id = a.user_id
            WHERE a.activity_id IS NULL;
        """)
    else:
        cur.execute("""
            SELECT COUNT(*) 
            FROM users u
            LEFT JOIN activities a ON u.id = a.user_id
            WHERE a.activity_id IS NULL;
        """)
    print(f"  No activities logged: {cur.fetchone()[0]} users")

if has_journal:
    if user_table_name == 'user_settings':
        cur.execute("""
            SELECT COUNT(DISTINCT u.id)
            FROM user_settings u
            LEFT JOIN journal_entries j ON u.id = j.user_id
            WHERE j.id IS NULL;
        """)
    else:
        cur.execute("""
            SELECT COUNT(DISTINCT u.id)
            FROM users u
            LEFT JOIN journal_entries j ON u.id = j.user_id
            WHERE j.id IS NULL;
        """)
    print(f"  No journal entries: {cur.fetchone()[0]} users")

if has_planned:
    if user_table_name == 'user_settings':
        cur.execute("""
            SELECT COUNT(DISTINCT u.id)
            FROM user_settings u
            LEFT JOIN planned_workouts p ON u.id = p.user_id
            WHERE p.id IS NULL;
        """)
    else:
        cur.execute("""
            SELECT COUNT(DISTINCT u.id)
            FROM users u
            LEFT JOIN planned_workouts p ON u.id = p.user_id
            WHERE p.id IS NULL;
        """)
    print(f"  No planned workouts: {cur.fetchone()[0]} users")

if has_llm:
    if user_table_name == 'user_settings':
        cur.execute("""
            SELECT COUNT(DISTINCT u.id)
            FROM user_settings u
            LEFT JOIN llm_recommendations r ON u.id = r.user_id
            WHERE r.id IS NULL;
        """)
    else:
        cur.execute("""
            SELECT COUNT(DISTINCT u.id)
            FROM users u
            LEFT JOIN llm_recommendations r ON u.id = r.user_id
            WHERE r.id IS NULL;
        """)
    print(f"  No LLM recommendations: {cur.fetchone()[0]} users")

# === SECTION 8: TOP USERS ===
print("\n" + "=" * 80)
print("SECTION 8: TOP USERS (POWER USERS)")
print("=" * 80)

if has_activities:
    print("\n--- Top 20 Users by Activity Count ---")
    cur.execute(f"""
        SELECT 
            u.id,
            u.email,
            COUNT(a.activity_id) as activity_count,
            MIN(a.date) as first_activity,
            MAX(a.date) as last_activity,
            (MAX(a.date) - MIN(a.date)) as active_days
        FROM {user_table_name} u
        JOIN activities a ON u.id = a.user_id
        GROUP BY u.id, u.email
        ORDER BY activity_count DESC
        LIMIT 20;
    """)
    top_users = cur.fetchall()
    for i, user in enumerate(top_users, 1):
        email_display = user[1][:30] + "..." if user[1] and len(user[1]) > 30 else user[1] or "N/A"
        print(f"  {i}. User {user[0]} ({email_display})")
        print(f"      Activities: {user[2]}, Active days: {user[5]:.0f}, Last activity: {user[4]}")

# === SECTION 9: RECOMMENDATIONS ===
print("\n" + "=" * 80)
print("SECTION 9: KEY INSIGHTS & RECOMMENDATIONS")
print("=" * 80)

# Calculate key metrics for recommendations
cur.execute("SELECT COUNT(*) FROM users;")
total = cur.fetchone()[0]

# Check for Strava connections in user_settings if it exists
with_strava = 0
if has_user_settings:
    cur.execute("""
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name = 'user_settings' 
        AND column_name IN ('strava_athlete_id', 'strava_id');
    """)
    strava_cols = cur.fetchall()
    if strava_cols:
        strava_field = strava_cols[0][0]
        cur.execute(f"""
            SELECT COUNT(*) 
            FROM user_settings 
            WHERE {strava_field} IS NOT NULL;
        """)
        with_strava = cur.fetchone()[0]

user_stats = (total, with_strava)

if has_activities:
    cur.execute("""
        SELECT COUNT(DISTINCT user_id)
        FROM activities
        WHERE date >= NOW() - INTERVAL '30 days';
    """)
    active_30d = cur.fetchone()[0]
    
    cur.execute(f"""
        SELECT COUNT(*)
        FROM {user_table_name} u
        LEFT JOIN activities a ON u.id = a.user_id
        WHERE a.activity_id IS NULL;
    """)
    no_activities = cur.fetchone()[0]
else:
    active_30d = 0
    no_activities = user_stats[0]

print("\n[USER BASE HEALTH]")
print(f"  - Total registered users: {user_stats[0]}")
if user_stats[0] > 0:
    print(f"  - Strava connection rate: {100.0*user_stats[1]/user_stats[0]:.1f}%")
    if has_activities:
        print(f"  - 30-day active rate: {100.0*active_30d/user_stats[0]:.1f}%")
        print(f"  - Users with no activities: {no_activities} ({100.0*no_activities/user_stats[0]:.1f}%)")
else:
    print("  - No users in database yet")

print("\n[RECOMMENDATIONS]")
if no_activities > user_stats[0] * 0.3:
    print(f"  1. HIGH PRIORITY: {no_activities} users have never logged activities")
    print("     - Improve onboarding flow")
    print("     - Send activation emails")
    print("     - Simplify Strava sync")

if has_journal:
    cur.execute(f"SELECT COUNT(DISTINCT u.id) FROM {user_table_name} u LEFT JOIN journal_entries j ON u.id = j.user_id WHERE j.id IS NULL;")
    no_journal = cur.fetchone()[0]
    if no_journal > user_stats[0] * 0.7:
        print(f"  2. Feature adoption: {no_journal} users haven't used the training journal")
        print("     - Highlight journal feature in dashboard")
        print("     - Provide templates or prompts")

if user_stats[1] < user_stats[0]:
    print(f"  3. Strava integration: {user_stats[0] - user_stats[1]} users without Strava")
    print("     - Emphasize Strava benefits")
    print("     - Support manual activity entry")

if has_activities and active_30d < user_stats[0] * 0.5:
    inactive = user_stats[0] - active_30d
    print(f"  4. Retention: {inactive} users inactive in last 30 days")
    print("     - Re-engagement email campaign")
    print("     - Identify churn reasons")

print("\n" + "=" * 80)
print("END OF REPORT")
print("=" * 80)

cur.close()
conn.close()

