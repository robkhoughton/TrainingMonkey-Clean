"""
Legal Compliance Tracking Module

This module handles tracking and validation of user acceptance of legal documents
(Terms and Conditions, Privacy Policy, Medical Disclaimer) with version control
and audit trail functionality.
"""

import logging
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any
from flask import request
import json

from db_utils import get_db_connection, execute_query, USE_POSTGRES
from legal_document_versioning import (
    LegalDocumentVersioning, 
    validate_legal_acceptance, 
    get_current_legal_versions
)

logger = logging.getLogger(__name__)

# Global versioning instance
legal_versioning = LegalDocumentVersioning()


class LegalComplianceTracker:
    """
    Manages legal compliance tracking for user acceptance of legal documents.
    Integrates with database and versioning system for comprehensive tracking.
    """
    
    def __init__(self):
        """Initialize the legal compliance tracker."""
        self.versioning = legal_versioning
    
    def log_legal_acceptance(
        self, 
        user_id: int, 
        document_type: str, 
        version: str,
        ip_address: str = None,
        user_agent: str = None
    ) -> bool:
        """
        Log user acceptance of a legal document.
        
        Args:
            user_id: User ID
            document_type: Type of document ('terms', 'privacy', 'disclaimer')
            version: Document version accepted
            ip_address: User's IP address (optional)
            user_agent: User's browser agent (optional)
            
        Returns:
            True if successfully logged, False otherwise
        """
        try:
            # Get IP and user agent if not provided
            if ip_address is None:
                ip_address = request.remote_addr if request else "unknown"
            if user_agent is None:
                user_agent = request.headers.get('User-Agent', "unknown") if request else "unknown"
            
            # Validate document type and version
            if document_type not in ['terms', 'privacy', 'disclaimer']:
                logger.error(f"Invalid document type: {document_type}")
                return False
            
            # Check if version exists
            try:
                self.versioning.get_effective_date(document_type, version)
            except ValueError as e:
                logger.error(f"Invalid version {version} for document type {document_type}: {e}")
                return False
            
            # Log acceptance in legal_compliance table
            with get_db_connection() as conn:
                cursor = conn.cursor()
                
                # Insert into legal_compliance table
                if USE_POSTGRES:
                    insert_sql = """
                    INSERT INTO legal_compliance 
                    (user_id, document_type, version, accepted_at, ip_address, user_agent, created_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    """
                else:
                    insert_sql = """
                    INSERT INTO legal_compliance 
                    (user_id, document_type, version, accepted_at, ip_address, user_agent, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """
                
                current_time = datetime.now()
                cursor.execute(insert_sql, (
                    user_id, document_type, version, current_time, 
                    ip_address, user_agent, current_time
                ))
                
                # Update user_settings table with acceptance timestamp
                if document_type == 'terms':
                    update_sql = "UPDATE user_settings SET terms_accepted_at = %s WHERE id = %s"
                elif document_type == 'privacy':
                    update_sql = "UPDATE user_settings SET privacy_policy_accepted_at = %s WHERE id = %s"
                elif document_type == 'disclaimer':
                    update_sql = "UPDATE user_settings SET disclaimer_accepted_at = %s WHERE id = %s"
                
                if USE_POSTGRES:
                    cursor.execute(update_sql, (current_time, user_id))
                else:
                    cursor.execute(update_sql.replace('%s', '?'), (current_time, user_id))
                
                conn.commit()
                
                logger.info(f"Legal acceptance logged: user_id={user_id}, document={document_type}, version={version}")
                return True
                
        except Exception as e:
            logger.error(f"Error logging legal acceptance: {str(e)}")
            return False
    
    def get_user_legal_status(self, user_id: int) -> Dict[str, Any]:
        """
        Get comprehensive legal compliance status for a user.
        
        Args:
            user_id: User ID
            
        Returns:
            Dictionary with legal compliance status
        """
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                
                # Get user's legal acceptance timestamps
                if USE_POSTGRES:
                    select_sql = """
                    SELECT terms_accepted_at, privacy_policy_accepted_at, disclaimer_accepted_at,
                           account_status, registration_date
                    FROM user_settings 
                    WHERE id = %s
                    """
                else:
                    select_sql = """
                    SELECT terms_accepted_at, privacy_policy_accepted_at, disclaimer_accepted_at,
                           account_status, registration_date
                    FROM user_settings 
                    WHERE id = ?
                    """
                
                cursor.execute(select_sql, (user_id,))
                result = cursor.fetchone()
                
                if not result:
                    return {"error": "User not found"}
                
                terms_accepted_at, privacy_accepted_at, disclaimer_accepted_at, account_status, registration_date = result
                
                # Get latest acceptance records from legal_compliance table
                if USE_POSTGRES:
                    compliance_sql = """
                    SELECT document_type, version, accepted_at
                    FROM legal_compliance 
                    WHERE user_id = %s 
                    AND (document_type, accepted_at) IN (
                        SELECT document_type, MAX(accepted_at)
                        FROM legal_compliance 
                        WHERE user_id = %s 
                        GROUP BY document_type
                    )
                    """
                else:
                    compliance_sql = """
                    SELECT document_type, version, accepted_at
                    FROM legal_compliance 
                    WHERE user_id = ? 
                    AND (document_type, accepted_at) IN (
                        SELECT document_type, MAX(accepted_at)
                        FROM legal_compliance 
                        WHERE user_id = ? 
                        GROUP BY document_type
                    )
                    """
                
                cursor.execute(compliance_sql, (user_id, user_id))
                compliance_records = cursor.fetchall()
                
                # Build user versions dictionary
                user_versions = {}
                for doc_type, version, accepted_at in compliance_records:
                    user_versions[doc_type] = version
                
                # Validate current versions
                current_versions = get_current_legal_versions()
                required_updates = validate_legal_acceptance(user_versions)
                
                # Build status response
                status = {
                    "user_id": user_id,
                    "account_status": account_status,
                    "registration_date": registration_date.isoformat() if registration_date else None,
                    "legal_documents": {
                        "terms": {
                            "accepted_at": terms_accepted_at.isoformat() if terms_accepted_at else None,
                            "version": user_versions.get("terms"),
                            "current_version": current_versions.get("terms"),
                            "needs_update": "terms" in required_updates
                        },
                        "privacy": {
                            "accepted_at": privacy_accepted_at.isoformat() if privacy_accepted_at else None,
                            "version": user_versions.get("privacy"),
                            "current_version": current_versions.get("privacy"),
                            "needs_update": "privacy" in required_updates
                        },
                        "disclaimer": {
                            "accepted_at": disclaimer_accepted_at.isoformat() if disclaimer_accepted_at else None,
                            "version": user_versions.get("disclaimer"),
                            "current_version": current_versions.get("disclaimer"),
                            "needs_update": "disclaimer" in required_updates
                        }
                    },
                    "compliance_status": {
                        "all_documents_accepted": all([
                            terms_accepted_at, privacy_accepted_at, disclaimer_accepted_at
                        ]),
                        "all_versions_current": len(required_updates) == 0,
                        "required_updates": required_updates
                    }
                }
                
                return status
                
        except Exception as e:
            logger.error(f"Error getting user legal status: {str(e)}")
            return {"error": f"Database error: {str(e)}"}
    
    def validate_user_compliance(self, user_id: int) -> Tuple[bool, Dict[str, Any]]:
        """
        Validate if a user is fully compliant with all legal requirements.
        
        Args:
            user_id: User ID
            
        Returns:
            Tuple of (is_compliant, details)
        """
        status = self.get_user_legal_status(user_id)
        
        if "error" in status:
            return False, status
        
        # Check if all documents are accepted
        docs = status["legal_documents"]
        all_accepted = all([
            docs["terms"]["accepted_at"] is not None,
            docs["privacy"]["accepted_at"] is not None,
            docs["disclaimer"]["accepted_at"] is not None
        ])
        
        # Check if all versions are current
        all_current = status["compliance_status"]["all_versions_current"]
        
        is_compliant = all_accepted and all_current
        
        details = {
            "is_compliant": is_compliant,
            "all_documents_accepted": all_accepted,
            "all_versions_current": all_current,
            "required_updates": status["compliance_status"]["required_updates"],
            "missing_documents": []
        }
        
        # Identify missing documents
        for doc_type, doc_info in docs.items():
            if doc_info["accepted_at"] is None:
                details["missing_documents"].append(doc_type)
        
        return is_compliant, details
    
    def get_legal_acceptance_history(self, user_id: int, document_type: str = None) -> List[Dict]:
        """
        Get acceptance history for a user's legal documents.
        
        Args:
            user_id: User ID
            document_type: Optional document type filter
            
        Returns:
            List of acceptance records
        """
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                
                if document_type:
                    if USE_POSTGRES:
                        select_sql = """
                        SELECT id, document_type, version, accepted_at, ip_address, user_agent, created_at
                        FROM legal_compliance 
                        WHERE user_id = %s AND document_type = %s
                        ORDER BY accepted_at DESC
                        """
                    else:
                        select_sql = """
                        SELECT id, document_type, version, accepted_at, ip_address, user_agent, created_at
                        FROM legal_compliance 
                        WHERE user_id = ? AND document_type = ?
                        ORDER BY accepted_at DESC
                        """
                    cursor.execute(select_sql, (user_id, document_type))
                else:
                    if USE_POSTGRES:
                        select_sql = """
                        SELECT id, document_type, version, accepted_at, ip_address, user_agent, created_at
                        FROM legal_compliance 
                        WHERE user_id = %s
                        ORDER BY accepted_at DESC
                        """
                    else:
                        select_sql = """
                        SELECT id, document_type, version, accepted_at, ip_address, user_agent, created_at
                        FROM legal_compliance 
                        WHERE user_id = ?
                        ORDER BY accepted_at DESC
                        """
                    cursor.execute(select_sql, (user_id,))
                
                records = cursor.fetchall()
                
                history = []
                for record in records:
                    record_id, doc_type, version, accepted_at, ip_address, user_agent, created_at = record
                    history.append({
                        "id": record_id,
                        "document_type": doc_type,
                        "version": version,
                        "accepted_at": accepted_at.isoformat() if accepted_at else None,
                        "ip_address": ip_address,
                        "user_agent": user_agent,
                        "created_at": created_at.isoformat() if created_at else None
                    })
                
                return history
                
        except Exception as e:
            logger.error(f"Error getting legal acceptance history: {str(e)}")
            return []
    
    def revoke_legal_acceptance(self, user_id: int, document_type: str) -> bool:
        """
        Revoke a user's acceptance of a legal document.
        This will require them to re-accept the current version.
        
        Args:
            user_id: User ID
            document_type: Type of document to revoke
            
        Returns:
            True if successfully revoked, False otherwise
        """
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                
                # Clear acceptance timestamp in user_settings
                if document_type == 'terms':
                    update_sql = "UPDATE user_settings SET terms_accepted_at = NULL WHERE id = %s"
                elif document_type == 'privacy':
                    update_sql = "UPDATE user_settings SET privacy_policy_accepted_at = NULL WHERE id = %s"
                elif document_type == 'disclaimer':
                    update_sql = "UPDATE user_settings SET disclaimer_accepted_at = NULL WHERE id = %s"
                else:
                    logger.error(f"Invalid document type for revocation: {document_type}")
                    return False
                
                if USE_POSTGRES:
                    cursor.execute(update_sql, (user_id,))
                else:
                    cursor.execute(update_sql.replace('%s', '?'), (user_id,))
                
                conn.commit()
                
                logger.info(f"Legal acceptance revoked: user_id={user_id}, document={document_type}")
                return True
                
        except Exception as e:
            logger.error(f"Error revoking legal acceptance: {str(e)}")
            return False
    
    def get_compliance_statistics(self) -> Dict[str, Any]:
        """
        Get compliance statistics across all users.
        
        Returns:
            Dictionary with compliance statistics
        """
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                
                # Get total user count
                if USE_POSTGRES:
                    total_sql = "SELECT COUNT(*) FROM user_settings"
                else:
                    total_sql = "SELECT COUNT(*) FROM user_settings"
                
                cursor.execute(total_sql)
                total_users = cursor.fetchone()[0]
                
                # Get compliance counts
                if USE_POSTGRES:
                    compliance_sql = """
                    SELECT 
                        COUNT(CASE WHEN terms_accepted_at IS NOT NULL THEN 1 END) as terms_accepted,
                        COUNT(CASE WHEN privacy_policy_accepted_at IS NOT NULL THEN 1 END) as privacy_accepted,
                        COUNT(CASE WHEN disclaimer_accepted_at IS NOT NULL THEN 1 END) as disclaimer_accepted,
                        COUNT(CASE WHEN terms_accepted_at IS NOT NULL 
                                   AND privacy_policy_accepted_at IS NOT NULL 
                                   AND disclaimer_accepted_at IS NOT NULL THEN 1 END) as fully_compliant
                    FROM user_settings
                    """
                else:
                    compliance_sql = """
                    SELECT 
                        COUNT(CASE WHEN terms_accepted_at IS NOT NULL THEN 1 END) as terms_accepted,
                        COUNT(CASE WHEN privacy_policy_accepted_at IS NOT NULL THEN 1 END) as privacy_accepted,
                        COUNT(CASE WHEN disclaimer_accepted_at IS NOT NULL THEN 1 END) as disclaimer_accepted,
                        COUNT(CASE WHEN terms_accepted_at IS NOT NULL 
                                   AND privacy_policy_accepted_at IS NOT NULL 
                                   AND disclaimer_accepted_at IS NOT NULL THEN 1 END) as fully_compliant
                    FROM user_settings
                    """
                
                cursor.execute(compliance_sql)
                result = cursor.fetchone()
                terms_accepted, privacy_accepted, disclaimer_accepted, fully_compliant = result
                
                # Calculate percentages
                stats = {
                    "total_users": total_users,
                    "terms_acceptance": {
                        "count": terms_accepted,
                        "percentage": round((terms_accepted / total_users * 100), 2) if total_users > 0 else 0
                    },
                    "privacy_acceptance": {
                        "count": privacy_accepted,
                        "percentage": round((privacy_accepted / total_users * 100), 2) if total_users > 0 else 0
                    },
                    "disclaimer_acceptance": {
                        "count": disclaimer_accepted,
                        "percentage": round((disclaimer_accepted / total_users * 100), 2) if total_users > 0 else 0
                    },
                    "fully_compliant": {
                        "count": fully_compliant,
                        "percentage": round((fully_compliant / total_users * 100), 2) if total_users > 0 else 0
                    }
                }
                
                return stats
                
        except Exception as e:
            logger.error(f"Error getting compliance statistics: {str(e)}")
            return {"error": f"Database error: {str(e)}"}

    def get_total_users_count(self) -> int:
        """Get total number of users in the system"""
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                
                if USE_POSTGRES:
                    cursor.execute("SELECT COUNT(*) FROM users")
                else:
                    cursor.execute("SELECT COUNT(*) FROM users")
                
                result = cursor.fetchone()
                return result[0] if result else 0
                
        except Exception as e:
            logger.error(f"Error getting total users count: {str(e)}")
            return 0

    def get_compliant_users_count(self) -> int:
        """Get number of users who are fully compliant with all legal documents"""
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                
                if USE_POSTGRES:
                    cursor.execute("""
                        SELECT COUNT(DISTINCT u.id) 
                        FROM users u
                        JOIN user_settings us ON u.id = us.user_id
                        WHERE us.legal_terms_accepted_at IS NOT NULL
                        AND us.legal_privacy_accepted_at IS NOT NULL
                        AND us.legal_disclaimer_accepted_at IS NOT NULL
                    """)
                else:
                    cursor.execute("""
                        SELECT COUNT(DISTINCT u.id) 
                        FROM users u
                        JOIN user_settings us ON u.id = us.user_id
                        WHERE us.legal_terms_accepted_at IS NOT NULL
                        AND us.legal_privacy_accepted_at IS NOT NULL
                        AND us.legal_disclaimer_accepted_at IS NOT NULL
                    """)
                
                result = cursor.fetchone()
                return result[0] if result else 0
                
        except Exception as e:
            logger.error(f"Error getting compliant users count: {str(e)}")
            return 0


