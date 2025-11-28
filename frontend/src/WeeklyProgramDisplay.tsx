import React, { useState } from 'react';
import styles from './TrainingLoadDashboard.module.css';

// ============================================================================
// INTERFACES
// ============================================================================

interface DailyWorkout {
  day: string;
  date: string;
  workout_type: string;
  description: string;
  duration_estimate: string;
  intensity: string;
  key_focus: string;
  terrain_notes?: string;
}

interface WeeklyProgram {
  week_start_date: string;
  week_summary: string;
  predicted_metrics: {
    acwr_estimate: number;
    divergence_estimate: number;
    total_weekly_miles: number;
  };
  daily_program: DailyWorkout[];
  key_workouts_this_week: string[];
  nutrition_reminder?: string;
  injury_prevention_note?: string;
  from_cache?: boolean;
}

interface WeeklyProgramDisplayProps {
  program: WeeklyProgram | null;
  onRefresh: () => void;
}

// ============================================================================
// COMPONENT
// ============================================================================

const WeeklyProgramDisplay: React.FC<WeeklyProgramDisplayProps> = ({ program, onRefresh }) => {
  const [isRegenerating, setIsRegenerating] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // ============================================================================
  // HANDLERS
  // ============================================================================

  const handleRegenerate = async () => {
    if (!window.confirm('Generate a new weekly program? This will replace the current program.')) {
      return;
    }

    setIsRegenerating(true);
    setError(null);

    try {
      const response = await fetch('/api/coach/weekly-program/generate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({})
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || 'Failed to generate program');
      }

      onRefresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to generate program');
    } finally {
      setIsRegenerating(false);
    }
  };

  // ============================================================================
  // HELPERS
  // ============================================================================

  const getIntensityColor = (intensity: string): string => {
    if (!intensity) return '#95a5a6';
    switch (intensity.toLowerCase()) {
      case 'low': return '#2ecc71'; // green
      case 'moderate': return '#f39c12'; // orange
      case 'high': return '#e74c3c'; // red
      default: return '#95a5a6';
    }
  };

  const getWorkoutTypeIcon = (workoutType: string): string => {
    if (!workoutType) return '🏃';
    const type = workoutType.toLowerCase();
    if (type.includes('long')) return '🏃‍♂️';
    if (type.includes('tempo')) return '⚡';
    if (type.includes('interval') || type.includes('speed')) return '🔥';
    if (type.includes('hill')) return '⛰️';
    if (type.includes('easy') || type.includes('recovery')) return '😌';
    if (type.includes('rest')) return '💤';
    if (type.includes('cross')) return '🚴';
    if (type.includes('strength')) return '💪';
    return '🏃';
  };

  const formatDate = (dateStr: string): string => {
    const date = new Date(dateStr);
    return date.toLocaleDateString('en-US', { 
      weekday: 'short', 
      month: 'short', 
      day: 'numeric' 
    });
  };

  const getACWRColor = (acwr: number): string => {
    if (acwr < 0.8) return '#3498db'; // blue - low load
    if (acwr <= 1.3) return '#2ecc71'; // green - optimal
    if (acwr <= 1.5) return '#f39c12'; // orange - moderate risk
    return '#e74c3c'; // red - high risk
  };

  const getDivergenceColor = (div: number): string => {
    if (Math.abs(div) <= 0.15) return '#2ecc71'; // green - optimal
    if (Math.abs(div) <= 0.30) return '#f39c12'; // orange - moderate
    return '#e74c3c'; // red - high
  };

  // ============================================================================
  // RENDER
  // ============================================================================

  if (!program) {
    return (
      <div>
        <h2 className={styles.cardHeader}>Weekly Training Program</h2>
        <div style={{ textAlign: 'center', padding: '40px 20px', color: '#95a5a6' }}>
          <p style={{ fontSize: '18px', marginBottom: '15px' }}>No weekly program loaded</p>
          <p style={{ fontSize: '14px', marginBottom: '20px' }}>
            Complete your profile (race goals, schedule) to generate your first program!
          </p>
        </div>
      </div>
    );
  }

  return (
    <div>
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
        <div>
          <h2 className={styles.cardHeader}>
            Weekly Training Program
          </h2>
          <div style={{ fontSize: '14px', color: '#7f8c8d', marginTop: '5px' }}>
            Week of {formatDate(program.week_start_date)}
            {program.from_cache && (
              <span style={{ 
                marginLeft: '10px', 
                padding: '2px 8px', 
                backgroundColor: '#e8f4f8', 
                borderRadius: '10px',
                fontSize: '12px',
                color: '#555'
              }}>
                Cached
              </span>
            )}
          </div>
        </div>
        <button
          onClick={handleRegenerate}
          disabled={isRegenerating}
          style={{
            padding: '10px 20px',
            backgroundColor: '#9b59b6',
            color: 'white',
            border: 'none',
            borderRadius: '4px',
            cursor: isRegenerating ? 'not-allowed' : 'pointer',
            fontSize: '14px',
            fontWeight: '600',
            opacity: isRegenerating ? 0.6 : 1
          }}
        >
          {isRegenerating ? '⏳ Generating...' : '🔄 Regenerate Program'}
        </button>
      </div>

      {/* Error Display */}
      {error && (
        <div style={{
          padding: '15px',
          backgroundColor: '#fee',
          border: '1px solid #fcc',
          borderRadius: '4px',
          marginBottom: '15px',
          color: '#c33'
        }}>
          {error}
        </div>
      )}

      {/* Week Summary */}
      <div style={{
        padding: '20px',
        backgroundColor: '#f8f9fa',
        borderRadius: '8px',
        marginBottom: '20px',
        border: '1px solid #e1e8ed'
      }}>
        <h3 style={{ marginTop: 0, marginBottom: '10px', fontSize: '16px', color: '#2c3e50' }}>
          📋 Week Overview
        </h3>
        <p style={{ margin: 0, fontSize: '14px', lineHeight: '1.6', color: '#555' }}>
          {program.week_summary}
        </p>
      </div>

      {/* Predicted Metrics */}
      <div style={{ 
        display: 'grid', 
        gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))', 
        gap: '15px', 
        marginBottom: '20px' 
      }}>
        <div style={{
          padding: '15px',
          backgroundColor: getACWRColor(program.predicted_metrics.acwr_estimate),
          color: 'white',
          borderRadius: '8px',
          textAlign: 'center'
        }}>
          <div style={{ fontSize: '24px', fontWeight: 'bold', marginBottom: '5px' }}>
            {program.predicted_metrics.acwr_estimate.toFixed(2)}
          </div>
          <div style={{ fontSize: '12px', opacity: 0.9 }}>Predicted ACWR</div>
        </div>

        <div style={{
          padding: '15px',
          backgroundColor: getDivergenceColor(program.predicted_metrics.divergence_estimate),
          color: 'white',
          borderRadius: '8px',
          textAlign: 'center'
        }}>
          <div style={{ fontSize: '24px', fontWeight: 'bold', marginBottom: '5px' }}>
            {program.predicted_metrics.divergence_estimate.toFixed(3)}
          </div>
          <div style={{ fontSize: '12px', opacity: 0.9 }}>Predicted Divergence</div>
        </div>

        <div style={{
          padding: '15px',
          backgroundColor: '#3498db',
          color: 'white',
          borderRadius: '8px',
          textAlign: 'center'
        }}>
          <div style={{ fontSize: '24px', fontWeight: 'bold', marginBottom: '5px' }}>
            {program.predicted_metrics.total_weekly_miles.toFixed(1)}
          </div>
          <div style={{ fontSize: '12px', opacity: 0.9 }}>Total Miles</div>
        </div>
      </div>

      {/* Key Workouts */}
      {program.key_workouts_this_week && program.key_workouts_this_week.length > 0 && (
        <div style={{
          padding: '15px',
          backgroundColor: '#fff3cd',
          border: '1px solid #ffeaa7',
          borderRadius: '8px',
          marginBottom: '20px'
        }}>
          <h3 style={{ marginTop: 0, marginBottom: '10px', fontSize: '14px', color: '#856404' }}>
            ⭐ Key Workouts This Week:
          </h3>
          <ul style={{ margin: 0, paddingLeft: '20px', fontSize: '13px', color: '#856404' }}>
            {program.key_workouts_this_week.map((workout, index) => (
              <li key={index} style={{ marginBottom: '5px' }}>{workout}</li>
            ))}
          </ul>
        </div>
      )}

      {/* Daily Program */}
      <h3 style={{ fontSize: '16px', marginBottom: '15px', color: '#2c3e50' }}>
        7-Day Training Schedule
      </h3>
      <div style={{ display: 'grid', gap: '15px', marginBottom: '20px' }}>
        {program.daily_program.map((workout, index) => {
          const isToday = new Date(workout.date).toDateString() === new Date().toDateString();
          
          return (
            <div
              key={index}
              style={{
                border: isToday ? '3px solid #f39c12' : '1px solid #e1e8ed',
                borderRadius: '8px',
                padding: '15px',
                backgroundColor: isToday ? '#fff9e6' : 'white',
                position: 'relative'
              }}
            >
              {/* Today Badge */}
              {isToday && (
                <div style={{
                  position: 'absolute',
                  top: '10px',
                  right: '10px',
                  padding: '4px 12px',
                  backgroundColor: '#f39c12',
                  color: 'white',
                  borderRadius: '12px',
                  fontSize: '12px',
                  fontWeight: 'bold'
                }}>
                  TODAY
                </div>
              )}

              {/* Day & Date */}
              <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '10px' }}>
                <div style={{ fontSize: '32px' }}>
                  {getWorkoutTypeIcon(workout.workout_type)}
                </div>
                <div>
                  <div style={{ fontSize: '18px', fontWeight: 'bold', color: '#2c3e50' }}>
                    {workout.day}
                  </div>
                  <div style={{ fontSize: '13px', color: '#7f8c8d' }}>
                    {formatDate(workout.date)}
                  </div>
                </div>
                <div style={{ marginLeft: 'auto', textAlign: 'right' }}>
                  <div style={{
                    padding: '4px 10px',
                    backgroundColor: getIntensityColor(workout.intensity),
                    color: 'white',
                    borderRadius: '12px',
                    fontSize: '12px',
                    fontWeight: 'bold',
                    marginBottom: '5px'
                  }}>
                    {workout.intensity.toUpperCase()}
                  </div>
                  <div style={{ fontSize: '12px', color: '#7f8c8d' }}>
                    {workout.duration_estimate}
                  </div>
                </div>
              </div>

              {/* Workout Type */}
              <div style={{
                fontSize: '16px',
                fontWeight: '600',
                color: '#555',
                marginBottom: '8px'
              }}>
                {workout.workout_type}
              </div>

              {/* Description */}
              <div style={{
                fontSize: '14px',
                color: '#555',
                marginBottom: '10px',
                lineHeight: '1.5'
              }}>
                {workout.description}
              </div>

              {/* Key Focus */}
              <div style={{
                padding: '10px',
                backgroundColor: '#e8f4f8',
                borderRadius: '6px',
                fontSize: '13px',
                color: '#555',
                marginBottom: workout.terrain_notes ? '8px' : 0
              }}>
                <strong>Focus:</strong> {workout.key_focus}
              </div>

              {/* Terrain Notes */}
              {workout.terrain_notes && (
                <div style={{
                  fontSize: '13px',
                  color: '#7f8c8d',
                  fontStyle: 'italic'
                }}>
                  🗺️ {workout.terrain_notes}
                </div>
              )}
            </div>
          );
        })}
      </div>

      {/* Nutrition Reminder */}
      {program.nutrition_reminder && (
        <div style={{
          padding: '15px',
          backgroundColor: '#d1f2eb',
          border: '1px solid #a8e6cf',
          borderRadius: '8px',
          marginBottom: '15px'
        }}>
          <h3 style={{ marginTop: 0, marginBottom: '8px', fontSize: '14px', color: '#0e6655' }}>
            🥗 Nutrition Reminder:
          </h3>
          <p style={{ margin: 0, fontSize: '13px', color: '#0e6655', lineHeight: '1.5' }}>
            {program.nutrition_reminder}
          </p>
        </div>
      )}

      {/* Injury Prevention Note */}
      {program.injury_prevention_note && (
        <div style={{
          padding: '15px',
          backgroundColor: '#fce4ec',
          border: '1px solid #f8bbd0',
          borderRadius: '8px',
          marginBottom: '15px'
        }}>
          <h3 style={{ marginTop: 0, marginBottom: '8px', fontSize: '14px', color: '#c2185b' }}>
            🏥 Injury Prevention:
          </h3>
          <p style={{ margin: 0, fontSize: '13px', color: '#c2185b', lineHeight: '1.5' }}>
            {program.injury_prevention_note}
          </p>
        </div>
      )}

      {/* Footer Note */}
      <div style={{
        padding: '15px',
        backgroundColor: '#f8f9fa',
        borderRadius: '6px',
        fontSize: '13px',
        color: '#7f8c8d',
        textAlign: 'center'
      }}>
        💡 This program is optimized for your race goals, current fitness, and weekly schedule.
        Adjust as needed based on how you feel!
      </div>
    </div>
  );
};

export default WeeklyProgramDisplay;

