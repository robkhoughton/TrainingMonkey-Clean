import React, { useState, useEffect, useCallback } from 'react';
import styles from './TrainingLoadDashboard.module.css'; // Reuse existing styles
import { usePagePerformanceMonitoring, useComponentPerformanceMonitoring } from './usePerformanceMonitoring';

interface JournalEntry {
  date: string;
  is_today: boolean;
  is_future?: boolean;  // NEW: indicates if entry is for a future date
  is_tomorrow?: boolean;  // NEW: indicates if entry is for tomorrow
  has_observations?: boolean;  // NEW: indicates if journal observations have been saved
  is_next_incomplete?: boolean;  // NEW: indicates this is the next workout to complete
  todays_decision: string;
  activity_summary: {
    type: string;
    distance: number;
    elevation: number;
    workout_classification: string;
    total_trimp: number;
    activity_id?: number;
  } | null;  // Can be null for future dates
  observations: {
    energy_level: number | null;
    rpe_score: number | null;
    pain_percentage: number | null;
    notes: string;
  };
  ai_autopsy: {
    autopsy_analysis?: string;
    alignment_score?: number;
    generated_at?: string;
  };
}

interface JournalResponse {
  success: boolean;
  data: JournalEntry[];
  center_date: string;
  date_range: string;
  error?: string;
}

