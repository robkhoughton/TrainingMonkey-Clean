// App.tsx - UPDATED with compact file folder tab styling
import React, { useState, useEffect } from 'react';
import './App.css';
import TrainingLoadDashboard from './TrainingLoadDashboard';
import ActivitiesPage from './ActivitiesPage';
import JournalPage from './JournalPage';
import SettingsPage from './SettingsPage';

function App() {
  // Get initial tab from URL parameters
  const getInitialTab = () => {
    const urlParams = new URLSearchParams(window.location.search);
    const tabParam = urlParams.get('tab');
    return tabParam || 'dashboard';
  };

  const [activeTab, setActiveTab] = useState(getInitialTab());

  // Update tab when URL parameters change
  useEffect(() => {
    const urlParams = new URLSearchParams(window.location.search);
    const tabParam = urlParams.get('tab');
    if (tabParam && tabParam !== activeTab) {
      setActiveTab(tabParam);
    }
  }, [activeTab]);

  const renderTabContent = () => {
    switch(activeTab) {
      case 'dashboard':
        return <TrainingLoadDashboard onNavigateToTab={setActiveTab} />;
      case 'activities':
        return <ActivitiesPage />;
      case 'journal':
        return <JournalPage />;
      case 'guide':
        // Redirect to the guide page
        window.location.href = '/guide';
        return null;
      case 'settings':
        return <SettingsPage />;
      default:
        return <TrainingLoadDashboard onNavigateToTab={setActiveTab} />;
    }
  };

  return (
    <div className="App">
      {/* Your existing tab navigation code */}
      <div style={{
        backgroundColor: '#f1f5f9',
        paddingTop: '4px',
        position: 'relative'
      }}>
        <div style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'flex-end',
          paddingRight: '20px'
        }}>
          <nav style={{
            display: 'flex',
            alignItems: 'flex-end',
            paddingLeft: '20px',
            position: 'relative',
            zIndex: 10
          }}>
            {[
              { key: 'dashboard', label: 'Dashboard' },
              { key: 'activities', label: 'Activities' },
              { key: 'journal', label: 'Journal' },
              { key: 'guide', label: 'Guide' },
              { key: 'settings', label: 'Settings' }
            ].map((tab, index) => (
            <button
              key={tab.key}
              onClick={() => setActiveTab(tab.key)}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '0.5rem',
                padding: '6px 16px 7px 16px',
                border: 'none',
                backgroundColor: activeTab === tab.key ? 'white' : '#e2e8f0',
                color: activeTab === tab.key ? '#1e293b' : '#64748b',
                cursor: 'pointer',
                fontWeight: activeTab === tab.key ? '600' : '500',
                fontSize: '0.9rem',
                position: 'relative',
                marginRight: '2px',
                transition: 'all 0.2s ease',
                minWidth: '120px',
                justifyContent: 'center',
                zIndex: activeTab === tab.key ? 20 : 10,
                borderTopLeftRadius: index === 0 ? '8px' : '0',
                borderTopRightRadius: '8px',
                borderBottomLeftRadius: '0',
                borderBottomRightRadius: '0',
                transform: activeTab === tab.key ? 'translateY(0)' : 'translateY(1px)',
                boxShadow: activeTab === tab.key ? '0 -2px 4px rgba(0,0,0,0.1)' : 'none'
              }}
            >
              <span>{tab.label}</span>
            </button>
            ))}
          </nav>
          
          {/* App Branding - Upper Right */}
          <div style={{
            paddingBottom: '8px',
            paddingRight: '20px'
          }}>
            <h1 style={{
              margin: 0,
              fontSize: '1.5rem',
              fontWeight: '900',
              color: '#1e293b',
              letterSpacing: '0.15em',
              textTransform: 'uppercase',
              fontVariant: 'small-caps',
              fontFamily: '"Arial Black", "Arial Bold", sans-serif',
              textShadow: '2px 2px 0px rgba(59, 130, 246, 0.15)',
              WebkitTextStroke: '0.5px rgba(0, 0, 0, 0.1)'
            }}>
              <span style={{ 
                fontSize: '1.8rem', 
                color: '#7a9b76',
                fontVariant: 'normal'
              }}>Y</span>our{' '}
              <span style={{ 
                fontSize: '1.8rem', 
                color: '#7a9b76',
                fontVariant: 'normal'
              }}>T</span>raining{' '}
              <span style={{ 
                fontSize: '1.8rem', 
                color: '#7a9b76',
                fontVariant: 'normal'
              }}>M</span>onkey
            </h1>
          </div>
        </div>
      </div>

      {/* Content area */}
      <main style={{
        backgroundColor: 'white',
        minHeight: 'calc(100vh - 60px)',
        position: 'relative',
        zIndex: 1
      }}>
        {renderTabContent()}
      </main>
    </div>
  );
}

export default App;