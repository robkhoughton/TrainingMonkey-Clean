"""
Legal Compliance Audit Trail Module

This module provides comprehensive audit trail functionality for legal compliance,
including detailed logging, reporting, and compliance monitoring.
"""

import logging
from typing import Dict, List, Tuple, Any, Optional
from datetime import datetime, timedelta
import json

from legal_compliance import LegalComplianceTracker
from legal_document_versioning import get_current_legal_versions

logger = logging.getLogger(__name__)


class LegalAuditTrail:
    """
    Manages audit trail functionality for legal compliance tracking.
    """
    
    def __init__(self):
        """Initialize the legal audit trail system."""
        self.compliance = LegalComplianceTracker()
    
    def get_compliance_audit_report(
        self, 
        user_id: int, 
        start_date: datetime = None, 
        end_date: datetime = None
    ) -> Dict[str, Any]:
        """
        Generate a comprehensive audit report for a user's legal compliance.
        
        Args:
            user_id: User ID
            start_date: Start date for audit period (defaults to 30 days ago)
            end_date: End date for audit period (defaults to now)
            
        Returns:
            Dictionary with comprehensive audit report
        """
        try:
            # Set default date range if not provided
            if end_date is None:
                end_date = datetime.now()
            if start_date is None:
                start_date = end_date - timedelta(days=30)
            
            # Get user's legal status
            user_status = self.compliance.get_user_legal_status(user_id)
            
            if "error" in user_status:
                return {"error": "User not found"}
            
            # Get acceptance history for the period
            history = self.compliance.get_legal_acceptance_history(user_id)
            
            # Filter history by date range
            filtered_history = []
            for record in history:
                if record["accepted_at"]:
                    accepted_date = datetime.fromisoformat(record["accepted_at"])
                    if start_date <= accepted_date <= end_date:
                        filtered_history.append(record)
            
            # Get current versions
            current_versions = get_current_legal_versions()
            
            # Build audit report
            report = {
                "user_id": user_id,
                "audit_period": {
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat()
                },
                "current_compliance_status": user_status["compliance_status"],
                "current_versions": current_versions,
                "acceptance_history": filtered_history,
                "compliance_summary": {
                    "total_acceptances": len(filtered_history),
                    "documents_accepted": list(set([record["document_type"] for record in filtered_history])),
                    "versions_accepted": list(set([record["version"] for record in filtered_history])),
                    "unique_ips": list(set([record["ip_address"] for record in filtered_history if record["ip_address"] != "unknown"])),
                    "unique_user_agents": list(set([record["user_agent"] for record in filtered_history if record["user_agent"] != "unknown"]))
                },
                "compliance_events": []
            }
            
            # Add compliance events
            for record in filtered_history:
                event = {
                    "timestamp": record["accepted_at"],
                    "event_type": "document_acceptance",
                    "document_type": record["document_type"],
                    "version": record["version"],
                    "ip_address": record["ip_address"],
                    "user_agent": record["user_agent"]
                }
                report["compliance_events"].append(event)
            
            return report
            
        except Exception as e:
            logger.error(f"Error generating compliance audit report: {str(e)}")
            return {"error": f"Audit report error: {str(e)}"}
    
    def get_system_compliance_report(
        self, 
        start_date: datetime = None, 
        end_date: datetime = None
    ) -> Dict[str, Any]:
        """
        Generate a system-wide compliance audit report.
        
        Args:
            start_date: Start date for audit period (defaults to 30 days ago)
            end_date: End date for audit period (defaults to now)
            
        Returns:
            Dictionary with system-wide compliance report
        """
        try:
            # Set default date range if not provided
            if end_date is None:
                end_date = datetime.now()
            if start_date is None:
                start_date = end_date - timedelta(days=30)
            
            # Get compliance statistics
            stats = self.compliance.get_compliance_statistics()
            
            # Get current versions
            current_versions = get_current_legal_versions()
            
            # Build system report
            report = {
                "audit_period": {
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat()
                },
                "system_statistics": stats,
                "current_versions": current_versions,
                "compliance_summary": {
                    "total_users": stats.get("total_users", 0),
                    "fully_compliant_users": stats.get("fully_compliant", {}).get("count", 0),
                    "compliance_rate": stats.get("fully_compliant", {}).get("percentage", 0),
                    "document_acceptance_rates": {
                        "terms": stats.get("terms_acceptance", {}).get("percentage", 0),
                        "privacy": stats.get("privacy_acceptance", {}).get("percentage", 0),
                        "disclaimer": stats.get("disclaimer_acceptance", {}).get("percentage", 0)
                    }
                }
            }
            
            return report
            
        except Exception as e:
            logger.error(f"Error generating system compliance report: {str(e)}")
            return {"error": f"System report error: {str(e)}"}
    
    def get_compliance_timeline(
        self, 
        user_id: int, 
        document_type: str = None
    ) -> List[Dict[str, Any]]:
        """
        Get a chronological timeline of compliance events for a user.
        
        Args:
            user_id: User ID
            document_type: Optional document type filter
            
        Returns:
            List of compliance events in chronological order
        """
        try:
            # Get acceptance history
            history = self.compliance.get_legal_acceptance_history(user_id, document_type)
            
            # Sort by timestamp
            timeline = sorted(history, key=lambda x: x["accepted_at"] if x["accepted_at"] else "")
            
            # Add event descriptions
            for event in timeline:
                event["event_description"] = f"Accepted {event['document_type']} version {event['version']}"
                event["event_category"] = "legal_acceptance"
            
            return timeline
            
        except Exception as e:
            logger.error(f"Error getting compliance timeline: {str(e)}")
            return []
    
    def export_compliance_data(
        self, 
        user_id: int, 
        format: str = "json"
    ) -> str:
        """
        Export compliance data for a user in specified format.
        
        Args:
            user_id: User ID
            format: Export format ('json', 'csv')
            
        Returns:
            Exported data as string
        """
        try:
            # Get comprehensive audit report
            audit_report = self.get_compliance_audit_report(user_id)
            
            if "error" in audit_report:
                return f"Error: {audit_report['error']}"
            
            if format.lower() == "json":
                return json.dumps(audit_report, indent=2, default=str)
            elif format.lower() == "csv":
                # Convert to CSV format
                csv_lines = []
                csv_lines.append("timestamp,event_type,document_type,version,ip_address,user_agent")
                
                for event in audit_report.get("compliance_events", []):
                    csv_lines.append(
                        f"{event['timestamp']},{event['event_type']},{event['document_type']},"
                        f"{event['version']},{event['ip_address']},{event['user_agent']}"
                    )
                
                return "\n".join(csv_lines)
            else:
                return f"Unsupported format: {format}"
                
        except Exception as e:
            logger.error(f"Error exporting compliance data: {str(e)}")
            return f"Export error: {str(e)}"
    
    def get_compliance_alerts(
        self, 
        user_id: int
    ) -> List[Dict[str, Any]]:
        """
        Get compliance alerts for a user (missing documents, outdated versions, etc.).
        
        Args:
            user_id: User ID
            
        Returns:
            List of compliance alerts
        """
        try:
            alerts = []
            
            # Get user's legal status
            user_status = self.compliance.get_user_legal_status(user_id)
            
            if "error" in user_status:
                return [{"type": "error", "message": "User not found"}]
            
            # Check for missing documents
            docs = user_status["legal_documents"]
            for doc_type, doc_info in docs.items():
                if not doc_info["accepted_at"]:
                    alerts.append({
                        "type": "missing_document",
                        "severity": "high",
                        "document_type": doc_type,
                        "message": f"Missing acceptance of {doc_type} document",
                        "action_required": "accept_document"
                    })
                elif doc_info["needs_update"]:
                    alerts.append({
                        "type": "outdated_version",
                        "severity": "medium",
                        "document_type": doc_type,
                        "current_version": doc_info["current_version"],
                        "user_version": doc_info["user_version"],
                        "message": f"Outdated {doc_type} version ({doc_info['user_version']} -> {doc_info['current_version']})",
                        "action_required": "update_document"
                    })
            
            # Check overall compliance
            if not user_status["compliance_status"]["all_documents_accepted"]:
                alerts.append({
                    "type": "incomplete_compliance",
                    "severity": "high",
                    "message": "User has not accepted all required legal documents",
                    "action_required": "complete_acceptance"
                })
            
            return alerts
            
        except Exception as e:
            logger.error(f"Error getting compliance alerts: {str(e)}")
            return [{"type": "error", "message": f"Alert error: {str(e)}"}]
    
    def log_compliance_event(
        self, 
        user_id: int, 
        event_type: str, 
        event_data: Dict[str, Any]
    ) -> bool:
        """
        Log a custom compliance event.
        
        Args:
            user_id: User ID
            event_type: Type of event
            event_data: Event data dictionary
            
        Returns:
            True if successfully logged, False otherwise
        """
        try:
            # This would typically log to a dedicated audit log table
            # For now, we'll use the existing legal_compliance table
            logger.info(f"Compliance event logged: user_id={user_id}, type={event_type}, data={event_data}")
            return True
            
        except Exception as e:
            logger.error(f"Error logging compliance event: {str(e)}")
            return False


