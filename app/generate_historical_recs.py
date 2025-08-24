# Create a script to generate missing historical recommendations
# Run this manually to populate the missing dates: generate_historical_recs.py

import sys
import os
from datetime import datetime, timedelta

# Add the app directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from strava_app import generate_daily_recommendation_only
from db_utils import execute_query
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def generate_missing_historical_recommendations(user_id=1):
    """Generate recommendations for dates that are missing proper target_date entries."""

    # List of dates that should have recommendations
    dates_to_check = [
        '2025-08-05', '2025-08-06', '2025-08-07', '2025-08-08',
        '2025-08-09', '2025-08-10', '2025-08-11'
    ]

    for date_str in dates_to_check:
        # Check if recommendation exists for this target_date
        existing = execute_query(
            """
            SELECT COUNT(*) as count 
            FROM llm_recommendations 
            WHERE user_id = ? AND target_date = ?
            """,
            (user_id, date_str),
            fetch=True
        )

        if existing and dict(existing[0])['count'] > 0:
            logger.info(f"✅ Recommendation already exists for {date_str}")
            continue

        logger.info(f"🔄 Generating missing recommendation for {date_str}")

        try:
            # Generate a specific recommendation for this date
            recommendation = generate_daily_recommendation_only(user_id, target_date=date_str)

            if recommendation:
                logger.info(f"✅ Generated recommendation for {date_str}")
            else:
                logger.error(f"❌ Failed to generate recommendation for {date_str}")

        except Exception as e:
            logger.error(f"❌ Error generating recommendation for {date_str}: {str(e)}")

    # Verify results
    logger.info("\n📊 Final verification:")
    for date_str in dates_to_check:
        count_result = execute_query(
            """
            SELECT COUNT(*) as count 
            FROM llm_recommendations 
            WHERE user_id = ? AND target_date = ?
            """,
            (user_id, date_str),
            fetch=True
        )

        count = dict(count_result[0])['count'] if count_result else 0
        status = "✅ EXISTS" if count > 0 else "❌ MISSING"
        logger.info(f"  {date_str}: {status}")


if __name__ == "__main__":
    print("Generating missing historical recommendations...")
    generate_missing_historical_recommendations(user_id=1)
    print("Done!")

    # Optional: Check current database state
    print("\n📊 Current recommendations by target_date:")
    results = execute_query(
        """
        SELECT target_date, COUNT(*) as count
        FROM llm_recommendations 
        WHERE user_id = 1 AND target_date IS NOT NULL
        GROUP BY target_date
        ORDER BY target_date DESC
        """,
        fetch=True
    )

    if results:
        for row in results:
            row_dict = dict(row)
            print(f"  {row_dict['target_date']}: {row_dict['count']} recommendation(s)")
    else:
        print("  No recommendations found with target_date values")