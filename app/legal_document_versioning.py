"""
Legal Document Versioning System

This module manages versioning for legal documents (Terms and Conditions, 
Privacy Policy, Medical Disclaimer) to ensure proper tracking of which 
version users have accepted and to handle document updates.
"""

import json
import os
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import logging

logger = logging.getLogger(__name__)

# Legal document configuration
LEGAL_DOCUMENTS_CONFIG = {
    "terms": {
        "current_version": "2.0",
        "effective_date": "2025-01-01",
        "template_path": "templates/legal/terms.html",
        "versions": {
            "1.0": {
                "effective_date": "2024-01-01",
                "template_path": "templates/legal/terms_v1.html",
                "deprecated": True,
                "deprecation_date": "2025-01-01"
            },
            "2.0": {
                "effective_date": "2025-01-01",
                "template_path": "templates/legal/terms.html",
                "deprecated": False,
                "changes": [
                    "Added centralized OAuth integration details",
                    "Updated data security and privacy sections",
                    "Enhanced user rights and account management"
                ]
            }
        }
    },
    "privacy": {
        "current_version": "2.0",
        "effective_date": "2025-01-01",
        "template_path": "templates/legal/privacy.html",
        "versions": {
            "1.0": {
                "effective_date": "2024-01-01",
                "template_path": "templates/legal/privacy_v1.html",
                "deprecated": True,
                "deprecation_date": "2025-01-01"
            },
            "2.0": {
                "effective_date": "2025-01-01",
                "template_path": "templates/legal/privacy.html",
                "deprecated": False,
                "changes": [
                    "Enhanced OAuth security and token management",
                    "Updated data retention policies",
                    "Improved GDPR compliance sections"
                ]
            }
        }
    },
    "disclaimer": {
        "current_version": "2.0",
        "effective_date": "2025-01-01",
        "template_path": "templates/legal/disclaimer.html",
        "versions": {
            "1.0": {
                "effective_date": "2024-01-01",
                "template_path": "templates/legal/disclaimer_v1.html",
                "deprecated": True,
                "deprecation_date": "2025-01-01"
            },
            "2.0": {
                "effective_date": "2025-01-01",
                "template_path": "templates/legal/disclaimer.html",
                "deprecated": False,
                "changes": [
                    "Enhanced safety guidelines and warnings",
                    "Updated emergency protocols",
                    "Improved professional consultation requirements"
                ]
            }
        }
    }
}


