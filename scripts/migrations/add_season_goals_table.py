# scripts/migrations/add_season_goals_table.py
"""
Adds the season_goals table: non-race season goals (fitness, weight loss,
base-building) that live alongside race_goals rather than inside it.

Why a separate table instead of extending race_goals: race_name and race_date
are NOT NULL on race_goals, and ~10 files read that table assuming a race
exists (readiness engine, weekly-plan logic, chat context loaders). A
separate table means every existing race_goals consumer is unaffected by
construction, and season-goal *presence* (race or non-race) is exposed
through one new helper — coach_recommendations.has_season_goal() — rather
than by touching race_goals' constraints or its ~10 call sites.

See .scratch/model-confidence-redesign/issues/01-non-race-season-goals.md
"""
from dotenv import load_dotenv
load_dotenv('.env')
from db_credentials_loader import set_database_url
set_database_url()
import db_utils

check_query = """
    SELECT table_name FROM information_schema.tables
    WHERE table_name = 'season_goals'
"""
result = db_utils.execute_query(check_query, fetch=True)

if not result:
    db_utils.execute_query("""
        CREATE TABLE season_goals (
            id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL,
            goal_type VARCHAR(30) NOT NULL,
            name VARCHAR(255) NOT NULL,
            target_date DATE,
            notes TEXT,
            created_at TIMESTAMP DEFAULT NOW(),
            updated_at TIMESTAMP DEFAULT NOW()
        )
    """)
    db_utils.execute_query("""
        CREATE INDEX idx_season_goals_user_id ON season_goals(user_id)
    """)
    print("Table 'season_goals' created successfully")
else:
    print("Table 'season_goals' already exists")
