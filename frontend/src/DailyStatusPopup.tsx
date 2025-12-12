import React from 'react';
import './DailyStatusPopup.css';

interface DailyStatusPopupProps {
  metrics: {
    externalAcwr: number;
    internalAcwr: number;
    normalizedDivergence: number;
    daysSinceRest: number;
  };
  onNavigateToJournal: () => void;
  onDismiss: () => void;
}

// Helper functions for status calculations
function calculateRiskLevel(metrics: DailyStatusPopupProps['metrics']): string {
  const { externalAcwr, normalizedDivergence } = metrics;

  if (externalAcwr > 1.3 && normalizedDivergence < -0.05) return 'HIGH';
  if (externalAcwr > 1.3 || normalizedDivergence < -0.05) return 'MODERATE';
  if (externalAcwr < 0.8) return 'LOW';
  return 'LOW';
}

function generateBriefRecommendation(riskLevel: string, daysSinceRest: number): string {
  if (riskLevel === 'HIGH') {
    return 'Rest day strongly recommended';
  }

  if (riskLevel === 'MODERATE' && daysSinceRest > 5) {
    return 'Easy recovery or rest day';
  }

  if (riskLevel === 'MODERATE') {
    return 'Light training - monitor how you feel';
  }

  return 'You\'re primed for a quality session today';
}

const DailyStatusPopup: React.FC<DailyStatusPopupProps> = ({
  metrics,
  onNavigateToJournal,
  onDismiss
}) => {
  // Calculate risk assessment and recommendation
  const riskLevel = calculateRiskLevel(metrics);
  const briefRecommendation = generateBriefRecommendation(riskLevel, metrics.daysSinceRest);

  return (
    <div className="popup-overlay">
      <div className="popup-content">
        <button className="popup-close" onClick={onDismiss} aria-label="Close">✕</button>

        <h2 className="popup-title">YOUR TRAINING STATUS</h2>

        {/* Brief Recommendation */}
        <div className="recommendation-preview">
          <div className="rec-label">NEXT WORKOUT:</div>
          <div className="rec-text">{briefRecommendation}</div>
        </div>

        {/* Actions */}
        <div className="popup-actions">
          <button className="btn-primary" onClick={onNavigateToJournal}>
            Log your workout and see full analysis
          </button>
        </div>
      </div>
    </div>
  );
};

export default DailyStatusPopup;
