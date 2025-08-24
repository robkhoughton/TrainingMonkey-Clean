// Add these interfaces at the top of your TrainingLoadDashboard.tsx file (after existing interfaces)

interface LLMRecommendation {
  id: number;
  generation_date: string;
  valid_until: string;
  daily_recommendation: string;
  weekly_recommendation: string;
  pattern_insights: string;
}

// Add these state variables to your component (after existing useState declarations)

const [recommendation, setRecommendation] = useState<LLMRecommendation | null>(null);
const [isLoadingRecommendation, setIsLoadingRecommendation] = useState<boolean>(false);

// Add these functions to your component (after existing helper functions)

// Function to fetch LLM recommendations
const fetchRecommendations = async () => {
  console.log("fetchRecommendations called");
  try {
    setIsLoadingRecommendation(true);
    console.log("Fetching recommendations from /api/llm-recommendations");
    const response = await fetch('/api/llm-recommendations');
    console.log("Response status:", response.status);

    if (!response.ok) {
      console.error(`API response not OK: ${response.status}`);
      throw new Error(`API responded with status ${response.status}`);
    }

    const result = await response.json();
    console.log("Recommendation API result:", result);

    if (result.recommendation) {
      console.log("Setting recommendation state with:", result.recommendation);
      setRecommendation(result.recommendation);
    } else {
      console.log("No recommendation in result:", result);
    }
  } catch (error) {
    console.error("Error fetching recommendations:", error);
  } finally {
    setIsLoadingRecommendation(false);
  }
};

// Function to generate new recommendations
const generateNewRecommendation = async () => {
  try {
    setIsLoadingRecommendation(true);
    const response = await fetch('/api/llm-recommendations/generate', {
      method: 'POST'
    });

    if (!response.ok) {
      throw new Error(`API responded with status ${response.status}`);
    }

    const result = await response.json();

    if (result.recommendation) {
      setRecommendation(result.recommendation);
    }
  } catch (error) {
    console.error("Error generating new recommendation:", error);
  } finally {
    setIsLoadingRecommendation(false);
  }
};

// Add this call to your main useEffect (after the existing API calls)
// Add this line after the existing fetchWellnessMetrics() call in your main useEffect:

fetchRecommendations();

// Add this component right before the closing </div> of your main container
// (after the Distance & Elevation Chart)

