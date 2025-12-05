import React, { useState, useEffect } from 'react';
import styles from './TrainingLoadDashboard.module.css';
import { usePagePerformanceMonitoring, useComponentPerformanceMonitoring } from './usePerformanceMonitoring';
import RaceGoalsManager from './RaceGoalsManager';

interface RaceGoal {
  id: number;
  race_name: string;
  race_date: string;
  race_type: string | null;
  priority: 'A' | 'B' | 'C';
  target_time: string | null;
  notes: string | null;
  elevation_gain_feet: number | null;
}

const RaceGoalsPage: React.FC = () => {
  // Performance monitoring
  usePagePerformanceMonitoring('race-goals');
  const perfMonitor = useComponentPerformanceMonitoring('RaceGoalsPage');

  const [raceGoals, setRaceGoals] = useState<RaceGoal[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const fetchRaceGoals = async () => {
    try {
      perfMonitor.trackFetchStart();
      const response = await fetch('/api/coach/race-goals');
      if (!response.ok) {
        throw new Error('Failed to fetch race goals');
      }
      const data = await response.json();
      setRaceGoals(data.goals || []);
      perfMonitor.trackFetchEnd();
      perfMonitor.reportMetrics(data.goals?.length || 0);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to load race goals';
      setError(errorMessage);
      perfMonitor.reportMetrics(0, errorMessage);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchRaceGoals();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const handleGoalsChange = () => {
    fetchRaceGoals();
  };

  if (isLoading) {
    return (
      <div className={styles.dashboardContainer}>
        <div className={styles.card} style={{ textAlign: 'center', padding: '60px 20px' }}>
          <div className={styles.spinner}></div>
          <p style={{ marginTop: '20px', color: '#7f8c8d' }}>
            Loading race goals...
          </p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className={styles.dashboardContainer}>
        <div className={styles.card} style={{ textAlign: 'center', padding: '60px 20px' }}>
          <h2 style={{ color: '#e74c3c', marginBottom: '20px' }}>⚠️ Error Loading Race Goals</h2>
          <p style={{ color: '#7f8c8d', marginBottom: '30px' }}>{error}</p>
          <button
            onClick={fetchRaceGoals}
            style={{
              padding: '12px 24px',
              fontSize: '16px',
              backgroundColor: '#3498db',
              color: 'white',
              border: 'none',
              borderRadius: '4px',
              cursor: 'pointer'
            }}
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className={styles.dashboardContainer}>
      <div className={styles.card} style={{ marginBottom: '20px' }}>
        <RaceGoalsManager goals={raceGoals} onGoalsChange={handleGoalsChange} />
      </div>
    </div>
  );
};

export default RaceGoalsPage;