// Function to format training decision text with styled components
const formatTrainingDecision = (text: string): React.ReactNode => {
  if (!text || text === 'No AI recommendation available') {
    return <span style={{ fontStyle: 'italic', color: '#6b7280' }}>{text}</span>;
  }

  // Split by lines and process each
  const lines = text.split('\n');
  const elements: React.ReactNode[] = [];
  
  lines.forEach((line, index) => {
    const trimmedLine = line.trim();
    
    // Skip empty lines
    if (!trimmedLine) {
      elements.push(<br key={`br-${index}`} />);
      return;
    }
    
    // Check for headers (##)
    if (trimmedLine.startsWith('##')) {
      const headerText = trimmedLine.replace(/^##+\s*/, '');
      elements.push(
        <h3 key={`h3-${index}`} style={{
          fontSize: '1rem',
          fontWeight: '700',
          color: '#1e293b',
          marginTop: index > 0 ? '1rem' : '0',
          marginBottom: '0.5rem',
          paddingBottom: '0.25rem',
          borderBottom: '2px solid #e2e8f0'
        }}>
          {formatBoldText(headerText)}
        </h3>
      );
      return;
    }
    
    // Check for main headers (#)
    if (trimmedLine.startsWith('# ')) {
      const headerText = trimmedLine.replace(/^#+\s*/, '');
      elements.push(
        <h2 key={`h2-${index}`} style={{
          fontSize: '1.1rem',
          fontWeight: '700',
          color: '#1e293b',
          marginTop: index > 0 ? '1.25rem' : '0',
          marginBottom: '0.75rem',
          paddingBottom: '0.5rem',
          borderBottom: '3px solid #3b82f6'
        }}>
          {formatBoldText(headerText)}
        </h2>
      );
      return;
    }
    
    // Regular paragraph
    const paragraph = (
      <p key={`p-${index}`} style={{
        margin: '0.5rem 0',
        lineHeight: '1.6',
        color: '#374151'
      }}>
        {formatBoldText(trimmedLine)}
      </p>
    );
    elements.push(paragraph);
  });
  
  return <div>{elements}</div>;
};

// Helper function to format bold text (**text**)
const formatBoldText = (text: string): React.ReactNode => {
  const parts: React.ReactNode[] = [];
  const boldRegex = /\*\*(.*?)\*\*/g;
  let lastIndex = 0;
  let match;
  let key = 0;
  
  while ((match = boldRegex.exec(text)) !== null) {
    // Add text before the match
    if (match.index > lastIndex) {
      parts.push(text.substring(lastIndex, match.index));
    }
    
    // Add bold text
    parts.push(
      <strong key={`bold-${key++}`} style={{
        fontWeight: '700',
        color: '#1e293b'
      }}>
        {match[1]}
      </strong>
    );
    
    lastIndex = match.index + match[0].length;
  }
  
  // Add remaining text
  if (lastIndex < text.length) {
    parts.push(text.substring(lastIndex));
  }
  
  return parts.length > 0 ? <>{parts}</> : text;
};

const JournalPage: React.FC = () => {
  // Performance monitoring
  usePagePerformanceMonitoring('journal');
  const perfMonitor = useComponentPerformanceMonitoring('JournalPage');

  const [journalData, setJournalData] = useState<JournalEntry[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [centerDate, setCenterDate] = useState<string>('');
  const [isSaving, setIsSaving] = useState<string | null>(null);
  const [savedEntries, setSavedEntries] = useState<Set<string>>(new Set()); // Track saved entries
  
  // Modal state for full-screen autopsy display
  const [modalOpen, setModalOpen] = useState(false);
  const [modalAutopsy, setModalAutopsy] = useState<JournalEntry | null>(null);

  // Open modal with autopsy analysis
  const openAutopsyModal = (entry: JournalEntry) => {
    setModalAutopsy(entry);
    setModalOpen(true);
  };

  // Close modal
  const closeAutopsyModal = () => {
    setModalOpen(false);
    setModalAutopsy(null);
  };

  // Helper function to get alignment score color
  const getAlignmentScoreColor = (score: number): string => {
    if (score >= 8) return '#10b981'; // green
    if (score >= 6) return '#f59e0b'; // yellow
    if (score >= 4) return '#f97316'; // orange
    return '#ef4444'; // red
  };

  // Check if entry has been modified from saved state
  const hasUnsavedChanges = (entry: JournalEntry): boolean => {
    // If we just saved this entry, no unsaved changes
    if (savedEntries.has(entry.date)) {
      return false;
    }

    // Check if any field has a value (indicating user input)
    return !!(
      entry.observations.energy_level ||
      entry.observations.rpe_score ||
      entry.observations.pain_percentage ||
      entry.observations.notes?.trim()
    );
  };

  // Fetch journal data
  const fetchJournalData = useCallback(async (date?: string) => {
    try {
      setIsLoading(true);
      setError(null);

      perfMonitor.trackFetchStart();
      const url = date ? `/api/journal?date=${date}` : '/api/journal';
      const response = await fetch(url);

      if (!response.ok) {
        throw new Error(`Failed to fetch journal data: ${response.status}`);
      }

      const result: JournalResponse = await response.json();
      perfMonitor.trackFetchEnd();

      if (result.success) {
        setJournalData(result.data);
        setCenterDate(result.center_date);

        // Mark entries as saved if they have observations in the database
        const newSavedEntries = new Set<string>();
        result.data.forEach(entry => {
          if (entry.observations.energy_level ||
              entry.observations.rpe_score ||
              entry.observations.pain_percentage ||
              entry.observations.notes?.trim()) {
            newSavedEntries.add(entry.date);
          }
        });
        setSavedEntries(newSavedEntries);
        perfMonitor.reportMetrics(result.data.length);
      } else {
        throw new Error(result.error || 'Unknown error');
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load journal data');
      perfMonitor.reportMetrics(0, err instanceof Error ? err.message : 'Failed to load journal data');
    } finally {
      setIsLoading(false);
    }
  }, []); // perfMonitor uses refs internally and doesn't need to be a dependency

  // Save journal entry
  const saveJournalEntry = async (date: string, observations: any) => {
    try {
      setIsSaving(date);

      const response = await fetch('/api/journal', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          date,
          energy_level: observations.energy_level,
          rpe_score: observations.rpe_score,
          pain_percentage: observations.pain_percentage,
          notes: observations.notes
        })
      });

      const result = await response.json();

      if (result.success) {
        // Update local state to preserve user selections
        setJournalData(prev => prev.map(entry =>
          entry.date === date
            ? {
                ...entry,
                observations: {
                  ...entry.observations,
                  energy_level: observations.energy_level,
                  rpe_score: observations.rpe_score,
                  pain_percentage: observations.pain_percentage,
                  notes: observations.notes
                }
              }
            : entry
        ));

        // Mark this entry as saved
        setSavedEntries(prev => new Set(prev).add(date));

        // Refresh data to get any new autopsy analysis and auto-open modal
        setTimeout(async () => {
          try {
            const url = centerDate ? `/api/journal?date=${centerDate}` : '/api/journal';
            const response = await fetch(url);
            
            if (response.ok) {
              const result: JournalResponse = await response.json();
              if (result.success) {
                setJournalData(result.data);
                
                // Find the saved entry and open modal if autopsy is available
                const savedEntry = result.data.find(e => e.date === date);
                if (savedEntry?.ai_autopsy?.autopsy_analysis) {
                  openAutopsyModal(savedEntry);
                }
              }
            }
          } catch (err) {
            console.error('Failed to refresh data:', err);
          }
        }, 1500);

      } else {
        throw new Error(result.error || 'Failed to save journal entry');
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to save journal entry');

      // On error, refresh data to ensure consistency
      try {
        const refreshResponse = await fetch('/api/journal');
        const refreshData = await refreshResponse.json();
        if (refreshData.success) {
          setJournalData(refreshData.data);
        }
      } catch (refreshErr) {
        console.error('Failed to refresh data after error:', refreshErr);
      }
    } finally {
      setIsSaving(null);
    }
  };

  // Handle observation changes
  const handleObservationChange = (date: string, field: string, value: any) => {
    setJournalData(prev => prev.map(entry =>
      entry.date === date
        ? {
            ...entry,
            observations: {
              ...entry.observations,
              [field]: value
            }
          }
        : entry
    ));

    // Remove from saved entries when user makes changes
    setSavedEntries(prev => {
      const newSet = new Set(prev);
      newSet.delete(date);
      return newSet;
    });
  };

  // Handle save
  const handleSave = (date: string) => {
    const entry = journalData.find(e => e.date === date);
    if (entry) {
      saveJournalEntry(date, entry.observations);
    }
  };

  // NEW: Handle marking rest day
  const handleMarkRestDay = async (date: string) => {
    // Prompt user for notes about why they're skipping the workout
    const notes = window.prompt(
      `Why are you skipping today's prescribed workout?\n\nEnter your notes (this will be used to generate an autopsy and inform tomorrow's recommendation):`,
      'Decided to rest due to '
    );

    // If user cancels, don't proceed
    if (notes === null) {
      return;
    }

    // Require at least some input
    if (!notes.trim()) {
      alert('Please enter a reason for skipping the workout.');
      return;
    }

    try {
      setIsSaving(date);

      const response = await fetch('/api/journal', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          date: date,
          is_rest_day: true,
          notes: notes.trim()
        }),
      });

      if (!response.ok) {
        throw new Error('Failed to mark rest day');
      }

      const result = await response.json();
      console.log('Rest day marked successfully:', result);

      if (result.user_message) {
        alert(result.user_message);
      }

      // Mark as saved
      setSavedEntries(prev => new Set(prev).add(date));

      // Refresh journal data to get updated autopsy and tomorrow's recommendation
      try {
        await fetchJournalData(centerDate);
      } catch (refreshErr) {
        console.error('Failed to refresh data after rest day:', refreshErr);
      }

    } catch (error) {
      console.error('Error marking rest day:', error);
      alert(`Failed to mark rest day: ${error instanceof Error ? error.message : String(error)}`);
    } finally {
      setIsSaving(null);
    }
  };

  // Navigation functions
  const navigateToPrevious = () => {
    const prevDate = new Date(centerDate);
    prevDate.setDate(prevDate.getDate() - 7);
    fetchJournalData(prevDate.toISOString().split('T')[0]);
  };

  const navigateToNext = () => {
    const nextDate = new Date(centerDate);
    nextDate.setDate(nextDate.getDate() + 7);
    fetchJournalData(nextDate.toISOString().split('T')[0]);
  };

  const navigateToToday = () => {
    fetchJournalData(); // No date parameter = today
  };

  // Initial load
  useEffect(() => {
    fetchJournalData();
  }, [fetchJournalData]);

  // Format date for display
  const formatDate = (dateStr: string) => {
    const date = new Date(`${dateStr}T12:00:00Z`);
    return date.toLocaleDateString(undefined, {
      weekday: 'short',
      month: 'short',
      day: 'numeric'
    });
  };

  const formatFullDate = (dateStr: string) => {
    const date = new Date(`${dateStr}T12:00:00Z`);
    return date.toLocaleDateString(undefined, {
      weekday: 'long',
      year: 'numeric',
      month: 'long',
      day: 'numeric'
    });
  };

  if (isLoading) {
    return (
      <div className={styles.loading}>
        <h2>Loading Training Journal...</h2>
        <p>Fetching your training diary...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className={styles.error}>
        <h2>Error Loading Journal</h2>
        <p>{error}</p>
        <button onClick={() => fetchJournalData()} className={styles.retryButtonEnhanced}>Retry</button>
      </div>
    );
  }

  return (
    <div style={{ padding: '20px', fontFamily: 'Arial, sans-serif' }}>
      <div style={{
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        marginBottom: '20px'
      }}>
        <h1 style={{ margin: 0, color: '#1f2937' }}>Training Journal</h1>
        <div style={{ display: 'flex', gap: '10px', alignItems: 'center' }}>
          <button
            onClick={navigateToPrevious}
            className={`${styles.journalNavButton} ${styles.navButtonBlue}`}
          >
            ← Previous Week
          </button>
          <button
            onClick={navigateToToday}
            className={`${styles.journalNavButton} ${styles.navButtonGreen}`}
          >
            Today
          </button>
          <button
            onClick={navigateToNext}
            className={`${styles.journalNavButton} ${styles.navButtonBlue}`}
          >
            Next Week →
          </button>
        </div>
      </div>

      {error && (
        <div style={{
          padding: '12px',
          backgroundColor: '#fef2f2',
          border: '1px solid #fecaca',
          borderRadius: '4px',
          color: '#dc2626',
          marginBottom: '20px'
        }}>
          {error}
        </div>
      )}

      <div style={{ backgroundColor: 'white', borderRadius: '8px', padding: '20px' }}>
        <div style={{ overflowX: 'auto', overflowY: 'auto', maxHeight: '80vh' }}>
          <table style={{
            width: '100%',
            borderCollapse: 'collapse',
            fontSize: '0.9rem'
          }}>
            <thead style={{
              position: 'sticky',
              top: 0,
              backgroundColor: '#f8f9fa',
              zIndex: 10,
              boxShadow: '0 2px 4px rgba(0,0,0,0.1)'
            }}>
              <tr style={{ borderBottom: '2px solid #dee2e6' }}>
                <th style={{ padding: '12px 4px', textAlign: 'center', minWidth: '120px' }}>Date</th>
                <th style={{ padding: '12px 4px', textAlign: 'center', maxWidth: '500px', minWidth: '350px' }}>Today's Training Decision</th>
                <th style={{ padding: '12px 4px', textAlign: 'center', minWidth: '160px' }}>Actual Activity</th>
                <th style={{ padding: '12px 4px', textAlign: 'center', minWidth: '70px' }}>
                  <span 
                    style={{ cursor: 'help', borderBottom: '1px dotted #6b7280' }}
                    title="How did you feel going into the session? Fired up = 5, Barely got out of bed = 1"
                  >
                    Energy
                  </span>
                </th>
                <th style={{ padding: '12px 4px', textAlign: 'center', minWidth: '70px' }}>
                  <span 
                    style={{ cursor: 'help', borderBottom: '1px dotted #6b7280' }}
                    title="Rate of Perceived Exertion: How hard did the workout feel? 1 = Very Easy, 10 = Maximum Effort"
                  >
                    RPE
                  </span>
                </th>
                <th style={{ padding: '12px 4px', textAlign: 'center', minWidth: '70px' }}>
                  <span 
                    style={{ cursor: 'help', borderBottom: '1px dotted #6b7280' }}
                    title="The % of time during your activity that you were thinking about the pain"
                  >
                    Pain %
                  </span>
                </th>
                <th style={{ padding: '12px 4px', textAlign: 'center', maxWidth: '450px', minWidth: '350px' }}>Notes</th>
                <th style={{ padding: '12px 4px', textAlign: 'center', minWidth: '70px' }}>Alignment</th>
                <th style={{ padding: '12px 4px', textAlign: 'center', minWidth: '100px' }}>Actions</th>
              </tr>
            </thead>

            <tbody>
              {journalData.map((entry) => (
                <React.Fragment key={entry.date}>
                  {/* Next Incomplete Workout row - special rendering */}
                  {entry.is_next_incomplete ? (
                    <tr style={{
                      borderBottom: '2px solid #3b82f6',
                      backgroundColor: '#eff6ff'
                    }}>
                      {/* Date Column */}
                      <td style={{ padding: '16px 8px', verticalAlign: 'top' }}>
                        <div style={{ fontWeight: '600', color: '#3b82f6' }}>
                          {formatDate(entry.date)}
                          <div style={{ fontSize: '0.75rem', color: '#6b7280', marginTop: '4px' }}>
                            NEXT WORKOUT
                          </div>
                        </div>
                      </td>

                      {/* Next Workout Recommendation - spans multiple columns */}
                      <td colSpan={8} style={{ padding: '16px', verticalAlign: 'top' }}>
                        {entry.todays_decision && !entry.todays_decision.includes('No recommendation available') ? (
                          /* Has actual recommendation */
                          <div style={{
                            border: '2px solid #3b82f6',
                            borderRadius: '8px',
                            padding: '16px',
                            backgroundColor: 'white'
                          }}>
                            <div style={{
                              display: 'flex',
                              alignItems: 'center',
                              justifyContent: 'space-between',
                              marginBottom: '12px',
                              gap: '8px'
                            }}>
                              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                                <span style={{
                                  fontSize: '1.1rem',
                                  fontWeight: '600',
                                  color: '#1f2937'
                                }}>
                                  Training Decision for {formatDate(entry.date)}
                                </span>
                                <span style={{
                                  backgroundColor: '#10b981',
                                  color: 'white',
                                  padding: '4px 8px',
                                  borderRadius: '12px',
                                  fontSize: '0.75rem',
                                  fontWeight: '600'
                                }}>
                                  Autopsy-Informed
                                </span>
                              </div>
                              {/* Compact Mark as Rest Day button */}
                              <button
                                onClick={() => handleMarkRestDay(entry.date)}
                                disabled={isSaving === entry.date}
                                style={{
                                  backgroundColor: '#9333ea',
                                  color: 'white',
                                  padding: '6px 12px',
                                  borderRadius: '4px',
                                  border: 'none',
                                  fontSize: '0.8rem',
                                  fontWeight: '600',
                                  cursor: isSaving === entry.date ? 'not-allowed' : 'pointer',
                                  opacity: isSaving === entry.date ? 0.6 : 1,
                                  whiteSpace: 'nowrap'
                                }}
                              >
                                {isSaving === entry.date ? 'Marking...' : 'Mark as Rest Day'}
                              </button>
                            </div>
                            <div style={{
                              fontSize: '0.9rem',
                              lineHeight: '1.6',
                              color: '#374151',
                              textAlign: 'left',
                              maxHeight: '400px',
                              overflowY: 'auto'
                            }}>
                              {formatTrainingDecision(entry.todays_decision)}
                            </div>
                          </div>
                        ) : (
                          /* No recommendation yet - prompt to complete journal */
                          <div style={{
                            border: '2px dashed #d1d5db',
                            borderRadius: '8px',
                            padding: '24px',
                            backgroundColor: '#f9fafb',
                            textAlign: 'center'
                          }}>
                            <div style={{ fontSize: '2rem', marginBottom: '12px' }}>📝</div>
                            <div style={{
                              fontSize: '1rem',
                              fontWeight: '600',
                              color: '#374151',
                              marginBottom: '8px'
                            }}>
                              No Recommendation Available for {formatDate(entry.date)}
                            </div>
                            <div style={{
                              fontSize: '0.875rem',
                              color: '#6b7280',
                              lineHeight: '1.5'
                            }}>
                              Generate fresh recommendations on the Dashboard tab.
                            </div>
                          </div>
                        )}
                      </td>
                    </tr>
                  ) : (
                    /* Regular past/today row */
                    <tr style={{
                      borderBottom: '1px solid #e5e7eb',
                      backgroundColor: entry.is_today ? '#f0f9ff' : 'white'
                    }}>
                      {/* Date Column */}
                      <td style={{ padding: '12px 8px', verticalAlign: 'top' }}>
                        <div style={{ fontWeight: entry.is_today ? '600' : 'normal' }}>
                          {formatDate(entry.date)}
                        </div>
                      </td>

                      {/* Today's Training Decision */}
                      <td style={{ padding: '12px 8px', verticalAlign: 'top' }}>
                        <div style={{
                          display: 'flex',
                          flexDirection: 'column',
                          gap: '8px',
                          width: '350px',
                          minWidth: '350px',
                          maxWidth: '500px'
                        }}>
                          <div style={{
                            fontSize: '0.875rem',
                            lineHeight: '1.6',
                            maxHeight: '120px',
                            overflowY: 'auto',
                            color: '#374151',
                            textAlign: 'left'
                          }}>
                            {formatTrainingDecision(entry.todays_decision || 'No AI recommendation available')}
                          </div>
                        </div>
                      </td>


                      <td style={{ padding: '12px 4px', verticalAlign: 'top' }}>
                        <div style={{ fontSize: '0.875rem', lineHeight: '1.4', color: '#374151' }}>
                          {/* IMPROVED: Check for activity type properly */}
                          {!entry.activity_summary || !entry.activity_summary.type || entry.activity_summary.type === 'rest' ? (
                            <span style={{ fontStyle: 'italic', color: '#6b7280' }}>Rest Day</span>
                          ) : (
                          <>
                            <div><strong>{entry.activity_summary.type}</strong></div>
                            <div>
                              {entry.activity_summary.distance != null ? entry.activity_summary.distance.toFixed(1) : '0.0'} mi, {entry.activity_summary.elevation || 0} ft
                            </div>
                            <div>TRIMP: {entry.activity_summary.total_trimp || 0}</div>
                            <div style={{ fontSize: '0.75rem', color: '#6b7280' }}>
                              ({entry.activity_summary.workout_classification})
                            </div>

                            {/* REQUIRED: "View on Strava" link for each actual activity */}
                            {entry.activity_summary.activity_id && entry.activity_summary.activity_id > 0 && (
                              <div style={{ marginTop: '6px' }}>
                                <a
                                  href={`https://www.strava.com/activities/${entry.activity_summary.activity_id}`}
                                  target="_blank"
                                  rel="noopener noreferrer"
                                  style={{
                                    fontSize: '0.75rem',
                                    color: '#FC5200',
                                    textDecoration: 'none',
                                    fontWeight: 'bold',
                                    padding: '2px 6px',
                                    borderRadius: '3px',
                                    backgroundColor: '#fef3c7',
                                    border: '1px solid #FC5200',
                                    display: 'inline-block'
                                  }}
                                  onMouseEnter={(e) => {
                                    e.currentTarget.style.backgroundColor = '#FC5200';
                                    e.currentTarget.style.color = 'white';
                                  }}
                                  onMouseLeave={(e) => {
                                    e.currentTarget.style.backgroundColor = '#fef3c7';
                                    e.currentTarget.style.color = '#FC5200';
                                  }}
                                >
                                  View on Strava
                                </a>
                              </div>
                            )}
                          </>
                        )}
                      </div>
                    </td>

                    {/* Energy Level */}
                    <td style={{ padding: '12px 4px', textAlign: 'center', verticalAlign: 'top' }}>
                      <select
                        value={entry.observations.energy_level || ''}
                        onChange={(e) => handleObservationChange(
                          entry.date,
                          'energy_level',
                          e.target.value ? parseInt(e.target.value) : null
                        )}
                        style={{
                          width: '50px',
                          padding: '4px',
                          border: '1px solid #d1d5db',
                          borderRadius: '4px',
                          fontSize: '0.875rem'
                        }}
                      >
                        <option value="">-</option>
                        <option value="1">1</option>
                        <option value="2">2</option>
                        <option value="3">3</option>
                        <option value="4">4</option>
                        <option value="5">5</option>
                      </select>
                    </td>

                    {/* RPE Score */}
                    <td style={{ padding: '12px 4px', textAlign: 'center', verticalAlign: 'top' }}>
                      <select
                        value={entry.observations.rpe_score || ''}
                        onChange={(e) => handleObservationChange(
                          entry.date,
                          'rpe_score',
                          e.target.value ? parseInt(e.target.value) : null
                        )}
                        style={{
                          width: '50px',
                          padding: '4px',
                          border: '1px solid #d1d5db',
                          borderRadius: '4px',
                          fontSize: '0.875rem'
                        }}
                      >
                        <option value="">-</option>
                        {[1,2,3,4,5,6,7,8,9,10].map(n => (
                          <option key={n} value={n}>{n}</option>
                        ))}
                      </select>
                    </td>

                    {/* Pain Percentage */}
                    <td style={{ padding: '12px 4px', textAlign: 'center', verticalAlign: 'top' }}>
                      <select
                        value={entry.observations.pain_percentage ?? ''}
                        onChange={(e) => handleObservationChange(
                          entry.date,
                          'pain_percentage',
                          e.target.value ? parseInt(e.target.value) : null
                        )}
                        style={{
                          width: '60px',
                          padding: '4px',
                          border: '1px solid #d1d5db',
                          borderRadius: '4px',
                          fontSize: '0.875rem'
                        }}
                      >
                        <option value="">-</option>
                        <option value="0">0%</option>
                        <option value="20">20%</option>
                        <option value="40">40%</option>
                        <option value="60">60%</option>
                        <option value="80">80%</option>
                        <option value="100">100%</option>
                      </select>
                    </td>

                    {/* Notes */}
                    <td style={{ padding: '12px 8px', verticalAlign: 'top' }}>
                      <textarea
                        value={entry.observations.notes || ''}
                        onChange={(e) => handleObservationChange(entry.date, 'notes', e.target.value)}
                        placeholder="Training notes..."
                        style={{
                          height: '100px',
                          padding: '6px',
                          border: '1px solid #d1d5db',
                          borderRadius: '4px',
                          fontSize: '0.875rem',
                          resize: 'vertical',
                          width: '350px',
                          minWidth: '350px',
                          maxWidth: '450px'
                        }}
                      />
                    </td>

                    {/* Alignment Score Column */}
                    <td style={{ padding: '12px 8px', textAlign: 'center', verticalAlign: 'top' }}>
                      {entry.ai_autopsy.alignment_score ? (
                        <div style={{
                          padding: '4px 8px',
                          backgroundColor: getAlignmentScoreColor(entry.ai_autopsy.alignment_score),
                          color: 'white',
                          borderRadius: '12px',
                          fontSize: '0.8rem',
                          fontWeight: '600',
                          display: 'inline-block',
                          minWidth: '35px'
                        }}>
                          {entry.ai_autopsy.alignment_score}/10
                        </div>
                      ) : (
                        <span style={{ color: '#9ca3af', fontSize: '0.8rem' }}>-</span>
                      )}
                    </td>

                    {/* Actions - Progressive Multi-State Button */}
                    <td style={{ padding: '12px 8px', textAlign: 'center', verticalAlign: 'top' }}>
                      {(() => {
                        // Determine button state based on data and user actions
                        const hasUnsaved = hasUnsavedChanges(entry);
                        const isSaved = savedEntries.has(entry.date);
                        const hasAnalysis = entry.ai_autopsy.autopsy_analysis;
                        const isCurrentlySaving = isSaving === entry.date;
                        const isRestDay = !entry.activity_summary || entry.activity_summary.type === 'rest';
                        const isToday = entry.is_today;

                        // State 1: Unsaved changes - Show Save button (CHECK THIS FIRST)
                        if (hasUnsaved || (!isSaved && !isCurrentlySaving)) {
                          return (
                            <button
                              onClick={() => handleSave(entry.date)}
                              disabled={isCurrentlySaving}
                              className={`${styles.journalButton} ${isCurrentlySaving ? styles.buttonSaving : styles.buttonSave}`}
                            >
                              {isCurrentlySaving ? '💾 Saving...' : '💾 Save'}
                            </button>
                          );
                        }

                        // State 0: Today with no activity and NO observations, show "Mark as Rest Day" button
                        if (isToday && isRestDay && !isSaved && !hasUnsaved) {
                          return (
                            <button
                              onClick={() => handleMarkRestDay(entry.date)}
                              disabled={isCurrentlySaving}
                              className={`${styles.journalButton} ${isCurrentlySaving ? styles.buttonSaving : styles.buttonSave}`}
                              style={{
                                backgroundColor: '#9333ea',
                                color: 'white',
                                border: 'none'
                              }}
                            >
                              {isCurrentlySaving ? '🛌 Marking...' : '🛌 Mark as Rest Day'}
                            </button>
                          );
                        }

                        // State 2: Just saved but no analysis yet - Show temporary "Saved!" state
                        if (isSaved && !hasAnalysis) {
                          return (
                            <button
                              disabled
                              className={`${styles.journalButton} ${styles.buttonSaved}`}
                            >
                              ✅ Saved!
                            </button>
                          );
                        }

                        // State 3: Analysis available - Show Analysis button
                        if (hasAnalysis) {
                          return (
                            <button
                              onClick={() => openAutopsyModal(entry)}
                              className={`${styles.journalButton} ${styles.buttonAnalysis}`}
                            >
                              🔍 Analysis
                            </button>
                          );
                        }

                        // Fallback state - shouldn't happen
                        return (
                          <button
                            disabled
                            className={`${styles.journalButton} ${styles.buttonFallback}`}
                          >
                            --
                          </button>
                        );
                      })()}
                    </td>
                  </tr>
                  )}
                  {/* End of next-incomplete/regular row conditional */}

                </React.Fragment>
              ))}
            </tbody>
          </table>
        </div>

        {/* Summary section for all autopsies if any exist */}
        {journalData.some(entry => entry.ai_autopsy.autopsy_analysis) && (
          <div style={{
            marginTop: '2rem',
            padding: '16px',
            backgroundColor: '#f8f9fa',
            borderRadius: '8px',
            border: '1px solid #e9ecef'
          }}>
            <h3 style={{
              margin: '0 0 12px 0',
              color: '#374151',
              fontSize: '1.1rem'
            }}>
              📊 Training Analysis Summary
            </h3>
            <div style={{ fontSize: '0.9rem', color: '#6b7280' }}>
              {journalData.filter(entry => entry.ai_autopsy.autopsy_analysis).length} autopsy analysis(es) available.
              Click "🔍 View Analysis" buttons above to expand individual insights.
            </div>
          </div>
        )}

        {/* Strava Branding Compliance */}
        <div style={{
          display: 'flex',
          justifyContent: 'center',
          alignItems: 'center',
          marginTop: '20px',
          paddingTop: '15px',
          borderTop: '1px solid #e5e7eb',
          fontSize: '0.9rem'
        }}>
          <span style={{
            fontWeight: 'bold',
            color: '#FC5200',
            letterSpacing: '0.5px'
          }}>
            POWERED BY STRAVA
          </span>
        </div>
      </div>

      {/* Full-Screen Autopsy Modal */}
      {modalOpen && modalAutopsy && (
        <div style={{
          position: 'fixed',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          backgroundColor: 'rgba(0, 0, 0, 0.7)',
          zIndex: 1000,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          padding: '20px'
        }}
        onClick={closeAutopsyModal}
        >
          <div style={{
            backgroundColor: 'white',
            borderRadius: '12px',
            width: '95vw',
            maxHeight: '85vh',
            maxWidth: '1600px',
            display: 'flex',
            flexDirection: 'column',
            overflow: 'hidden',
            boxShadow: '0 25px 50px -12px rgba(0, 0, 0, 0.5)'
          }}
          onClick={(e) => e.stopPropagation()}
          >
            {/* Modal Header */}
            <div style={{
              padding: '24px 32px',
              borderBottom: '2px solid #e5e7eb',
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              backgroundColor: '#f8f9fa'
            }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
                <h2 style={{
                  margin: 0,
                  color: '#1f2937',
                  fontSize: '1.5rem',
                  fontWeight: '700'
                }}>
                  🔍 AI Training Analysis
                </h2>
                <div style={{
                  fontSize: '1.1rem',
                  color: '#6b7280',
                  fontWeight: '500'
                }}>
                  {formatFullDate(modalAutopsy.date)}
                </div>
                {modalAutopsy.ai_autopsy.alignment_score && (
                  <div style={{
                    padding: '8px 16px',
                    backgroundColor: getAlignmentScoreColor(modalAutopsy.ai_autopsy.alignment_score),
                    color: 'white',
                    borderRadius: '20px',
                    fontSize: '1rem',
                    fontWeight: '700'
                  }}>
                    Alignment: {modalAutopsy.ai_autopsy.alignment_score}/10
                  </div>
                )}
              </div>
              <button
                onClick={closeAutopsyModal}
                style={{
                  backgroundColor: '#ef4444',
                  color: 'white',
                  border: 'none',
                  borderRadius: '8px',
                  padding: '12px 24px',
                  fontSize: '1rem',
                  fontWeight: '600',
                  cursor: 'pointer',
                  transition: 'background-color 0.2s'
                }}
                onMouseEnter={(e) => e.currentTarget.style.backgroundColor = '#dc2626'}
                onMouseLeave={(e) => e.currentTarget.style.backgroundColor = '#ef4444'}
              >
                ✕ Close
              </button>
            </div>

            {/* Modal Body - Multi-Column Layout */}
            <div style={{
              flex: 1,
              padding: '32px',
              overflowY: 'auto',
              backgroundColor: '#ffffff'
            }}>
              {(() => {
                const text = modalAutopsy.ai_autopsy.autopsy_analysis || '';
                const paragraphs = text.split('\n\n').filter(p => p.trim());
                
                // Split paragraphs in half
                const midpoint = Math.ceil(paragraphs.length / 2);
                const column1 = paragraphs.slice(0, midpoint);
                const column2 = paragraphs.slice(midpoint);
                
                return (
                  <div style={{
                    display: 'flex',
                    gap: '40px',
                    position: 'relative',
                    alignItems: 'flex-start',
                    justifyContent: 'center',
                    maxWidth: '100%'
                  }}>
                    {/* Column 1 */}
                    <div style={{
                      flex: '0 1 auto',
                      maxWidth: '70ch',
                      fontSize: '0.95rem',
                      lineHeight: '1.6',
                      color: '#374151',
                      textAlign: 'left',
                      paddingRight: '20px'
                    }}>
                      {column1.map((para, idx) => {
                        // Detect section headings (all caps followed by colon)
                        const isSection = para.match(/^[A-Z\s&']+:/);
                        
                        if (isSection) {
                          return (
                            <div key={`col1-${idx}`} style={{
                              marginTop: idx > 0 ? '2em' : '0',
                              marginBottom: '1em',
                              paddingBottom: '0.5em',
                              borderBottom: '2px solid #3b82f6'
                            }}>
                              <h3 style={{
                                margin: 0,
                                fontSize: '1.05rem',
                                fontWeight: '700',
                                color: '#1f2937',
                                letterSpacing: '0.02em'
                              }}>
                                {para}
                              </h3>
                            </div>
                          );
                        }
                        
                        return (
                          <p key={`col1-${idx}`} style={{ 
                            margin: '0 0 1.2em 0',
                            fontWeight: '400'
                          }}>
                            {formatBoldText(para)}
                          </p>
                        );
                      })}
                    </div>
                    
                    {/* Column Divider */}
                    <div style={{
                      width: '2px',
                      backgroundColor: '#d1d5db',
                      margin: '0 20px'
                    }} />
                    
                    {/* Column 2 */}
                    <div style={{
                      flex: '0 1 auto',
                      maxWidth: '70ch',
                      fontSize: '0.95rem',
                      lineHeight: '1.6',
                      color: '#374151',
                      textAlign: 'left',
                      paddingLeft: '20px'
                    }}>
                      {column2.map((para, idx) => {
                        // Detect section headings (all caps followed by colon)
                        const isSection = para.match(/^[A-Z\s&']+:/);
                        
                        if (isSection) {
                          return (
                            <div key={`col2-${idx}`} style={{
                              marginTop: idx > 0 ? '2em' : '0',
                              marginBottom: '1em',
                              paddingBottom: '0.5em',
                              borderBottom: '2px solid #3b82f6'
                            }}>
                              <h3 style={{
                                margin: 0,
                                fontSize: '1.05rem',
                                fontWeight: '700',
                                color: '#1f2937',
                                letterSpacing: '0.02em'
                              }}>
                                {para}
                              </h3>
                            </div>
                          );
                        }
                        
                        return (
                          <p key={`col2-${idx}`} style={{ 
                            margin: '0 0 1.2em 0',
                            fontWeight: '400'
                          }}>
                            {formatBoldText(para)}
                          </p>
                        );
                      })}
                    </div>
                  </div>
                );
              })()}
            </div>

            {/* Modal Footer */}
            {modalAutopsy.ai_autopsy.generated_at && (
              <div style={{
                padding: '16px 32px',
                borderTop: '1px solid #e5e7eb',
                backgroundColor: '#f8f9fa',
                fontSize: '0.875rem',
                color: '#6b7280',
                fontStyle: 'italic',
                textAlign: 'right'
              }}>
                Generated: {new Date(modalAutopsy.ai_autopsy.generated_at).toLocaleString()}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default JournalPage;