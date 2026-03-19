import React, { useState, useRef } from 'react';
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

  // Time field refs for auto-advance
  const timeHRef = useRef<HTMLInputElement>(null);
  const timeMRef = useRef<HTMLInputElement>(null);
  const timeSRef = useRef<HTMLInputElement>(null);

  // Manual form state
  const [formData, setFormData] = useState({
    race_name: '',
    distance_miles: '',
    race_date: '',
    time_h: '',
    time_m: '',
    time_s: ''
  });

  // Convert stored decimal minutes → H/MM/SS display
  const minutesToHMS = (totalMinutes: number) => {
    const h = Math.floor(totalMinutes / 60);
    const m = Math.floor(totalMinutes % 60);
    const s = Math.round((totalMinutes % 1) * 60);
    return {
      time_h: h.toString(),
      time_m: m.toString().padStart(2, '0'),
      time_s: s.toString().padStart(2, '0')
    };
  };

  // Convert H/MM/SS fields → decimal minutes for storage
  const hmsToMinutes = (h: string, m: string, s: string): number => {
    return (parseInt(h || '0', 10) * 60) +
           parseInt(m || '0', 10) +
           (parseInt(s || '0', 10) / 60);
  };

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
      time_h: '',
      time_m: '',
      time_s: ''
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
      ...minutesToHMS(race.finish_time_minutes)
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
        finish_time_minutes: hmsToMinutes(formData.time_h, formData.time_m, formData.time_s)
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
      const savedCount = data.count || 0;
      const totalAttempted = extractedRaces.length;
      const failedCount = totalAttempted - savedCount;
      
      if (failedCount > 0) {
        alert(`Successfully saved ${savedCount} race(s). ${failedCount} failed to save.`);
      } else {
        alert(`Successfully saved ${savedCount} race(s)!`);
      }

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

      {/* Manual Entry Form — Tactical Modal */}
      {showManualForm && (
        <div
          onClick={(e) => { if (e.target === e.currentTarget) handleCancelManual(); }}
          style={{
            position: 'fixed',
            inset: 0,
            background: 'rgba(0,0,0,0.65)',
            zIndex: 1000,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            padding: '20px',
          }}
        >
          <div style={{
            backgroundColor: '#1B2E4B',
            backgroundImage: 'linear-gradient(135deg, rgba(255,255,255,0.04) 25%, transparent 25%), linear-gradient(225deg, rgba(255,255,255,0.04) 25%, transparent 25%), linear-gradient(315deg, rgba(255,255,255,0.04) 25%, transparent 25%), linear-gradient(45deg, rgba(255,255,255,0.04) 25%, transparent 25%)',
            backgroundSize: '4px 4px',
            border: '1px solid rgba(255,87,34,0.7)',
            borderRadius: '6px',
            overflow: 'hidden',
            width: '100%',
            maxWidth: '560px',
            maxHeight: '90vh',
            overflowY: 'auto',
          }}>
            {/* Header strip */}
            <div style={{
              background: 'linear-gradient(90deg, #E6F0FF 0%, #7D9CB8 50%, #1B2E4B 100%)',
              padding: '0.75rem 1.25rem',
              fontSize: '10px',
              letterSpacing: '0.15em',
              fontWeight: '700',
              color: '#1B2E4B',
              textTransform: 'uppercase',
            }}>
              {editingRace ? 'Modify Result' : 'Log Race Result'}
            </div>

            <div style={{ padding: '20px' }}>
              {error && (
                <div style={{
                  padding: '10px 14px',
                  background: 'rgba(239,68,68,0.15)',
                  border: '1px solid rgba(239,68,68,0.4)',
                  borderRadius: '4px',
                  marginBottom: '16px',
                  color: '#fca5a5',
                  fontSize: '13px',
                }}>
                  {error}
                </div>
              )}

              <style>{`
                .ytm-hist-input {
                  width: 100%;
                  padding: 8px 10px;
                  background: #162440;
                  border: 1px solid rgba(125,156,184,0.3);
                  border-radius: 4px;
                  font-size: 0.875rem;
                  color: #E6F0FF;
                  box-sizing: border-box;
                }
                .ytm-hist-input::placeholder { color: rgba(230,240,255,0.25); }
                .ytm-hist-input:focus {
                  outline: none;
                  border-color: #7D9CB8;
                  background: #1a2d4e;
                  box-shadow: 0 0 0 2px rgba(125,156,184,0.2);
                }
                .ytm-hist-input[type=number]::-webkit-inner-spin-button,
                .ytm-hist-input[type=number]::-webkit-outer-spin-button { -webkit-appearance: none; margin: 0; }
                .ytm-hist-input[type=number] { -moz-appearance: textfield; }
              `}</style>

              <form onSubmit={handleManualSubmit}>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '15px', marginBottom: '20px' }}>

                  {/* Race Name */}
                  <div style={{ gridColumn: '1 / -1' }}>
                    <label style={{ display: 'block', marginBottom: '5px', fontSize: '0.7rem', fontWeight: '700', letterSpacing: '0.12em', textTransform: 'uppercase', color: '#7D9CB8' }}>
                      Race Name <span style={{ color: '#FF5722' }}>*</span>
                    </label>
                    <input
                      type="text"
                      value={formData.race_name}
                      onChange={(e) => setFormData({ ...formData, race_name: e.target.value })}
                      required
                      className="ytm-hist-input"
                      placeholder="e.g., Lake Sonoma 50"
                    />
                  </div>

                  {/* Distance */}
                  <div>
                    <label style={{ display: 'block', marginBottom: '5px', fontSize: '0.7rem', fontWeight: '700', letterSpacing: '0.12em', textTransform: 'uppercase', color: '#7D9CB8' }}>
                      Distance <span style={{ color: 'rgba(125,156,184,0.6)', fontWeight: '400', textTransform: 'none', letterSpacing: 0 }}>mi</span> <span style={{ color: '#FF5722' }}>*</span>
                    </label>
                    <input
                      type="number"
                      step="0.1"
                      min="0.1"
                      value={formData.distance_miles}
                      onChange={(e) => setFormData({ ...formData, distance_miles: e.target.value })}
                      required
                      className="ytm-hist-input"
                      placeholder="50.0"
                    />
                  </div>

                  {/* Date */}
                  <div>
                    <label style={{ display: 'block', marginBottom: '5px', fontSize: '0.7rem', fontWeight: '700', letterSpacing: '0.12em', textTransform: 'uppercase', color: '#7D9CB8' }}>
                      Race Date <span style={{ color: '#FF5722' }}>*</span>
                    </label>
                    <input
                      type="date"
                      value={formData.race_date}
                      onChange={(e) => setFormData({ ...formData, race_date: e.target.value })}
                      required
                      className="ytm-hist-input"
                    />
                  </div>

                  {/* Finish Time */}
                  <div style={{ gridColumn: '1 / -1' }}>
                    <label style={{ display: 'block', marginBottom: '5px', fontSize: '0.7rem', fontWeight: '700', letterSpacing: '0.12em', textTransform: 'uppercase', color: '#7D9CB8' }}>
                      Finish Time <span style={{ color: '#FF5722' }}>*</span>
                    </label>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                      <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '3px' }}>
                        <input
                          ref={timeHRef}
                          type="number"
                          min="0"
                          max="99"
                          value={formData.time_h}
                          onChange={(e) => {
                            setFormData({ ...formData, time_h: e.target.value });
                            if (e.target.value.length >= 2) timeMRef.current?.focus();
                          }}
                          required
                          className="ytm-hist-input"
                          style={{ width: '64px', textAlign: 'center' }}
                          placeholder="0"
                        />
                        <span style={{ fontSize: '0.65rem', color: 'rgba(125,156,184,0.6)', letterSpacing: '0.08em', textTransform: 'uppercase' }}>hr</span>
                      </div>
                      <span style={{ color: '#7D9CB8', fontSize: '1.2rem', fontWeight: '300', paddingBottom: '18px' }}>:</span>
                      <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '3px' }}>
                        <input
                          ref={timeMRef}
                          type="number"
                          min="0"
                          max="59"
                          value={formData.time_m}
                          onChange={(e) => {
                            setFormData({ ...formData, time_m: e.target.value });
                            if (e.target.value.length >= 2) timeSRef.current?.focus();
                          }}
                          required
                          className="ytm-hist-input"
                          style={{ width: '64px', textAlign: 'center' }}
                          placeholder="00"
                        />
                        <span style={{ fontSize: '0.65rem', color: 'rgba(125,156,184,0.6)', letterSpacing: '0.08em', textTransform: 'uppercase' }}>min</span>
                      </div>
                      <span style={{ color: '#7D9CB8', fontSize: '1.2rem', fontWeight: '300', paddingBottom: '18px' }}>:</span>
                      <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '3px' }}>
                        <input
                          ref={timeSRef}
                          type="number"
                          min="0"
                          max="59"
                          value={formData.time_s}
                          onChange={(e) => setFormData({ ...formData, time_s: e.target.value })}
                          className="ytm-hist-input"
                          style={{ width: '64px', textAlign: 'center' }}
                          placeholder="00"
                        />
                        <span style={{ fontSize: '0.65rem', color: 'rgba(125,156,184,0.6)', letterSpacing: '0.08em', textTransform: 'uppercase' }}>sec</span>
                      </div>
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
                      padding: '10px 16px',
                      background: 'transparent',
                      color: '#7D9CB8',
                      border: '1px solid rgba(125,156,184,0.3)',
                      borderRadius: '4px',
                      cursor: isSaving ? 'not-allowed' : 'pointer',
                      fontSize: '0.8rem',
                      fontWeight: '600',
                      letterSpacing: '0.05em',
                      opacity: isSaving ? 0.5 : 1,
                    }}
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    disabled={isSaving}
                    style={{
                      padding: '10px 24px',
                      background: isSaving ? 'rgba(255,87,34,0.5)' : '#FF5722',
                      color: 'white',
                      border: 'none',
                      borderRadius: '4px',
                      cursor: isSaving ? 'not-allowed' : 'pointer',
                      fontSize: '0.8rem',
                      fontWeight: '700',
                      letterSpacing: '0.08em',
                      textTransform: 'uppercase',
                    }}
                  >
                    {isSaving ? 'Working...' : (editingRace ? 'Commit Changes' : 'Log Result')}
                  </button>
                </div>
              </form>
            </div>
          </div>
        </div>
      )}

      {/* Screenshot Upload Modal — Tactical */}
      {showScreenshotUpload && (
        <div
          onClick={(e) => { if (e.target === e.currentTarget) handleCancelScreenshot(); }}
          style={{
            position: 'fixed',
            inset: 0,
            background: 'rgba(0,0,0,0.65)',
            zIndex: 1000,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            padding: '20px',
          }}
        >
          <div style={{
            backgroundColor: '#1B2E4B',
            backgroundImage: 'linear-gradient(135deg, rgba(255,255,255,0.04) 25%, transparent 25%), linear-gradient(225deg, rgba(255,255,255,0.04) 25%, transparent 25%), linear-gradient(315deg, rgba(255,255,255,0.04) 25%, transparent 25%), linear-gradient(45deg, rgba(255,255,255,0.04) 25%, transparent 25%)',
            backgroundSize: '4px 4px',
            border: '1px solid rgba(255,87,34,0.7)',
            borderRadius: '6px',
            overflow: 'hidden',
            width: '100%',
            maxWidth: '680px',
            maxHeight: '90vh',
            overflowY: 'auto',
          }}>
            {/* Header */}
            <div style={{
              background: 'linear-gradient(90deg, #E6F0FF 0%, #7D9CB8 50%, #1B2E4B 100%)',
              padding: '0.75rem 1.25rem',
              fontSize: '10px',
              letterSpacing: '0.15em',
              fontWeight: '700',
              color: '#1B2E4B',
              textTransform: 'uppercase',
            }}>
              Import Race Results
            </div>

            <div style={{ padding: '20px' }}>
              {error && (
                <div style={{
                  padding: '10px 14px',
                  background: 'rgba(239,68,68,0.15)',
                  border: '1px solid rgba(239,68,68,0.4)',
                  borderRadius: '4px',
                  marginBottom: '16px',
                  color: '#fca5a5',
                  fontSize: '13px',
                }}>
                  {error}
                </div>
              )}

              {/* File Picker */}
              {extractedRaces.length === 0 && (
                <div>
                  {/* Drop zone */}
                  <div style={{
                    border: '1px dashed rgba(125,156,184,0.4)',
                    borderRadius: '4px',
                    padding: '24px',
                    textAlign: 'center',
                    marginBottom: '16px',
                    background: 'rgba(255,255,255,0.04)',
                  }}>
                    <input
                      type="file"
                      accept="image/*"
                      onChange={handleFileSelect}
                      style={{ marginBottom: '10px', color: '#E6F0FF' }}
                    />
                    {selectedFile && (
                      <div style={{ marginTop: '8px', color: '#7D9CB8', fontSize: '13px' }}>
                        {selectedFile.name}
                      </div>
                    )}
                  </div>

                  {/* Upload Progress */}
                  {isUploading && (
                    <div style={{ marginBottom: '16px' }}>
                      <div style={{
                        height: '6px',
                        background: 'rgba(255,255,255,0.1)',
                        borderRadius: '3px',
                        overflow: 'hidden',
                      }}>
                        <div style={{
                          height: '100%',
                          width: `${uploadProgress}%`,
                          background: '#FF5722',
                          transition: 'width 0.3s ease',
                          borderRadius: '3px',
                        }} />
                      </div>
                      <div style={{ marginTop: '6px', color: '#7D9CB8', fontSize: '12px', letterSpacing: '0.06em' }}>
                        ANALYZING — {uploadProgress}%
                      </div>
                    </div>
                  )}

                  {/* Instructions */}
                  <div style={{
                    padding: '12px 14px',
                    background: 'rgba(125,156,184,0.08)',
                    border: '1px solid rgba(125,156,184,0.2)',
                    borderRadius: '4px',
                    fontSize: '12px',
                    color: 'rgba(230,240,255,0.6)',
                    marginBottom: '20px',
                    lineHeight: '1.6',
                  }}>
                    Screenshot race results from ultrasignup.com. Ensure names, dates, distances, and times are visible. One screenshot at a time. Review extracted data before committing.
                  </div>

                  {/* Actions */}
                  <div style={{ display: 'flex', gap: '10px', justifyContent: 'flex-end' }}>
                    <button
                      onClick={handleCancelScreenshot}
                      disabled={isUploading}
                      style={{
                        padding: '10px 16px',
                        background: 'transparent',
                        color: '#7D9CB8',
                        border: '1px solid rgba(125,156,184,0.3)',
                        borderRadius: '4px',
                        cursor: isUploading ? 'not-allowed' : 'pointer',
                        fontSize: '0.8rem',
                        fontWeight: '600',
                        opacity: isUploading ? 0.5 : 1,
                      }}
                    >
                      Cancel
                    </button>
                    <button
                      onClick={handleScreenshotUpload}
                      disabled={!selectedFile || isUploading}
                      style={{
                        padding: '10px 24px',
                        background: (!selectedFile || isUploading) ? 'rgba(255,87,34,0.35)' : '#FF5722',
                        color: 'white',
                        border: 'none',
                        borderRadius: '4px',
                        cursor: (!selectedFile || isUploading) ? 'not-allowed' : 'pointer',
                        fontSize: '0.8rem',
                        fontWeight: '700',
                        letterSpacing: '0.08em',
                        textTransform: 'uppercase',
                      }}
                    >
                      {isUploading ? 'Parsing...' : 'Parse Screenshot'}
                    </button>
                  </div>
                </div>
              )}

              {/* Extracted Races Review */}
              {extractedRaces.length > 0 && (
                <div>
                  <div style={{
                    padding: '10px 14px',
                    background: 'rgba(22,163,74,0.15)',
                    border: '1px solid rgba(22,163,74,0.4)',
                    borderRadius: '4px',
                    marginBottom: '16px',
                    color: '#86efac',
                    fontSize: '13px',
                  }}>
                    {extractedRaces.length} result{extractedRaces.length !== 1 ? 's' : ''} extracted. Review and edit before committing.
                  </div>

                  <div style={{ overflowX: 'auto', marginBottom: '20px' }}>
                    <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '13px' }}>
                      <thead>
                        <tr>
                          {['Race Name', 'Distance mi', 'Date', 'Time min'].map(h => (
                            <th key={h} style={{
                              padding: '8px 10px',
                              textAlign: 'left',
                              fontSize: '0.65rem',
                              fontWeight: '700',
                              letterSpacing: '0.1em',
                              textTransform: 'uppercase',
                              color: '#7D9CB8',
                              borderBottom: '1px solid rgba(125,156,184,0.2)',
                            }}>{h}</th>
                          ))}
                        </tr>
                      </thead>
                      <tbody>
                        {extractedRaces.map((race, index) => (
                          <tr key={index}>
                            {(['race_name', 'distance_miles', 'race_date', 'finish_time_minutes'] as const).map((field) => (
                              <td key={field} style={{ padding: '6px 4px' }}>
                                <input
                                  type={field === 'race_date' ? 'date' : field === 'race_name' ? 'text' : 'number'}
                                  value={(race as any)[field]}
                                  onChange={(e) => handleExtractedRaceEdit(index, field, e.target.value)}
                                  style={{
                                    width: '100%',
                                    padding: '6px 8px',
                                    background: race.error ? '#2a1a1a' : '#162440',
                                    border: `1px solid ${race.error ? 'rgba(239,68,68,0.4)' : 'rgba(125,156,184,0.3)'}`,
                                    borderRadius: '3px',
                                    fontSize: '13px',
                                    color: '#E6F0FF',
                                  }}
                                />
                              </td>
                            ))}
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
                        padding: '10px 16px',
                        background: 'transparent',
                        color: '#7D9CB8',
                        border: '1px solid rgba(125,156,184,0.3)',
                        borderRadius: '4px',
                        cursor: isSaving ? 'not-allowed' : 'pointer',
                        fontSize: '0.8rem',
                        fontWeight: '600',
                        opacity: isSaving ? 0.5 : 1,
                      }}
                    >
                      Cancel
                    </button>
                    <button
                      onClick={handleBulkSave}
                      disabled={isSaving}
                      style={{
                        padding: '10px 24px',
                        background: isSaving ? 'rgba(255,87,34,0.5)' : '#FF5722',
                        color: 'white',
                        border: 'none',
                        borderRadius: '4px',
                        cursor: isSaving ? 'not-allowed' : 'pointer',
                        fontSize: '0.8rem',
                        fontWeight: '700',
                        letterSpacing: '0.08em',
                        textTransform: 'uppercase',
                      }}
                    >
                      {isSaving ? 'Working...' : `Commit ${extractedRaces.length} Result${extractedRaces.length !== 1 ? 's' : ''}`}
                    </button>
                  </div>
                </div>
              )}
            </div>
          </div>
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