# Global instance for easy access
legal_compliance = LegalComplianceTracker()


def get_legal_compliance_tracker() -> LegalComplianceTracker:
    """
    Get the global legal compliance tracker instance.
    
    Returns:
        LegalComplianceTracker instance
    """
    return legal_compliance


def log_user_legal_acceptance(user_id: int, document_type: str, version: str) -> bool:
    """
    Convenience function to log user legal acceptance.
    
    Args:
        user_id: User ID
        document_type: Type of document
        version: Document version
        
    Returns:
        True if successfully logged, False otherwise
    """
    return legal_compliance.log_legal_acceptance(user_id, document_type, version)


def check_user_compliance(user_id: int) -> Tuple[bool, Dict[str, Any]]:
    """
    Convenience function to check user compliance.
    
    Args:
        user_id: User ID
        
    Returns:
        Tuple of (is_compliant, details)
    """
    return legal_compliance.validate_user_compliance(user_id)


if __name__ == "__main__":
    # Test the legal compliance tracking system
    print("Legal Compliance Tracking System Test")
    print("=" * 50)
    
    # Test compliance tracker
    tracker = LegalComplianceTracker()
    
    # Test current versions
    print("\n1. Current legal document versions:")
    current_versions = get_current_legal_versions()
    for doc_type, version in current_versions.items():
        print(f"   {doc_type}: {version}")
    
    # Test validation logic
    print("\n2. Validation test:")
    test_user_versions = {
        "terms": "1.0",
        "privacy": "2.0",
        "disclaimer": "2.0"
    }
    
    required_updates = validate_legal_acceptance(test_user_versions)
    print(f"   Required updates: {len(required_updates)}")
    for doc_type, update_info in required_updates.items():
        print(f"     {doc_type}: {update_info['message']}")
    
    print("\n" + "=" * 50)
    print("Legal compliance tracking system ready!")
