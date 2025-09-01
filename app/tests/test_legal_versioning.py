"""
Test script for legal document versioning system
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from legal_document_versioning import LegalDocumentVersioning, validate_legal_acceptance, get_current_legal_versions

def test_versioning_system():
    """Test the legal document versioning system"""
    print("Testing Legal Document Versioning System")
    print("=" * 50)
    
    # Create versioning instance
    versioning = LegalDocumentVersioning()
    
    # Test 1: Get current versions
    print("\n1. Current versions:")
    current_versions = get_current_legal_versions()
    for doc_type, version in current_versions.items():
        print(f"   {doc_type}: {version}")
    
    # Test 2: Validate user acceptance
    print("\n2. User acceptance validation:")
    test_user_versions = {
        "terms": "1.0",
        "privacy": "2.0", 
        "disclaimer": "2.0"
    }
    
    required_updates = validate_legal_acceptance(test_user_versions)
    for doc_type, update_info in required_updates.items():
        print(f"   {doc_type}: {update_info['message']}")
        print(f"     Current: {update_info['current_version']}")
        print(f"     User: {update_info['user_version']}")
        print(f"     Changes: {', '.join(update_info['changes'][:2])}...")
    
    # Test 3: Get document info
    print("\n3. Document information:")
    for doc_type in ["terms", "privacy", "disclaimer"]:
        info = versioning.get_document_info(doc_type)
        print(f"   {doc_type}:")
        print(f"     Version: {info['version']}")
        print(f"     Effective Date: {info['effective_date']}")
        print(f"     Deprecated: {info['deprecated']}")
        print(f"     Is Current: {info['is_current']}")
    
    # Test 4: Version deprecation
    print("\n4. Version deprecation check:")
    for doc_type in ["terms", "privacy", "disclaimer"]:
        is_deprecated = versioning.is_version_deprecated(doc_type, "1.0")
        print(f"   {doc_type} v1.0 deprecated: {is_deprecated}")
    
    # Test 5: Template paths
    print("\n5. Template paths:")
    for doc_type in ["terms", "privacy", "disclaimer"]:
        path = versioning.get_template_path(doc_type)
        print(f"   {doc_type}: {path}")
    
    print("\n" + "=" * 50)
    print("All tests completed successfully!")

if __name__ == "__main__":
    test_versioning_system()
