#!/usr/bin/env python3
"""
Batch SQLite Placeholder Fixer
Fixes SQLite placeholders in multiple files at once
"""

import sys
import os
from pathlib import Path

# Import the fixer function
sys.path.append(os.path.dirname(__file__))
from fix_sqlite_placeholders import fix_sqlite_placeholders

def main():
    """Fix SQLite placeholders in multiple critical files"""
    
    # List of critical files to fix
    critical_files = [
        "app/llm_recommendations_module.py",
        "app/onboarding_manager.py", 
        "app/onboarding_completion_tracker.py",
        "app/onboarding_progress_tracker.py",
        "app/onboarding_tutorial_system.py",
        "app/progressive_feature_triggers.py",
        "app/registration_session_manager.py",
        "app/registration_status_tracker.py",
        "app/secure_token_storage.py",
        "app/settings_utils.py",
        "app/system_monitoring_dashboard.py",
        "app/tiered_feature_unlock.py",
        "app/unified_metrics_service.py",
        "app/user_account_manager.py",
        "app/email_validation.py",
        "app/enhanced_token_management.py",
        "app/elevation_migration_module.py",
        "app/generate_historical_recs.py",
        "app/historical_trimp_recalculation.py",
        "app/oauth_rate_limiter.py",
        "app/sync_fix.py"
    ]
    
    total_fixes = 0
    files_processed = 0
    
    print("🔧 Batch fixing SQLite placeholders in critical files...")
    print("=" * 60)
    
    for file_path in critical_files:
        if Path(file_path).exists():
            print(f"\n📁 Processing: {file_path}")
            fixes = fix_sqlite_placeholders(file_path)
            total_fixes += fixes
            files_processed += 1
        else:
            print(f"⚠️  File not found: {file_path}")
    
    print("\n" + "=" * 60)
    print(f"🎉 Batch processing complete!")
    print(f"📊 Files processed: {files_processed}")
    print(f"🔧 Total fixes applied: {total_fixes}")
    print(f"📋 Run validation to check results: python scripts/validate_sql_syntax.py")
    
    return total_fixes

if __name__ == '__main__':
    main()
