#!/usr/bin/env python3
"""
Feedback Collection System for TRIMP Enhancement
Collects and validates feedback from beta users and external sources
"""

import logging
import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from enum import Enum

from db_utils import execute_query

logger = logging.getLogger(__name__)


class FeedbackType(Enum):
    """Types of feedback collected"""
    USER_FEEDBACK = "user_feedback"
    ACCURACY_VALIDATION = "accuracy_validation"
    PERFORMANCE_FEEDBACK = "performance_feedback"
    BUG_REPORT = "bug_report"
    FEATURE_REQUEST = "feature_request"


class FeedbackStatus(Enum):
    """Status of feedback items"""
    PENDING = "pending"
    REVIEWED = "reviewed"
    RESOLVED = "resolved"
    REJECTED = "rejected"


@dataclass
class FeedbackItem:
    """Individual feedback item"""
    feedback_id: str
    user_id: Optional[int]
    feedback_type: FeedbackType
    status: FeedbackStatus
    title: str
    description: str
    rating: Optional[int]  # 1-5 scale
    metadata: Dict[str, Any]
    created_at: datetime
    reviewed_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()


@dataclass
class AccuracyValidation:
    """Accuracy validation against external sources"""
    validation_id: str
    user_id: int
    activity_id: int
    external_source: str
    external_trimp_value: float
    our_trimp_value: float
    difference: float
    percentage_difference: float
    validation_method: str
    created_at: datetime