{/* Enhanced Training Recommendations Section */}
<div className={styles.chartContainer}>
  <h2 className={styles.chartTitle}>Training Recommendations & Analysis</h2>

  {/* Status Banner */}
  <div style={{
    backgroundColor:
      metrics.normalizedDivergence < -0.15 ? '#fee2e2' : // red-100
      metrics.normalizedDivergence < -0.05 ? '#fef3c7' : // yellow-100
      metrics.externalAcwr > 1.3 || metrics.internalAcwr > 1.3 ? '#fed7aa' : // orange-100
      '#d1fae5', // green-100
    color:
      metrics.normalizedDivergence < -0.15 ? '#991b1b' : // red-800
      metrics.normalizedDivergence < -0.05 ? '#92400e' : // yellow-800
      metrics.externalAcwr > 1.3 || metrics.internalAcwr > 1.3 ? '#9a3412' : // orange-800
      '#065f46', // green-800
    padding: '0.75rem',
    borderRadius: '0.5rem',
    marginBottom: '1rem',
    fontWeight: '600',
    textAlign: 'center' as const
  }}>
    Assessment Status: {
      metrics.normalizedDivergence < -0.15 ? 'HIGH OVERTRAINING RISK' :
      metrics.normalizedDivergence < -0.05 ? 'MODERATE FATIGUE' :
      metrics.externalAcwr > 1.3 || metrics.internalAcwr > 1.3 ? 'ELEVATED ACWR' :
      metrics.daysSinceRest > 7 ? 'EXTENDED TRAINING BLOCK' :
      'BALANCED TRAINING'
    }
  </div>

  <div className={styles.recommendationsGrid}>
    {/* Today's Training Decision */}
    <div>
      <h3 className={styles.recommendationHeading}>
        🎯 Today's Training Decision
      </h3>

      <div className={styles.recommendationTabs}>
        <div className={styles.recommendationTab} style={{borderLeft: '3px solid #3b82f6'}}>
          <h4 className={styles.tabHeading}>
            🤖 AI Analysis
          </h4>
          <div style={{padding: '0.5rem 0'}}>
            {recommendation ? (
              <>
                <p className={styles.recommendationText}>
                  {recommendation.daily_recommendation}
                </p>
                <div style={{marginTop: '0.5rem'}}>
                  <small style={{color: '#6b7280', fontSize: '0.75rem'}}>
                    Based on: Ext ACWR {metrics.externalAcwr?.toFixed(2)},
                    Int ACWR {metrics.internalAcwr?.toFixed(2)},
                    Divergence {metrics.normalizedDivergence?.toFixed(2)}
                  </small>
                </div>
              </>
            ) : (
              <div>
                {isLoadingRecommendation ? (
                  <p>Generating AI analysis...</p>
                ) : (
                  <p className={styles.recommendationText}>
                    No AI recommendation available. Click "Generate AI Analysis" below.
                  </p>
                )}
              </div>
            )}
          </div>
        </div>

        <div className={styles.recommendationTab} style={{borderLeft: '3px solid #10b981'}}>
          <h4 className={styles.tabHeading}>
            📋 Rules-Based Quick Check
          </h4>
          <div style={{padding: '0.5rem 0'}}>
            <p className={styles.recommendationText}>
              {metrics.daysSinceRest > 7 ? (
                <span style={{ color: colors.danger }}>
                  <strong>🛑 MANDATORY REST:</strong> {metrics.daysSinceRest} days without rest exceeds safe limits.
                  Complete rest day required.
                </span>
              ) : metrics.normalizedDivergence < -0.15 ? (
                <span style={{ color: colors.danger }}>
                  <strong>⚠️ HIGH RISK:</strong> Normalized divergence of {metrics.normalizedDivergence?.toFixed(2)}
                  indicates significant overtraining risk. Rest or very light activity only.
                </span>
              ) : metrics.normalizedDivergence < -0.05 ? (
                <span style={{ color: colors.warning }}>
                  <strong>🔶 CAUTION:</strong> Divergence of {metrics.normalizedDivergence?.toFixed(2)} shows
                  moderate fatigue. Reduce intensity by 20-30% from planned workout.
                </span>
              ) : metrics.externalAcwr > 1.3 || metrics.internalAcwr > 1.3 ? (
                <span style={{ color: colors.warning }}>
                  <strong>📈 ELEVATED ACWR:</strong> External: {metrics.externalAcwr?.toFixed(2)},
                  Internal: {metrics.internalAcwr?.toFixed(2)}. Reduce volume by 25% to manage injury risk.
                </span>
              ) : metrics.daysSinceRest > 5 && metrics.normalizedDivergence < -0.02 ? (
                <span style={{ color: colors.warning }}>
                  <strong>🔄 RECOVERY NEEDED:</strong> {metrics.daysSinceRest} days since rest with slight fatigue.
                  Active recovery or easy Zone 1-2 session recommended.
                </span>
              ) : metrics.externalAcwr < 0.8 && metrics.internalAcwr < 0.8 ? (
                <span style={{ color: colors.primary }}>
                  <strong>📊 PROGRESSION OPPORTUNITY:</strong> Both ACWR values below 0.8 indicate potential
                  for 10-15% load increase if feeling good.
                </span>
              ) : (
                <span style={{ color: colors.secondary }}>
                  <strong>✅ GREEN LIGHT:</strong> All metrics in optimal ranges. Proceed with planned training.
                  Current load balance looks sustainable.
                </span>
              )}
            </p>
          </div>
        </div>
      </div>
    </div>

    {/* Weekly Strategy */}
    <div>
      <h3 className={styles.recommendationHeading}>
        📅 Weekly Strategy
      </h3>

      <div className={styles.recommendationTabs}>
        <div className={styles.recommendationTab} style={{borderLeft: '3px solid #3b82f6'}}>
          <h4 className={styles.tabHeading}>
            🤖 Strategic Planning
          </h4>
          <div style={{padding: '0.5rem 0'}}>
            <p className={styles.recommendationText}>
              {recommendation ? recommendation.weekly_recommendation : "Generate AI analysis for weekly planning insights"}
            </p>
          </div>
        </div>

        <div className={styles.recommendationTab} style={{borderLeft: '3px solid #10b981'}}>
          <h4 className={styles.tabHeading}>
            📋 ACWR Management
          </h4>
          <div style={{padding: '0.5rem 0'}}>
            <p className={styles.recommendationText}>
              {metrics.externalAcwr > 1.3 || metrics.internalAcwr > 1.3 ? (
                <>
                  <strong>Step-back week needed:</strong> Current 7-day average ({metrics.sevenDayAvgLoad?.toFixed(1)} mi/day)
                  is too high. Target reducing to {(metrics.sevenDayAvgLoad * 0.75)?.toFixed(1)} mi/day over next 5-7 days.
                </>
              ) : metrics.externalAcwr < 0.8 && metrics.internalAcwr < 0.8 ? (
                <>
                  <strong>Progressive build opportunity:</strong> Gradually increase 7-day average from {metrics.sevenDayAvgLoad?.toFixed(1)}
                  to {(metrics.sevenDayAvgLoad * 1.15)?.toFixed(1)} mi/day over next 2 weeks.
                </>
              ) : (
                <>
                  <strong>Maintenance phase:</strong> Current 7-day average ({metrics.sevenDayAvgLoad?.toFixed(1)} mi/day)
                  is in optimal range. Continue with similar daily volumes.
                </>
              )}
            </p>
          </div>
        </div>
      </div>
    </div>

    {/* Pattern Analysis */}
    <div>
      <h3 className={styles.recommendationHeading}>
        🔍 Pattern Analysis
      </h3>

      <div className={styles.recommendationTabs}>
        <div className={styles.recommendationTab} style={{borderLeft: '3px solid #3b82f6'}}>
          <h4 className={styles.tabHeading}>
            🤖 Advanced Insights
          </h4>
          <div style={{padding: '0.5rem 0'}}>
            <p className={styles.recommendationText}>
              {recommendation ? recommendation.pattern_insights : "Generate AI analysis for detailed pattern recognition"}
            </p>
          </div>
        </div>

        <div className={styles.recommendationTab} style={{borderLeft: '3px solid #10b981'}}>
          <h4 className={styles.tabHeading}>
            📋 Key Observations
          </h4>
          <div style={{padding: '0.5rem 0'}}>
            <div style={{display: 'flex', flexDirection: 'column' as const, gap: '0.75rem'}}>
              <div>
                <strong>Load Balance:</strong>
                <span style={{marginLeft: '0.5rem', color: '#4b5563'}}>
                  {Math.abs(metrics.normalizedDivergence) < 0.05 ?
                    "External and internal loads are well-balanced, indicating good adaptation." :
                    metrics.normalizedDivergence < -0.05 ?
                    "Internal stress is elevated relative to external work - focus on recovery." :
                    "External work capacity exceeds internal stress - opportunity for intensity increases."
                  }
                </span>
              </div>

              <div>
                <strong>Recovery Pattern:</strong>
                <span style={{marginLeft: '0.5rem', color: '#4b5563'}}>
                  {metrics.daysSinceRest <= 2 ? "Recent rest day supporting good recovery cycle." :
                   metrics.daysSinceRest <= 5 ? `${metrics.daysSinceRest} days since rest - within normal range.` :
                   `${metrics.daysSinceRest} days without rest - consider scheduling recovery soon.`}
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>

  {/* Action Center */}
  <div style={{
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginTop: '1.5rem',
    padding: '1rem',
    backgroundColor: '#f8f9fa',
    borderRadius: '0.5rem'
  }}>
    <div>
      {recommendation ? (
        <div>
          <span style={{fontWeight: '500', color: '#374151'}}>AI Analysis:</span>
          <span style={{marginLeft: '0.5rem', color: '#6b7280'}}>
            {new Date(recommendation.generation_date).toLocaleDateString()}
          </span>
        </div>
      ) : (
        <div>
          <span style={{color: '#6b7280', fontSize: '0.875rem'}}>
            AI analysis provides personalized insights based on your training patterns.
          </span>
        </div>
      )}
    </div>

    <div style={{display: 'flex', alignItems: 'center', gap: '1rem'}}>
      {recommendation ? (
        <button
          onClick={generateNewRecommendation}
          className={styles.refreshButton}
          disabled={isLoadingRecommendation}
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '0.5rem'
          }}
        >
          {isLoadingRecommendation ? (
            <>
              <span style={{
                display: 'inline-block',
                width: '1rem',
                height: '1rem',
                border: '2px solid #f3f4f6',
                borderTop: '2px solid #3b82f6',
                borderRadius: '50%',
                animation: 'spin 1s linear infinite'
              }}></span>
              Updating...
            </>
          ) : (
            <>
              <span>🔄</span>
              Refresh Analysis
            </>
          )}
        </button>
      ) : (
        <button
          onClick={generateNewRecommendation}
          className={styles.generateButton}
          disabled={isLoadingRecommendation}
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '0.5rem'
          }}
        >
          {isLoadingRecommendation ? (
            <>
              <span style={{
                display: 'inline-block',
                width: '1rem',
                height: '1rem',
                border: '2px solid #f3f4f6',
                borderTop: '2px solid #3b82f6',
                borderRadius: '50%',
                animation: 'spin 1s linear infinite'
              }}></span>
              Generating...
            </>
          ) : (
            <>
              <span>🤖</span>
              Generate AI Analysis
            </>
          )}
        </button>
      )}
    </div>
  </div>
</div>