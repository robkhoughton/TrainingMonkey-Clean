import React, { useState, useEffect } from 'react';
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

interface AutopsyData {
  alignment_score: number;
  date: string;
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
  strategic_context?: {
    race_context_periodization: string;
    load_management_pattern_analysis: string;
    strategic_rationale: string;
  };
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
  const [autopsyScores, setAutopsyScores] = useState<Record<string, number>>({});

  // Fetch autopsy alignment scores for the week
  useEffect(() => {
    if (!program) return;

    const fetchAutopsyScores = async () => {
      try {
        // Calculate week date range
        const weekStart = new Date(program.week_start_date);
        const weekEnd = new Date(weekStart);
        weekEnd.setDate(weekEnd.getDate() + 6);

        // Fetch journal entries for the week (which contain autopsy data)
        const response = await fetch(`/api/journal?days=7&date_from=${program.week_start_date}`);
        if (!response.ok) return;

        const result = await response.json();
        if (!result.success) return;

        // Extract autopsy scores by date
        const scores: Record<string, number> = {};
        result.data.forEach((entry: any) => {
          if (entry.ai_autopsy?.alignment_score) {
            scores[entry.date] = entry.ai_autopsy.alignment_score;
          }
        });

        setAutopsyScores(scores);
      } catch (err) {
        console.error('Error fetching autopsy scores:', err);
      }
    };

    fetchAutopsyScores();
  }, [program]);

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
        <h2 className={styles.cardHeader}>Workout Plan</h2>
        <div style={{ textAlign: 'center', padding: '40px 20px', color: '#95a5a6' }}>
          <p style={{ fontSize: '18px', marginBottom: '15px' }}>No weekly program loaded</p>
          <p style={{ fontSize: '14px', marginBottom: '20px' }}>
            Complete your profile (race goals, schedule) to generate your first program!
          </p>
        </div>
      </div>
    );
  }

  // Format date for header (e.g., "Dec 1, 2025")
  const formatHeaderDate = (dateStr: string): string => {
    const date = new Date(dateStr);
    return date.toLocaleDateString('en-US', { 
      month: 'short', 
      day: 'numeric',
      year: 'numeric'
    });
  };

  return (
    <div style={{ maxWidth: '1200px', margin: '0 auto' }}>
      {/* Header - Prominent */}
      <div style={{ 
        display: 'flex', 
        justifyContent: 'space-between', 
        alignItems: 'center', 
        marginBottom: '1rem',
        paddingBottom: '0.75rem',
        borderBottom: '2px solid #e1e8ed'
      }}>
        <div>
          <h2 style={{
            fontSize: '24px',
            fontWeight: '700',
            color: '#2c3e50',
            margin: 0,
            marginBottom: '0.25rem'
          }}>
            Workout Plan for the Week of {formatHeaderDate(program.week_start_date)}
          </h2>
          {program.from_cache && (
            <span style={{ 
              marginLeft: '0',
              padding: '2px 8px', 
              backgroundColor: '#e8f4f8', 
              borderRadius: '10px',
              fontSize: '11px',
              color: '#555'
            }}>
              Cached
            </span>
          )}
        </div>
        <button
          onClick={handleRegenerate}
          disabled={isRegenerating}
          style={{
            padding: '8px 16px',
            backgroundColor: '#9b59b6',
            color: 'white',
            border: 'none',
            borderRadius: '4px',
            cursor: isRegenerating ? 'not-allowed' : 'pointer',
            fontSize: '13px',
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
        padding: '1rem',
        backgroundColor: '#f8f9fa',
        borderRadius: '8px',
        marginBottom: '1rem',
        border: '1px solid #e1e8ed'
      }}>
        <h3 style={{ marginTop: 0, marginBottom: '0.5rem', fontSize: '15px', color: '#2c3e50' }}>
          ⚡ This Week at a Glance
        </h3>
        <p style={{ margin: 0, fontSize: '14px', lineHeight: '1.6', color: '#555', textAlign: 'left' }}>
          {program.week_summary}
        </p>
      </div>

      {/* Predicted Metrics */}
      <div style={{ 
        display: 'grid', 
        gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))', 
        gap: '0.75rem', 
        marginBottom: '1rem' 
      }}>
        <div style={{
          padding: '0.75rem',
          backgroundColor: getACWRColor(program.predicted_metrics.acwr_estimate),
          color: 'white',
          borderRadius: '8px',
          textAlign: 'center'
        }}>
          <div style={{ fontSize: '20px', fontWeight: 'bold', marginBottom: '3px' }}>
            {program.predicted_metrics.acwr_estimate.toFixed(2)}
          </div>
          <div style={{ fontSize: '11px', opacity: 0.9 }}>Predicted ACWR</div>
        </div>

        <div style={{
          padding: '0.75rem',
          backgroundColor: getDivergenceColor(program.predicted_metrics.divergence_estimate),
          color: 'white',
          borderRadius: '8px',
          textAlign: 'center'
        }}>
          <div style={{ fontSize: '20px', fontWeight: 'bold', marginBottom: '3px' }}>
            {program.predicted_metrics.divergence_estimate.toFixed(3)}
          </div>
          <div style={{ fontSize: '11px', opacity: 0.9 }}>Predicted Divergence</div>
        </div>

        <div style={{
          padding: '0.75rem',
          backgroundColor: '#3498db',
          color: 'white',
          borderRadius: '8px',
          textAlign: 'center'
        }}>
          <div style={{ fontSize: '20px', fontWeight: 'bold', marginBottom: '3px' }}>
            {program.predicted_metrics.total_weekly_miles.toFixed(1)}
          </div>
          <div style={{ fontSize: '11px', opacity: 0.9 }}>Total Miles</div>
        </div>
      </div>

      {/* Key Workouts */}
      {program.key_workouts_this_week && program.key_workouts_this_week.length > 0 && (
        <div style={{
          padding: '0.75rem',
          backgroundColor: '#fff3cd',
          border: '1px solid #ffeaa7',
          borderRadius: '8px',
          marginBottom: '1rem'
        }}>
          <h3 style={{ marginTop: 0, marginBottom: '0.5rem', fontSize: '13px', color: '#856404' }}>
            ⭐ Key Workouts This Week:
          </h3>
          <ul style={{ margin: 0, paddingLeft: '20px', fontSize: '13px', color: '#856404', textAlign: 'left' }}>
            {program.key_workouts_this_week.map((workout, index) => (
              <li key={index} style={{ marginBottom: '5px', textAlign: 'left' }}>{workout}</li>
            ))}
          </ul>
        </div>
      )}

      {/* Daily Program */}
      <div style={{ display: 'grid', gap: '0.75rem', marginBottom: '1rem' }}>
        {program.daily_program.map((workout, index) => {
          const workoutDate = new Date(workout.date);
          const today = new Date();
          today.setHours(0, 0, 0, 0);
          workoutDate.setHours(0, 0, 0, 0);
          
          const isToday = workoutDate.getTime() === today.getTime();
          const isPast = workoutDate < today;
          const isFuture = workoutDate > today;
          
          // Get autopsy score for past days
          const autopsyScore = autopsyScores[workout.date];
          const hasAutopsy = isPast && autopsyScore !== undefined;
          
          return (
            <div
              key={index}
              style={{
                border: isToday ? '3px solid #f39c12' : '1px solid #e1e8ed',
                borderRadius: '8px',
                padding: '0.75rem',
                backgroundColor: isToday ? '#fff9e6' : isPast ? '#f8f9fa' : 'white',
                position: 'relative',
                opacity: isPast && !hasAutopsy ? 0.7 : 1
              }}
            >
              {/* Today Badge with Journal Link */}
              {isToday && (
                <a
                  href="/dashboard?tab=journal"
                  style={{
                    position: 'absolute',
                    top: '10px',
                    right: '10px',
                    padding: '6px 14px',
                    backgroundColor: '#f39c12',
                    color: 'white',
                    borderRadius: '12px',
                    fontSize: '12px',
                    fontWeight: 'bold',
                    textDecoration: 'none',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '4px'
                  }}
                  title="View today's detailed training decision on Journal page"
                >
                  TODAY → JOURNAL
                </a>
              )}
              
              {/* Autopsy Alignment Badge for Past Days */}
              {hasAutopsy && (
                <div style={{
                  position: 'absolute',
                  top: '10px',
                  right: '10px',
                  padding: '6px 12px',
                  backgroundColor: autopsyScore >= 8 ? '#27ae60' : autopsyScore >= 6 ? '#f39c12' : '#e74c3c',
                  color: 'white',
                  borderRadius: '12px',
                  fontSize: '11px',
                  fontWeight: 'bold',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '4px'
                }}
                title={`Autopsy alignment score: ${autopsyScore}/10`}
              >
                📋 {autopsyScore}/10
                </div>
              )}

              {/* Workout Header: Day, Icon, Type, Intensity, Duration */}
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '0.75rem' }}>
                {/* Day of Week and Date */}
                <div style={{ 
                  minWidth: '70px',
                  textAlign: 'left'
                }}>
                  <div style={{
                    fontSize: '14px',
                    fontWeight: '700',
                    color: '#2c3e50',
                    lineHeight: '1.2'
                  }}>
                    {new Date(workout.date).toLocaleDateString('en-US', { weekday: 'long' })}
                  </div>
                  <div style={{
                    fontSize: '12px',
                    color: '#7f8c8d',
                    lineHeight: '1.2'
                  }}>
                    {formatDate(workout.date)}
                  </div>
                </div>
                
                <div style={{ fontSize: '28px' }}>
                  {getWorkoutTypeIcon(workout.workout_type)}
                </div>
                <div style={{ flex: 1 }}>
                  <div style={{
                    fontSize: '15px',
                    fontWeight: '600',
                    color: '#555',
                    textAlign: 'left'
                  }}>
                    {workout.workout_type}
                  </div>
                </div>
                <div style={{ textAlign: 'right' }}>
                  <div style={{
                    padding: '3px 8px',
                    backgroundColor: getIntensityColor(workout.intensity),
                    color: 'white',
                    borderRadius: '12px',
                    fontSize: '11px',
                    fontWeight: 'bold',
                    marginBottom: '3px'
                  }}>
                    {workout.intensity.toUpperCase()}
                  </div>
                  <div style={{ fontSize: '11px', color: '#7f8c8d' }}>
                    {workout.duration_estimate}
                  </div>
                </div>
              </div>

              {/* Description */}
              <div style={{
                fontSize: '13px',
                color: '#555',
                marginBottom: '0.75rem',
                lineHeight: '1.5',
                textAlign: 'left'
              }}>
                {workout.description}
              </div>

              {/* Key Focus */}
              <div style={{
                padding: '0.75rem',
                backgroundColor: '#e8f4f8',
                borderRadius: '6px',
                fontSize: '12px',
                color: '#555',
                marginBottom: workout.terrain_notes ? '0.5rem' : 0,
                textAlign: 'left'
              }}>
                <strong>Focus:</strong> {workout.key_focus}
              </div>

              {/* Terrain Notes */}
              {workout.terrain_notes && (
                <div style={{
                  fontSize: '12px',
                  color: '#7f8c8d',
                  fontStyle: 'italic',
                  textAlign: 'left'
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
          padding: '0.75rem',
          backgroundColor: '#d1f2eb',
          border: '1px solid #a8e6cf',
          borderRadius: '8px',
          marginBottom: '0.75rem'
        }}>
          <h3 style={{ marginTop: 0, marginBottom: '0.5rem', fontSize: '13px', color: '#0e6655' }}>
            🥗 Nutrition Reminder:
          </h3>
          <p style={{ margin: 0, fontSize: '13px', color: '#0e6655', lineHeight: '1.5', textAlign: 'left' }}>
            {program.nutrition_reminder}
          </p>
        </div>
      )}

      {/* Injury Prevention Note */}
      {program.injury_prevention_note && (
        <div style={{
          padding: '0.75rem',
          backgroundColor: '#fce4ec',
          border: '1px solid #f8bbd0',
          borderRadius: '8px',
          marginBottom: '0.75rem'
        }}>
          <h3 style={{ marginTop: 0, marginBottom: '0.5rem', fontSize: '13px', color: '#c2185b' }}>
            🏥 Injury Prevention:
          </h3>
          <p style={{ margin: 0, fontSize: '13px', color: '#c2185b', lineHeight: '1.5', textAlign: 'left' }}>
            {program.injury_prevention_note}
          </p>
        </div>
      )}

      {/* Footer Note */}
      <div style={{
        padding: '0.75rem',
        backgroundColor: '#f8f9fa',
        borderRadius: '6px',
        fontSize: '12px',
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

