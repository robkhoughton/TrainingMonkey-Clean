#!/usr/bin/env python3
"""
Simple Feature Flags Check
Tests the Python-based feature flags system without database dependencies
"""

import sys
import os

# Add the app directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def check_feature_flags():
    """Check feature flags system"""
    try:
        from utils.feature_flags import is_feature_enabled
        
        print("🔍 Testing Feature Flags System")
        print("=" * 40)
        
        # Test different users and features
        test_cases = [
            ('enhanced_acwr_calculation', 1, 'Admin (Rob)'),
            ('enhanced_acwr_calculation', 2, 'Beta User 2 (tballaine)'),
            ('enhanced_acwr_calculation', 3, 'Beta User 3 (iz.houghton)'),
            ('enhanced_acwr_calculation', 4, 'Regular User'),
            ('enhanced_trimp_calculation', 1, 'Admin TRIMP'),
            ('enhanced_trimp_calculation', 2, 'Beta User 2 TRIMP'),
            ('settings_page_enabled', 1, 'Admin Settings'),
            ('settings_page_enabled', 2, 'Beta User 2 Settings'),
        ]
        
        results = {}
        
        for feature, user_id, description in test_cases:
            try:
                enabled = is_feature_enabled(feature, user_id)
                status = "✅ ENABLED" if enabled else "❌ DISABLED"
                print(f"{status} {description}: {feature}")
                results[f"{feature}_user_{user_id}"] = enabled
            except Exception as e:
                print(f"❌ ERROR {description}: {feature} - {str(e)}")
                results[f"{feature}_user_{user_id}"] = False
        
        # Summary
        print("\n" + "=" * 40)
        print("📊 FEATURE FLAGS SUMMARY")
        print("=" * 40)
        
        acwr_enabled_count = sum(1 for k, v in results.items() if 'enhanced_acwr_calculation' in k and v)
        trimp_enabled_count = sum(1 for k, v in results.items() if 'enhanced_trimp_calculation' in k and v)
        settings_enabled_count = sum(1 for k, v in results.items() if 'settings_page_enabled' in k and v)
        
        print(f"Enhanced ACWR: {acwr_enabled_count}/4 users enabled")
        print(f"Enhanced TRIMP: {trimp_enabled_count}/2 users enabled") 
        print(f"Settings Page: {settings_enabled_count}/2 users enabled")
        
        # Check if beta rollout is working
        admin_acwr = results.get('enhanced_acwr_calculation_user_1', False)
        beta_2_acwr = results.get('enhanced_acwr_calculation_user_2', False)
        beta_3_acwr = results.get('enhanced_acwr_calculation_user_3', False)
        
        if admin_acwr and beta_2_acwr and beta_3_acwr:
            print("\n🎉 BETA ROLLOUT ACTIVE - Admin + Beta Users have ACWR access!")
        else:
            print("\n⚠️  BETA ROLLOUT INCOMPLETE - Some users missing ACWR access")
        
        return results
        
    except Exception as e:
        print(f"❌ Feature flags system error: {str(e)}")
        return {'error': str(e)}

if __name__ == "__main__":
    check_feature_flags()
