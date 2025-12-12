#!/usr/bin/env python3
"""Direct database query execution"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from db_credentials_loader import set_database_url
set_database_url()
import db_utils

print("="*80)
print("QUERY 1: FIELD POPULATION COUNT")
print("="*80)

results = db_utils.execute_query("""
    SELECT 
        COUNT(*) as total_users,
        COUNT(primary_sport) as has_primary_sport,
        COUNT(secondary_sport) as has_secondary_sport,
        COUNT(training_experience) as has_experience,
        COUNT(weekly_training_hours) as has_weekly_hours,
        COUNT(current_phase) as has_current_phase,
        COUNT(race_goal_date) as has_legacy_race_date,
        COUNT(training_schedule_json) as has_detailed_schedule,
        COUNT(include_strength_training) as has_strength_config,
        COUNT(include_mobility) as has_mobility_config,
        COUNT(include_cross_training) as has_cross_training_config
    FROM user_settings
    WHERE email IS NOT NULL
""", fetch=True)

if results:
    row = results[0]
    total = row['total_users']
    print(f"\nTotal Users: {total}\n")
    print("Settings/Training Page Fields:")
    print(f"  Primary Sport:         {row['has_primary_sport']:3d} ({row['has_primary_sport']/total*100 if total > 0 else 0:.1f}%)")
    print(f"  Secondary Sport:       {row['has_secondary_sport']:3d} ({row['has_secondary_sport']/total*100 if total > 0 else 0:.1f}%)")
    print(f"  Training Experience:   {row['has_experience']:3d} ({row['has_experience']/total*100 if total > 0 else 0:.1f}%)")
    print(f"  Weekly Training Hours: {row['has_weekly_hours']:3d} ({row['has_weekly_hours']/total*100 if total > 0 else 0:.1f}%)")
    print(f"  Current Phase:         {row['has_current_phase']:3d} ({row['has_current_phase']/total*100 if total > 0 else 0:.1f}%)")
    print(f"  Legacy Race Date:      {row['has_legacy_race_date']:3d} ({row['has_legacy_race_date']/total*100 if total > 0 else 0:.1f}%) ⚠️  DEPRECATED")
    print("\nCoach Page Schedule Tab Fields:")
    print(f"  Detailed Schedule:     {row['has_detailed_schedule']:3d} ({row['has_detailed_schedule']/total*100 if total > 0 else 0:.1f}%)")
    print(f"  Strength Config:       {row['has_strength_config']:3d} ({row['has_strength_config']/total*100 if total > 0 else 0:.1f}%)")
    print(f"  Mobility Config:       {row['has_mobility_config']:3d} ({row['has_mobility_config']/total*100 if total > 0 else 0:.1f}%)")
    print(f"  Cross Training Config: {row['has_cross_training_config']:3d} ({row['has_cross_training_config']/total*100 if total > 0 else 0:.1f}%)")

print("\n" + "="*80)
print("QUERY 2: USERS WITH LEGACY RACE GOAL DATE")
print("="*80)

results = db_utils.execute_query("""
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

if results:
    print(f"\nFound {len(results)} users with legacy race_goal_date:\n")
    for row in results:
        print(f"User {row['user_id']:3d} | {row['email']}")
        print(f"  Legacy Race Date: {row['race_goal_date']}")
        print(f"  Sport: {row['primary_sport'] or 'None'} | Experience: {row['training_experience'] or 'None'}")
        print(f"  Weekly Hours: {row['weekly_training_hours'] or 'None'} | Phase: {row['current_phase'] or 'None'}")
        print(f"  New System: {row['race_goals_count']} race goal(s) in race_goals table")
        if row['race_goals_count'] > 0:
            print(f"  ⚠️  STATUS: CONFLICT - Has both legacy date AND new race goals")
        else:
            print(f"  📋 STATUS: NEEDS MIGRATION - Only has legacy race date")
        print()
else:
    print("\n✓ No users have legacy race_goal_date set\n")

print("="*80)