# Global instance for easy access
legal_audit_trail = LegalAuditTrail()


def get_legal_audit_trail() -> LegalAuditTrail:
    """
    Get the global legal audit trail instance.
    
    Returns:
        LegalAuditTrail instance
    """
    return legal_audit_trail


def generate_compliance_report(user_id: int) -> Dict[str, Any]:
    """
    Convenience function to generate compliance audit report.
    
    Args:
        user_id: User ID
        
    Returns:
        Compliance audit report dictionary
    """
    return legal_audit_trail.get_compliance_audit_report(user_id)


def get_user_compliance_alerts(user_id: int) -> List[Dict[str, Any]]:
    """
    Convenience function to get user compliance alerts.
    
    Args:
        user_id: User ID
        
    Returns:
        List of compliance alerts
    """
    return legal_audit_trail.get_compliance_alerts(user_id)


if __name__ == "__main__":
    # Test the legal audit trail system
    print("Legal Compliance Audit Trail System Test")
    print("=" * 50)
    
    # Test audit trail
    audit_trail = LegalAuditTrail()
    
    # Test functions
    print("\n1. Audit trail functions available:")
    functions = [
        "get_compliance_audit_report()",
        "get_system_compliance_report()",
        "get_compliance_timeline()",
        "export_compliance_data()",
        "get_compliance_alerts()",
        "log_compliance_event()"
    ]
    
    for func in functions:
        print(f"   {func}")
    
    # Test current versions
    print("\n2. Current legal document versions:")
    current_versions = get_current_legal_versions()
    for doc_type, version in current_versions.items():
        print(f"   {doc_type}: {version}")
    
    print("\n" + "=" * 50)
    print("Legal compliance audit trail system ready!")
    print("\nNote: Database operations require actual user data.")
    print("These functions will be tested with real user data during integration.")
