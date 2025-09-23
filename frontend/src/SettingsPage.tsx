import React, { useEffect } from 'react';

export const SettingsPage: React.FC = () => {
  // Redirect to the new settings pages
  useEffect(() => {
    // Get the current URL to determine which settings page to redirect to
    const urlParams = new URLSearchParams(window.location.search);
    const tab = urlParams.get('tab');
    
    let redirectPath = '/settings/profile'; // default
    
    switch (tab) {
      case 'profile':
        redirectPath = '/settings/profile';
        break;
      case 'hrzones':
        redirectPath = '/settings/hrzones';
        break;
      case 'training':
        redirectPath = '/settings/training';
        break;
      case 'alerts':
      case 'coaching':
        redirectPath = '/settings/coaching';
        break;
      case 'acwr':
        redirectPath = '/settings/acwr';
        break;
      default:
        redirectPath = '/settings/profile';
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