import React, { useState, useEffect } from 'react';
import './JournalTeaserCard.css';

interface JournalTeaserCardProps {
  metrics: {
    externalAcwr: number;
    internalAcwr: number;
    normalizedDivergence: number;
  };
  onNavigateToJournal: () => void;
}

interface StatusLabel {
  label: string;
  color: string;
}

// Generate recommendation teaser based on metrics
function getRecommendationTeaser(metrics: JournalTeaserCardProps['metrics']): string {
  const { externalAcwr, normalizedDivergence } = metrics;

  // High risk scenario
  if (externalAcwr > 1.3 && normalizedDivergence < -0.05) {
    return 'Your body needs recovery. Time to take it easy.';
  }

  // Elevated load
  if (externalAcwr > 1.3) {
    return 'You\'re pushing hard. Let\'s keep you safe.';
  }

  // Fatigued
  if (normalizedDivergence < -0.05) {
    return 'Your body is showing fatigue. Let\'s adjust your plan.';
  }

  // Optimal zone
  if (externalAcwr >= 0.8 && externalAcwr <= 1.1 && normalizedDivergence >= -0.05) {
    return 'You\'re ready to up your game!';
  }

  // Undertrained
  if (externalAcwr < 0.8) {
    return 'You have room to build. Let\'s plan your next step.';
  }

  return 'Your personalized training recommendation is ready.';
}

const JournalTeaserCard: React.FC<JournalTeaserCardProps> = ({
  metrics,
  onNavigateToJournal
}) => {
  const [shouldShow, setShouldShow] = useState(true);

  useEffect(() => {
    // Check if user is routinely journaling (3+ entries in last 7 days)
    const checkJournalActivity = async () => {
      try {
        const response = await fetch('/api/journal-entries-count');
        if (response.ok) {
          const data = await response.json();
          // Hide teaser if user has 3+ journal entries in last week
          if (data.count_last_week >= 3) {
            setShouldShow(false);
          }
        }
      } catch (error) {
        console.error('Error checking journal activity:', error);
        // Show teaser by default if check fails
      }
    };

    checkJournalActivity();
  }, []);

  if (!shouldShow) {
    return null;
  }

  const recommendationTeaser = getRecommendationTeaser(metrics);

  return (
    <div className="teaser-card">
      <div className="teaser-content">
        <div className="teaser-message">
          {recommendationTeaser}
        </div>
        <div className="teaser-submessage">
          See full recommendation for your next workout.
        </div>
      </div>
      <button className="teaser-cta" onClick={onNavigateToJournal}>
        View on Journal →
      </button>
    </div>
  );
};

export default JournalTeaserCard;
