import React from 'react';
import styles from './TrainingLoadDashboard.module.css';

// ============================================================================
// INTERFACES
// ============================================================================

interface TimelineWeek {
  week_number: number;
  week_start: string;
  week_end: string;
  stage: string;
  is_current: boolean;
  races?: Array<{
    race_name: string;
    priority: string;
    date: string;
  }>;
}

interface TrainingStage {
  stage: string;
  weeks_to_race: number | null;
  race_name: string | null;
  priority?: string;
  details: string;
  timeline?: TimelineWeek[];
}

interface TimelineVisualizationProps {
  trainingStage: TrainingStage | null;
}

// ============================================================================
// COMPONENT
// ============================================================================

const TimelineVisualization: React.FC<TimelineVisualizationProps> = ({ trainingStage }) => {
  // ============================================================================
  // HELPERS
  // ============================================================================

  const getStageColor = (stage: string): string => {
    switch (stage.toLowerCase()) {
      case 'base': return '#3498db'; // blue
      case 'build': return '#2ecc71'; // green
      case 'specificity': return '#f39c12'; // orange
      case 'taper': return '#e74c3c'; // red
      case 'peak': return '#9b59b6'; // purple
      case 'recovery': return '#95a5a6'; // gray
      default: return '#7f8c8d';
    }
  };

  const getPriorityColor = (priority: string): string => {
    switch (priority.toUpperCase()) {
      case 'A': return '#e74c3c'; // red
      case 'B': return '#f39c12'; // orange
      case 'C': return '#3498db'; // blue
      default: return '#95a5a6';
    }
  };

  const formatDateShort = (dateStr: string): string => {
    const date = new Date(dateStr);
    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
  };

  // ============================================================================
  // RENDER
  // ============================================================================

  if (!trainingStage || !trainingStage.timeline || trainingStage.timeline.length === 0) {
    return (
      <div>
        <h2 className={styles.cardHeader}>Training Timeline</h2>
        <div style={{ textAlign: 'center', padding: '40px 20px', color: '#95a5a6' }}>
          <p style={{ fontSize: '18px', marginBottom: '10px' }}>No timeline available</p>
          <p style={{ fontSize: '14px' }}>Add a race goal to see your training periodization!</p>
        </div>
      </div>
    );
  }

  const timeline = trainingStage.timeline;
  const currentWeekIndex = timeline.findIndex(w => w.is_current);
  const totalWeeks = timeline.length;

  return (
    <div>
      {/* Header */}
      <h2 className={styles.cardHeader}>Training Timeline</h2>
      <div style={{ fontSize: '14px', color: '#7f8c8d', marginBottom: '20px' }}>
        {totalWeeks}-week plan to {trainingStage.race_name || 'your race'}
      </div>

      {/* Current Stage Info */}
      <div style={{
        padding: '15px 20px',
        backgroundColor: getStageColor(trainingStage.stage),
        color: 'white',
        borderRadius: '8px',
        marginBottom: '25px',
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center'
      }}>
        <div>
          <div style={{ fontSize: '18px', fontWeight: 'bold', marginBottom: '5px' }}>
            {trainingStage.stage} Phase
          </div>
          <div style={{ fontSize: '14px', opacity: 0.9 }}>
            {trainingStage.details}
          </div>
        </div>
        {trainingStage.weeks_to_race !== null && (
          <div style={{ textAlign: 'right' }}>
            <div style={{ fontSize: '32px', fontWeight: 'bold' }}>
              {trainingStage.weeks_to_race}
            </div>
            <div style={{ fontSize: '12px', opacity: 0.9 }}>
              weeks to race
            </div>
          </div>
        )}
      </div>

      {/* Timeline Visualization */}
      <div style={{
        overflowX: 'auto',
        marginBottom: '20px',
        padding: '20px 0'
      }}>
        {/* Week Numbers */}
        <div style={{
          display: 'flex',
          marginBottom: '10px',
          minWidth: `${totalWeeks * 60}px`
        }}>
          {timeline.map((week, index) => (
            <div
              key={index}
              style={{
                flex: '0 0 60px',
                textAlign: 'center',
                fontSize: '11px',
                fontWeight: week.is_current ? 'bold' : 'normal',
                color: week.is_current ? '#f39c12' : '#7f8c8d'
              }}
            >
              W{week.week_number}
            </div>
          ))}
        </div>

        {/* Timeline Bar */}
        <div style={{
          display: 'flex',
          height: '60px',
          borderRadius: '30px',
          overflow: 'hidden',
          marginBottom: '15px',
          minWidth: `${totalWeeks * 60}px`,
          boxShadow: '0 4px 6px rgba(0,0,0,0.1)'
        }}>
          {timeline.map((week, index) => {
            const isFirst = index === 0 || timeline[index - 1].stage !== week.stage;
            const isLast = index === timeline.length - 1 || timeline[index + 1].stage !== week.stage;

            return (
              <div
                key={index}
                style={{
                  flex: '0 0 60px',
                  backgroundColor: getStageColor(week.stage),
                  position: 'relative',
                  borderLeft: isFirst ? 'none' : '1px solid rgba(255,255,255,0.3)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  cursor: 'default'
                }}
                title={`Week ${week.week_number}: ${week.stage}`}
              >
                {/* Current Week Marker */}
                {week.is_current && (
                  <div style={{
                    position: 'absolute',
                    top: '-25px',
                    left: '50%',
                    transform: 'translateX(-50%)',
                    fontSize: '24px'
                  }}>
                    📍
                  </div>
                )}

                {/* Race Markers */}
                {week.races && week.races.map((race, raceIndex) => (
                  <div
                    key={raceIndex}
                    style={{
                      position: 'absolute',
                      top: '-35px',
                      left: '50%',
                      transform: 'translateX(-50%)',
                      backgroundColor: getPriorityColor(race.priority),
                      color: 'white',
                      padding: '4px 8px',
                      borderRadius: '4px',
                      fontSize: '11px',
                      fontWeight: 'bold',
                      whiteSpace: 'nowrap',
                      boxShadow: '0 2px 4px rgba(0,0,0,0.2)',
                      zIndex: 10
                    }}
                    title={`${race.race_name} - ${race.date}`}
                  >
                    {race.priority}
                  </div>
                ))}

                {/* Stage Label (on first week of each stage) */}
                {isFirst && (
                  <div style={{
                    fontSize: '11px',
                    fontWeight: 'bold',
                    color: 'white',
                    textShadow: '1px 1px 2px rgba(0,0,0,0.5)',
                    textTransform: 'uppercase',
                    letterSpacing: '0.5px'
                  }}>
                    {week.stage.slice(0, 4)}
                  </div>
                )}
              </div>
            );
          })}
        </div>

        {/* "You Are Here" Label */}
        {currentWeekIndex >= 0 && (
          <div style={{
            display: 'flex',
            minWidth: `${totalWeeks * 60}px`
          }}>
            <div style={{
              flex: `0 0 ${currentWeekIndex * 60}px`
            }}></div>
            <div style={{
              flex: '0 0 60px',
              textAlign: 'center',
              fontSize: '12px',
              fontWeight: 'bold',
              color: '#f39c12'
            }}>
              YOU ARE HERE
            </div>
          </div>
        )}

        {/* Date Range */}
        <div style={{
          display: 'flex',
          marginTop: '15px',
          minWidth: `${totalWeeks * 60}px`,
          fontSize: '11px',
          color: '#95a5a6'
        }}>
          {timeline.map((week, index) => {
            const showDate = index === 0 || index === timeline.length - 1 || week.is_current;
            return (
              <div
                key={index}
                style={{
                  flex: '0 0 60px',
                  textAlign: 'center'
                }}
              >
                {showDate && formatDateShort(week.week_start)}
              </div>
            );
          })}
        </div>
      </div>

      {/* Stage Legend */}
      <div style={{
        display: 'flex',
        flexWrap: 'wrap',
        gap: '10px',
        padding: '15px',
        backgroundColor: '#f8f9fa',
        borderRadius: '8px',
        fontSize: '13px'
      }}>
        <div style={{ fontWeight: '600', width: '100%', marginBottom: '5px', color: '#2c3e50' }}>
          Training Stage Guide:
        </div>
        
        <div style={{ display: 'flex', alignItems: 'center', gap: '5px' }}>
          <div style={{
            width: '20px',
            height: '20px',
            backgroundColor: getStageColor('Base'),
            borderRadius: '4px'
          }}></div>
          <span>Base - Building endurance foundation</span>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '5px' }}>
          <div style={{
            width: '20px',
            height: '20px',
            backgroundColor: getStageColor('Build'),
            borderRadius: '4px'
          }}></div>
          <span>Build - Increasing volume & intensity</span>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '5px' }}>
          <div style={{
            width: '20px',
            height: '20px',
            backgroundColor: getStageColor('Specificity'),
            borderRadius: '4px'
          }}></div>
          <span>Specificity - Race-specific training</span>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '5px' }}>
          <div style={{
            width: '20px',
            height: '20px',
            backgroundColor: getStageColor('Taper'),
            borderRadius: '4px'
          }}></div>
          <span>Taper - Reducing volume, maintaining intensity</span>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '5px' }}>
          <div style={{
            width: '20px',
            height: '20px',
            backgroundColor: getStageColor('Peak'),
            borderRadius: '4px'
          }}></div>
          <span>Peak - Race week!</span>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '5px' }}>
          <div style={{
            width: '20px',
            height: '20px',
            backgroundColor: getStageColor('Recovery'),
            borderRadius: '4px'
          }}></div>
          <span>Recovery - Post-race rest & adaptation</span>
        </div>
      </div>

      {/* Race Markers Legend */}
      {timeline.some(w => w.races && w.races.length > 0) && (
        <div style={{
          marginTop: '15px',
          padding: '15px',
          backgroundColor: '#f8f9fa',
          borderRadius: '8px',
          fontSize: '13px'
        }}>
          <div style={{ fontWeight: '600', marginBottom: '8px', color: '#2c3e50' }}>
            Race Priority Guide:
          </div>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '15px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '5px' }}>
              <div style={{
                padding: '4px 8px',
                backgroundColor: getPriorityColor('A'),
                color: 'white',
                borderRadius: '4px',
                fontSize: '12px',
                fontWeight: 'bold'
              }}>A</div>
              <span>Primary season focus</span>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '5px' }}>
              <div style={{
                padding: '4px 8px',
                backgroundColor: getPriorityColor('B'),
                color: 'white',
                borderRadius: '4px',
                fontSize: '12px',
                fontWeight: 'bold'
              }}>B</div>
              <span>Fitness evaluation race</span>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '5px' }}>
              <div style={{
                padding: '4px 8px',
                backgroundColor: getPriorityColor('C'),
                color: 'white',
                borderRadius: '4px',
                fontSize: '12px',
                fontWeight: 'bold'
              }}>C</div>
              <span>Training volume race</span>
            </div>
          </div>
        </div>
      )}

      {/* Help Text */}
      <div style={{
        marginTop: '20px',
        padding: '15px',
        backgroundColor: '#e8f4f8',
        borderRadius: '6px',
        fontSize: '13px',
        color: '#555'
      }}>
        <strong>💡 How to Read This Timeline:</strong>
        <ul style={{ marginTop: '8px', marginBottom: 0, paddingLeft: '20px' }}>
          <li>Each box represents one week of training</li>
          <li>Colors indicate your current training phase</li>
          <li>📍 marker shows your current position</li>
          <li>Letter badges (A/B/C) mark upcoming races</li>
          <li>Your training program adjusts based on which phase you're in</li>
        </ul>
      </div>
    </div>
  );
};

export default TimelineVisualization;

