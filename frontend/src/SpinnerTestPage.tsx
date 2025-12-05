import React from 'react';
import YTMSpinner from './YTMSpinner';

const SpinnerTestPage: React.FC = () => {
  return (
    <div style={{ padding: '40px' }}>
      <h2 style={{ marginBottom: '30px', color: '#1e293b' }}>YTM Spinner Test Page</h2>
      
      {/* Debug Info */}
      <div style={{ 
        marginBottom: '30px', 
        padding: '15px', 
        backgroundColor: '#fef3c7', 
        borderRadius: '6px',
        border: '1px solid #fbbf24'
      }}>
        <strong>Debug Info:</strong> Check browser console for image loading messages. 
        Images should be at: <code>/static/images/compass-bg.png</code> and <code>/static/images/monkey-fg.png</code>
      </div>
      
      {/* Default Size */}
      <div style={{ marginBottom: '60px' }}>
        <h3 style={{ color: '#64748b', marginBottom: '20px' }}>Default Size (200px) - Light Background</h3>
        <div style={{ 
          display: 'flex', 
          justifyContent: 'center', 
          padding: '40px',
          backgroundColor: '#f8fafc',
          borderRadius: '8px'
        }}>
          <YTMSpinner />
        </div>
      </div>

      {/* Default Size - Dark Background */}
      <div style={{ marginBottom: '60px' }}>
        <h3 style={{ color: '#64748b', marginBottom: '20px' }}>Default Size (200px) - Dark Background</h3>
        <div style={{ 
          display: 'flex', 
          justifyContent: 'center', 
          padding: '40px',
          backgroundColor: '#334155',
          borderRadius: '8px'
        }}>
          <YTMSpinner />
        </div>
      </div>

      {/* Small Size */}
      <div style={{ marginBottom: '60px' }}>
        <h3 style={{ color: '#64748b', marginBottom: '20px' }}>Small Size (100px)</h3>
        <div style={{ 
          display: 'flex', 
          justifyContent: 'center', 
          padding: '40px',
          backgroundColor: '#f8fafc',
          borderRadius: '8px'
        }}>
          <YTMSpinner size={100} />
        </div>
      </div>

      {/* Large Size */}
      <div style={{ marginBottom: '60px' }}>
        <h3 style={{ color: '#64748b', marginBottom: '20px' }}>Large Size (300px)</h3>
        <div style={{ 
          display: 'flex', 
          justifyContent: 'center', 
          padding: '40px',
          backgroundColor: '#f8fafc',
          borderRadius: '8px'
        }}>
          <YTMSpinner size={300} />
        </div>
      </div>

      {/* Multiple Spinners */}
      <div style={{ marginBottom: '60px' }}>
        <h3 style={{ color: '#64748b', marginBottom: '20px' }}>Multiple Spinners</h3>
        <div style={{ 
          display: 'flex', 
          justifyContent: 'space-around', 
          padding: '40px',
          backgroundColor: '#f8fafc',
          borderRadius: '8px'
        }}>
          <YTMSpinner size={80} />
          <YTMSpinner size={120} />
          <YTMSpinner size={80} />
        </div>
      </div>

      {/* Usage Example Code */}
      <div style={{ marginTop: '60px', padding: '20px', backgroundColor: '#f1f5f9', borderRadius: '8px' }}>
        <h3 style={{ color: '#1e293b', marginBottom: '15px' }}>Usage Examples</h3>
        <pre style={{ 
          backgroundColor: '#fff', 
          padding: '15px', 
          borderRadius: '4px',
          overflow: 'auto',
          fontSize: '14px'
        }}>
{`// Default size (200px)
<YTMSpinner />

// Custom size
<YTMSpinner size={150} />

// In a loading state
{isLoading ? <YTMSpinner /> : <YourContent />}`}
        </pre>
      </div>
    </div>
  );
};

export default SpinnerTestPage;

