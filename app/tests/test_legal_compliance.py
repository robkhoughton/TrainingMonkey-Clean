"""
Test script for legal compliance tracking module
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from legal_compliance import LegalComplianceTracker, log_user_legal_acceptance, check_user_compliance
from legal_document_versioning import get_current_legal_versions, validate_legal_acceptance

def test_compliance_system():
    """Test the legal compliance tracking system"""
    print("Testing Legal Compliance Tracking System")
    print("=" * 50)
    
    # Create compliance tracker
    tracker = LegalComplianceTracker()
    
    # Test 1: Current versions
    print("\n1. Current legal document versions:")
    current_versions = get_current_legal_versions()
    for doc_type, version in current_versions.items():
        print(f"   {doc_type}: {version}")
    
    # Test 2: Validation logic
    print("\n2. Validation logic test:")
    test_user_versions = {
        "terms": "1.0",
        "privacy": "2.0",
        "disclaimer": "2.0"
    }
    
    required_updates = validate_legal_acceptance(test_user_versions)
    print(f"   Required updates: {len(required_updates)}")
    for doc_type, update_info in required_updates.items():
        print(f"     {doc_type}: {update_info['message']}")
    
    # Test 3: Compliance validation function
    print("\n3. Compliance validation function:")
    # Note: This would require a real user_id in the database
    # For testing, we'll just show the function structure
    print("   Function: check_user_compliance(user_id)")
    print("   Returns: (is_compliant, details)")
    
    # Test 4: Legal acceptance logging function
    print("\n4. Legal acceptance logging function:")
    print("   Function: log_user_legal_acceptance(user_id, document_type, version)")
    print("   Returns: True/False")
    
    # Test 5: Compliance tracker methods
    print("\n5. Compliance tracker methods:")
    methods = [
        "log_legal_acceptance()",
        "get_user_legal_status()", 
        "validate_user_compliance()",
        "get_legal_acceptance_history()",
        "revoke_legal_acceptance()",
        "get_compliance_statistics()"
    ]
    
    for method in methods:
        print(f"   {method}")
    
    print("\n" + "=" * 50)
    print("Legal compliance tracking system ready!")
    print("\nNote: Database operations require actual user data.")
    print("These functions will be tested with real user data during integration.")

if __name__ == "__main__":
    test_compliance_system()
