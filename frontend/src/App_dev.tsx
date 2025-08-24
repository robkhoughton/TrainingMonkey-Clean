// Temporary modification for frontend/src/App.tsx

import React from 'react';
import BannerTest from './BannerTest';
// import TrainingLoadDashboard from './TrainingLoadDashboard'; // Temporarily commented out

function App() {
  return (
    <div className="App">
      {/* Temporarily using BannerTest for isolated development */}
      <BannerTest />

      {/* Original dashboard - temporarily commented out */}
      {/* <TrainingLoadDashboard /> */}
    </div>
  );
}

export default App;