class LegalDocumentVersioning:
    """
    Manages versioning for legal documents including version tracking,
    document retrieval, and acceptance validation.
    """
    
    def __init__(self, config: Dict = None):
        """
        Initialize the legal document versioning system.
        
        Args:
            config: Optional custom configuration dictionary
        """
        self.config = config or LEGAL_DOCUMENTS_CONFIG
        self.base_path = os.path.dirname(os.path.abspath(__file__))
        
    def get_current_version(self, document_type: str) -> str:
        """
        Get the current version of a legal document.
        
        Args:
            document_type: Type of document ('terms', 'privacy', 'disclaimer')
            
        Returns:
            Current version string
            
        Raises:
            ValueError: If document type is not found
        """
        if document_type not in self.config:
            raise ValueError(f"Unknown document type: {document_type}")
        
        return self.config[document_type]["current_version"]
    
    def get_effective_date(self, document_type: str, version: str = None) -> str:
        """
        Get the effective date of a legal document version.
        
        Args:
            document_type: Type of document ('terms', 'privacy', 'disclaimer')
            version: Specific version (defaults to current version)
            
        Returns:
            Effective date string
            
        Raises:
            ValueError: If document type or version is not found
        """
        if document_type not in self.config:
            raise ValueError(f"Unknown document type: {document_type}")
        
        if version is None:
            version = self.get_current_version(document_type)
        
        if version not in self.config[document_type]["versions"]:
            raise ValueError(f"Unknown version {version} for document type {document_type}")
        
        return self.config[document_type]["versions"][version]["effective_date"]
    
    def get_template_path(self, document_type: str, version: str = None) -> str:
        """
        Get the template path for a legal document version.
        
        Args:
            document_type: Type of document ('terms', 'privacy', 'disclaimer')
            version: Specific version (defaults to current version)
            
        Returns:
            Template file path
            
        Raises:
            ValueError: If document type or version is not found
        """
        if document_type not in self.config:
            raise ValueError(f"Unknown document type: {document_type}")
        
        if version is None:
            version = self.get_current_version(document_type)
        
        if version not in self.config[document_type]["versions"]:
            raise ValueError(f"Unknown version {version} for document type {document_type}")
        
        template_path = self.config[document_type]["versions"][version]["template_path"]
        return os.path.join(self.base_path, template_path)
    
    def is_version_deprecated(self, document_type: str, version: str) -> bool:
        """
        Check if a document version is deprecated.
        
        Args:
            document_type: Type of document ('terms', 'privacy', 'disclaimer')
            version: Version to check
            
        Returns:
            True if deprecated, False otherwise
            
        Raises:
            ValueError: If document type or version is not found
        """
        if document_type not in self.config:
            raise ValueError(f"Unknown document type: {document_type}")
        
        if version not in self.config[document_type]["versions"]:
            raise ValueError(f"Unknown version {version} for document type {document_type}")
        
        return self.config[document_type]["versions"][version]["deprecated"]
    
    def get_version_changes(self, document_type: str, version: str) -> List[str]:
        """
        Get the list of changes for a specific version.
        
        Args:
            document_type: Type of document ('terms', 'privacy', 'disclaimer')
            version: Version to get changes for
            
        Returns:
            List of changes for the version
            
        Raises:
            ValueError: If document type or version is not found
        """
        if document_type not in self.config:
            raise ValueError(f"Unknown document type: {document_type}")
        
        if version not in self.config[document_type]["versions"]:
            raise ValueError(f"Unknown version {version} for document type {document_type}")
        
        return self.config[document_type]["versions"][version].get("changes", [])
    
    def get_available_versions(self, document_type: str) -> List[str]:
        """
        Get all available versions for a document type.
        
        Args:
            document_type: Type of document ('terms', 'privacy', 'disclaimer')
            
        Returns:
            List of available version strings
            
        Raises:
            ValueError: If document type is not found
        """
        if document_type not in self.config:
            raise ValueError(f"Unknown document type: {document_type}")
        
        return list(self.config[document_type]["versions"].keys())
    
    def validate_user_acceptance(self, document_type: str, user_version: str) -> Tuple[bool, str]:
        """
        Validate if a user's accepted version is still valid.
        
        Args:
            document_type: Type of document ('terms', 'privacy', 'disclaimer')
            user_version: Version the user has accepted
            
        Returns:
            Tuple of (is_valid, message)
        """
        try:
            current_version = self.get_current_version(document_type)
            
            # If user has current version, it's valid
            if user_version == current_version:
                return True, "User has current version"
            
            # If user version is deprecated, it's invalid
            if self.is_version_deprecated(document_type, user_version):
                return False, f"User version {user_version} is deprecated"
            
            # Check if user version is older than current
            user_effective_date = datetime.strptime(
                self.get_effective_date(document_type, user_version), 
                "%Y-%m-%d"
            )
            current_effective_date = datetime.strptime(
                self.get_effective_date(document_type, current_version), 
                "%Y-%m-%d"
            )
            
            if user_effective_date < current_effective_date:
                return False, f"User version {user_version} is outdated"
            
            return True, "User version is valid"
            
        except Exception as e:
            logger.error(f"Error validating user acceptance: {str(e)}")
            return False, f"Error validating version: {str(e)}"
    
    def get_required_updates(self, user_versions: Dict[str, str]) -> Dict[str, Dict]:
        """
        Get required updates for user's accepted versions.
        
        Args:
            user_versions: Dictionary of {document_type: version}
            
        Returns:
            Dictionary of required updates
        """
        required_updates = {}
        
        for doc_type, user_version in user_versions.items():
            is_valid, message = self.validate_user_acceptance(doc_type, user_version)
            
            if not is_valid:
                current_version = self.get_current_version(doc_type)
                required_updates[doc_type] = {
                    "current_version": current_version,
                    "user_version": user_version,
                    "message": message,
                    "changes": self.get_version_changes(doc_type, current_version),
                    "effective_date": self.get_effective_date(doc_type, current_version)
                }
        
        return required_updates
    
    def get_document_info(self, document_type: str, version: str = None) -> Dict:
        """
        Get comprehensive information about a document version.
        
        Args:
            document_type: Type of document ('terms', 'privacy', 'disclaimer')
            version: Specific version (defaults to current version)
            
        Returns:
            Dictionary with document information
        """
        if version is None:
            version = self.get_current_version(document_type)
        
        return {
            "document_type": document_type,
            "version": version,
            "effective_date": self.get_effective_date(document_type, version),
            "template_path": self.get_template_path(document_type, version),
            "deprecated": self.is_version_deprecated(document_type, version),
            "changes": self.get_version_changes(document_type, version),
            "is_current": version == self.get_current_version(document_type)
        }
    
    def get_all_document_info(self) -> Dict[str, Dict]:
        """
        Get information about all document types and their current versions.
        
        Returns:
            Dictionary with information about all documents
        """
        all_info = {}
        
        for doc_type in self.config.keys():
            all_info[doc_type] = self.get_document_info(doc_type)
        
        return all_info


# Global instance for easy access
legal_versioning = LegalDocumentVersioning()


def get_legal_document_versioning() -> LegalDocumentVersioning:
    """
    Get the global legal document versioning instance.
    
    Returns:
        LegalDocumentVersioning instance
    """
    return legal_versioning


def validate_legal_acceptance(user_versions: Dict[str, str]) -> Dict[str, Dict]:
    """
    Convenience function to validate user's legal document acceptance.
    
    Args:
        user_versions: Dictionary of {document_type: version}
        
    Returns:
        Dictionary of validation results
    """
    return legal_versioning.get_required_updates(user_versions)


def get_current_legal_versions() -> Dict[str, str]:
    """
    Get current versions of all legal documents.
    
    Returns:
        Dictionary of {document_type: current_version}
    """
    return {
        doc_type: legal_versioning.get_current_version(doc_type)
        for doc_type in legal_versioning.config.keys()
    }


if __name__ == "__main__":
    # Test the versioning system
    print("Legal Document Versioning System Test")
    print("=" * 40)
    
    # Test current versions
    print("Current versions:")
    for doc_type in ["terms", "privacy", "disclaimer"]:
        version = legal_versioning.get_current_version(doc_type)
        print(f"  {doc_type}: {version}")
    
    # Test validation
    print("\nValidation tests:")
    test_versions = {
        "terms": "1.0",
        "privacy": "2.0",
        "disclaimer": "2.0"
    }
    
    updates = legal_versioning.get_required_updates(test_versions)
    for doc_type, update_info in updates.items():
        print(f"  {doc_type}: {update_info['message']}")
    
    # Test document info
    print("\nDocument information:")
    for doc_type in ["terms", "privacy", "disclaimer"]:
        info = legal_versioning.get_document_info(doc_type)
        print(f"  {doc_type} {info['version']}: {info['effective_date']}")
