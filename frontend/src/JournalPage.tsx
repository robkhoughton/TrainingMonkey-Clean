import React, { useState, useEffect, useCallback } from 'react';
import styles from './TrainingLoadDashboard.module.css'; // Reuse existing styles

interface JournalEntry {
  date: string;
  is_today: boolean;
  todays_decision: string;
  activity_summary: {
    type: string;
    distance: number;
    elevation: number;
    workout_classification: string;
    total_trimp: number;
  };
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

const JournalPage: React.FC = () => {
  const [journalData, setJournalData] = useState<JournalEntry[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [centerDate, setCenterDate] = useState<string>('');
  const [isSaving, setIsSaving] = useState<string | null>(null);
  const [savedEntries, setSavedEntries] = useState<Set<string>>(new Set()); // Track saved entries
  const [expandedAutopsies, setExpandedAutopsies] = useState<Set<string>>(new Set());

  // Toggle autopsy expansion for a specific date
  const toggleAutopsyExpansion = (date: string) => {
    setExpandedAutopsies(prev => {
      const newSet = new Set(prev);
      if (newSet.has(date)) {
        newSet.delete(date);
      } else {
        newSet.add(date);
      }
      return newSet;
    });
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

      const url = date ? `/api/journal?date=${date}` : '/api/journal';
      const response = await fetch(url);

      if (!response.ok) {
        throw new Error(`Failed to fetch journal data: ${response.status}`);
      }

      const result: JournalResponse = await response.json();

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
      } else {
        throw new Error(result.error || 'Unknown error');
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load journal data');
    } finally {
      setIsLoading(false);
    }
  }, []);

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

        // Refresh data to get any new autopsy analysis
        setTimeout(() => {
          fetchJournalData();
        }, 1000);

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
                <th style={{ padding: '12px 4px', textAlign: 'center', minWidth: '70px' }}>Energy</th>
                <th style={{ padding: '12px 4px', textAlign: 'center', minWidth: '70px' }}>RPE</th>
                <th style={{ padding: '12px 4px', textAlign: 'center', minWidth: '70px' }}>Pain %</th>
                <th style={{ padding: '12px 4px', textAlign: 'center', maxWidth: '450px', minWidth: '350px' }}>Notes</th>
                <th style={{ padding: '12px 4px', textAlign: 'center', minWidth: '70px' }}>Alignment</th>
                <th style={{ padding: '12px 4px', textAlign: 'center', minWidth: '100px' }}>Actions</th>
              </tr>
            </thead>

            <tbody>
              {journalData.map((entry) => (
                <React.Fragment key={entry.date}>
                  {/* Main data row */}
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
                        fontSize: '0.875rem',
                        lineHeight: '1.4',
                        maxHeight: '100px',
                        overflowY: 'auto',
                        color: '#374151',
                        textAlign: 'left',
                        width: '350px',
                        minWidth: '350px',
                        maxWidth: '500px'
                      }}>
                        {entry.todays_decision || 'No AI recommendation available'}
                      </div>
                    </td>


                    <td style={{ padding: '12px 4px', verticalAlign: 'top' }}>
                      <div style={{ fontSize: '0.875rem', lineHeight: '1.4', color: '#374151' }}>
                        {/* IMPROVED: Check for activity type properly */}
                        {!entry.activity_summary.type || entry.activity_summary.type === 'rest' ? (
                          <span style={{ fontStyle: 'italic', color: '#6b7280' }}>Rest Day</span>
                        ) : (
                          <>
                            <div><strong>{entry.activity_summary.type}</strong></div>
                            <div>{entry.activity_summary.distance.toFixed(1)} mi, {entry.activity_summary.elevation} ft</div>
                            <div>TRIMP: {entry.activity_summary.total_trimp}</div>
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
                        const isAnalysisExpanded = expandedAutopsies.has(entry.date);

                        // State 1: Unsaved changes - Show Save button
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
                              onClick={() => toggleAutopsyExpansion(entry.date)}
                              className={`${styles.journalButton} ${isAnalysisExpanded ? styles.buttonAnalysisExpanded : styles.buttonAnalysis}`}
                            >
                              {isAnalysisExpanded ? '📖 Hide' : '🔍 Analysis'}
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

                  {/* Expanded Autopsy Row */}
                  {entry.ai_autopsy.autopsy_analysis && expandedAutopsies.has(entry.date) && (
                    <tr style={{ backgroundColor: '#f8f9fa', borderBottom: '2px solid #dee2e6' }}>
                      <td colSpan={9} style={{ textAlign: 'right', padding: '16px' }}>
                        <div style={{
                          border: '1px solid #d1d5db',
                          borderRadius: '8px',
                          padding: '16px',
                          backgroundColor: 'white',
                          maxWidth: '800px', // Limit width as requested
                          margin: '0' // Left justify the content
                        }}>
                          <div style={{
                            display: 'flex',
                            justifyContent: 'space-between',
                            alignItems: 'center',
                            marginBottom: '12px'
                          }}>
                            <h4 style={{
                              margin: 0,
                              color: '#1f2937',
                              fontSize: '1rem',
                              fontWeight: '600'
                            }}>
                              🔍 AI Training Analysis - {formatFullDate(entry.date)}
                            </h4>
                            {entry.ai_autopsy.alignment_score && (
                              <div style={{
                                padding: '4px 12px',
                                backgroundColor: getAlignmentScoreColor(entry.ai_autopsy.alignment_score),
                                color: 'white',
                                borderRadius: '16px',
                                fontSize: '0.8rem',
                                fontWeight: '600'
                              }}>
                                Alignment: {entry.ai_autopsy.alignment_score}/10
                              </div>
                            )}
                          </div>

                          <div style={{
                            whiteSpace: 'pre-line',
                            fontSize: '0.9rem',
                            lineHeight: '1.6',
                            color: '#4b5563',
                            marginBottom: '12px',
                            textAlign: 'left'
                          }}>
                            {entry.ai_autopsy.autopsy_analysis}
                          </div>

                          {entry.ai_autopsy.generated_at && (
                            <div style={{
                              fontSize: '0.75rem',
                              color: '#6b7280',
                              fontStyle: 'italic',
                              textAlign: 'right'
                            }}>
                              Generated: {new Date(entry.ai_autopsy.generated_at).toLocaleString()}
                            </div>
                          )}
                        </div>
                      </td>
                    </tr>
                  )}
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
    </div>
  );
};

export default JournalPage;