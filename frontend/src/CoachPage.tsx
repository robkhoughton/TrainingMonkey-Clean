import React, { useState, useEffect } from 'react';
import styles from './TrainingLoadDashboard.module.css';
import { usePagePerformanceMonitoring, useComponentPerformanceMonitoring } from './usePerformanceMonitoring';
import WeeklyProgramDisplay from './WeeklyProgramDisplay';
import TimelineVisualization from './TimelineVisualization';
import RaceGoalsPage from './RaceGoalsPage';
import RaceHistoryPage from './RaceHistoryPage';
import TrainingSchedulePage from './TrainingSchedulePage';

// ============================================================================
// STRATEGIC CONTEXT DISPLAY COMPONENT (Collapsible Sections)
// ============================================================================

interface StrategicContextProps {
  strategicContext: {
    race_context_periodization: string;
    load_management_pattern_analysis: string;
    strategic_rationale: string;
  };
}

const StrategicContextDisplay: React.FC<StrategicContextProps> = ({ strategicContext }) => {
  const [expandedSection, setExpandedSection] = useState<string | null>(null);

  // Debug: log the strategic context to see what we're receiving
  console.log('Strategic Context Data:', strategicContext);

  const toggleSection = (section: string) => {
    setExpandedSection(expandedSection === section ? null : section);
  };

  const CollapsibleSection = ({ 
    id, 
    title, 
    emoji, 
    content, 
    bgColor, 
    borderColor, 
    textColor 
  }: { 
    id: string; 
    title: string; 
    emoji: string; 
    content: string; 
    bgColor: string; 
    borderColor: string; 
    textColor: string;
  }) => {
    const isExpanded = expandedSection === id;

    return (
      <div style={{
        marginBottom: '0.75rem',
        border: `1px solid ${borderColor}`,
        borderRadius: '8px',
        overflow: 'hidden'
      }}>
        <button
          onClick={() => toggleSection(id)}
          style={{
            width: '100%',
            padding: '1rem',
            backgroundColor: bgColor,
            border: 'none',
            cursor: 'pointer',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            textAlign: 'left'
          }}
        >
          <h3 style={{
            fontSize: '16px',
            fontWeight: '600',
            color: textColor,
            margin: 0,
            display: 'flex',
            alignItems: 'center',
            gap: '0.5rem'
          }}>
            {emoji} {title}
          </h3>
          <span style={{ fontSize: '18px', color: textColor }}>
            {isExpanded ? '▼' : '▶'}
          </span>
        </button>
        {isExpanded && (
          <div style={{
            padding: '1rem',
            backgroundColor: 'white',
            borderTop: `1px solid ${borderColor}`
          }}>
            <p style={{
              margin: 0,
              lineHeight: '1.7',
              color: '#374151',
              fontSize: '15px',
              whiteSpace: 'pre-wrap'
            }}>
              {content}
            </p>
          </div>
        )}
      </div>
    );
  };

  return (
    <div className={styles.card} style={{ marginBottom: '0.75rem', padding: '1rem' }}>
      <h2 style={{
        fontSize: '20px',
        fontWeight: '700',
        marginBottom: '1rem',
        color: '#1e293b',
        borderBottom: '2px solid #e1e8ed',
        paddingBottom: '0.5rem'
      }}>
        Strategic Analysis & Context
      </h2>

      <CollapsibleSection
        id="race"
        title="Race Context & Periodization"
        emoji=""
        content={strategicContext.race_context_periodization}
        bgColor="#f0f9ff"
        borderColor="#3b82f6"
        textColor="#1e40af"
      />

      <CollapsibleSection
        id="load"
        title="Load Management & Pattern Analysis"
        emoji=""
        content={strategicContext.load_management_pattern_analysis}
        bgColor="#fef3c7"
        borderColor="#f59e0b"
        textColor="#92400e"
      />

      <CollapsibleSection
        id="rationale"
        title="Strategic Rationale & Training Science"
        emoji=""
        content={strategicContext.strategic_rationale}
        bgColor="#f0fdf4"
        borderColor="#10b981"
        textColor="#065f46"
      />

      {/* Integration Hint */}
      <div style={{
        marginTop: '1rem',
        padding: '0.75rem',
        backgroundColor: '#f8f9fa',
        borderRadius: '6px',
        fontSize: '13px',
        color: '#6b7280',
        fontStyle: 'italic',
        textAlign: 'center'
      }}>
        💡 Visit the <strong>Journal</strong> page daily for today's specific guidance and post-workout analysis
      </div>
    </div>
  );
};

