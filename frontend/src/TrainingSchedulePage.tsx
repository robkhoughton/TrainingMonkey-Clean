import React, { useState, useEffect } from 'react';
import styles from './TrainingLoadDashboard.module.css';
import { usePagePerformanceMonitoring, useComponentPerformanceMonitoring } from './usePerformanceMonitoring';
import TrainingScheduleConfig from './TrainingScheduleConfig';

interface TrainingSchedule {
  schedule: {
    total_hours_per_week: number;
    available_days: string[];
    time_blocks: Array<{
      day: string;
      start_time: string;
      end_time: string;
    }>;
    constraints: Array<{ description: string }>;
  };
  include_strength: boolean;
  strength_hours: number;
  include_mobility: boolean;
  mobility_hours: number;
  include_cross_training: boolean;
  cross_training_type: string | null;
  cross_training_hours: number;
}

const TrainingSchedulePage: React.FC = () => {
  // Performance monitoring
  usePagePerformanceMonitoring('training-schedule');
  const perfMonitor = useComponentPerformanceMonitoring('TrainingSchedulePage');

  const [trainingSchedule, setTrainingSchedule] = useState<TrainingSchedule | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const fetchTrainingSchedule = async () => {
    try {
      perfMonitor.trackFetchStart();
      const response = await fetch('/api/coach/training-schedule');
      if (!response.ok) {
        throw new Error('Failed to fetch training schedule');
      }
      const data = await response.json();
      setTrainingSchedule(data.schedule || null);
      perfMonitor.trackFetchEnd();
      perfMonitor.reportMetrics(data.schedule ? 1 : 0);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to load training schedule';
      setError(errorMessage);
      perfMonitor.reportMetrics(0, errorMessage);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchTrainingSchedule();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const handleScheduleChange = () => {
    fetchTrainingSchedule();
  };

  if (isLoading) {
    return (
      <div className={styles.dashboardContainer}>
        <div className={styles.card} style={{ textAlign: 'center', padding: '60px 20px' }}>
          <div className={styles.spinner}></div>
          <p style={{ marginTop: '20px', color: '#7f8c8d' }}>
            Loading training schedule...
          </p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className={styles.dashboardContainer}>
        <div className={styles.card} style={{ textAlign: 'center', padding: '60px 20px' }}>
          <h2 style={{ color: '#e74c3c', marginBottom: '20px' }}>⚠️ Error Loading Training Schedule</h2>
          <p style={{ color: '#7f8c8d', marginBottom: '30px' }}>{error}</p>
          <button
            onClick={fetchTrainingSchedule}
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
        <TrainingScheduleConfig schedule={trainingSchedule} onScheduleChange={handleScheduleChange} />
      </div>
    </div>
  );
};

export default TrainingSchedulePage;


