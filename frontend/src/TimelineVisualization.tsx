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
    if (!stage) return '#7f8c8d';
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
    if (!priority) return '#95a5a6';
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

  // Debug: Log races data
  console.log('[Timeline] Total weeks:', totalWeeks);
  console.log('[Timeline] Full timeline data:', JSON.stringify(timeline, null, 2));
  const weeksWithRaces = timeline.filter(w => w.races && Array.isArray(w.races) && w.races.length > 0);
  console.log('[Timeline] Weeks with races:', weeksWithRaces.length);
  weeksWithRaces.forEach((week, idx) => {
    console.log(`[Timeline] Week ${week.week_number} (${week.week_start}) has ${week.races?.length || 0} race(s):`, week.races);
  });
  
  // Specific check for B races
  const bRaces = timeline.flatMap(w => (w.races || []).filter(r => r.priority === 'B'));
  console.log('[Timeline] Total B races found:', bRaces.length);
  bRaces.forEach(race => {
    console.log('[Timeline] B Race:', race);
  });

  // Calculate reverse week numbers (weeks until race)
  // Last week (race week) = 0, first week = totalWeeks - 1
  const getWeeksUntilRace = (index: number): number => {
    return totalWeeks - index - 1;
  };

  return (
    <div style={{ marginTop: '0', paddingTop: '0' }}>
      {/* Consolidated Timeline Bar */}
      <div style={{
        overflowX: 'auto',
        marginBottom: '0.5rem',
        marginTop: '0',
        padding: '30px 0 0.25rem 0' // Tighter padding
      }}>
        {/* Single Timeline Bar with Week Numbers */}
        <div style={{
          display: 'flex',
          height: '60px', // Reduced from 80px
          borderRadius: '30px',
          overflow: 'hidden',
          marginBottom: '0.25rem', // Tight spacing
          minWidth: `${totalWeeks * 60}px`,
          boxShadow: '0 4px 6px rgba(0,0,0,0.1)'
        }}>
          {timeline.map((week, index) => {
            const isFirst = index === 0 || timeline[index - 1].stage !== week.stage;
            const weeksUntilRace = getWeeksUntilRace(index);
            const isRaceWeek = weeksUntilRace === 0;

            return (
              <div
                key={index}
                style={{
                  flex: '0 0 60px',
                  backgroundColor: getStageColor(week.stage),
                  position: 'relative',
                  borderLeft: isFirst ? 'none' : '1px solid rgba(255,255,255,0.3)',
                  display: 'flex',
                  flexDirection: 'column',
                  alignItems: 'center',
                  justifyContent: 'center',
                  cursor: 'default',
                  padding: '4px 0'
                }}
                title={`${weeksUntilRace} weeks until race - ${week.stage}`}
              >
                {/* Week Number (reverse order - weeks until race) */}
                <div style={{
                  fontSize: isRaceWeek ? '14px' : '12px',
                  fontWeight: week.is_current || isRaceWeek ? 'bold' : '600',
                  color: 'white',
                  textShadow: '1px 1px 2px rgba(0,0,0,0.5)',
                  marginBottom: '2px'
                }}>
                  {isRaceWeek ? 'RACE' : `${weeksUntilRace}`}
                </div>

                {/* Stage Label (on first week of each stage) */}
                {isFirst && (
                  <div style={{
                    fontSize: '9px',
                    fontWeight: 'bold',
                    color: 'white',
                    textShadow: '1px 1px 2px rgba(0,0,0,0.5)',
                    textTransform: 'uppercase',
                    letterSpacing: '0.5px',
                    opacity: 0.9
                  }}>
                    {week.stage.slice(0, 4)}
                  </div>
                )}

                {/* Current Week Marker - Pin */}
                {week.is_current && (
                  <div style={{
                    position: 'absolute',
                    top: '-25px', // Reduced from -30px
                    left: '50%',
                    transform: 'translateX(-50%)',
                    fontSize: '18px', // Slightly smaller
                    zIndex: 20,
                    filter: 'drop-shadow(0 2px 4px rgba(0,0,0,0.3))'
                  }}>
                    📍
                  </div>
                )}

                {/* Race Markers */}
                {week.races && Array.isArray(week.races) && week.races.length > 0 && week.races.map((race, raceIndex) => (
                  <div
                    key={raceIndex}
                    style={{
                      position: 'absolute',
                      top: week.is_current ? '-42px' : '-35px', // Reduced spacing
                      left: '50%',
                      transform: 'translateX(-50%)',
                      backgroundColor: getPriorityColor(race.priority),
                      color: 'white',
                      padding: '3px 6px', // Tighter padding
                      borderRadius: '4px',
                      fontSize: '10px', // Smaller font
                      fontWeight: 'bold',
                      whiteSpace: 'nowrap',
                      boxShadow: '0 2px 4px rgba(0,0,0,0.2)',
                      zIndex: 15
                    }}
                    title={`${race.race_name} - ${race.date}`}
                  >
                    {race.priority}
                  </div>
                ))}
              </div>
            );
          })}
        </div>

        {/* Weeks until race label */}
        <div style={{
          display: 'flex',
          minWidth: `${totalWeeks * 60}px`,
          alignItems: 'center',
          marginTop: '0.25rem',
          fontSize: '11px',
          color: '#1e293b',
          fontWeight: '600'
        }}>
          <span>Weeks until race</span>
        </div>
      </div>

      {/* Stage Legend - Compact with Phase and Races on same line */}
      <div style={{
        display: 'flex',
        flexWrap: 'wrap',
        gap: '0.5rem',
        padding: '0.5rem',
        backgroundColor: '#f8f9fa',
        borderRadius: '6px',
        fontSize: '11px',
        marginTop: '0.25rem',
        alignItems: 'center'
      }}>
        <span style={{ fontWeight: '700', color: '#1e293b', marginRight: '0.25rem', textTransform: 'uppercase' }}>PHASES:</span>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.25rem' }}>
          <div style={{ width: '14px', height: '14px', backgroundColor: getStageColor('Base'), borderRadius: '3px' }}></div>
          <span>Base</span>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.25rem' }}>
          <div style={{ width: '14px', height: '14px', backgroundColor: getStageColor('Build'), borderRadius: '3px' }}></div>
          <span>Build</span>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.25rem' }}>
          <div style={{ width: '14px', height: '14px', backgroundColor: getStageColor('Specificity'), borderRadius: '3px' }}></div>
          <span>Specificity</span>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.25rem' }}>
          <div style={{ width: '14px', height: '14px', backgroundColor: getStageColor('Taper'), borderRadius: '3px' }}></div>
          <span>Taper</span>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.25rem' }}>
          <div style={{ width: '14px', height: '14px', backgroundColor: getStageColor('Peak'), borderRadius: '3px' }}></div>
          <span>Peak</span>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.25rem' }}>
          <div style={{ width: '14px', height: '14px', backgroundColor: getStageColor('Recovery'), borderRadius: '3px' }}></div>
          <span>Recovery</span>
        </div>
        
        {/* Races on same line */}
        {timeline.some(w => w.races && w.races.length > 0) && (
          <>
            <span style={{ fontWeight: '700', color: '#1e293b', marginLeft: '0.5rem', marginRight: '0.25rem', textTransform: 'uppercase' }}>RACES:</span>
            <div style={{
              padding: '2px 6px',
              backgroundColor: getPriorityColor('A'),
              color: 'white',
              borderRadius: '3px',
              fontSize: '10px',
              fontWeight: 'bold'
            }}>A</div>
            <div style={{
              padding: '2px 6px',
              backgroundColor: getPriorityColor('B'),
              color: 'white',
              borderRadius: '3px',
              fontSize: '10px',
              fontWeight: 'bold'
            }}>B</div>
            <div style={{
              padding: '2px 6px',
              backgroundColor: getPriorityColor('C'),
              color: 'white',
              borderRadius: '3px',
              fontSize: '10px',
              fontWeight: 'bold'
            }}>C</div>
          </>
        )}
      </div>
    </div>
  );
};

export default TimelineVisualization;

