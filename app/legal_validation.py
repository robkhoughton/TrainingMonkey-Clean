"""
Legal Document Acceptance Validation Module

This module provides comprehensive validation for legal document acceptance,
including version checking, compliance validation, and acceptance requirements.
"""

import logging
from typing import Dict, List, Tuple, Any, Optional
from datetime import datetime

from legal_document_versioning import (
    LegalDocumentVersioning, 
    validate_legal_acceptance, 
    get_current_legal_versions
)
from legal_compliance import LegalComplianceTracker

logger = logging.getLogger(__name__)


class LegalDocumentValidator:
    """
    Validates legal document acceptance and compliance requirements.
    """
    
    def __init__(self):
        """Initialize the legal document validator."""
        self.versioning = LegalDocumentVersioning()
        self.compliance = LegalComplianceTracker()
    
    def validate_acceptance_requirements(
        self, 
        user_id: int, 
        document_type: str
    ) -> Dict[str, Any]:
        """
        Validate if a user can accept a specific legal document.
        
        Args:
            user_id: User ID
            document_type: Type of document ('terms', 'privacy', 'disclaimer')
            
        Returns:
            Dictionary with validation results
        """
        try:
            # Get current version
            current_version = self.versioning.get_current_version(document_type)
            
            # Get user's current status
            user_status = self.compliance.get_user_legal_status(user_id)
            
            if "error" in user_status:
                return {
                    "can_accept": False,
                    "reason": "User not found",
                    "current_version": current_version,
                    "user_version": None
                }
            
            # Check if user has already accepted this document
            doc_info = user_status["legal_documents"].get(document_type, {})
            user_version = doc_info.get("version")
            accepted_at = doc_info.get("accepted_at")
            
            # If user has accepted current version, they can't accept again
            if user_version == current_version and accepted_at:
                return {
                    "can_accept": False,
                    "reason": "Already accepted current version",
                    "current_version": current_version,
                    "user_version": user_version,
                    "accepted_at": accepted_at
                }
            
            # User can accept if:
            # 1. They haven't accepted this document before, OR
            # 2. They have an older version that needs updating
            can_accept = True
            reason = "Ready to accept"
            
            if user_version and user_version != current_version:
                # Check if their version is deprecated or outdated
                is_valid, message = self.versioning.validate_user_acceptance(document_type, user_version)
                if is_valid:
                    can_accept = False
                    reason = f"Current version ({user_version}) is still valid"
                else:
                    reason = f"Version {user_version} needs update to {current_version}"
            
            return {
                "can_accept": can_accept,
                "reason": reason,
                "current_version": current_version,
                "user_version": user_version,
                "accepted_at": accepted_at,
                "effective_date": self.versioning.get_effective_date(document_type, current_version)
            }
            
        except Exception as e:
            logger.error(f"Error validating acceptance requirements: {str(e)}")
            return {
                "can_accept": False,
                "reason": f"Validation error: {str(e)}",
                "current_version": None,
                "user_version": None
            }
    
    def validate_registration_requirements(self, user_id: int) -> Dict[str, Any]:
        """
        Validate if a user meets all requirements for account registration.
        
        Args:
            user_id: User ID
            
        Returns:
            Dictionary with registration validation results
        """
        try:
            # Get user's compliance status
            is_compliant, details = self.compliance.validate_user_compliance(user_id)
            
            # Get current versions of all documents
            current_versions = get_current_legal_versions()
            
            # Check if all required documents are accepted
            required_documents = ['terms', 'privacy', 'disclaimer']
            missing_documents = []
            outdated_documents = []
            
            for doc_type in required_documents:
                validation = self.validate_acceptance_requirements(user_id, doc_type)
                if not validation["user_version"]:
                    missing_documents.append(doc_type)
                elif validation["user_version"] != validation["current_version"]:
                    outdated_documents.append(doc_type)
            
            can_register = len(missing_documents) == 0 and len(outdated_documents) == 0
            
            return {
                "can_register": can_register,
                "is_compliant": is_compliant,
                "missing_documents": missing_documents,
                "outdated_documents": outdated_documents,
                "current_versions": current_versions,
                "details": details
            }
            
        except Exception as e:
            logger.error(f"Error validating registration requirements: {str(e)}")
            return {
                "can_register": False,
                "is_compliant": False,
                "missing_documents": ["terms", "privacy", "disclaimer"],
                "outdated_documents": [],
                "error": str(e)
            }
    
    def validate_document_access(self, user_id: int, document_type: str) -> Dict[str, Any]:
        """
        Validate if a user can access a specific legal document.
        
        Args:
            user_id: User ID
            document_type: Type of document
            
        Returns:
            Dictionary with access validation results
        """
        try:
            # Get current version
            current_version = self.versioning.get_current_version(document_type)
            
            # Get user's status
            user_status = self.compliance.get_user_legal_status(user_id)
            
            if "error" in user_status:
                return {
                    "can_access": False,
                    "reason": "User not found",
                    "current_version": current_version
                }
            
            # Users can always access legal documents for reading
            # The validation is more about tracking what they've seen
            doc_info = user_status["legal_documents"].get(document_type, {})
            user_version = doc_info.get("version")
            
            return {
                "can_access": True,
                "reason": "Document access granted",
                "current_version": current_version,
                "user_version": user_version,
                "needs_acceptance": user_version != current_version
            }
            
        except Exception as e:
            logger.error(f"Error validating document access: {str(e)}")
            return {
                "can_access": False,
                "reason": f"Access validation error: {str(e)}",
                "current_version": None
            }
    
    def get_acceptance_summary(self, user_id: int) -> Dict[str, Any]:
        """
        Get a summary of user's legal document acceptance status.
        
        Args:
            user_id: User ID
            
        Returns:
            Dictionary with acceptance summary
        """
        try:
            user_status = self.compliance.get_user_legal_status(user_id)
            
            if "error" in user_status:
                return {"error": "User not found"}
            
            docs = user_status["legal_documents"]
            current_versions = get_current_legal_versions()
            
            summary = {
                "user_id": user_id,
                "overall_compliance": user_status["compliance_status"]["all_documents_accepted"],
                "all_versions_current": user_status["compliance_status"]["all_versions_current"],
                "documents": {}
            }
            
            for doc_type in ['terms', 'privacy', 'disclaimer']:
                doc_info = docs[doc_type]
                current_version = current_versions.get(doc_type)
                
                summary["documents"][doc_type] = {
                    "accepted": doc_info["accepted_at"] is not None,
                    "current_version": current_version,
                    "user_version": doc_info["version"],
                    "needs_update": doc_info["needs_update"],
                    "accepted_at": doc_info["accepted_at"]
                }
            
            return summary
            
        except Exception as e:
            logger.error(f"Error getting acceptance summary: {str(e)}")
            return {"error": f"Summary error: {str(e)}"}
    
    def validate_bulk_acceptance(
        self, 
        user_id: int, 
        documents: List[str]
    ) -> Dict[str, Any]:
        """
        Validate if a user can accept multiple documents at once.
        
        Args:
            user_id: User ID
            documents: List of document types to accept
            
        Returns:
            Dictionary with bulk acceptance validation results
        """
        try:
            results = {}
            all_valid = True
            
            for doc_type in documents:
                validation = self.validate_acceptance_requirements(user_id, doc_type)
                results[doc_type] = validation
                
                if not validation["can_accept"]:
                    all_valid = False
            
            return {
                "can_accept_all": all_valid,
                "individual_results": results,
                "valid_documents": [doc for doc, result in results.items() if result["can_accept"]],
                "invalid_documents": [doc for doc, result in results.items() if not result["can_accept"]]
            }
            
        except Exception as e:
            logger.error(f"Error validating bulk acceptance: {str(e)}")
            return {
                "can_accept_all": False,
                "error": str(e),
                "individual_results": {},
                "valid_documents": [],
                "invalid_documents": documents
            }


