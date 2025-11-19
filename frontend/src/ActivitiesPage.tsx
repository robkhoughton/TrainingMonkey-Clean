import React, { useState, useEffect, useCallback } from 'react';
import styles from './TrainingLoadDashboard.module.css'; // Reuse existing styles
import { usePagePerformanceMonitoring, useComponentPerformanceMonitoring } from './usePerformanceMonitoring';

interface Activity {
  activity_id: number;
  date: string;
  start_time?: string | null; // Time of activity start in 'HH:MM:SS' format
  name: string;
  type: string;
  sport_type?: string;
  device_name?: string | null; // Device used to record activity (Garmin branding compliance)
  distance_miles: number;
  elevation_gain_feet: number | null;
  total_load_miles: number;
  trimp: number;
  duration_minutes: number;
  has_missing_elevation: boolean;
  user_edited_elevation?: boolean; // Track if user has edited this value
  strength_rpe?: number | null;
  strength_equivalent_miles?: number | null;
}

interface PaginationInfo {
  current_page: number;
  per_page: number;
  total_items: number;
  total_pages: number;
  has_next: boolean;
  has_prev: boolean;
}

const ActivitiesPage: React.FC = () => {
  // Performance monitoring
  usePagePerformanceMonitoring('activities');
  const perfMonitor = useComponentPerformanceMonitoring('ActivitiesPage');

  const [activities, setActivities] = useState<Activity[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [days, setDays] = useState('30');
  const [pagination, setPagination] = useState<PaginationInfo | null>(null);
  const [currentPage, setCurrentPage] = useState(1);
  const [editingElevation, setEditingElevation] = useState<number | null>(null);
  const [elevationValue, setElevationValue] = useState('');
  const [editingRPE, setEditingRPE] = useState<number | null>(null);
  const [rpeValue, setRPEValue] = useState('');
  const [sortField, setSortField] = useState<keyof Activity>('date');
  const [sortDirection, setSortDirection] = useState<'asc' | 'desc'>('desc'); // FIXED: Default to reverse chronological

  // UPDATED: Use same data source as dashboard charts
  const fetchActivities = useCallback(async (page: number = 1) => {
    try {
      setIsLoading(true);
      setError(null);

      perfMonitor.trackFetchStart();
      // Use the dedicated activities management endpoint that returns individual activities
      const response = await fetch(`/api/activities-management?days=${days}&page=${page}&t=${Date.now()}`);

      if (!response.ok) {
        throw new Error(`Failed to fetch activities: ${response.status}`);
      }

      const result = await response.json();
      perfMonitor.trackFetchEnd();

      if (result.success) {
        // The activities-management endpoint already returns individual activities with proper pagination
        const activitiesData = result.data.map((item: any) => ({
          activity_id: item.activity_id,
          date: item.date,
          start_time: item.start_time || null, // Map the start time field
          name: item.name,
          type: item.type,
          sport_type: item.sport_type,
          device_name: item.device_name || null, // Device name for Garmin branding
          distance_miles: item.distance_miles || 0,
          elevation_gain_feet: item.elevation_gain_feet,
          total_load_miles: item.total_load_miles || 0,
          trimp: item.trimp || 0,
          duration_minutes: item.duration_minutes || 0,
          has_missing_elevation: (
            item.elevation_gain_feet === null ||
            item.elevation_gain_feet === 0
          ) && item.activity_id > 0, // Only flag missing elevation for real activities
          user_edited_elevation: false, // Initialize as false, will be updated after edits
          strength_rpe: item.strength_rpe,
          strength_equivalent_miles: item.strength_equivalent_miles
        }));

        setActivities(activitiesData);
        setPagination(result.pagination);
        setCurrentPage(page);
        perfMonitor.reportMetrics(activitiesData.length);
      } else {
        throw new Error(result.error || 'Unknown error');
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load activities');
      perfMonitor.reportMetrics(0, err instanceof Error ? err.message : 'Failed to load activities');
    } finally {
      setIsLoading(false);
    }
  }, [days]);

  const handleSort = (field: keyof Activity) => {
    const newDirection = sortField === field && sortDirection === 'desc' ? 'asc' : 'desc';
    setSortField(field);
    setSortDirection(newDirection);

    const sorted = [...activities].sort((a, b) => {
      let aVal = a[field];
      let bVal = b[field];

      // Handle null values
      if (aVal === null) aVal = 0;
      if (bVal === null) bVal = 0;

      if (typeof aVal === 'string' && typeof bVal === 'string') {
        return newDirection === 'asc' ? aVal.localeCompare(bVal) : bVal.localeCompare(aVal);
      }

      if (typeof aVal === 'number' && typeof bVal === 'number') {
        return newDirection === 'asc' ? aVal - bVal : bVal - aVal;
      }

      return 0;
    });

    setActivities(sorted);
  };

  const handleElevationEdit = (activityId: number, currentElevation: number | null) => {
    setEditingElevation(activityId);
    setElevationValue(currentElevation?.toString() || '');
  };

  const handleElevationSave = async (activityId: number) => {
    try {
      const elevation = parseFloat(elevationValue);

      if (isNaN(elevation) || elevation < 0 || elevation > 15000) {
        alert('Please enter a valid elevation between 0 and 15,000 feet');
        return;
      }

      const response = await fetch('/api/activities-management/update-elevation', {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          activity_id: activityId,
          elevation_gain_feet: elevation
        })
      });

      const result = await response.json();

      if (result.success) {
        // FIX: Use the values returned from backend (don't recalculate with wrong factor!)
        setActivities(prev => prev.map(activity =>
          activity.activity_id === activityId
            ? {
                ...activity,
                elevation_gain_feet: result.updated_values.elevation_gain_feet,
                total_load_miles: result.updated_values.total_load_miles,
                has_missing_elevation: false,
                user_edited_elevation: true, // Mark as user edited
              }
            : activity
        ));

        setEditingElevation(null);
        setElevationValue('');
      } else {
        alert(result.error || 'Failed to update elevation');
      }
    } catch (err) {
      alert('Error saving elevation data');
    }
  };

  const handleElevationCancel = () => {
    setEditingElevation(null);
    setElevationValue('');
  };

  const handleRPEEdit = (activityId: number, currentRPE: number | null) => {
    setEditingRPE(activityId);
    setRPEValue(currentRPE?.toString() || '6'); // Default to 6 (moderate)
  };

  const handleRPESave = async (activityId: number) => {
    try {
      const rpe = parseInt(rpeValue);

      if (isNaN(rpe) || rpe < 1 || rpe > 10) {
        alert('Please enter a valid RPE between 1 and 10');
        return;
      }

      const response = await fetch('/api/activities-management/update-rpe', {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          activity_id: activityId,
          rpe_score: rpe
        })
      });

      const result = await response.json();

      if (result.success) {
        // Update activity with new RPE and recalculated load
        setActivities(prev => prev.map(activity =>
          activity.activity_id === activityId
            ? {
                ...activity,
                strength_rpe: result.updated_values.strength_rpe,
                total_load_miles: result.updated_values.total_load_miles,
                strength_equivalent_miles: result.updated_values.strength_equivalent_miles
              }
            : activity
        ));

        setEditingRPE(null);
        setRPEValue('');
      } else {
        alert(result.error || 'Failed to update RPE');
      }
    } catch (err) {
      alert('Error saving RPE data');
    }
  };

  const handleRPECancel = () => {
    setEditingRPE(null);
    setRPEValue('');
  };

  useEffect(() => {
    fetchActivities(1);
  }, [days, fetchActivities]);

  // IMPROVEMENT 4: Enhanced date formatting with day of week
  const formatDateWithDayOfWeek = (dateStr: string) => {
    const date = new Date(dateStr + 'T12:00:00Z');
    return date.toLocaleDateString(undefined, {
      weekday: 'short', // Mon, Tue, Wed, etc.
      month: 'short',   // Jan, Feb, Mar, etc.
      day: 'numeric',   // 1, 2, 3, etc.
      year: 'numeric'   // 2025
    });
  };

  // IMPROVEMENT 2: Format duration in hours and minutes (always h:mm format)
  const formatDuration = (minutes: number) => {
    if (!minutes || minutes === 0) return '0:00';

    const hours = Math.floor(minutes / 60);
    const remainingMinutes = Math.round(minutes % 60);

    return `${hours}:${remainingMinutes.toString().padStart(2, '0')}`;
  };

  // Format start time from 'HH:MM:SS' to '12:34 PM' format
  const formatStartTime = (timeStr: string | null | undefined) => {
    if (!timeStr) return null;
    
    try {
      const [hours, minutes] = timeStr.split(':').map(Number);
      const period = hours >= 12 ? 'PM' : 'AM';
      const displayHours = hours % 12 || 12; // Convert 0 to 12 for midnight
      return `${displayHours}:${minutes.toString().padStart(2, '0')} ${period}`;
    } catch {
      return null;
    }
  };

  if (isLoading) {
    return (
      <div className={styles.loading}>
        <h2>Loading Activities...</h2>
        <p>Fetching your training data...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className={styles.error}>
        <h2>Error Loading Activities</h2>
        <p>{error}</p>
        <button onClick={() => fetchActivities(currentPage)} className={styles.retryButton}>
          Retry
        </button>
      </div>
    );
  }

  return (
    <div className={styles.container}>
      {/* Header */}
      <div className={styles.header}>
        <h1 className={styles.title}>
          Training Activities
          {pagination && (
            <span style={{ fontSize: '1rem', fontWeight: 'normal', color: '#6b7280', marginLeft: '0.5rem' }}>
              ({pagination.total_items} total)
            </span>
          )}
        </h1>

        <div className={styles.dateSelector}>
          <label className={styles.dateSelectorLabel}>Time Period:</label>
          <select
            value={days}
            onChange={(e) => setDays(e.target.value)}
            className={styles.dateSelectorInput}
          >
            <option value="10">Last 10 Days</option>
            <option value="30">Last 30 Days</option>
            <option value="60">Last 60 Days</option>
          </select>
        </div>
      </div>

      {/* Activities Table */}
      <div className={styles.chartContainer}>

        <div style={{
          overflowX: 'auto',
          overflowY: 'auto',
          maxHeight: '70vh',
          border: '1px solid #e5e7eb',
          borderRadius: '0.5rem'
        }}>
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
                {[
                  { key: 'date', label: 'Date' },
                  { key: 'type', label: 'Type' },
                  { key: 'name', label: 'Activity' },
                  { key: 'duration_minutes', label: 'Duration' }, // IMPROVEMENT 2: Added duration column
                  { key: 'distance_miles', label: 'Miles' },
                  { key: 'elevation_gain_feet', label: 'Elevation (ft)' },
                  { key: 'total_load_miles', label: 'Total Load' },
                  { key: 'trimp', label: 'TRIMP' },
                  { key: 'strength_rpe', label: 'RPE (Strength)' }
                ].map((col) => (
                  <th
                    key={col.key}
                    style={{
                      padding: '12px 8px',
                      textAlign: 'center', // HEADERS REMAIN CENTERED
                      fontWeight: '600',
                      color: '#374151',
                      cursor: 'pointer',
                      userSelect: 'none'
                    }}
                    onClick={() => handleSort(col.key as keyof Activity)}
                  >
                    {col.label}
                    {sortField === col.key && (
                      <span style={{ marginLeft: '4px' }}>
                        {sortDirection === 'asc' ? '↑' : '↓'}
                      </span>
                    )}
                  </th>
                ))}
              </tr>
            </thead>

            <tbody>
              {activities.map((activity) => (
                <tr
                  key={`${activity.date}-${activity.activity_id}`}
                  style={{
                    borderBottom: '1px solid #e5e7eb',
                    backgroundColor: activity.has_missing_elevation ? '#fef3c7' :
                                   activity.activity_id <= 0 ? '#f3f4f6' : 'white' // Rest days get gray background
                  }}
                >
                  {/* DATE - LEFT JUSTIFIED WITH DAY OF WEEK AND START TIME */}
                  <td style={{ padding: '10px 8px', textAlign: 'left' }}>
                    <div>{formatDateWithDayOfWeek(activity.date)}</div>
                    {formatStartTime(activity.start_time) && (
                      <div style={{ fontSize: '0.8rem', color: '#6b7280', marginTop: '2px' }}>
                        {formatStartTime(activity.start_time)}
                      </div>
                    )}
                  </td>

                  {/* TYPE - LEFT JUSTIFIED (text) - IMPROVEMENT 3: Shows specific types */}
                  <td style={{ padding: '10px 8px', textAlign: 'left' }}>
                    <span style={{
                      fontSize: '0.85rem',
                      fontWeight: activity.type.includes('Trail') ? '600' : 'normal',
                      color: activity.type.includes('Trail') ? '#059669' :
                             activity.type.includes('Treadmill') ? '#7c3aed' :
                             activity.type.includes('Track') ? '#dc2626' :
                             activity.type.includes('Race') ? '#f59e0b' : '#374151'
                    }}>
                      {activity.type}
                    </span>
                  </td>

                  {/* NAME - LEFT JUSTIFIED (text) WITH STRAVA LINK AND DEVICE ATTRIBUTION */}
                  <td style={{ padding: '10px 8px', textAlign: 'left', maxWidth: '200px' }}>
                    <div>
                      <div style={{
                        overflow: 'hidden',
                        textOverflow: 'ellipsis',
                        whiteSpace: 'nowrap'
                      }}>
                        {activity.name}
                      </div>

                      {/* GARMIN DEVICE ATTRIBUTION - Required per Garmin branding guidelines (Nov 1, 2025) */}
                      {activity.device_name && activity.device_name.toLowerCase().includes('garmin') && (
                        <div style={{ 
                          marginTop: '2px',
                          fontSize: '0.7rem',
                          color: '#6b7280',
                          fontStyle: 'italic'
                        }}>
                          {activity.device_name}
                        </div>
                      )}

                      {/* REQUIRED: "View on Strava" link for real activities */}
                      {activity.activity_id > 0 && (
                        <div style={{ marginTop: '4px' }}>
                          <a
                            href={`https://www.strava.com/activities/${activity.activity_id}`}
                            target="_blank"
                            rel="noopener noreferrer"
                            style={{
                              fontSize: '0.75rem',
                              color: '#FC5200',
                              textDecoration: 'none',
                              fontWeight: 'bold'
                            }}
                            onMouseEnter={(e) => {
                              e.currentTarget.style.textDecoration = 'underline';
                            }}
                            onMouseLeave={(e) => {
                              e.currentTarget.style.textDecoration = 'none';
                            }}
                          >
                            View on Strava
                          </a>
                        </div>
                      )}
                    </div>
                  </td>

                  {/* DURATION - RIGHT JUSTIFIED - IMPROVEMENT 2: New duration column */}
                  <td style={{ padding: '10px 8px', textAlign: 'right' }}>
                    {formatDuration(activity.duration_minutes)}
                  </td>

                  {/* DISTANCE - RIGHT JUSTIFIED (number) */}
                  <td style={{ padding: '10px 8px', textAlign: 'right' }}>
                    {activity.distance_miles?.toFixed(2) || '0.00'}
                  </td>

                  {/* ELEVATION - RIGHT JUSTIFIED (number) with edit functionality */}
                  <td style={{ padding: '10px 8px', textAlign: 'right' }}>
                    {editingElevation === activity.activity_id ? (
                      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'flex-end', gap: '4px' }}>
                        <input
                          type="number"
                          value={elevationValue}
                          onChange={(e) => setElevationValue(e.target.value)}
                          style={{
                            width: '80px',
                            padding: '4px',
                            border: '1px solid #d1d5db',
                            borderRadius: '4px',
                            fontSize: '0.85rem',
                            textAlign: 'right'
                          }}
                          min="0"
                          max="15000"
                          placeholder="0"
                        />
                        <button
                          onClick={() => handleElevationSave(activity.activity_id)}
                          style={{
                            padding: '4px 8px',
                            backgroundColor: '#10b981',
                            color: 'white',
                            border: 'none',
                            borderRadius: '4px',
                            fontSize: '0.75rem',
                            cursor: 'pointer'
                          }}
                        >
                          ✓
                        </button>
                        <button
                          onClick={handleElevationCancel}
                          style={{
                            padding: '4px 8px',
                            backgroundColor: '#ef4444',
                            color: 'white',
                            border: 'none',
                            borderRadius: '4px',
                            fontSize: '0.75rem',
                            cursor: 'pointer'
                          }}
                        >
                          ✕
                        </button>
                      </div>
                    ) : (
                      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'flex-end', gap: '8px' }}>
                        <span>
                          {activity.elevation_gain_feet?.toFixed(0) || '0'}
                          {/* ASTERISK for user edits */}
                          {activity.user_edited_elevation && (
                            <span style={{ color: '#f59e0b', marginLeft: '2px' }}>*</span>
                          )}
                        </span>
                        {activity.has_missing_elevation && (
                          <button
                            onClick={() => handleElevationEdit(activity.activity_id, activity.elevation_gain_feet)}
                            style={{
                              padding: '2px 6px',
                              backgroundColor: '#f59e0b',
                              color: 'white',
                              border: 'none',
                              borderRadius: '4px',
                              fontSize: '0.75rem',
                              cursor: 'pointer'
                            }}
                          >
                            Edit
                          </button>
                        )}
                      </div>
                    )}
                  </td>

                  {/* TOTAL LOAD - RIGHT JUSTIFIED (number) */}
                  <td style={{ padding: '10px 8px', textAlign: 'right' }}>
                    {activity.total_load_miles?.toFixed(2) || '0.00'}
                  </td>

                  {/* TRIMP - RIGHT JUSTIFIED (number) */}
                  <td style={{ padding: '10px 8px', textAlign: 'right' }}>
                    {activity.trimp?.toFixed(1) || '0.0'}
                  </td>

                  {/* RPE - RIGHT JUSTIFIED (Strength activities only) */}
                  <td style={{ padding: '10px 8px', textAlign: 'right' }}>
                    {activity.sport_type === 'strength' ? (
                      editingRPE === activity.activity_id ? (
                        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'flex-end', gap: '4px' }}>
                          <input
                            type="number"
                            value={rpeValue}
                            onChange={(e) => setRPEValue(e.target.value)}
                            style={{
                              width: '60px',
                              padding: '4px',
                              border: '1px solid #d1d5db',
                              borderRadius: '4px',
                              fontSize: '0.85rem',
                              textAlign: 'right'
                            }}
                            min="1"
                            max="10"
                            placeholder="6"
                          />
                          <button
                            onClick={() => handleRPESave(activity.activity_id)}
                            style={{
                              padding: '4px 8px',
                              backgroundColor: '#10b981',
                              color: 'white',
                              border: 'none',
                              borderRadius: '4px',
                              fontSize: '0.75rem',
                              cursor: 'pointer'
                            }}
                          >
                            ✓
                          </button>
                          <button
                            onClick={handleRPECancel}
                            style={{
                              padding: '4px 8px',
                              backgroundColor: '#ef4444',
                              color: 'white',
                              border: 'none',
                              borderRadius: '4px',
                              fontSize: '0.75rem',
                              cursor: 'pointer'
                            }}
                          >
                            ✕
                          </button>
                        </div>
                      ) : (
                        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'flex-end', gap: '8px' }}>
                          <span style={{
                            fontWeight: activity.strength_rpe ? '600' : 'normal',
                            color: activity.strength_rpe ? '#059669' : '#9ca3af'
                          }}>
                            {activity.strength_rpe || '-'}
                          </span>
                          <button
                            onClick={() => handleRPEEdit(activity.activity_id, activity.strength_rpe)}
                            style={{
                              padding: '2px 6px',
                              backgroundColor: activity.strength_rpe ? '#3b82f6' : '#f59e0b',
                              color: 'white',
                              border: 'none',
                              borderRadius: '4px',
                              fontSize: '0.75rem',
                              cursor: 'pointer'
                            }}
                            title={activity.strength_rpe ? 'Edit RPE' : 'Set RPE for load calculation'}
                          >
                            {activity.strength_rpe ? 'Edit' : 'Set RPE'}
                          </button>
                        </div>
                      )
                    ) : (
                      <span style={{ color: '#9ca3af' }}>-</span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {/* Pagination */}
        {pagination && pagination.total_pages > 1 && (
          <div style={{
            display: 'flex',
            justifyContent: 'center',
            alignItems: 'center',
            gap: '10px',
            marginTop: '20px',
            padding: '10px'
          }}>
            <button
              onClick={() => fetchActivities(currentPage - 1)}
              disabled={!pagination.has_prev}
              style={{
                padding: '8px 12px',
                backgroundColor: pagination.has_prev ? '#3b82f6' : '#9ca3af',
                color: 'white',
                border: 'none',
                borderRadius: '4px',
                cursor: pagination.has_prev ? 'pointer' : 'not-allowed'
              }}
            >
              Previous
            </button>

            <span style={{ color: '#6b7280' }}>
              Page {pagination.current_page} of {pagination.total_pages}
            </span>

            <button
              onClick={() => fetchActivities(currentPage + 1)}
              disabled={!pagination.has_next}
              style={{
                padding: '8px 12px',
                backgroundColor: pagination.has_next ? '#3b82f6' : '#9ca3af',
                color: 'white',
                border: 'none',
                borderRadius: '4px',
                cursor: pagination.has_next ? 'pointer' : 'not-allowed'
              }}
            >
              Next
            </button>
          </div>
        )}

        {/* STRAVA BRAND COMPLIANT FOOTER - REPLACE LINES 384-402 */}
        <div style={{
          display: 'flex',
          justifyContent: 'center',
          alignItems: 'center',
          gap: '0.5rem',
          marginTop: '20px',
          paddingTop: '15px',
          borderTop: '1px solid #e5e7eb',
          fontSize: '0.9rem'
        }}>
          {/* OFFICIAL STRAVA LOGO */}
          <img
            src="/static/powered-by-strava-orange.svg"
            alt="Powered by Strava"
            style={{
              height: '18px',
              width: 'auto',
              display: 'block'
            }}
            onError={(e) => {
              // Fallback to compliant text if logo fails to load
              const target = e.currentTarget;
              target.style.display = 'none';

              // Create fallback text element
              const fallbackSpan = document.createElement('span');
              fallbackSpan.style.fontWeight = 'bold';
              fallbackSpan.style.color = '#FC5200';
              fallbackSpan.style.letterSpacing = '0.5px';
              fallbackSpan.style.fontSize = '0.9rem';
              fallbackSpan.textContent = 'POWERED BY STRAVA';

              // Insert before the current image
              target.parentNode?.insertBefore(fallbackSpan, target);
            }}
          />

          {/* User edit notation */}
          <span style={{
            fontSize: '0.8rem',
            color: '#6b7280'
          }}>
            • * denotes manual entry by user
          </span>
        </div>
      </div>
    </div>
  );
};

export default ActivitiesPage;