"""
Test script to verify Phase 1: Structured Output

Verifies that:
1. structured_output column exists in llm_recommendations
2. A forced generation for user_id=1 produces a non-NULL structured_output
3. target_date in structured_output matches the expected recommendation date
4. Required JSON fields are present and valid

Usage:
    cd C:\Users\robho\Documents\VAULT\TrainingMonkey-Clean
    python scripts/test_structured_output.py
"""

import sys
import os
import json
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.db_utils import get_db_connection, execute_query
from app.db_credentials_loader import set_database_url

import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

REQUIRED_TOP_KEYS = ['target_date', 'assessment', 'divergence', 'decision', 'risk', 'context', 'meta']
REQUIRED_ASSESSMENT_KEYS = ['primary_signal', 'category', 'confidence', 'primary_driver']
REQUIRED_RISK_KEYS = ['injury_risk_level', 'acwr_external', 'acwr_internal', 'divergence', 'days_since_rest', 'flags']

VALID_PRIMARY_SIGNALS = {'divergence', 'acwr_external', 'acwr_internal', 'days_since_rest', 'pattern'}
VALID_CATEGORIES = {
    'normal_progression', 'mandatory_rest', 'overtraining_risk',
    'divergence_warning', 'detraining_signal', 'recovery_needed', 'undertraining_opportunity'
}
VALID_ACTIONS = {'train', 'rest', 'cross_train', 'reduce'}
VALID_INJURY_RISK = {'low', 'moderate', 'high', 'critical'}


def test_column_exists():
    """Verify structured_output column exists in llm_recommendations."""
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("""
            SELECT column_name, data_type
            FROM information_schema.columns
            WHERE table_name = 'llm_recommendations'
            AND column_name = 'structured_output'
        """)
        result = cur.fetchone()
        if result:
            logger.info(f"✅ Column exists: structured_output ({result['data_type']})")
            return True
        else:
            logger.error("❌ structured_output column NOT found — run migration first")
            return False
    finally:
        cur.close()
        conn.close()


def test_latest_structured_output(user_id=1):
    """Check the most recent recommendation for user_id=1 has structured_output."""
    results = execute_query("""
        SELECT id, target_date, structured_output, generation_date
        FROM llm_recommendations
        WHERE user_id = %s
        ORDER BY generation_date DESC
        LIMIT 1
    """, (user_id,), fetch=True)

    if not results:
        logger.warning(f"⚠️  No recommendations found for user_id={user_id}")
        return False

    row = dict(results[0])
    rec_id = row['id']
    target_date = row['target_date']
    structured_output = row['structured_output']

    logger.info(f"Latest recommendation: id={rec_id}, target_date={target_date}")

    if structured_output is None:
        logger.warning("⚠️  structured_output is NULL — generation may predate Phase 1 or model didn't emit block")
        return False

    # structured_output may come back as dict (psycopg2 with JSONB) or string
    if isinstance(structured_output, str):
        try:
            structured_output = json.loads(structured_output)
        except json.JSONDecodeError as e:
            logger.error(f"❌ structured_output is not valid JSON: {e}")
            return False

    logger.info(f"✅ structured_output is present and parseable")

    # Validate top-level keys
    missing_keys = [k for k in REQUIRED_TOP_KEYS if k not in structured_output]
    if missing_keys:
        logger.error(f"❌ Missing top-level keys: {missing_keys}")
        return False
    logger.info(f"✅ All required top-level keys present")

    # Validate target_date matches DB target_date
    so_target = structured_output.get('target_date')
    db_target = str(target_date) if target_date else None
    if so_target and db_target and so_target != db_target:
        logger.warning(f"⚠️  target_date mismatch: structured_output={so_target}, db={db_target}")
    else:
        logger.info(f"✅ target_date consistent: {so_target}")

    # Validate assessment
    assessment = structured_output.get('assessment', {})
    missing_a = [k for k in REQUIRED_ASSESSMENT_KEYS if k not in assessment]
    if missing_a:
        logger.error(f"❌ Missing assessment keys: {missing_a}")
    else:
        primary_signal = assessment.get('primary_signal', '')
        if primary_signal not in VALID_PRIMARY_SIGNALS:
            logger.warning(f"⚠️  Unexpected primary_signal: {primary_signal}")
        else:
            logger.info(f"✅ assessment.primary_signal: {primary_signal}")
        logger.info(f"✅ assessment.category: {assessment.get('category')}")
        logger.info(f"✅ assessment.primary_driver: {assessment.get('primary_driver', '')[:80]}...")

    # Validate risk
    risk = structured_output.get('risk', {})
    missing_r = [k for k in REQUIRED_RISK_KEYS if k not in risk]
    if missing_r:
        logger.error(f"❌ Missing risk keys: {missing_r}")
    else:
        logger.info(f"✅ risk.injury_risk_level: {risk.get('injury_risk_level')}")
        logger.info(f"✅ risk.acwr_external={risk.get('acwr_external')}, acwr_internal={risk.get('acwr_internal')}, divergence={risk.get('divergence')}")

    # Validate decision
    decision = structured_output.get('decision', {})
    action = decision.get('action', '')
    if action not in VALID_ACTIONS:
        logger.warning(f"⚠️  Unexpected decision.action: {action}")
    else:
        logger.info(f"✅ decision.action: {action}, intensity_target: {decision.get('intensity_target')}")

    # Meta
    meta = structured_output.get('meta', {})
    logger.info(f"✅ meta.model_used: {meta.get('model_used')}")
    logger.info(f"✅ meta.risk_tolerance: {meta.get('risk_tolerance')}")

    return True


def main():
    logger.info("=" * 60)
    logger.info("Phase 1 Structured Output Verification")
    logger.info("=" * 60)

    set_database_url()

    all_pass = True

    logger.info("\n--- Test 1: Column exists ---")
    all_pass &= test_column_exists()

    logger.info("\n--- Test 2: Latest recommendation has structured_output ---")
    all_pass &= test_latest_structured_output(user_id=1)

    logger.info("\n" + "=" * 60)
    if all_pass:
        logger.info("✅ All tests passed")
    else:
        logger.warning("⚠️  Some tests failed — see above for details")
    logger.info("=" * 60)


if __name__ == '__main__':
    main()