// ============================================================================
// TYPESCRIPT INTERFACES
// ============================================================================

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

interface RaceHistory {
  id: number;
  race_date: string;
  race_name: string;
  distance_miles: number;
  finish_time_minutes: number;
}

interface TrainingSchedule {
  schedule: {
    total_hours_per_week?: number;
    available_days?: string[];
    time_blocks?: { [key: string]: string[] };
    constraints?: string;
  } | null;
  include_strength: boolean;
  strength_hours: number;
  include_mobility: boolean;
  mobility_hours: number;
  include_cross_training: boolean;
  cross_training_type: string | null;
  cross_training_hours: number;
}

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
  strategic_context?: {
    race_context_periodization: string;
    load_management_pattern_analysis: string;
    strategic_rationale: string;
  };
  from_cache?: boolean;
}

interface TrainingStage {
  stage: string;
  weeks_to_race: number | null;
  race_name: string | null;
  priority?: string;
  details: string;
  timeline?: TimelineWeek[];
}

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

interface RaceAnalysis {
  prs: Array<{
    distance_miles: number;
    finish_time_minutes: number;
    race_name: string;
    race_date: string;
    pace_per_mile: number;
  }>;
  trend: string;
  trend_description: string;
  base_fitness: string;
  total_races: number;
}

// ============================================================================
// MAIN COMPONENT
// ============================================================================

