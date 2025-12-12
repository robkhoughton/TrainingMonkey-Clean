import React, { useState, useEffect } from 'react';
import './DashboardTour.css';
import './DailyStatusPopup.css';

interface Metrics {
  externalAcwr: number;
  internalAcwr: number;
  normalizedDivergence: number;
}

interface DashboardTourProps {
  step: number;
  onNext: () => void;
  onSkip: () => void;
  metrics: Metrics;
}

interface TooltipPosition {
  top: number;
  left: number;
  maxWidth: string;
  transform?: string;
}

const DashboardTour: React.FC<DashboardTourProps> = ({ step, onNext, onSkip, metrics }) => {
  const [syncButtonRect, setSyncButtonRect] = useState<DOMRect | null>(null);
  const [chartRect, setChartRect] = useState<DOMRect | null>(null);
  const [metersRect, setMetersRect] = useState<DOMRect | null>(null);
  const [recoveryRect, setRecoveryRect] = useState<DOMRect | null>(null);

  console.log('DashboardTour render - step:', step);

  // Helper function to calculate optimal tooltip position
  const calculateTooltipPosition = (
    targetRect: DOMRect,
    tooltipWidth: number = 320,
    preferredPosition: 'below' | 'above' | 'auto' = 'auto'
  ): TooltipPosition => {
    const TOOLTIP_OFFSET = 20;
    const SCREEN_PADDING = 20;
    const ESTIMATED_TOOLTIP_HEIGHT = 200; // Approximate height

    const viewportHeight = window.innerHeight;
    const viewportWidth = window.innerWidth;

    // Determine if tooltip should go above or below
    const spaceBelow = viewportHeight - targetRect.bottom;
    const spaceAbove = targetRect.top;

    let shouldPositionAbove = preferredPosition === 'above';
    if (preferredPosition === 'auto') {
      shouldPositionAbove = spaceBelow < ESTIMATED_TOOLTIP_HEIGHT && spaceAbove > spaceBelow;
    }

    // Calculate vertical position
    let top: number;
    if (shouldPositionAbove) {
      // Position above the target
      top = targetRect.top - TOOLTIP_OFFSET;
    } else {
      // Position below the target
      top = targetRect.bottom + TOOLTIP_OFFSET;
    }

    // Ensure tooltip doesn't go off screen vertically
    top = Math.max(SCREEN_PADDING, Math.min(top, viewportHeight - ESTIMATED_TOOLTIP_HEIGHT - SCREEN_PADDING));

    // Calculate horizontal position
    let left = targetRect.left;

    // Check if tooltip would go off screen on the right
    if (left + tooltipWidth > viewportWidth - SCREEN_PADDING) {
      left = viewportWidth - tooltipWidth - SCREEN_PADDING;
    }

    // Check if tooltip would go off screen on the left
    left = Math.max(SCREEN_PADDING, left);

    return {
      top,
      left,
      maxWidth: `${tooltipWidth}px`
    };
  };

  // Helper function to wait for element and get its rect
  const waitForElementAndGetRect = (
    elementId: string,
    setRect: (rect: DOMRect | null) => void,
    maxAttempts: number = 10
  ) => {
    let attempts = 0;
    const checkElement = () => {
      const element = document.getElementById(elementId);
      if (element) {
        // Scroll element into view if needed
        element.scrollIntoView({ behavior: 'smooth', block: 'center' });

        // Wait a moment for scroll to settle before getting rect
        setTimeout(() => {
          const rect = element.getBoundingClientRect();
          setRect(rect);
          console.log(`${elementId} rect set:`, rect);
        }, 300);
      } else if (attempts < maxAttempts) {
        attempts++;
        console.log(`${elementId} not found, attempt ${attempts}/${maxAttempts}`);
        setTimeout(checkElement, 100);
      } else {
        console.log(`${elementId} not found after ${maxAttempts} attempts`);
      }
    };
    checkElement();
  };

  // Update sync button position when step changes to 1
  useEffect(() => {
    if (step === 1) {
      waitForElementAndGetRect('sync-data-button', setSyncButtonRect);
    }
  }, [step]);

  // Update chart position when step changes to 2
  useEffect(() => {
    if (step === 2) {
      waitForElementAndGetRect('overtraining-risk-chart', setChartRect);
    }
  }, [step]);

  // Update at-a-glance meters position when step changes to 3 or 5
  useEffect(() => {
    if (step === 3 || step === 5) {
      waitForElementAndGetRect('at-a-glance-meters', setMetersRect);
    }
  }, [step]);

  // Update recovery metrics position when step changes to 4
  useEffect(() => {
    if (step === 4) {
      waitForElementAndGetRect('recovery-metrics', setRecoveryRect);
    }
  }, [step]);

  if (step === 0) {
    console.log('Tour step is 0, returning null');
    return null;
  }

  // Step 1: Sync Data Button
  if (step === 1) {
    const tooltipPosition = syncButtonRect ? calculateTooltipPosition(syncButtonRect, 280, 'auto') : null;

    return (
      <>
        {/* Overlay to dim the rest of the page */}
        <div className="tour-overlay" onClick={onSkip}></div>

        {/* Highlight box around Sync Data button */}
        {syncButtonRect && (
          <div
            className="tour-highlight"
            style={{
              top: syncButtonRect.top + window.scrollY - 8,
              left: syncButtonRect.left + window.scrollX - 8,
              width: syncButtonRect.width + 16,
              height: syncButtonRect.height + 16
            }}
          ></div>
        )}

        {/* Tooltip with explanation */}
        {syncButtonRect && tooltipPosition && (
          <div
            className="tour-tooltip"
            style={{
              position: 'fixed',
              ...tooltipPosition
            }}
          >
            <div className="tour-tooltip-header">
              <h3 className="tour-tooltip-title">Sync Your Data</h3>
              <button className="tour-close" onClick={onSkip}>×</button>
            </div>

            <p className="tour-tooltip-text">
              Start by syncing your latest activities from Strava. This ensures you're seeing
              your most up-to-date training metrics and recommendations.
            </p>

            <div className="tour-tooltip-actions">
              <span className="tour-step-indicator">Step 1 of 5</span>
              <button className="tour-btn-skip" onClick={onSkip}>
                Skip Tour
              </button>
              <button className="tour-btn-next" onClick={onNext}>
                Next →
              </button>
            </div>
          </div>
        )}
      </>
    );
  }

  // Step 2: Overtraining Risk Chart
  if (step === 2) {
    // Generate contextual assessment based on actual metrics
    const getStatusAssessment = (): string => {
      const { externalAcwr, normalizedDivergence } = metrics;

      // High risk
      if (externalAcwr > 1.3 && normalizedDivergence < -0.05) {
        return 'Values in the red zone indicate high injury risk and accumulated fatigue. Your body needs recovery.';
      }

      // Elevated load
      if (externalAcwr > 1.3) {
        return 'Values in the orange/yellow zone indicate elevated training load. Monitor carefully to avoid overtraining.';
      }

      // Fatigued but not overtrained
      if (normalizedDivergence < -0.05) {
        return 'Divergence in the red indicates accumulated fatigue. Consider lighter training to allow recovery.';
      }

      // Optimal zone
      if (externalAcwr >= 0.8 && externalAcwr <= 1.1 && normalizedDivergence >= -0.05) {
        return 'Values in the green indicate optimal training balance with low injury risk. You\'re adapting well!';
      }

      // Undertrained
      if (externalAcwr < 0.8) {
        return 'Values in the green indicate a low risk of injury and potential detraining. You have room to safely increase training volume.';
      }

      return 'Your metrics are within acceptable ranges. This chart helps you track trends over time.';
    };

    const assessment = getStatusAssessment();

    // Calculate centered position for the chart tooltip
    const tooltipPosition = chartRect ? (() => {
      const basePosition = calculateTooltipPosition(chartRect, 320, 'auto');
      // Center the tooltip horizontally relative to the chart
      const chartCenter = chartRect.left + (chartRect.width / 2);
      const tooltipLeft = Math.max(20, Math.min(
        chartCenter - 160, // 160 is half of 320px tooltip width
        window.innerWidth - 340 // 320px tooltip + 20px padding
      ));
      return { ...basePosition, left: tooltipLeft };
    })() : null;

    return (
      <>
        {/* Overlay */}
        <div className="tour-overlay" onClick={onSkip}></div>

        {/* Highlight box around chart */}
        {chartRect && (
          <div
            className="tour-highlight"
            style={{
              top: chartRect.top + window.scrollY - 8,
              left: chartRect.left + window.scrollX - 8,
              width: chartRect.width + 16,
              height: chartRect.height + 16
            }}
          ></div>
        )}

        {/* Tooltip */}
        {chartRect && tooltipPosition && (
          <div
            className="tour-tooltip"
            style={{
              position: 'fixed',
              ...tooltipPosition
            }}
          >
            <div className="tour-tooltip-header">
              <h3 className="tour-tooltip-title">Your Current Status</h3>
              <button className="tour-close" onClick={onSkip}>×</button>
            </div>

            <p className="tour-tooltip-text">
              <strong>External ACWR: {metrics.externalAcwr.toFixed(2)}</strong><br/>
              <strong>Internal ACWR: {metrics.internalAcwr.toFixed(2)}</strong><br/>
              <strong>Divergence: {metrics.normalizedDivergence > 0 ? '+' : ''}{metrics.normalizedDivergence.toFixed(2)}</strong>
            </p>
            <p className="tour-tooltip-text">
              {assessment}
            </p>

            <div className="tour-tooltip-actions">
              <span className="tour-step-indicator">Step 2 of 5</span>
              <button className="tour-btn-skip" onClick={onSkip}>
                Skip Tour
              </button>
              <button className="tour-btn-next" onClick={onNext}>
                Next →
              </button>
            </div>
          </div>
        )}
      </>
    );
  }

  // Step 3: At-A-Glance Meters
  if (step === 3) {
    const tooltipPosition = metersRect ? calculateTooltipPosition(metersRect, 320, 'auto') : null;

    return (
      <>
        {/* Overlay */}
        <div className="tour-overlay" onClick={onSkip}></div>

        {/* Highlight box around meters */}
        {metersRect && (
          <div
            className="tour-highlight"
            style={{
              top: metersRect.top + window.scrollY - 8,
              left: metersRect.left + window.scrollX - 8,
              width: metersRect.width + 16,
              height: metersRect.height + 16
            }}
          ></div>
        )}

        {/* Tooltip */}
        {metersRect && tooltipPosition && (
          <div
            className="tour-tooltip"
            style={{
              position: 'fixed',
              ...tooltipPosition
            }}
          >
            <div className="tour-tooltip-header">
              <h3 className="tour-tooltip-title">At-A-Glance Summary</h3>
              <button className="tour-close" onClick={onSkip}>×</button>
            </div>

            <p className="tour-tooltip-text">
              This card summarizes your current injury risk and training balance at a glance. The gauges show your External and Internal ACWR values, giving you instant feedback on your training status.
            </p>

            <div className="tour-tooltip-actions">
              <span className="tour-step-indicator">Step 3 of 5</span>
              <button className="tour-btn-skip" onClick={onSkip}>
                Skip Tour
              </button>
              <button className="tour-btn-next" onClick={onNext}>
                Next →
              </button>
            </div>
          </div>
        )}
      </>
    );
  }

  // Step 4: Recovery Metrics
  if (step === 4) {
    const tooltipPosition = recoveryRect ? calculateTooltipPosition(recoveryRect, 320, 'auto') : null;

    return (
      <>
        {/* Overlay */}
        <div className="tour-overlay" onClick={onSkip}></div>

        {/* Highlight box around recovery metrics */}
        {recoveryRect && (
          <div
            className="tour-highlight"
            style={{
              top: recoveryRect.top + window.scrollY - 8,
              left: recoveryRect.left + window.scrollX - 8,
              width: recoveryRect.width + 16,
              height: recoveryRect.height + 16
            }}
          ></div>
        )}

        {/* Tooltip */}
        {recoveryRect && tooltipPosition && (
          <div
            className="tour-tooltip"
            style={{
              position: 'fixed',
              ...tooltipPosition
            }}
          >
            <div className="tour-tooltip-header">
              <h3 className="tour-tooltip-title">Recovery Tracking</h3>
              <button className="tour-close" onClick={onSkip}>×</button>
            </div>

            <p className="tour-tooltip-text">
              This card shows your Days Since Rest and 7-Day Total Load. These metrics help you know when you need recovery or can handle more training volume.
            </p>

            <div className="tour-tooltip-actions">
              <span className="tour-step-indicator">Step 4 of 5</span>
              <button className="tour-btn-skip" onClick={onSkip}>
                Skip Tour
              </button>
              <button className="tour-btn-next" onClick={onNext}>
                Next →
              </button>
            </div>
          </div>
        )}
      </>
    );
  }

  // Step 5: Final Summary - Highlight actual Injury Risk card and show recommendation
  if (step === 5) {
    const handleJournalClick = () => {
      // Complete the tour
      localStorage.setItem('dashboardTour_completed', 'true');
      // Navigate to journal
      window.location.href = '/journal';
    };

    const handleDismiss = () => {
      // Complete the tour
      localStorage.setItem('dashboardTour_completed', 'true');
      onSkip();
    };

    // Helper functions for recommendation
    const calculateRiskLevel = () => {
      const { externalAcwr, normalizedDivergence } = metrics;
      if (externalAcwr > 1.3 && normalizedDivergence < -0.05) return 'HIGH';
      if (externalAcwr > 1.3 || normalizedDivergence < -0.05) return 'MODERATE';
      if (externalAcwr < 0.8) return 'LOW';
      return 'LOW';
    };

    const generateBriefRecommendation = (riskLevel: string) => {
      if (riskLevel === 'HIGH') {
        return 'Rest day strongly recommended';
      }
      if (riskLevel === 'MODERATE') {
        return 'Light training - monitor how you feel';
      }
      return 'You\'re primed for a quality session today';
    };

    const riskLevel = calculateRiskLevel();
    const briefRecommendation = generateBriefRecommendation(riskLevel);

    const tooltipPosition = metersRect ? calculateTooltipPosition(metersRect, 360, 'below') : null;

    return (
      <>
        {/* Overlay */}
        <div className="popup-overlay" onClick={handleDismiss}></div>

        {/* Highlight box around the actual Injury Risk At-A-Glance card */}
        {metersRect && (
          <div
            className="tour-highlight"
            style={{
              top: metersRect.top + window.scrollY - 8,
              left: metersRect.left + window.scrollX - 8,
              width: metersRect.width + 16,
              height: metersRect.height + 16
            }}
          ></div>
        )}

        {/* Tooltip with recommendation and action */}
        {metersRect && tooltipPosition && (
          <div
            className="tour-tooltip"
            style={{
              position: 'fixed',
              ...tooltipPosition
            }}
          >
            <div className="tour-tooltip-header">
              <h3 className="tour-tooltip-title">Ready to Track Your Training?</h3>
              <button className="tour-close" onClick={handleDismiss}>×</button>
            </div>

            <p className="tour-tooltip-text" style={{ marginBottom: '12px' }}>
              Based on your Injury Risk metrics above, here's your personalized recommendation:
            </p>

            {/* Brief Recommendation - styled as informational, not a button */}
            <div style={{
              background: '#f3f4f6',
              border: '2px solid #e5e7eb',
              borderLeft: '4px solid #667eea',
              padding: '12px 16px',
              borderRadius: '6px',
              marginBottom: '16px'
            }}>
              <div style={{
                fontSize: '10px',
                fontWeight: '700',
                textTransform: 'uppercase',
                letterSpacing: '0.5px',
                color: '#6b7280',
                marginBottom: '6px'
              }}>
                TODAY'S RECOMMENDATION:
              </div>
              <div style={{
                fontSize: '15px',
                fontWeight: '600',
                lineHeight: 1.4,
                color: '#1f2937'
              }}>
                {briefRecommendation}
              </div>
            </div>

            <p className="tour-tooltip-text" style={{
              marginBottom: '16px',
              fontSize: '13px',
              fontStyle: 'italic',
              color: '#6b7280'
            }}>
              💡 <strong>Daily workflow:</strong> Check your Injury Risk metrics here on the Dashboard, then visit the <strong>Journal</strong> page to log workouts and see your full AI-powered analysis.
            </p>

            {/* Action button - clearly styled as clickable CTA */}
            <button
              onClick={handleJournalClick}
              style={{
                width: '100%',
                background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                color: 'white',
                padding: '14px 24px',
                borderRadius: '8px',
                fontWeight: '700',
                fontSize: '15px',
                border: 'none',
                cursor: 'pointer',
                transition: 'transform 0.2s, box-shadow 0.2s',
                boxShadow: '0 4px 12px rgba(102, 126, 234, 0.4)',
                textTransform: 'uppercase',
                letterSpacing: '0.5px'
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.transform = 'translateY(-2px)';
                e.currentTarget.style.boxShadow = '0 6px 20px rgba(102, 126, 234, 0.5)';
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.transform = 'translateY(0)';
                e.currentTarget.style.boxShadow = '0 4px 12px rgba(102, 126, 234, 0.4)';
              }}
            >
              Go to Journal →
            </button>

            <p style={{
              marginTop: '12px',
              fontSize: '12px',
              color: '#9ca3af',
              textAlign: 'center'
            }}>
              Step 5 of 5
            </p>
          </div>
        )}
      </>
    );
  }

  return null;
};

export default DashboardTour;