class FeedbackCollectionSystem:
    """System for collecting and managing feedback for TRIMP enhancement"""
    
    def __init__(self):
        self.feedback_items: List[FeedbackItem] = []
        self.accuracy_validations: List[AccuracyValidation] = []
    
    def collect_user_feedback(self, user_id: int, title: str, description: str, 
                            rating: int = None, feedback_type: FeedbackType = FeedbackType.USER_FEEDBACK) -> str:
        """Collect feedback from a user"""
        try:
            feedback_id = f"feedback_{int(time.time() * 1000)}"
            
            feedback_item = FeedbackItem(
                feedback_id=feedback_id,
                user_id=user_id,
                feedback_type=feedback_type,
                status=FeedbackStatus.PENDING,
                title=title,
                description=description,
                rating=rating,
                metadata={
                    'source': 'user_input',
                    'collection_method': 'direct_feedback'
                },
                created_at=datetime.now()
            )
            
            self.feedback_items.append(feedback_item)
            
            # Log the feedback
            logger.info(f"Collected feedback from user {user_id}: {title}")
            
            return feedback_id
            
        except Exception as e:
            logger.error(f"Error collecting user feedback: {str(e)}")
            raise
    
    def collect_accuracy_validation(self, user_id: int, activity_id: int, 
                                  external_source: str, external_trimp: float,
                                  our_trimp: float, validation_method: str) -> str:
        """Collect accuracy validation against external sources"""
        try:
            validation_id = f"validation_{int(time.time() * 1000)}"
            
            difference = our_trimp - external_trimp
            percentage_difference = (difference / external_trimp * 100) if external_trimp > 0 else 0
            
            validation = AccuracyValidation(
                validation_id=validation_id,
                user_id=user_id,
                activity_id=activity_id,
                external_source=external_source,
                external_trimp_value=external_trimp,
                our_trimp_value=our_trimp,
                difference=difference,
                percentage_difference=percentage_difference,
                validation_method=validation_method,
                created_at=datetime.now()
            )
            
            self.accuracy_validations.append(validation)
            
            # Log the validation
            logger.info(f"Collected accuracy validation for user {user_id}, activity {activity_id}: "
                       f"External: {external_trimp}, Our: {our_trimp}, Diff: {difference:.2f}")
            
            return validation_id
            
        except Exception as e:
            logger.error(f"Error collecting accuracy validation: {str(e)}")
            raise
    
    def get_feedback_summary(self, days_back: int = 30) -> Dict[str, Any]:
        """Get summary of feedback collected"""
        try:
            cutoff_date = datetime.now() - timedelta(days=days_back)
            
            # Filter feedback by date
            recent_feedback = [f for f in self.feedback_items if f.created_at >= cutoff_date]
            recent_validations = [v for v in self.accuracy_validations if v.created_at >= cutoff_date]
            
            # Calculate statistics
            total_feedback = len(recent_feedback)
            total_validations = len(recent_validations)
            
            # Feedback by type
            feedback_by_type = {}
            for feedback in recent_feedback:
                feedback_type = feedback.feedback_type.value
                feedback_by_type[feedback_type] = feedback_by_type.get(feedback_type, 0) + 1
            
            # Feedback by status
            feedback_by_status = {}
            for feedback in recent_feedback:
                status = feedback.status.value
                feedback_by_status[status] = feedback_by_status.get(status, 0) + 1
            
            # Average rating
            ratings = [f.rating for f in recent_feedback if f.rating is not None]
            avg_rating = sum(ratings) / len(ratings) if ratings else None
            
            # Accuracy validation statistics
            if recent_validations:
                avg_difference = sum(v.difference for v in recent_validations) / len(recent_validations)
                avg_percentage_difference = sum(v.percentage_difference for v in recent_validations) / len(recent_validations)
                accuracy_within_5_percent = sum(1 for v in recent_validations if abs(v.percentage_difference) <= 5)
                accuracy_within_10_percent = sum(1 for v in recent_validations if abs(v.percentage_difference) <= 10)
            else:
                avg_difference = 0
                avg_percentage_difference = 0
                accuracy_within_5_percent = 0
                accuracy_within_10_percent = 0
            
            return {
                'summary_period_days': days_back,
                'total_feedback': total_feedback,
                'total_validations': total_validations,
                'feedback_by_type': feedback_by_type,
                'feedback_by_status': feedback_by_status,
                'average_rating': round(avg_rating, 2) if avg_rating else None,
                'accuracy_statistics': {
                    'average_difference': round(avg_difference, 2),
                    'average_percentage_difference': round(avg_percentage_difference, 2),
                    'within_5_percent': accuracy_within_5_percent,
                    'within_10_percent': accuracy_within_10_percent,
                    'accuracy_rate_5_percent': round((accuracy_within_5_percent / total_validations * 100) if total_validations > 0 else 0, 1),
                    'accuracy_rate_10_percent': round((accuracy_within_10_percent / total_validations * 100) if total_validations > 0 else 0, 1)
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting feedback summary: {str(e)}")
            return {}
    
    def get_recent_feedback(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Get recent feedback items"""
        try:
            # Sort by creation date (newest first) and limit
            sorted_feedback = sorted(self.feedback_items, key=lambda x: x.created_at, reverse=True)[:limit]
            
            return [
                {
                    'feedback_id': f.feedback_id,
                    'user_id': f.user_id,
                    'feedback_type': f.feedback_type.value,
                    'status': f.status.value,
                    'title': f.title,
                    'description': f.description,
                    'rating': f.rating,
                    'created_at': f.created_at.isoformat(),
                    'reviewed_at': f.reviewed_at.isoformat() if f.reviewed_at else None,
                    'resolved_at': f.resolved_at.isoformat() if f.resolved_at else None
                }
                for f in sorted_feedback
            ]
            
        except Exception as e:
            logger.error(f"Error getting recent feedback: {str(e)}")
            return []
    
    def get_accuracy_validations(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Get recent accuracy validations"""
        try:
            # Sort by creation date (newest first) and limit
            sorted_validations = sorted(self.accuracy_validations, key=lambda x: x.created_at, reverse=True)[:limit]
            
            return [
                {
                    'validation_id': v.validation_id,
                    'user_id': v.user_id,
                    'activity_id': v.activity_id,
                    'external_source': v.external_source,
                    'external_trimp_value': v.external_trimp_value,
                    'our_trimp_value': v.our_trimp_value,
                    'difference': v.difference,
                    'percentage_difference': v.percentage_difference,
                    'validation_method': v.validation_method,
                    'created_at': v.created_at.isoformat()
                }
                for v in sorted_validations
            ]
            
        except Exception as e:
            logger.error(f"Error getting accuracy validations: {str(e)}")
            return []
    
    def update_feedback_status(self, feedback_id: str, new_status: FeedbackStatus, 
                             notes: str = None) -> bool:
        """Update the status of a feedback item"""
        try:
            for feedback in self.feedback_items:
                if feedback.feedback_id == feedback_id:
                    feedback.status = new_status
                    
                    if new_status == FeedbackStatus.REVIEWED:
                        feedback.reviewed_at = datetime.now()
                    elif new_status == FeedbackStatus.RESOLVED:
                        feedback.resolved_at = datetime.now()
                    
                    if notes:
                        feedback.metadata['admin_notes'] = notes
                    
                    logger.info(f"Updated feedback {feedback_id} status to {new_status.value}")
                    return True
            
            logger.warning(f"Feedback item {feedback_id} not found")
            return False
            
        except Exception as e:
            logger.error(f"Error updating feedback status: {str(e)}")
            return False
    
    def generate_feedback_report(self) -> Dict[str, Any]:
        """Generate a comprehensive feedback report"""
        try:
            summary = self.get_feedback_summary(30)  # Last 30 days
            recent_feedback = self.get_recent_feedback(50)
            recent_validations = self.get_accuracy_validations(50)
            
            # Calculate overall satisfaction score
            ratings = [f['rating'] for f in recent_feedback if f['rating'] is not None]
            satisfaction_score = sum(ratings) / len(ratings) if ratings else None
            
            # Calculate accuracy score
            accuracy_score = summary['accuracy_statistics']['accuracy_rate_5_percent']
            
            # Generate recommendations
            recommendations = self._generate_feedback_recommendations(summary, recent_feedback, recent_validations)
            
            return {
                'report_generated_at': datetime.now().isoformat(),
                'summary': summary,
                'recent_feedback': recent_feedback,
                'recent_validations': recent_validations,
                'overall_scores': {
                    'satisfaction_score': round(satisfaction_score, 2) if satisfaction_score else None,
                    'accuracy_score': accuracy_score
                },
                'recommendations': recommendations
            }
            
        except Exception as e:
            logger.error(f"Error generating feedback report: {str(e)}")
            return {}
    
    def _generate_feedback_recommendations(self, summary: Dict, recent_feedback: List, 
                                         recent_validations: List) -> List[str]:
        """Generate recommendations based on feedback analysis"""
        recommendations = []
        
        # Check satisfaction score
        ratings = [f['rating'] for f in recent_feedback if f['rating'] is not None]
        if ratings:
            avg_rating = sum(ratings) / len(ratings)
            if avg_rating < 3.0:
                recommendations.append("⚠️ Low user satisfaction - investigate and address user concerns")
            elif avg_rating >= 4.0:
                recommendations.append("✅ High user satisfaction - consider proceeding to general release")
        
        # Check accuracy
        accuracy_5_percent = summary['accuracy_statistics']['accuracy_rate_5_percent']
        if accuracy_5_percent < 80:
            recommendations.append("⚠️ Accuracy below 80% - review TRIMP calculation algorithm")
        elif accuracy_5_percent >= 90:
            recommendations.append("✅ High accuracy achieved - TRIMP calculations are reliable")
        
        # Check feedback volume
        total_feedback = summary['total_feedback']
        if total_feedback < 5:
            recommendations.append("📊 Low feedback volume - encourage more user feedback")
        elif total_feedback > 50:
            recommendations.append("📈 High feedback volume - prioritize addressing common issues")
        
        # Check bug reports
        bug_reports = [f for f in recent_feedback if f['feedback_type'] == 'bug_report']
        if len(bug_reports) > 5:
            recommendations.append("🐛 Multiple bug reports - prioritize bug fixes before general release")
        
        # Check feature requests
        feature_requests = [f for f in recent_feedback if f['feedback_type'] == 'feature_request']
        if len(feature_requests) > 10:
            recommendations.append("💡 Many feature requests - consider roadmap planning")
        
        return recommendations


# Global instance for use in routes
feedback_system = FeedbackCollectionSystem()
