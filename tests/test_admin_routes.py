#!/usr/bin/env python3
"""
Test Admin Routes Accessibility
Quick test to verify all ACWR admin routes are accessible
"""

import requests
import json
from urllib.parse import urljoin

def test_admin_routes():
    """Test all ACWR admin routes"""
    
    # Base URL - update this to your deployed URL
    base_url = "https://yourtrainingmonkey.com"
    
    # Routes to test
    routes_to_test = [
        # ACWR Configuration Admin
        "/admin/acwr-configuration",
        "/api/admin/acwr-configurations",
        
        # ACWR Feature Flags Admin  
        "/admin/acwr-feature-flags",
        "/api/admin/acwr-feature-flags",
        "/api/admin/acwr-feature-flags/status",
        
        # ACWR Migration Admin (correct URLs with prefix)
        "/admin/migration/",
        "/admin/migration/create",
        "/admin/migration/history",
        
        # General Feature Flags (existing)
        "/api/admin/feature-flags",
        
        # ACWR Visualization
        "/admin/acwr-visualization",
        "/api/admin/acwr-visualization/users",
        "/api/admin/acwr-visualization/configurations"
    ]
    
    results = {}
    
    print("🔍 Testing ACWR Admin Routes...")
    print("=" * 50)
    
    for route in routes_to_test:
        url = urljoin(base_url, route)
        try:
            response = requests.get(url, timeout=10)
            status = "✅" if response.status_code < 400 else "❌"
            results[route] = {
                'status_code': response.status_code,
                'accessible': response.status_code < 400,
                'content_type': response.headers.get('content-type', 'unknown')
            }
            print(f"{status} {route} - {response.status_code}")
            
        except requests.exceptions.RequestException as e:
            status = "❌"
            results[route] = {
                'status_code': 'ERROR',
                'accessible': False,
                'error': str(e)
            }
            print(f"{status} {route} - ERROR: {str(e)}")
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 ROUTE TEST SUMMARY")
    print("=" * 50)
    
    accessible_count = sum(1 for r in results.values() if r['accessible'])
    total_count = len(results)
    
    print(f"Accessible Routes: {accessible_count}/{total_count}")
    
    if accessible_count == total_count:
        print("🎉 ALL ROUTES ACCESSIBLE!")
    else:
        print("⚠️  SOME ROUTES INACCESSIBLE:")
        for route, result in results.items():
            if not result['accessible']:
                print(f"  ❌ {route} - {result.get('status_code', 'ERROR')}")
    
    return results

if __name__ == "__main__":
    test_admin_routes()
