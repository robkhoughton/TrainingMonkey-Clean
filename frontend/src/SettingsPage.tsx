import React, { useEffect } from 'react';
import { usePagePerformanceMonitoring } from './usePerformanceMonitoring';

export const SettingsPage: React.FC = () => {
  // Performance monitoring
  usePagePerformanceMonitoring('settings');

  // Redirect to the new settings pages
  useEffect(() => {
    // Get the current URL to determine which settings page to redirect to
    const urlParams = new URLSearchParams(window.location.search);
    const tab = urlParams.get('tab');
    
    let redirectPath = '/settings/hrzones'; // default

    switch (tab) {
      case 'hrzones':
        redirectPath = '/settings/hrzones';
        break;
      case 'acwr':
        redirectPath = '/settings/acwr';
        break;
      case 'integrations':
        redirectPath = '/settings/integrations';
        break;
      default:
        redirectPath = '/settings/hrzones';
    }
    
    // Redirect to the new settings page
    window.location.href = redirectPath;
  }, []);

  // Show loading while redirecting
  return (
          <div style={{
            display: 'flex',
            justifyContent: 'center',
                alignItems: 'center',
      height: '100vh',
      fontSize: '1.2rem',
      color: '#6b7280'
    }}>
      Redirecting to settings...
    </div>
  );
};

export default SettingsPage;