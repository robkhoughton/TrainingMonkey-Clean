#!/usr/bin/env python3
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from db_credentials_loader import set_database_url
set_database_url()
import db_utils

# QUERY 1
print("="*80)
print("QUERY 1: FIELD POPULATION COUNT")
print("="*80)

q1 = db_utils.execute_query("""
    SELECT 
        COUNT(*) as total_users,
        COUNT(primary_sport) as has_primary_sport,
        COUNT(secondary_sport) as has_secondary_sport,
        COUNT(training_experience) as has_experience,
        COUNT(weekly_training_hours) as has_weekly_hours,
        COUNT(current_phase) as has_current_phase,
        COUNT(race_goal_date) as has_legacy_race_date,
        COUNT(training_schedule_json) as has_detailed_schedule
    FROM user_settings
    WHERE email IS NOT NULL
""", fetch=True)

if q1:
    r = q1[0]
    t = r['total_users']
    print(f"\nTotal Users: {t}\n")
    print(f"Primary Sport:         {r['has_primary_sport']} ({r['has_primary_sport']/t*100:.1f}%)")
    print(f"Secondary Sport:       {r['has_secondary_sport']} ({r['has_secondary_sport']/t*100:.1f}%)")
    print(f"Training Experience:   {r['has_experience']} ({r['has_experience']/t*100:.1f}%)")
    print(f"Weekly Training Hours: {r['has_weekly_hours']} ({r['has_weekly_hours']/t*100:.1f}%)")
    print(f"Current Phase:         {r['has_current_phase']} ({r['has_current_phase']/t*100:.1f}%)")
    print(f"Legacy Race Date:      {r['has_legacy_race_date']} ({r['has_legacy_race_date']/t*100:.1f}%) ⚠️ DEPRECATED")
    print(f"Detailed Schedule:     {r['has_detailed_schedule']} ({r['has_detailed_schedule']/t*100:.1f}%)")

# QUERY 2
print("\n" + "="*80)
print("QUERY 2: USERS WITH LEGACY RACE GOAL DATE")
print("="*80)

q2 = db_utils.execute_query("""
    SELECT 
        id as user_id,
        email,
        race_goal_date,
        current_phase,
        weekly_training_hours,
        primary_sport,
        training_experience,
        (SELECT COUNT(*) FROM race_goals WHERE user_id = user_settings.id) as race_goals_count
    FROM user_settings
    WHERE race_goal_date IS NOT NULL
    ORDER BY race_goal_date ASC
""", fetch=True)

if q2:
    print(f"\nFound {len(q2)} users with legacy race_goal_date:\n")
    for r in q2:
        print(f"User {r['user_id']} | {r['email']}")
        print(f"  Race Date: {r['race_goal_date']} | Phase: {r['current_phase'] or 'None'}")
        print(f"  Sport: {r['primary_sport'] or 'None'} | Experience: {r['training_experience'] or 'None'}")
        print(f"  Hours/Week: {r['weekly_training_hours'] or 'None'}")
        print(f"  New race_goals table: {r['race_goals_count']} entries")
        print(f"  STATUS: {'⚠️ CONFLICT' if r['race_goals_count'] > 0 else '📋 NEEDS MIGRATION'}")
        print()
else:
    print("\n✓ No users have legacy race_goal_date set\n")

print("="*80)
sys.stdout.flush()


