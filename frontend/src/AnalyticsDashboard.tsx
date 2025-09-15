import React, { useState, useEffect } from 'react';

interface ClickThroughRate {
  integration_point: string;
  total_impressions: number;
  total_clicks: number;
  click_through_rate: number;
  unique_users: number;
  conversion_rate: number;
  time_period: string;
  date_range: {
    start: string;
    end: string;
  };
}

interface UserJourneyFunnel {
  time_period: string;
  date_range: {
    start: string;
    end: string;
  };
  steps: Array<{
    step_name: string;
    unique_users: number;
    total_events: number;
    conversion_rate: number | null;
  }>;
}

interface TutorialAnalytics {
  time_period: string;
  date_range: {
    start: string;
    end: string;
  };
  tutorials: Array<{
    tutorial_id: string;
    starts: number;
    completions: number;
    skips: number;
    unique_users: number;
    completion_rate: number;
    skip_rate: number;
  }>;
}

const AnalyticsDashboard: React.FC = () => {
  const [clickThroughRates, setClickThroughRates] = useState<ClickThroughRate[]>([]);
  const [userJourneyFunnel, setUserJourneyFunnel] = useState<UserJourneyFunnel | null>(null);
  const [tutorialAnalytics, setTutorialAnalytics] = useState<TutorialAnalytics | null>(null);
  const [timePeriod, setTimePeriod] = useState<string>('7d');
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [activeTab, setActiveTab] = useState<'ctr' | 'funnel' | 'tutorials'>('ctr');

  // Load analytics data
  useEffect(() => {
    loadAnalyticsData();
  }, [timePeriod]);

  const loadAnalyticsData = async () => {
    setIsLoading(true);
    try {
      // Load click-through rates
      const ctrResponse = await fetch(`/api/analytics/click-through-rates?time_period=${timePeriod}`);
      const ctrData = await ctrResponse.json();
      if (ctrData.success) {
        setClickThroughRates(ctrData.data);
      }

      // Load user journey funnel
      const funnelResponse = await fetch(`/api/analytics/user-journey-funnel?time_period=${timePeriod}`);
      const funnelData = await funnelResponse.json();
      if (funnelData.success) {
        setUserJourneyFunnel(funnelData.data);
      }

      // Load tutorial analytics
      const tutorialResponse = await fetch(`/api/analytics/tutorial-metrics?time_period=${timePeriod}`);
      const tutorialData = await tutorialResponse.json();
      if (tutorialData.success) {
        setTutorialAnalytics(tutorialData.data);
      }

    } catch (error) {
      console.error('Error loading analytics data:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const formatIntegrationPointName = (point: string): string => {
    return point.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
  };

  const getCTRColor = (ctr: number): string => {
    if (ctr >= 10) return '#10b981'; // Green
    if (ctr >= 5) return '#f59e0b'; // Yellow
    if (ctr >= 2) return '#ef4444'; // Red
    return '#6b7280'; // Gray
  };

  const getConversionColor = (rate: number): string => {
    if (rate >= 20) return '#10b981'; // Green
    if (rate >= 10) return '#f59e0b'; // Yellow
    if (rate >= 5) return '#ef4444'; // Red
    return '#6b7280'; // Gray
  };

  if (isLoading) {
    return (
      <div style={{ padding: '2rem', textAlign: 'center' }}>
        <div style={{ fontSize: '1.5rem', marginBottom: '1rem' }}>⏳</div>
        <p>Loading analytics data...</p>
      </div>
    );
  }

  return (
    <div style={{ padding: '2rem', maxWidth: '1200px', margin: '0 auto' }}>
      {/* Header */}
      <div style={{ marginBottom: '2rem' }}>
        <h1 style={{ margin: '0 0 0.5rem 0', fontSize: '2rem', fontWeight: '600', color: '#374151' }}>
          Analytics Dashboard
        </h1>
        <p style={{ margin: 0, color: '#6b7280' }}>
          Track integration point performance and user journey metrics
        </p>
      </div>

      {/* Time Period Selector */}
      <div style={{ marginBottom: '2rem' }}>
        <label style={{ marginRight: '1rem', fontWeight: '500', color: '#374151' }}>
          Time Period:
        </label>
        <select
          value={timePeriod}
          onChange={(e) => setTimePeriod(e.target.value)}
          style={{
            padding: '0.5rem',
            border: '1px solid #d1d5db',
            borderRadius: '6px',
            backgroundColor: 'white',
            fontSize: '0.875rem'
          }}
        >
          <option value="1d">Last 24 Hours</option>
          <option value="7d">Last 7 Days</option>
          <option value="30d">Last 30 Days</option>
          <option value="90d">Last 90 Days</option>
        </select>
      </div>

      {/* Tabs */}
      <div style={{ marginBottom: '2rem' }}>
        <div style={{ display: 'flex', gap: '0.5rem', borderBottom: '1px solid #e5e7eb' }}>
          {[
            { id: 'ctr', label: 'Click-Through Rates', icon: '📊' },
            { id: 'funnel', label: 'User Journey Funnel', icon: '🔄' },
            { id: 'tutorials', label: 'Tutorial Analytics', icon: '🎓' }
          ].map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id as any)}
              style={{
                padding: '0.75rem 1.5rem',
                border: 'none',
                borderBottom: activeTab === tab.id ? '2px solid #3b82f6' : '2px solid transparent',
                backgroundColor: 'transparent',
                color: activeTab === tab.id ? '#3b82f6' : '#6b7280',
                cursor: 'pointer',
                fontSize: '0.875rem',
                fontWeight: '500',
                display: 'flex',
                alignItems: 'center',
                gap: '0.5rem'
              }}
            >
              <span>{tab.icon}</span>
              {tab.label}
            </button>
          ))}
        </div>
      </div>

      {/* Click-Through Rates Tab */}
      {activeTab === 'ctr' && (
        <div>
          <h2 style={{ margin: '0 0 1.5rem 0', fontSize: '1.5rem', fontWeight: '600', color: '#374151' }}>
            Integration Point Performance
          </h2>
          
          {clickThroughRates.length === 0 ? (
            <div style={{ textAlign: 'center', padding: '3rem', color: '#6b7280' }}>
              <div style={{ fontSize: '2rem', marginBottom: '1rem' }}>📈</div>
              <p>No click-through rate data available for the selected time period.</p>
            </div>
          ) : (
            <div style={{ display: 'grid', gap: '1rem' }}>
              {clickThroughRates.map((ctr, index) => (
                <div
                  key={ctr.integration_point}
                  style={{
                    border: '1px solid #e5e7eb',
                    borderRadius: '8px',
                    padding: '1.5rem',
                    backgroundColor: 'white',
                    boxShadow: '0 1px 3px rgba(0, 0, 0, 0.1)'
                  }}
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '1rem' }}>
                    <div>
                      <h3 style={{ margin: '0 0 0.5rem 0', fontSize: '1.125rem', fontWeight: '600', color: '#374151' }}>
                        {formatIntegrationPointName(ctr.integration_point)}
                      </h3>
                      <p style={{ margin: 0, color: '#6b7280', fontSize: '0.875rem' }}>
                        {ctr.date_range.start} to {ctr.date_range.end}
                      </p>
                    </div>
                    <div style={{ textAlign: 'right' }}>
                      <div style={{ fontSize: '1.5rem', fontWeight: '700', color: getCTRColor(ctr.click_through_rate) }}>
                        {ctr.click_through_rate}%
                      </div>
                      <div style={{ fontSize: '0.75rem', color: '#6b7280' }}>CTR</div>
                    </div>
                  </div>
                  
                  <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(120px, 1fr))', gap: '1rem' }}>
                    <div>
                      <div style={{ fontSize: '1.25rem', fontWeight: '600', color: '#374151' }}>
                        {ctr.total_impressions.toLocaleString()}
                      </div>
                      <div style={{ fontSize: '0.75rem', color: '#6b7280' }}>Impressions</div>
                    </div>
                    <div>
                      <div style={{ fontSize: '1.25rem', fontWeight: '600', color: '#374151' }}>
                        {ctr.total_clicks.toLocaleString()}
                      </div>
                      <div style={{ fontSize: '0.75rem', color: '#6b7280' }}>Clicks</div>
                    </div>
                    <div>
                      <div style={{ fontSize: '1.25rem', fontWeight: '600', color: '#374151' }}>
                        {ctr.unique_users.toLocaleString()}
                      </div>
                      <div style={{ fontSize: '0.75rem', color: '#6b7280' }}>Unique Users</div>
                    </div>
                    <div>
                      <div style={{ fontSize: '1.25rem', fontWeight: '600', color: getConversionColor(ctr.conversion_rate) }}>
                        {ctr.conversion_rate}%
                      </div>
                      <div style={{ fontSize: '0.75rem', color: '#6b7280' }}>Conversion</div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* User Journey Funnel Tab */}
      {activeTab === 'funnel' && userJourneyFunnel && (
        <div>
          <h2 style={{ margin: '0 0 1.5rem 0', fontSize: '1.5rem', fontWeight: '600', color: '#374151' }}>
            User Journey Conversion Funnel
          </h2>
          
          <div style={{ display: 'grid', gap: '1rem' }}>
            {userJourneyFunnel.steps.map((step, index) => (
              <div
                key={step.step_name}
                style={{
                  border: '1px solid #e5e7eb',
                  borderRadius: '8px',
                  padding: '1.5rem',
                  backgroundColor: 'white',
                  boxShadow: '0 1px 3px rgba(0, 0, 0, 0.1)',
                  position: 'relative'
                }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <div>
                    <h3 style={{ margin: '0 0 0.5rem 0', fontSize: '1.125rem', fontWeight: '600', color: '#374151' }}>
                      {step.step_name}
                    </h3>
                    <p style={{ margin: 0, color: '#6b7280', fontSize: '0.875rem' }}>
                      {step.total_events.toLocaleString()} total events
                    </p>
                  </div>
                  <div style={{ textAlign: 'right' }}>
                    <div style={{ fontSize: '1.5rem', fontWeight: '700', color: '#374151' }}>
                      {step.unique_users.toLocaleString()}
                    </div>
                    <div style={{ fontSize: '0.75rem', color: '#6b7280' }}>Users</div>
                    {step.conversion_rate !== null && (
                      <div style={{ fontSize: '0.875rem', color: '#10b981', fontWeight: '500', marginTop: '0.25rem' }}>
                        {step.conversion_rate}% conversion
                      </div>
                    )}
                  </div>
                </div>
                
                {/* Progress bar */}
                <div style={{ marginTop: '1rem' }}>
                  <div style={{ 
                    width: '100%', 
                    height: '8px', 
                    backgroundColor: '#e5e7eb', 
                    borderRadius: '4px',
                    overflow: 'hidden'
                  }}>
                    <div style={{
                      width: `${Math.min(100, (step.unique_users / (userJourneyFunnel.steps[0]?.unique_users || 1)) * 100)}%`,
                      height: '100%',
                      backgroundColor: '#3b82f6',
                      transition: 'width 0.3s ease'
                    }} />
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Tutorial Analytics Tab */}
      {activeTab === 'tutorials' && tutorialAnalytics && (
        <div>
          <h2 style={{ margin: '0 0 1.5rem 0', fontSize: '1.5rem', fontWeight: '600', color: '#374151' }}>
            Tutorial Performance Analytics
          </h2>
          
          {tutorialAnalytics.tutorials.length === 0 ? (
            <div style={{ textAlign: 'center', padding: '3rem', color: '#6b7280' }}>
              <div style={{ fontSize: '2rem', marginBottom: '1rem' }}>🎓</div>
              <p>No tutorial analytics data available for the selected time period.</p>
            </div>
          ) : (
            <div style={{ display: 'grid', gap: '1rem' }}>
              {tutorialAnalytics.tutorials.map((tutorial) => (
                <div
                  key={tutorial.tutorial_id}
                  style={{
                    border: '1px solid #e5e7eb',
                    borderRadius: '8px',
                    padding: '1.5rem',
                    backgroundColor: 'white',
                    boxShadow: '0 1px 3px rgba(0, 0, 0, 0.1)'
                  }}
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '1rem' }}>
                    <div>
                      <h3 style={{ margin: '0 0 0.5rem 0', fontSize: '1.125rem', fontWeight: '600', color: '#374151' }}>
                        {tutorial.tutorial_id.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
                      </h3>
                      <p style={{ margin: 0, color: '#6b7280', fontSize: '0.875rem' }}>
                        {tutorialAnalytics.date_range.start} to {tutorialAnalytics.date_range.end}
                      </p>
                    </div>
                    <div style={{ textAlign: 'right' }}>
                      <div style={{ fontSize: '1.5rem', fontWeight: '700', color: getConversionColor(tutorial.completion_rate) }}>
                        {tutorial.completion_rate}%
                      </div>
                      <div style={{ fontSize: '0.75rem', color: '#6b7280' }}>Completion</div>
                    </div>
                  </div>
                  
                  <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(120px, 1fr))', gap: '1rem' }}>
                    <div>
                      <div style={{ fontSize: '1.25rem', fontWeight: '600', color: '#374151' }}>
                        {tutorial.starts.toLocaleString()}
                      </div>
                      <div style={{ fontSize: '0.75rem', color: '#6b7280' }}>Starts</div>
                    </div>
                    <div>
                      <div style={{ fontSize: '1.25rem', fontWeight: '600', color: '#10b981' }}>
                        {tutorial.completions.toLocaleString()}
                      </div>
                      <div style={{ fontSize: '0.75rem', color: '#6b7280' }}>Completions</div>
                    </div>
                    <div>
                      <div style={{ fontSize: '1.25rem', fontWeight: '600', color: '#ef4444' }}>
                        {tutorial.skips.toLocaleString()}
                      </div>
                      <div style={{ fontSize: '0.75rem', color: '#6b7280' }}>Skips</div>
                    </div>
                    <div>
                      <div style={{ fontSize: '1.25rem', fontWeight: '600', color: '#374151' }}>
                        {tutorial.unique_users.toLocaleString()}
                      </div>
                      <div style={{ fontSize: '0.75rem', color: '#6b7280' }}>Unique Users</div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default AnalyticsDashboard;