const CoachPage: React.FC = () => {
  // Performance monitoring
  usePagePerformanceMonitoring('coach');
  const perfMonitor = useComponentPerformanceMonitoring('CoachPage');

  // State management (only what's needed for Coach page display)
  const [raceGoals, setRaceGoals] = useState<RaceGoal[]>([]);
  const [weeklyProgram, setWeeklyProgram] = useState<WeeklyProgram | null>(null);
  const [trainingStage, setTrainingStage] = useState<TrainingStage | null>(null);
  
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [showOnboarding, setShowOnboarding] = useState<boolean>(false);
  
  // Secondary navigation state
  const [activeSubTab, setActiveSubTab] = useState<'workout' | 'goals' | 'history' | 'schedule'>('workout');

  // Schedule review state
  const [scheduleReviewStatus, setScheduleReviewStatus] = useState<{
    needs_review: boolean;
    week_start: string;
    is_sunday: boolean;
  } | null>(null);
  const [showScheduleReviewBanner, setShowScheduleReviewBanner] = useState<boolean>(false);

  // ============================================================================
  // DATA FETCHING
  // ============================================================================

  const fetchCoachData = async () => {
    const startTime = performance.now();
    setIsLoading(true);
    setError(null);

    try {
      // Fetch only data needed for Coach page display
      const [
        goalsRes,
        stageRes,
        programRes,
        reviewStatusRes
      ] = await Promise.all([
        fetch('/api/coach/race-goals'),
        fetch('/api/coach/training-stage'),
        fetch('/api/coach/weekly-program'),
        fetch('/api/coach/schedule-review-status')
      ]);

      // Check for critical errors (race goals is essential)
      if (!goalsRes.ok) throw new Error('Failed to fetch race goals');

      // Parse race goals (critical for countdown banner)
      const goalsData = await goalsRes.json();
      setRaceGoals(goalsData.goals || []);

      // Parse training stage (for timeline and countdown banner color)
      if (stageRes.ok) {
        const stageData = await stageRes.json();
        // API returns { current_stage: {...}, timeline: [...] }
        // Transform to match TrainingStage interface
        // Ensure races arrays are always arrays (not null)
        const transformedTimeline = (stageData.timeline || []).map((week: any) => ({
          ...week,
          races: Array.isArray(week.races) ? week.races : []
        }));
        
        setTrainingStage({
          stage: stageData.current_stage?.stage || null,
          weeks_to_race: stageData.current_stage?.weeks_to_race || null,
          race_name: stageData.current_stage?.race_name || null,
          priority: stageData.current_stage?.priority || null,
          details: stageData.current_stage?.stage_description || '',
          timeline: transformedTimeline
        });
      } else {
        console.warn('Failed to fetch training stage');
        setTrainingStage(null);
      }

      // Parse weekly program
      if (programRes.ok) {
        const programData = await programRes.json();
        setWeeklyProgram(programData.program || null);
      } else {
        console.warn('Failed to fetch weekly program');
        setWeeklyProgram(null);
      }

      // Parse schedule review status
      if (reviewStatusRes.ok) {
        const reviewData = await reviewStatusRes.json();
        if (reviewData.success) {
          setScheduleReviewStatus({
            needs_review: reviewData.needs_review,
            week_start: reviewData.week_start,
            is_sunday: reviewData.is_sunday
          });
          setShowScheduleReviewBanner(reviewData.needs_review);
        }
      }

      // Check if onboarding needed (no race goals)
      if (!goalsData.goals || goalsData.goals.length === 0) {
        setShowOnboarding(true);
      } else {
        setShowOnboarding(false);  // Hide onboarding if goals exist
      }

      // Report performance
      const loadTime = performance.now() - startTime;
      perfMonitor.reportMetrics(loadTime);

    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to load coach data';
      setError(errorMessage);
      perfMonitor.reportMetrics(0, errorMessage);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchCoachData();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // ============================================================================
  // HELPER FUNCTIONS
  // ============================================================================

  const calculateDaysToRace = (raceDate: string): number => {
    const today = new Date();
    const race = new Date(raceDate);
    const diffTime = race.getTime() - today.getTime();
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
    return diffDays;
  };

  const getPrimaryRace = (): RaceGoal | null => {
    // Find A race first, then B, then C, then first race
    const aRace = raceGoals.find(g => g.priority === 'A');
    if (aRace) return aRace;
    
    const bRace = raceGoals.find(g => g.priority === 'B');
    if (bRace) return bRace;
    
    const cRace = raceGoals.find(g => g.priority === 'C');
    if (cRace) return cRace;
    
    return raceGoals.length > 0 ? raceGoals[0] : null;
  };

  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  const formatTime = (minutes: number): string => {
    const hours = Math.floor(minutes / 60);
    const mins = Math.floor(minutes % 60);
    if (hours > 0) {
      return `${hours}h ${mins}m`;
    }
    return `${mins}m`;
  };

  const handleAcceptSchedule = async () => {
    try {
      const response = await fetch('/api/coach/schedule-review-accept', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' }
      });
      
      if (response.ok) {
        setShowScheduleReviewBanner(false);
        setScheduleReviewStatus(prev => prev ? { ...prev, needs_review: false } : null);
      }
    } catch (err) {
      console.error('Error accepting schedule:', err);
    }
  };

  const handleDismissBanner = () => {
    setShowScheduleReviewBanner(false);
  };

  // ============================================================================
  // RENDER: LOADING STATE
  // ============================================================================

  if (isLoading) {
    return (
      <div className={styles.dashboardContainer}>
        <div className={styles.card} style={{ textAlign: 'center', padding: '60px 20px' }}>
          <div className={styles.spinner}></div>
          <p style={{ marginTop: '20px', color: '#7f8c8d' }}>
            Loading your coaching dashboard...
          </p>
        </div>
      </div>
    );
  }

  // ============================================================================
  // RENDER: ERROR STATE
  // ============================================================================

  if (error) {
    return (
      <div className={styles.dashboardContainer}>
        <div className={styles.card} style={{ textAlign: 'center', padding: '60px 20px' }}>
          <h2 style={{ color: '#e74c3c', marginBottom: '20px' }}>⚠️ Error Loading Coach Page</h2>
          <p style={{ color: '#7f8c8d', marginBottom: '30px' }}>{error}</p>
          <button
            onClick={() => window.location.reload()}
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

  // ============================================================================
  // RENDER: ONBOARDING MODAL
  // ============================================================================

  if (showOnboarding) {
    return (
      <div className={styles.dashboardContainer}>
        <div className={styles.card} style={{ maxWidth: '600px', margin: '40px auto', padding: '40px' }}>
          <h1 style={{ fontSize: '32px', marginBottom: '20px', textAlign: 'center' }}>
            Welcome to Coach YTM! 🐵
          </h1>
          <p style={{ fontSize: '18px', color: '#7f8c8d', marginBottom: '30px', textAlign: 'center' }}>
            Let's set up your coaching profile to generate personalized training programs.
          </p>

          <div style={{ marginBottom: '30px' }}>
            <h3 style={{ marginBottom: '15px' }}>Quick Setup (3 steps):</h3>
            <ol style={{ fontSize: '16px', lineHeight: '1.8', paddingLeft: '20px' }}>
              <li>
                <strong>Add Your Race Goals</strong> - What races are you training for?
                (A races are your primary focus, B races help evaluate fitness, C races are training volume)
              </li>
              <li>
                <strong>Upload Race History</strong> - Past race results help assess your fitness trends
                (optional but recommended)
              </li>
              <li>
                <strong>Configure Training Schedule</strong> - Tell us your weekly availability
                so we can fit training into your life
              </li>
            </ol>
          </div>

          <div style={{ display: 'flex', gap: '15px', justifyContent: 'center' }}>
            <button
              onClick={() => {
                setShowOnboarding(false);
                setActiveSubTab('goals'); // Navigate to Race Goals tab
              }}
              style={{
                padding: '14px 28px',
                fontSize: '16px',
                backgroundColor: '#3498db',
                color: 'white',
                border: 'none',
                borderRadius: '4px',
                cursor: 'pointer',
                fontWeight: 'bold'
              }}
            >
              Let's Get Started! 🚀
            </button>
            <button
              onClick={() => setShowOnboarding(false)}
              style={{
                padding: '14px 28px',
                fontSize: '16px',
                backgroundColor: '#95a5a6',
                color: 'white',
                border: 'none',
                borderRadius: '4px',
                cursor: 'pointer'
              }}
            >
              Skip for Now
            </button>
          </div>

          <p style={{ 
            marginTop: '30px', 
            fontSize: '14px', 
            color: '#95a5a6', 
            textAlign: 'center' 
          }}>
            Don't worry - you can set this up anytime. But the more we know,<br />
            the better your personalized training programs will be!
          </p>
        </div>
      </div>
    );
  }

  // ============================================================================
  // RENDER: MAIN COACH PAGE
  // ============================================================================

  const primaryRace = getPrimaryRace();
  const daysToRace = primaryRace ? calculateDaysToRace(primaryRace.race_date) : null;

  return (
    <div className={styles.dashboardContainer}>
      
      {/* ============================================================
          HEADER (matching Guide page style)
      ============================================================ */}
      <style>{`
        .coach-header {
          background: linear-gradient(90deg, #E6F0FF 0%, #7D9CB8 50%, #1B2E4B 100%);
          color: white;
          text-align: right;
          padding: 1.2rem 1.6rem; /* 80% of 1.5rem and 2rem */
          position: relative;
          overflow: hidden;
          min-height: 180px;
          display: flex;
          align-items: center;
          justify-content: space-between;
          margin-bottom: 0;
        }
        .coach-header::before {
          content: '';
          position: absolute;
          top: 0;
          left: 0;
          right: 0;
          bottom: 0;
          background: 
            radial-gradient(circle at 20% 30%, rgba(230, 240, 255, 0.3) 0%, transparent 50%),
            radial-gradient(circle at 80% 70%, rgba(125, 156, 184, 0.25) 0%, transparent 50%),
            radial-gradient(circle at 50% 50%, rgba(180, 200, 220, 0.2) 0%, transparent 60%),
            radial-gradient(circle at 10% 80%, rgba(27, 46, 75, 0.25) 0%, transparent 45%),
            radial-gradient(circle at 90% 20%, rgba(100, 130, 160, 0.2) 0%, transparent 50%);
          pointer-events: none;
          mix-blend-mode: multiply;
        }
        .coach-header::after {
          content: '';
          position: absolute;
          top: 0;
          left: 0;
          right: 0;
          bottom: 0;
          background-image: 
            repeating-linear-gradient(0deg, transparent, transparent 2px, rgba(255, 255, 255, 0.03) 2px, rgba(255, 255, 255, 0.03) 4px),
            repeating-linear-gradient(90deg, transparent, transparent 2px, rgba(0, 0, 0, 0.02) 2px, rgba(0, 0, 0, 0.02) 4px);
          pointer-events: none;
          opacity: 0.4;
        }
        .coach-header-logo {
          flex-shrink: 0;
          width: 200px;
          height: 200px;
          margin-left: 1.6rem; /* 80% of 2rem */
          filter: drop-shadow(2px 4px 8px rgba(0,0,0,0.3));
        }
        .coach-header-logo img {
          width: 100%;
          height: 100%;
          object-fit: contain;
          display: block;
        }
        .coach-header-content {
          position: relative;
          z-index: 2;
          max-width: 500px;
          margin: 0;
          margin-right: calc(50% - 700px);
          display: flex;
          flex-direction: column;
          justify-content: center;
          height: 100%;
          text-align: right;
        }
        .coach-header-content h1 {
          font-size: 2.5rem;
          font-weight: 700;
          margin: 0.5rem 0;
          text-shadow: 2px 2px 4px rgba(0,0,0,0.4);
          white-space: nowrap;
          line-height: 1.2;
        }
        .coach-header-content .subtitle {
          font-size: 1.2rem;
          margin: 0.25rem 0;
          opacity: 0.95;
          font-weight: 300;
          text-shadow: 1px 1px 2px rgba(0,0,0,0.3);
          line-height: 1.4;
        }
        @media (max-width: 768px) {
          .coach-header {
            min-height: 160px;
            padding: 0.8rem; /* 80% of 1rem */
            flex-direction: column;
            text-align: center;
          }
          .coach-header-logo {
            width: 150px;
            height: 150px;
            margin-left: 1rem;
          }
          .coach-header-content {
            margin-right: 0;
            text-align: center;
          }
          .coach-header-content h1 {
            font-size: 2rem;
            white-space: nowrap;
          }
          .coach-header-content .subtitle {
            font-size: 1.1rem;
          }
        }
        @media (max-width: 480px) {
          .coach-header {
            padding: 1.2rem 0.8rem; /* 80% of 1.5rem and 1rem */
            min-height: 140px;
          }
          .coach-header-logo {
            width: 120px;
            height: 120px;
            margin-left: 0.4rem; /* 80% of 0.5rem */
          }
          .coach-header-content h1 {
            font-size: 1.8rem;
            white-space: nowrap;
          }
        }
      `}</style>
      <div className="coach-header">
        {/* YTM Logo - Left Side */}
        <div className="coach-header-logo">
          <img 
            src="/static/images/YTM_waterColor_patch800x800_clean.webp" 
            alt="Your Training Monkey - YTM Logo"
          />
        </div>
        
        {/* Header Text - Right Side with Secondary Nav */}
        <div className="coach-header-content">
          <div style={{ textAlign: 'right', marginBottom: '1rem' }}>
            <h1>
              <span style={{ color: '#7ec8e3', fontWeight: '800', fontSize: '1.1em' }}>Y</span>our{' '}
              <span style={{ color: '#7ec8e3', fontWeight: '800', fontSize: '1.1em' }}>T</span>raining{' '}
              <span style={{ color: '#7ec8e3', fontWeight: '800', fontSize: '1.1em' }}>M</span>onkey
            </h1>
            <p className="subtitle">Divergence-Optimized Training Programs for Ultrarunners</p>
          </div>
          
          {/* Secondary Navigation - Right side under header text with white border container */}
          <div style={{ 
            display: 'flex', 
            justifyContent: 'flex-end',
            marginTop: '1rem'
          }}>
            <div style={{
              border: '2px solid white',
              borderRadius: '10px',
              padding: '0.5rem',
              backgroundColor: 'rgba(255, 255, 255, 0.1)',
              backdropFilter: 'blur(10px)',
              display: 'inline-block'
            }}>
              <ul style={{
                display: 'flex',
                gap: '0.5rem',
                listStyle: 'none',
                alignItems: 'center',
                margin: 0,
                padding: 0,
                flexWrap: 'nowrap'
              }}>
                {[
                  { key: 'workout', label: 'Workout Plan' },
                  { key: 'goals', label: 'Race Goals' },
                  { key: 'history', label: 'Race History' },
                  { key: 'schedule', label: 'Training Schedule' }
                ].map((tab) => (
                  <li key={tab.key} style={{ flexShrink: 0 }}>
                    <a
                      onClick={(e) => {
                        e.preventDefault();
                        setActiveSubTab(tab.key as 'workout' | 'goals' | 'history' | 'schedule');
                      }}
                      style={{
                        display: 'inline-block',
                        padding: '0.6rem 1rem',
                        background: activeSubTab === tab.key 
                          ? 'rgba(255, 255, 255, 0.95)' 
                          : 'rgba(255, 255, 255, 0.7)',
                        color: activeSubTab === tab.key ? '#1B2E4B' : '#1f2937',
                        textDecoration: 'none',
                        fontWeight: activeSubTab === tab.key ? '700' : '500',
                        fontSize: activeSubTab === tab.key ? '0.95rem' : '0.9rem',
                        border: '2px solid',
                        borderColor: activeSubTab === tab.key 
                          ? 'rgba(27, 46, 75, 0.3)' 
                          : 'transparent',
                        borderRadius: '8px',
                        transition: 'all 0.3s ease',
                        boxShadow: activeSubTab === tab.key 
                          ? '0 2px 6px rgba(27, 46, 75, 0.2)' 
                          : '0 1px 3px rgba(0, 0, 0, 0.05)',
                        position: 'relative',
                        cursor: 'pointer',
                        textAlign: 'center',
                        whiteSpace: 'nowrap',
                        minWidth: 'auto'
                      }}
                      onMouseEnter={(e) => {
                        if (activeSubTab !== tab.key) {
                          e.currentTarget.style.color = '#667eea';
                          e.currentTarget.style.background = 'rgba(255, 255, 255, 0.95)';
                          e.currentTarget.style.borderColor = 'rgba(102, 126, 234, 0.3)';
                          e.currentTarget.style.transform = 'translateY(-2px)';
                          e.currentTarget.style.boxShadow = '0 4px 8px rgba(102, 126, 234, 0.15)';
                        }
                      }}
                      onMouseLeave={(e) => {
                        if (activeSubTab !== tab.key) {
                          e.currentTarget.style.color = '#1f2937';
                          e.currentTarget.style.background = 'rgba(255, 255, 255, 0.7)';
                          e.currentTarget.style.borderColor = 'transparent';
                          e.currentTarget.style.transform = 'translateY(0)';
                          e.currentTarget.style.boxShadow = '0 1px 3px rgba(0, 0, 0, 0.05)';
                        }
                      }}
                    >
                      {/* Top arrow for active tab - white */}
                      {activeSubTab === tab.key && (
                        <div style={{
                          position: 'absolute',
                          top: '-12px',
                          left: '50%',
                          transform: 'translateX(-50%)',
                          width: 0,
                          height: 0,
                          borderLeft: '10px solid transparent',
                          borderRight: '10px solid transparent',
                          borderBottom: '10px solid white',
                          filter: 'drop-shadow(0 2px 4px rgba(0, 0, 0, 0.3))',
                          zIndex: 10
                        }}></div>
                      )}
                      {/* Center-aligned text */}
                      <span style={{ 
                        display: 'block', 
                        textAlign: 'center',
                        fontWeight: activeSubTab === tab.key ? '700' : '500',
                        fontSize: activeSubTab === tab.key ? '0.95rem' : '0.9rem',
                        letterSpacing: activeSubTab === tab.key ? '0.02em' : 'normal'
                      }}>
                        {tab.label}
                      </span>
                      {/* Bottom arrow for active tab - white */}
                      {activeSubTab === tab.key && (
                        <div style={{
                          position: 'absolute',
                          bottom: '-12px',
                          left: '50%',
                          transform: 'translateX(-50%)',
                          width: 0,
                          height: 0,
                          borderLeft: '10px solid transparent',
                          borderRight: '10px solid transparent',
                          borderTop: '10px solid white',
                          filter: 'drop-shadow(0 2px 4px rgba(0, 0, 0, 0.3))',
                          zIndex: 10
                        }}></div>
                      )}
                    </a>
                  </li>
                ))}
              </ul>
            </div>
          </div>
        </div>
      </div>

      {/* ============================================================
          BOUNDARY BETWEEN HEADER AND COUNTDOWN (2px white gap)
      ============================================================ */}
      <div style={{
        height: '0.125rem', // 2px on desktop (16px base)
        backgroundColor: 'white',
        marginBottom: '0'
      }}></div>

      {/* ============================================================
          COUNTDOWN BANNER (two columns, matches phase color)
      ============================================================ */}
      {primaryRace && daysToRace !== null && (() => {
        // Get phase color for text based on training stage
        const getPhaseTextColor = (stage: string | null): string => {
          if (!stage) return '#ffffff';
          
          const stageColors: { [key: string]: string } = {
            'base': '#7ec8e3',      // Light blue
            'build': '#81c784',     // Light green
            'specificity': '#ffb74d', // Light orange
            'taper': '#ba68c8',     // Light purple
            'peak': '#e57373',      // Light red
            'recovery': '#90a4ae'   // Light gray
          };
          
          return stageColors[stage.toLowerCase()] || '#ffffff';
        };
        
        const textColor = trainingStage?.stage ? getPhaseTextColor(trainingStage.stage) : '#ffffff';
        
        return (
          <div className={styles.card} style={{ 
            marginBottom: '0 !important', // Override CSS class default margin
            padding: '1rem 1.25rem',
            background: 'linear-gradient(90deg, #1B2E4B 0%, #4A5F7F 50%, #B8C5D6 100%)', // Darker gradient: deep navy to lighter gray-blue
            color: textColor,
            display: 'flex',
            alignItems: 'center'
          }}>
            {/* 5-segment layout: 1=empty, 2=countdown, 3=empty, 4=race info, 5=empty */}
            
            {/* Segment 1: Empty (20% width) */}
            <div style={{ flex: '0 0 20%' }}></div>
            
            {/* Segment 2: Days Countdown (20% width) */}
            <div style={{ flex: '0 0 20%', textAlign: 'center' }}>
              <div style={{ fontSize: '48px', fontWeight: 'bold', lineHeight: '1' }}>
                {daysToRace}
              </div>
              <div style={{ fontSize: '16px', marginTop: '5px', opacity: 0.9 }}>
                {daysToRace === 1 ? 'day' : 'days'}
              </div>
            </div>
            
            {/* Segment 3: Empty (20% width) */}
            <div style={{ flex: '0 0 20%' }}></div>
            
            {/* Segment 4: Race Description (20% width) */}
            <div style={{ flex: '0 0 20%' }}>
              <div style={{ fontSize: '20px', fontWeight: 'bold', marginBottom: '5px' }}>
                {primaryRace.race_name}
              </div>
              <div style={{ fontSize: '16px', opacity: 0.9 }}>
                {primaryRace.race_type} • {primaryRace.race_date} • Priority {primaryRace.priority}
              </div>
            </div>
            
            {/* Segment 5: Empty (20% width) */}
            <div style={{ flex: '0 0 20%' }}></div>
          </div>
        );
      })()}

      {/* ============================================================
          SCHEDULE REVIEW BANNER (Sunday only)
      ============================================================ */}
      {scheduleReviewStatus?.needs_review && showScheduleReviewBanner && (
        <div className={styles.card} style={{
          marginTop: '0.75rem',
          marginBottom: '0.75rem',
          padding: '1rem 1.25rem',
          backgroundColor: '#fff3cd',
          border: '2px solid #ffc107',
          borderRadius: '8px'
        }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: '1rem' }}>
            <div style={{ flex: 1 }}>
              <h3 style={{ margin: 0, marginBottom: '0.5rem', color: '#856404', fontSize: '18px', fontWeight: '600' }}>
                📅 Review Your Training Schedule for Next Week
              </h3>
              <p style={{ margin: 0, color: '#856404', fontSize: '14px' }}>
                Week of {scheduleReviewStatus.week_start ? new Date(scheduleReviewStatus.week_start).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' }) : ''} - Confirm your availability before Sunday 6 PM
              </p>
            </div>
            <div style={{ display: 'flex', gap: '0.5rem', flexShrink: 0 }}>
              <button
                onClick={handleAcceptSchedule}
                style={{
                  padding: '10px 20px',
                  backgroundColor: '#28a745',
                  color: 'white',
                  border: 'none',
                  borderRadius: '6px',
                  cursor: 'pointer',
                  fontSize: '14px',
                  fontWeight: '600',
                  whiteSpace: 'nowrap'
                }}
              >
                ✓ Keep Current Schedule
              </button>
              <button
                onClick={() => setActiveSubTab('schedule')}
                style={{
                  padding: '10px 20px',
                  backgroundColor: '#007bff',
                  color: 'white',
                  border: 'none',
                  borderRadius: '6px',
                  cursor: 'pointer',
                  fontSize: '14px',
                  fontWeight: '600',
                  whiteSpace: 'nowrap'
                }}
              >
                ✏️ Update Schedule
              </button>
              <button
                onClick={handleDismissBanner}
                style={{
                  padding: '10px 15px',
                  backgroundColor: 'transparent',
                  color: '#856404',
                  border: '1px solid #856404',
                  borderRadius: '6px',
                  cursor: 'pointer',
                  fontSize: '14px',
                  fontWeight: '600'
                }}
                title="Dismiss"
              >
                ✕
              </button>
            </div>
          </div>
        </div>
      )}

      {/* ============================================================
          TIMELINE VISUALIZATION (immediately below countdown with minimal gap)
      ============================================================ */}
      {trainingStage && trainingStage.timeline && trainingStage.timeline.length > 0 && (
        <>
          {/* Minimal white gap - reduced to absolute minimum */}
          <div style={{
            height: '1px', // Absolute minimum 1px
            backgroundColor: 'white',
            margin: '0',
            padding: '0',
            lineHeight: '0'
          }}></div>
          <div className={styles.card} style={{ 
            marginTop: '0 !important', 
            marginBottom: '0.125rem !important', 
            paddingTop: '0.5rem',
            paddingBottom: '0.5rem',
            paddingLeft: '1rem',
            paddingRight: '1rem'
          }}>
            <TimelineVisualization trainingStage={trainingStage} />
          </div>
        </>
      )}

      {/* ============================================================
          TAB CONTENT AREA - Route to separate pages
      ============================================================ */}
      {activeSubTab === 'workout' && (
        <>
          {/* 7-Day Workout Plan */}
          <div className={styles.card} style={{ marginBottom: '0.75rem', padding: '0.75rem 1rem' }}>
            <WeeklyProgramDisplay program={weeklyProgram} onRefresh={fetchCoachData} />
          </div>

          {/* Strategic Analysis & Context - Enhanced with collapsible sections */}
          {weeklyProgram?.strategic_context && (
            <StrategicContextDisplay strategicContext={weeklyProgram.strategic_context} />
          )}
        </>
      )}
      {activeSubTab === 'goals' && <RaceGoalsPage />}
      {activeSubTab === 'history' && <RaceHistoryPage />}
      {activeSubTab === 'schedule' && <TrainingSchedulePage />}

    </div>
  );
};

export default CoachPage;

