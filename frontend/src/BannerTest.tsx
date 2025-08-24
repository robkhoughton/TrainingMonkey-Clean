import React, { useState } from 'react';
import IntegratedDashboardBanner from './IntegratedDashboardBanner';

const BannerTest: React.FC = () => {
  const [dateRange, setDateRange] = useState('14');

  const handleSyncComplete = () => {
    console.log('Sync completed - this would normally refresh the dashboard');
    alert('Sync functionality working! (This is just a test)');
  };

  return (
    <div style={{
      padding: '20px',
      backgroundColor: '#f9fafb',
      minHeight: '100vh'
    }}>
      <h1 style={{
        textAlign: 'center',
        color: '#374151',
        marginBottom: '2rem',
        fontFamily: 'Arial, sans-serif'
      }}>
        🎨 Banner Development & Fine-Tuning
      </h1>

      <IntegratedDashboardBanner
        dateRange={dateRange}
        setDateRange={setDateRange}
        onSyncComplete={handleSyncComplete}
      />

      {/* Development Info */}
      <div style={{
        marginTop: '2rem',
        padding: '1rem',
        backgroundColor: 'white',
        borderRadius: '0.5rem',
        boxShadow: '0 1px 2px rgba(0,0,0,0.1)'
      }}>
        <h3 style={{ margin: '0 0 1rem 0', color: '#374151' }}>🛠️ Development Controls</h3>
        <p><strong>Current Date Range:</strong> {dateRange} days</p>
        <p><strong>Hot Reload:</strong> ✅ Active - changes appear instantly</p>
        <p><strong>Focus Areas:</strong> Colors, spacing, typography, responsiveness</p>

        <div style={{ marginTop: '1rem' }}>
          <button
            onClick={() => setDateRange('7')}
            style={{ margin: '0 0.5rem', padding: '0.5rem 1rem', cursor: 'pointer' }}
          >
            Test 7 Days
          </button>
          <button
            onClick={() => setDateRange('30')}
            style={{ margin: '0 0.5rem', padding: '0.5rem 1rem', cursor: 'pointer' }}
          >
            Test 30 Days
          </button>
          <button
            onClick={() => setDateRange('90')}
            style={{ margin: '0 0.5rem', padding: '0.5rem 1rem', cursor: 'pointer' }}
          >
            Test 90 Days
          </button>
        </div>
      </div>

      {/* Responsive Testing Helper */}
      <div style={{
        marginTop: '1rem',
        padding: '1rem',
        backgroundColor: '#eff6ff',
        borderRadius: '0.5rem',
        fontSize: '0.875rem',
        color: '#1e40af'
      }}>
        <strong>📱 Responsive Testing:</strong> Resize your browser window to test mobile/tablet layouts
      </div>
    </div>
  );
};

export default BannerTest;