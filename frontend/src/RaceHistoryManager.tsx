import React, { useState } from 'react';
import styles from './TrainingLoadDashboard.module.css';

// ============================================================================
// INTERFACES
// ============================================================================

interface RaceHistory {
  id: number;
  race_date: string;
  race_name: string;
  distance_miles: number;
  finish_time_minutes: number;
}

interface ExtractedRace {
  race_name: string;
  distance_miles: number;
  race_date: string;
  finish_time_minutes: number;
  error?: string;
}

interface RaceHistoryManagerProps {
  history: RaceHistory[];
  onHistoryChange: () => void;
}

// ============================================================================
// COMPONENT
// ============================================================================

const RaceHistoryManager: React.FC<RaceHistoryManagerProps> = ({ history, onHistoryChange }) => {
  const [showManualForm, setShowManualForm] = useState(false);
  const [showScreenshotUpload, setShowScreenshotUpload] = useState(false);
  const [editingRace, setEditingRace] = useState<RaceHistory | null>(null);
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Manual form state
  const [formData, setFormData] = useState({
    race_name: '',
    distance_miles: '',
    race_date: '',
    finish_time_minutes: ''
  });

  // Screenshot upload state
  const [isUploading, setIsUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [extractedRaces, setExtractedRaces] = useState<ExtractedRace[]>([]);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);

  // ============================================================================
  // MANUAL RACE ENTRY HANDLERS
  // ============================================================================

  const handleAddManual = () => {
    setEditingRace(null);
    setFormData({
      race_name: '',
      distance_miles: '',
      race_date: '',
      finish_time_minutes: ''
    });
    setShowManualForm(true);
    setError(null);
  };

  const handleEdit = (race: RaceHistory) => {
    setEditingRace(race);
    setFormData({
      race_name: race.race_name,
      distance_miles: race.distance_miles.toString(),
      race_date: race.race_date,
      finish_time_minutes: race.finish_time_minutes.toString()
    });
    setShowManualForm(true);
    setError(null);
  };

  const handleCancelManual = () => {
    setShowManualForm(false);
    setEditingRace(null);
    setError(null);
  };

  const handleManualSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSaving(true);
    setError(null);

    try {
      const payload = {
        race_name: formData.race_name.trim(),
        distance_miles: parseFloat(formData.distance_miles),
        race_date: formData.race_date,
        finish_time_minutes: parseInt(formData.finish_time_minutes, 10)
      };

      const url = editingRace
        ? `/api/coach/race-history/${editingRace.id}`
        : '/api/coach/race-history';

      const method = editingRace ? 'PUT' : 'POST';

      const response = await fetch(url, {
        method,
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || 'Failed to save race');
      }

      setShowManualForm(false);
      setEditingRace(null);
      onHistoryChange();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to save race');
    } finally {
      setIsSaving(false);
    }
  };

  const handleDelete = async (raceId: number) => {
    if (!window.confirm('Are you sure you want to delete this race result?')) {
      return;
    }

    try {
      const response = await fetch(`/api/coach/race-history/${raceId}`, {
        method: 'DELETE'
      });

      if (!response.ok) {
        throw new Error('Failed to delete race');
      }

      onHistoryChange();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to delete race');
    }
  };

  // ============================================================================
  // SCREENSHOT UPLOAD HANDLERS
  // ============================================================================

  const handleScreenshotClick = () => {
    setShowScreenshotUpload(true);
    setExtractedRaces([]);
    setSelectedFile(null);
    setError(null);
  };

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      setSelectedFile(file);
      setError(null);
    }
  };

  const handleScreenshotUpload = async () => {
    if (!selectedFile) {
      setError('Please select a screenshot file');
      return;
    }

    setIsUploading(true);
    setUploadProgress(0);
    setError(null);

    try {
      const formData = new FormData();
      formData.append('screenshot', selectedFile);

      // Simulate progress (since fetch doesn't provide upload progress easily)
      const progressInterval = setInterval(() => {
        setUploadProgress(prev => Math.min(prev + 10, 90));
      }, 200);

      const response = await fetch('/api/coach/race-history/screenshot', {
        method: 'POST',
        body: formData
      });

      clearInterval(progressInterval);
      setUploadProgress(100);

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || 'Failed to parse screenshot');
      }

      const data = await response.json();
      setExtractedRaces(data.races || []);

      // Show success message if races extracted
      if (data.races && data.races.length > 0) {
        setError(null);
      } else {
        setError('No races found in screenshot. Please check the image and try again.');
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to upload screenshot');
      setExtractedRaces([]);
    } finally {
      setIsUploading(false);
      setUploadProgress(0);
    }
  };

  const handleExtractedRaceEdit = (index: number, field: string, value: string) => {
    const updated = [...extractedRaces];
    updated[index] = { ...updated[index], [field]: value };
    setExtractedRaces(updated);
  };

  const handleBulkSave = async () => {
    if (extractedRaces.length === 0) {
      return;
    }

    setIsSaving(true);
    setError(null);

    try {
      const response = await fetch('/api/coach/race-history/bulk', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ races: extractedRaces })
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || 'Failed to save races');
      }

      const data = await response.json();

      // Show results
      alert(`Successfully saved ${data.saved} race(s). ${data.failed} failed.`);

      // Refresh and close
      setShowScreenshotUpload(false);
      setExtractedRaces([]);
      setSelectedFile(null);
      onHistoryChange();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to save races');
    } finally {
      setIsSaving(false);
    }
  };

  const handleCancelScreenshot = () => {
    setShowScreenshotUpload(false);
    setExtractedRaces([]);
    setSelectedFile(null);
    setError(null);
  };

  // ============================================================================
  // HELPERS
  // ============================================================================

  const formatTime = (minutes: number): string => {
    const hours = Math.floor(minutes / 60);
    const mins = Math.floor(minutes % 60);
    return hours > 0 ? `${hours}h ${mins}m` : `${mins}m`;
  };

  const calculatePace = (distanceMiles: number, timeMinutes: number): string => {
    const paceMinPerMile = timeMinutes / distanceMiles;
    const paceMin = Math.floor(paceMinPerMile);
    const paceSec = Math.round((paceMinPerMile - paceMin) * 60);
    return `${paceMin}:${paceSec.toString().padStart(2, '0')}/mi`;
  };

  // Sort history by date (most recent first)
  const sortedHistory = [...history].sort((a, b) => 
    new Date(b.race_date).getTime() - new Date(a.race_date).getTime()
  );

  // ============================================================================
  // RENDER
  // ============================================================================

  return (
    <div>
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
        <h2 className={styles.cardHeader}>Race History ({history.length})</h2>
        <div style={{ display: 'flex', gap: '10px' }}>
          <button
            onClick={handleScreenshotClick}
            style={{
              padding: '10px 20px',
              backgroundColor: '#9b59b6',
              color: 'white',
              border: 'none',
              borderRadius: '4px',
              cursor: 'pointer',
              fontSize: '14px',
              fontWeight: '600'
            }}
          >
            📷 Upload Screenshot
          </button>
          <button
            onClick={handleAddManual}
            style={{
              padding: '10px 20px',
              backgroundColor: '#3498db',
              color: 'white',
              border: 'none',
              borderRadius: '4px',
              cursor: 'pointer',
              fontSize: '14px',
              fontWeight: '600'
            }}
          >
            + Add Race Manually
          </button>
        </div>
      </div>

      {/* Error Display */}
      {error && !showManualForm && !showScreenshotUpload && (
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

      {/* Manual Entry Form */}
      {showManualForm && (
        <div style={{
          backgroundColor: '#f8f9fa',
          padding: '20px',
          borderRadius: '8px',
          marginBottom: '20px',
          border: '2px solid #3498db'
        }}>
          <h3 style={{ marginTop: 0, marginBottom: '20px', color: '#2c3e50' }}>
            {editingRace ? 'Edit Race Result' : 'Add Race Manually'}
          </h3>

          {error && (
            <div style={{
              padding: '12px',
              backgroundColor: '#fee',
              border: '1px solid #fcc',
              borderRadius: '4px',
              marginBottom: '15px',
              color: '#c33',
              fontSize: '14px'
            }}>
              {error}
            </div>
          )}

          <form onSubmit={handleManualSubmit}>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '15px', marginBottom: '15px' }}>
              {/* Race Name */}
              <div style={{ gridColumn: '1 / -1' }}>
                <label style={{ display: 'block', marginBottom: '5px', fontWeight: '600', fontSize: '14px' }}>
                  Race Name <span style={{ color: '#e74c3c' }}>*</span>
                </label>
                <input
                  type="text"
                  value={formData.race_name}
                  onChange={(e) => setFormData({ ...formData, race_name: e.target.value })}
                  required
                  style={{
                    width: '100%',
                    padding: '10px',
                    border: '1px solid #ddd',
                    borderRadius: '4px',
                    fontSize: '14px'
                  }}
                  placeholder="e.g., Lake Sonoma 50"
                />
              </div>

              {/* Distance */}
              <div>
                <label style={{ display: 'block', marginBottom: '5px', fontWeight: '600', fontSize: '14px' }}>
                  Distance (miles) <span style={{ color: '#e74c3c' }}>*</span>
                </label>
                <input
                  type="number"
                  step="0.1"
                  min="0.1"
                  value={formData.distance_miles}
                  onChange={(e) => setFormData({ ...formData, distance_miles: e.target.value })}
                  required
                  style={{
                    width: '100%',
                    padding: '10px',
                    border: '1px solid #ddd',
                    borderRadius: '4px',
                    fontSize: '14px'
                  }}
                  placeholder="e.g., 50.0"
                />
              </div>

              {/* Date */}
              <div>
                <label style={{ display: 'block', marginBottom: '5px', fontWeight: '600', fontSize: '14px' }}>
                  Race Date <span style={{ color: '#e74c3c' }}>*</span>
                </label>
                <input
                  type="date"
                  value={formData.race_date}
                  onChange={(e) => setFormData({ ...formData, race_date: e.target.value })}
                  required
                  style={{
                    width: '100%',
                    padding: '10px',
                    border: '1px solid #ddd',
                    borderRadius: '4px',
                    fontSize: '14px'
                  }}
                />
              </div>

              {/* Finish Time */}
              <div style={{ gridColumn: '1 / -1' }}>
                <label style={{ display: 'block', marginBottom: '5px', fontWeight: '600', fontSize: '14px' }}>
                  Finish Time (total minutes) <span style={{ color: '#e74c3c' }}>*</span>
                </label>
                <input
                  type="number"
                  min="1"
                  value={formData.finish_time_minutes}
                  onChange={(e) => setFormData({ ...formData, finish_time_minutes: e.target.value })}
                  required
                  style={{
                    width: '100%',
                    padding: '10px',
                    border: '1px solid #ddd',
                    borderRadius: '4px',
                    fontSize: '14px'
                  }}
                  placeholder="e.g., 480 (for 8 hours)"
                />
                <div style={{ marginTop: '5px', fontSize: '12px', color: '#7f8c8d' }}>
                  💡 Tip: Convert hours to minutes (e.g., 8:30 = 510 minutes)
                </div>
              </div>
            </div>

            {/* Form Actions */}
            <div style={{ display: 'flex', gap: '10px', justifyContent: 'flex-end' }}>
              <button
                type="button"
                onClick={handleCancelManual}
                disabled={isSaving}
                style={{
                  padding: '10px 20px',
                  backgroundColor: '#95a5a6',
                  color: 'white',
                  border: 'none',
                  borderRadius: '4px',
                  cursor: isSaving ? 'not-allowed' : 'pointer',
                  fontSize: '14px',
                  fontWeight: '600',
                  opacity: isSaving ? 0.6 : 1
                }}
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={isSaving}
                style={{
                  padding: '10px 20px',
                  backgroundColor: '#10b981',
                  color: 'white',
                  border: 'none',
                  borderRadius: '4px',
                  cursor: isSaving ? 'not-allowed' : 'pointer',
                  fontSize: '14px',
                  fontWeight: '600',
                  opacity: isSaving ? 0.6 : 1
                }}
              >
                {isSaving ? 'Saving...' : (editingRace ? 'Update Race' : 'Save Race')}
              </button>
            </div>
          </form>
        </div>
      )}

      {/* Screenshot Upload Modal */}
      {showScreenshotUpload && (
        <div style={{
          backgroundColor: '#f8f9fa',
          padding: '20px',
          borderRadius: '8px',
          marginBottom: '20px',
          border: '2px solid #9b59b6'
        }}>
          <h3 style={{ marginTop: 0, marginBottom: '20px', color: '#2c3e50' }}>
            📷 Upload Ultrasignup Screenshot
          </h3>

          {error && (
            <div style={{
              padding: '12px',
              backgroundColor: '#fee',
              border: '1px solid #fcc',
              borderRadius: '4px',
              marginBottom: '15px',
              color: '#c33',
              fontSize: '14px'
            }}>
              {error}
            </div>
          )}

          {/* File Picker */}
          {extractedRaces.length === 0 && (
            <div>
              <div style={{
                border: '2px dashed #9b59b6',
                borderRadius: '8px',
                padding: '30px',
                textAlign: 'center',
                marginBottom: '20px',
                backgroundColor: 'white'
              }}>
                <input
                  type="file"
                  accept="image/*"
                  onChange={handleFileSelect}
                  style={{ marginBottom: '15px' }}
                />
                {selectedFile && (
                  <div style={{ marginTop: '10px', color: '#7f8c8d', fontSize: '14px' }}>
                    Selected: {selectedFile.name}
                  </div>
                )}
              </div>

              {/* Upload Progress */}
              {isUploading && (
                <div style={{ marginBottom: '20px' }}>
                  <div style={{
                    height: '30px',
                    backgroundColor: '#e1e8ed',
                    borderRadius: '15px',
                    overflow: 'hidden',
                    position: 'relative'
                  }}>
                    <div style={{
                      height: '100%',
                      width: `${uploadProgress}%`,
                      backgroundColor: '#9b59b6',
                      transition: 'width 0.3s ease',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      color: 'white',
                      fontSize: '14px',
                      fontWeight: '600'
                    }}>
                      {uploadProgress}%
                    </div>
                  </div>
                  <div style={{ textAlign: 'center', marginTop: '10px', color: '#7f8c8d', fontSize: '14px' }}>
                    Analyzing screenshot with AI...
                  </div>
                </div>
              )}

              {/* Upload Instructions */}
              <div style={{
                padding: '15px',
                backgroundColor: '#e8f4f8',
                borderRadius: '6px',
                fontSize: '13px',
                color: '#555',
                marginBottom: '20px'
              }}>
                <strong>📋 Instructions:</strong>
                <ul style={{ marginTop: '8px', marginBottom: 0, paddingLeft: '20px' }}>
                  <li>Screenshot your race results from ultrasignup.com</li>
                  <li>Make sure race names, dates, distances, and times are clearly visible</li>
                  <li>Upload one screenshot at a time</li>
                  <li>Review and edit the extracted data before saving</li>
                </ul>
              </div>

              {/* Action Buttons */}
              <div style={{ display: 'flex', gap: '10px', justifyContent: 'flex-end' }}>
                <button
                  onClick={handleCancelScreenshot}
                  disabled={isUploading}
                  style={{
                    padding: '10px 20px',
                    backgroundColor: '#95a5a6',
                    color: 'white',
                    border: 'none',
                    borderRadius: '4px',
                    cursor: isUploading ? 'not-allowed' : 'pointer',
                    fontSize: '14px',
                    fontWeight: '600',
                    opacity: isUploading ? 0.6 : 1
                  }}
                >
                  Cancel
                </button>
                <button
                  onClick={handleScreenshotUpload}
                  disabled={!selectedFile || isUploading}
                  style={{
                    padding: '10px 20px',
                    backgroundColor: '#9b59b6',
                    color: 'white',
                    border: 'none',
                    borderRadius: '4px',
                    cursor: (!selectedFile || isUploading) ? 'not-allowed' : 'pointer',
                    fontSize: '14px',
                    fontWeight: '600',
                    opacity: (!selectedFile || isUploading) ? 0.6 : 1
                  }}
                >
                  {isUploading ? 'Uploading...' : 'Upload & Parse'}
                </button>
              </div>
            </div>
          )}

          {/* Extracted Races Review Table */}
          {extractedRaces.length > 0 && (
            <div>
              <div style={{
                backgroundColor: '#d1f2eb',
                padding: '12px',
                borderRadius: '6px',
                marginBottom: '15px',
                fontSize: '14px',
                color: '#0e6655'
              }}>
                ✅ Found {extractedRaces.length} race(s)! Review and edit if needed, then save.
              </div>

              <div style={{ overflowX: 'auto', marginBottom: '20px' }}>
                <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '14px' }}>
                  <thead>
                    <tr style={{ backgroundColor: '#e1e8ed' }}>
                      <th style={{ padding: '10px', textAlign: 'left', border: '1px solid #ccc' }}>Race Name</th>
                      <th style={{ padding: '10px', textAlign: 'left', border: '1px solid #ccc' }}>Distance (mi)</th>
                      <th style={{ padding: '10px', textAlign: 'left', border: '1px solid #ccc' }}>Date</th>
                      <th style={{ padding: '10px', textAlign: 'left', border: '1px solid #ccc' }}>Time (min)</th>
                    </tr>
                  </thead>
                  <tbody>
                    {extractedRaces.map((race, index) => (
                      <tr key={index} style={{ backgroundColor: race.error ? '#fee' : 'white' }}>
                        <td style={{ padding: '8px', border: '1px solid #ccc' }}>
                          <input
                            type="text"
                            value={race.race_name}
                            onChange={(e) => handleExtractedRaceEdit(index, 'race_name', e.target.value)}
                            style={{
                              width: '100%',
                              padding: '6px',
                              border: '1px solid #ddd',
                              borderRadius: '3px',
                              fontSize: '13px'
                            }}
                          />
                        </td>
                        <td style={{ padding: '8px', border: '1px solid #ccc' }}>
                          <input
                            type="number"
                            step="0.1"
                            value={race.distance_miles}
                            onChange={(e) => handleExtractedRaceEdit(index, 'distance_miles', e.target.value)}
                            style={{
                              width: '100%',
                              padding: '6px',
                              border: '1px solid #ddd',
                              borderRadius: '3px',
                              fontSize: '13px'
                            }}
                          />
                        </td>
                        <td style={{ padding: '8px', border: '1px solid #ccc' }}>
                          <input
                            type="date"
                            value={race.race_date}
                            onChange={(e) => handleExtractedRaceEdit(index, 'race_date', e.target.value)}
                            style={{
                              width: '100%',
                              padding: '6px',
                              border: '1px solid #ddd',
                              borderRadius: '3px',
                              fontSize: '13px'
                            }}
                          />
                        </td>
                        <td style={{ padding: '8px', border: '1px solid #ccc' }}>
                          <input
                            type="number"
                            value={race.finish_time_minutes}
                            onChange={(e) => handleExtractedRaceEdit(index, 'finish_time_minutes', e.target.value)}
                            style={{
                              width: '100%',
                              padding: '6px',
                              border: '1px solid #ddd',
                              borderRadius: '3px',
                              fontSize: '13px'
                            }}
                          />
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              {/* Bulk Save Actions */}
              <div style={{ display: 'flex', gap: '10px', justifyContent: 'flex-end' }}>
                <button
                  onClick={handleCancelScreenshot}
                  disabled={isSaving}
                  style={{
                    padding: '10px 20px',
                    backgroundColor: '#95a5a6',
                    color: 'white',
                    border: 'none',
                    borderRadius: '4px',
                    cursor: isSaving ? 'not-allowed' : 'pointer',
                    fontSize: '14px',
                    fontWeight: '600',
                    opacity: isSaving ? 0.6 : 1
                  }}
                >
                  Cancel
                </button>
                <button
                  onClick={handleBulkSave}
                  disabled={isSaving}
                  style={{
                    padding: '10px 20px',
                    backgroundColor: '#10b981',
                    color: 'white',
                    border: 'none',
                    borderRadius: '4px',
                    cursor: isSaving ? 'not-allowed' : 'pointer',
                    fontSize: '14px',
                    fontWeight: '600',
                    opacity: isSaving ? 0.6 : 1
                  }}
                >
                  {isSaving ? 'Saving...' : `Save ${extractedRaces.length} Race(s)`}
                </button>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Race History Table */}
      {sortedHistory.length === 0 ? (
        <div style={{ textAlign: 'center', padding: '40px 20px', color: '#95a5a6' }}>
          <p style={{ fontSize: '18px', marginBottom: '10px' }}>No race history yet</p>
          <p style={{ fontSize: '14px' }}>Add your past races to help assess fitness trends and performance!</p>
        </div>
      ) : (
        <div style={{ overflowX: 'auto' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '14px' }}>
            <thead>
              <tr style={{ backgroundColor: '#e1e8ed' }}>
                <th style={{ padding: '12px', textAlign: 'left', border: '1px solid #ccc' }}>Date</th>
                <th style={{ padding: '12px', textAlign: 'left', border: '1px solid #ccc' }}>Race Name</th>
                <th style={{ padding: '12px', textAlign: 'right', border: '1px solid #ccc' }}>Distance</th>
                <th style={{ padding: '12px', textAlign: 'right', border: '1px solid #ccc' }}>Time</th>
                <th style={{ padding: '12px', textAlign: 'right', border: '1px solid #ccc' }}>Pace</th>
                <th style={{ padding: '12px', textAlign: 'center', border: '1px solid #ccc' }}>Actions</th>
              </tr>
            </thead>
            <tbody>
              {sortedHistory.map(race => (
                <tr key={race.id} style={{ backgroundColor: 'white' }}>
                  <td style={{ padding: '10px', border: '1px solid #ccc' }}>
                    {new Date(race.race_date).toLocaleDateString('en-US', {
                      year: 'numeric',
                      month: 'short',
                      day: 'numeric'
                    })}
                  </td>
                  <td style={{ padding: '10px', border: '1px solid #ccc', fontWeight: '600' }}>
                    {race.race_name}
                  </td>
                  <td style={{ padding: '10px', border: '1px solid #ccc', textAlign: 'right' }}>
                    {race.distance_miles.toFixed(1)} mi
                  </td>
                  <td style={{ padding: '10px', border: '1px solid #ccc', textAlign: 'right' }}>
                    {formatTime(race.finish_time_minutes)}
                  </td>
                  <td style={{ padding: '10px', border: '1px solid #ccc', textAlign: 'right', color: '#7f8c8d' }}>
                    {calculatePace(race.distance_miles, race.finish_time_minutes)}
                  </td>
                  <td style={{ padding: '10px', border: '1px solid #ccc', textAlign: 'center' }}>
                    <div style={{ display: 'flex', gap: '5px', justifyContent: 'center' }}>
                      <button
                        onClick={() => handleEdit(race)}
                        style={{
                          padding: '4px 8px',
                          backgroundColor: '#3498db',
                          color: 'white',
                          border: 'none',
                          borderRadius: '3px',
                          cursor: 'pointer',
                          fontSize: '12px'
                        }}
                      >
                        Edit
                      </button>
                      <button
                        onClick={() => handleDelete(race.id)}
                        style={{
                          padding: '4px 8px',
                          backgroundColor: '#e74c3c',
                          color: 'white',
                          border: 'none',
                          borderRadius: '3px',
                          cursor: 'pointer',
                          fontSize: '12px'
                        }}
                      >
                        Delete
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
};

export default RaceHistoryManager;

