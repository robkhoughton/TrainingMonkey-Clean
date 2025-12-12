#!/usr/bin/env python3
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from db_credentials_loader import set_database_url
set_database_url()
import db_utils

output = []

# QUERY 1
output.append("="*80)
output.append("QUERY 1: FIELD POPULATION COUNT")
output.append("="*80)

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
    output.append(f"\nTotal Users: {t}\n")
    output.append(f"Primary Sport:         {r['has_primary_sport']} ({r['has_primary_sport']/t*100:.1f}%)")
    output.append(f"Secondary Sport:       {r['has_secondary_sport']} ({r['has_secondary_sport']/t*100:.1f}%)")
    output.append(f"Training Experience:   {r['has_experience']} ({r['has_experience']/t*100:.1f}%)")
    output.append(f"Weekly Training Hours: {r['has_weekly_hours']} ({r['has_weekly_hours']/t*100:.1f}%)")
    output.append(f"Current Phase:         {r['has_current_phase']} ({r['has_current_phase']/t*100:.1f}%)")
    output.append(f"Legacy Race Date:      {r['has_legacy_race_date']} ({r['has_legacy_race_date']/t*100:.1f}%) ⚠️ DEPRECATED")
    output.append(f"Detailed Schedule:     {r['has_detailed_schedule']} ({r['has_detailed_schedule']/t*100:.1f}%)")

# QUERY 2
output.append("\n" + "="*80)
output.append("QUERY 2: USERS WITH LEGACY RACE GOAL DATE")
output.append("="*80)

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
    output.append(f"\nFound {len(q2)} users with legacy race_goal_date:\n")
    for r in q2:
        output.append(f"User {r['user_id']} | {r['email']}")
        output.append(f"  Race Date: {r['race_goal_date']} | Phase: {r['current_phase'] or 'None'}")
        output.append(f"  Sport: {r['primary_sport'] or 'None'} | Experience: {r['training_experience'] or 'None'}")
        output.append(f"  Hours/Week: {r['weekly_training_hours'] or 'None'}")
        output.append(f"  New race_goals table: {r['race_goals_count']} entries")
        output.append(f"  STATUS: {'⚠️ CONFLICT' if r['race_goals_count'] > 0 else '📋 NEEDS MIGRATION'}")
        output.append("")
else:
    output.append("\n✓ No users have legacy race_goal_date set\n")

output.append("="*80)

# Write to file in parent directory
output_text = '\n'.join(output)
with open('../QUERY_RESULTS.txt', 'w', encoding='utf-8') as f:
    f.write(output_text)

print("Query results written to QUERY_RESULTS.txt")
print(output_text)