# Global instance for easy access
legal_validator = LegalDocumentValidator()


def get_legal_validator() -> LegalDocumentValidator:
    """
    Get the global legal document validator instance.
    
    Returns:
        LegalDocumentValidator instance
    """
    return legal_validator


def validate_user_acceptance(user_id: int, document_type: str) -> Dict[str, Any]:
    """
    Convenience function to validate user acceptance requirements.
    
    Args:
        user_id: User ID
        document_type: Type of document
        
    Returns:
        Validation results dictionary
    """
    return legal_validator.validate_acceptance_requirements(user_id, document_type)


def validate_user_registration(user_id: int) -> Dict[str, Any]:
    """
    Convenience function to validate user registration requirements.
    
    Args:
        user_id: User ID
        
    Returns:
        Registration validation results dictionary
    """
    return legal_validator.validate_registration_requirements(user_id)


if __name__ == "__main__":
    # Test the legal validation system
    print("Legal Document Validation System Test")
    print("=" * 50)
    
    # Test validator
    validator = LegalDocumentValidator()
    
    # Test current versions
    print("\n1. Current legal document versions:")
    current_versions = get_current_legal_versions()
    for doc_type, version in current_versions.items():
        print(f"   {doc_type}: {version}")
    
    # Test validation functions
    print("\n2. Validation functions available:")
    functions = [
        "validate_acceptance_requirements()",
        "validate_registration_requirements()",
        "validate_document_access()",
        "get_acceptance_summary()",
        "validate_bulk_acceptance()"
    ]
    
    for func in functions:
        print(f"   {func}")
    
    print("\n" + "=" * 50)
    print("Legal document validation system ready!")
    print("\nNote: Database operations require actual user data.")
    print("These functions will be tested with real user data during integration.")
