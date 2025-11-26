import React, { useState, useEffect } from 'react';
import styles from './TrainingLoadDashboard.module.css';
import { usePagePerformanceMonitoring, useComponentPerformanceMonitoring } from './usePerformanceMonitoring';
import RaceGoalsManager from './RaceGoalsManager';
import RaceHistoryManager from './RaceHistoryManager';
import TrainingScheduleConfig from './TrainingScheduleConfig';
import WeeklyProgramDisplay from './WeeklyProgramDisplay';
import TimelineVisualization from './TimelineVisualization';

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

  // State management
  const [raceGoals, setRaceGoals] = useState<RaceGoal[]>([]);
  const [raceHistory, setRaceHistory] = useState<RaceHistory[]>([]);
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  const [raceAnalysis, setRaceAnalysis] = useState<RaceAnalysis | null>(null);
  const [trainingSchedule, setTrainingSchedule] = useState<TrainingSchedule | null>(null);
  const [weeklyProgram, setWeeklyProgram] = useState<WeeklyProgram | null>(null);
  const [trainingStage, setTrainingStage] = useState<TrainingStage | null>(null);
  
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [showOnboarding, setShowOnboarding] = useState<boolean>(false);

  // ============================================================================
  // DATA FETCHING
  // ============================================================================

  useEffect(() => {
    const fetchCoachData = async () => {
      const startTime = performance.now();
      setIsLoading(true);
      setError(null);

      try {
        // Fetch all data in parallel
        const [
          goalsRes,
          historyRes,
          analysisRes,
          scheduleRes,
          stageRes,
          programRes
        ] = await Promise.all([
          fetch('/api/coach/race-goals'),
          fetch('/api/coach/race-history'),
          fetch('/api/coach/race-analysis'),
          fetch('/api/coach/training-schedule'),
          fetch('/api/coach/training-stage'),
          fetch('/api/coach/weekly-program')
        ]);

        // Check for errors
        if (!goalsRes.ok) throw new Error('Failed to fetch race goals');
        if (!historyRes.ok) throw new Error('Failed to fetch race history');
        if (!analysisRes.ok) throw new Error('Failed to fetch race analysis');
        if (!scheduleRes.ok) throw new Error('Failed to fetch training schedule');
        if (!stageRes.ok) throw new Error('Failed to fetch training stage');
        if (!programRes.ok) throw new Error('Failed to fetch weekly program');

        // Parse responses
        const goalsData = await goalsRes.json();
        const historyData = await historyRes.json();
        const analysisData = await analysisRes.json();
        const scheduleData = await scheduleRes.json();
        const stageData = await stageRes.json();
        const programData = await programRes.json();

        // Update state
        setRaceGoals(goalsData.goals || []);
        setRaceHistory(historyData.history || []);
        setRaceAnalysis(analysisData);
        setTrainingSchedule(scheduleData.schedule || null);
        setTrainingStage(stageData);
        setWeeklyProgram(programData.program || null);

        // Check if onboarding needed (no race goals)
        if (!goalsData.goals || goalsData.goals.length === 0) {
          setShowOnboarding(true);
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
            Welcome to Your Training Monkey Coach! 🐵
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
              onClick={() => setShowOnboarding(false)}
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
          HEADER
      ============================================================ */}
      <div className={styles.card} style={{ 
        marginBottom: '20px', 
        padding: '30px',
        background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
        color: 'white',
        textAlign: 'center'
      }}>
        <h1 style={{ 
          fontSize: '36px', 
          margin: '0 0 10px 0', 
          fontWeight: 'bold',
          textShadow: '2px 2px 4px rgba(0,0,0,0.3)'
        }}>
          Your Training Monkey Coach 🐵
        </h1>
        <p style={{ 
          fontSize: '18px', 
          margin: 0, 
          opacity: 0.95,
          textShadow: '1px 1px 2px rgba(0,0,0,0.3)'
        }}>
          Divergence-Optimized Training Programs for Ultrarunners
        </p>
      </div>

      {/* ============================================================
          COUNTDOWN BANNER (if race goal exists)
      ============================================================ */}
      {primaryRace && daysToRace !== null && (
        <div className={styles.card} style={{ 
          marginBottom: '20px', 
          padding: '25px',
          background: daysToRace <= 14 ? 'linear-gradient(135deg, #f093fb 0%, #f5576c 100%)' : 
                      daysToRace <= 30 ? 'linear-gradient(135deg, #fa709a 0%, #fee140 100%)' :
                      'linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)',
          color: 'white',
          textAlign: 'center'
        }}>
          <div style={{ fontSize: '48px', fontWeight: 'bold', marginBottom: '10px' }}>
            {daysToRace}
          </div>
          <div style={{ fontSize: '20px', marginBottom: '5px' }}>
            {daysToRace === 1 ? 'day' : 'days'} until {primaryRace.race_name}
          </div>
          <div style={{ fontSize: '16px', opacity: 0.9 }}>
            {primaryRace.race_type} • {primaryRace.race_date} • Priority {primaryRace.priority}
          </div>
          {trainingStage && (
            <div style={{ 
              marginTop: '15px', 
              fontSize: '16px', 
              padding: '10px 20px',
              background: 'rgba(255, 255, 255, 0.2)',
              borderRadius: '20px',
              display: 'inline-block'
            }}>
              Current Stage: <strong>{trainingStage.stage}</strong>
            </div>
          )}
        </div>
      )}

      {/* ============================================================
          NO RACE GOAL NOTICE
      ============================================================ */}
      {!primaryRace && (
        <div className={styles.card} style={{ 
          marginBottom: '20px', 
          padding: '25px',
          background: '#f8f9fa',
          border: '2px dashed #3498db',
          textAlign: 'center'
        }}>
          <h3 style={{ color: '#3498db', marginBottom: '10px' }}>
            📅 No Race Goal Set
          </h3>
          <p style={{ color: '#7f8c8d', marginBottom: '15px' }}>
            Add a race goal to unlock personalized training programs and race-day countdown!
          </p>
          <button
            style={{
              padding: '10px 20px',
              backgroundColor: '#3498db',
              color: 'white',
              border: 'none',
              borderRadius: '4px',
              cursor: 'pointer',
              fontSize: '16px'
            }}
          >
            Add Race Goal
          </button>
        </div>
      )}

      {/* ============================================================
          PLACEHOLDER SECTIONS (to be implemented in Tasks 8-10)
      ============================================================ */}

      {/* Race Goals Card */}
      <div className={styles.card} style={{ marginBottom: '20px' }}>
        <RaceGoalsManager goals={raceGoals} onGoalsChange={() => window.location.reload()} />
      </div>

      {/* Race History Card */}
      <div className={styles.card} style={{ marginBottom: '20px' }}>
        <RaceHistoryManager history={raceHistory} onHistoryChange={() => window.location.reload()} />
      </div>

      {/* Training Schedule Card */}
      <div className={styles.card} style={{ marginBottom: '20px' }}>
        <TrainingScheduleConfig schedule={trainingSchedule} onScheduleChange={() => window.location.reload()} />
      </div>

      {/* Timeline Visualization Card */}
      <div className={styles.card} style={{ marginBottom: '20px' }}>
        <TimelineVisualization trainingStage={trainingStage} />
      </div>

      {/* Weekly Training Program Card */}
      <div className={styles.card} style={{ marginBottom: '20px' }}>
        <WeeklyProgramDisplay program={weeklyProgram} onRefresh={() => window.location.reload()} />
      </div>

      {/* Debug Info (remove in production) */}
      {process.env.NODE_ENV === 'development' && (
        <div className={styles.card} style={{ marginBottom: '20px', opacity: 0.7 }}>
          <h3 style={{ fontSize: '14px', marginBottom: '10px' }}>Debug Info:</h3>
          <pre style={{ fontSize: '12px', overflow: 'auto', maxHeight: '200px' }}>
            {JSON.stringify({
              raceGoalsCount: raceGoals.length,
              raceHistoryCount: raceHistory.length,
              hasSchedule: !!trainingSchedule,
              hasProgram: !!weeklyProgram,
              trainingStage: trainingStage?.stage,
              primaryRace: primaryRace?.race_name
            }, null, 2)}
          </pre>
        </div>
      )}

    </div>
  );
};

export default CoachPage;

