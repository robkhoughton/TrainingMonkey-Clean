import React from 'react';
import './YTMSpinner.css';

interface YTMSpinnerProps {
  size?: number; // Size in pixels, default 200
}

const YTMSpinner: React.FC<YTMSpinnerProps> = ({ size = 200 }) => {
  const handleImageError = (imageName: string) => {
    console.error(`Failed to load image: ${imageName}`);
  };

  return (
    <div 
      className="ytm-spinner-container" 
      style={{ width: `${size}px`, height: `${size}px` }}
    >
      <img 
        src="/static/images/compass-bg.png" 
        className="compass-bg" 
        alt="Loading Compass"
        onError={() => handleImageError('compass-bg.png')}
        onLoad={() => console.log('Compass loaded successfully')}
      />
      <img 
        src="/static/images/monkey-fg.png" 
        className="monkey-fg" 
        alt="YTM Monkey"
        onError={() => handleImageError('monkey-fg.png')}
        onLoad={() => console.log('Monkey loaded successfully')}
      />
    </div>
  );
};

export default YTMSpinner;

