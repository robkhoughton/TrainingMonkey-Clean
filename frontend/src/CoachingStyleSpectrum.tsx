import React, { useState, useEffect } from 'react';

interface CoachingStyleSpectrumProps {
  initialValue?: number;
  onChange?: (value: number) => void;
  disabled?: boolean;
}

const CoachingStyleSpectrum: React.FC<CoachingStyleSpectrumProps> = ({
  initialValue = 50,
  onChange = () => {},
  disabled = false
}) => {
  const [spectrumValue, setSpectrumValue] = useState(initialValue);

  useEffect(() => {
    setSpectrumValue(initialValue);
  }, [initialValue]);

  // Style definitions for each range
  const getStyleConfig = (value: number) => {
    if (value <= 25) {
      return {
        style: 'casual',
        label: 'Casual',
        description: 'Relaxed, friendly guidance',
        color: '#10B981'
      };
    } else if (value <= 50) {
      return {
        style: 'supportive',
        label: 'Supportive',
        description: 'Encouraging with gentle guidance',
        color: '#3B82F6'
      };
    } else if (value <= 75) {
      return {
        style: 'motivational',
        label: 'Motivational',
        description: 'Goal-oriented with push for improvement',
        color: '#F59E0B'
      };
    } else {
      return {
        style: 'analytical',
        label: 'Analytical',
        description: 'Technical, data-driven coaching',
        color: '#8B5CF6'
      };
    }
  };

  const currentStyle = getStyleConfig(spectrumValue);

  const handleSliderChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const newValue = parseInt(e.target.value);
    setSpectrumValue(newValue);
    onChange(newValue);
  };

  const handleMarkerClick = (value: number) => {
    setSpectrumValue(value);
    onChange(value);
  };

  return (
    <div style={{ width: '100%' }}>
      {/* Current Selection Display */}
      <div style={{
        marginBottom: '1rem',
        padding: '0.75rem',
        backgroundColor: '#f8fafc',
        borderRadius: '0.375rem',
        border: '2px solid',
        borderColor: currentStyle.color,
        transition: 'border-color 0.3s ease'
      }}>
        <div style={{
          textAlign: 'center',
          fontWeight: '600',
          color: '#374151',
          fontSize: '0.9rem',
          marginBottom: '0.25rem'
        }}>
          {currentStyle.label}
        </div>
        <div style={{
          textAlign: 'center',
          color: '#6b7280',
          fontSize: '0.8rem'
        }}>
          {currentStyle.description}
        </div>
      </div>

      {/* Spectrum Slider */}
      <div style={{ position: 'relative', marginBottom: '1rem' }}>
        {/* Gradient Background */}
        <div style={{
          height: '8px',
          borderRadius: '4px',
          background: 'linear-gradient(to right, #10B981 0%, #3B82F6 33%, #F59E0B 66%, #8B5CF6 100%)',
          marginBottom: '0.5rem'
        }}></div>

        {/* Slider Input */}
        <input
          type="range"
          min="0"
          max="100"
          value={spectrumValue}
          onChange={handleSliderChange}
          disabled={disabled}
          style={{
            position: 'absolute',
            top: '0',
            width: '100%',
            height: '8px',
            opacity: 0,
            cursor: disabled ? 'not-allowed' : 'pointer',
            margin: 0
          }}
        />

        {/* Custom Slider Thumb */}
        <div
          style={{
            position: 'absolute',
            top: '-4px',
            left: `calc(${spectrumValue}% - 8px)`,
            width: '16px',
            height: '16px',
            borderRadius: '50%',
            backgroundColor: currentStyle.color,
            border: '2px solid white',
            boxShadow: '0 2px 4px rgba(0,0,0,0.2)',
            cursor: disabled ? 'not-allowed' : 'pointer',
            transition: 'left 0.2s ease, background-color 0.3s ease',
            pointerEvents: 'none'
          }}
        ></div>

        {/* Labels */}
        <div style={{
          display: 'flex',
          justifyContent: 'space-between',
          marginTop: '1.5rem',
          fontSize: '0.75rem',
          fontWeight: '500'
        }}>
          <button
            onClick={() => handleMarkerClick(12)}
            disabled={disabled}
            style={{
              background: 'none',
              border: 'none',
              cursor: disabled ? 'not-allowed' : 'pointer',
              padding: '0.25rem',
              borderRadius: '0.25rem',
              transition: 'background-color 0.2s ease',
              backgroundColor: spectrumValue <= 25 ? '#10B981' : 'transparent',
              color: spectrumValue <= 25 ? 'white' : '#6b7280'
            }}
          >
            Casual
          </button>

          <button
            onClick={() => handleMarkerClick(37)}
            disabled={disabled}
            style={{
              background: 'none',
              border: 'none',
              cursor: disabled ? 'not-allowed' : 'pointer',
              padding: '0.25rem',
              borderRadius: '0.25rem',
              transition: 'background-color 0.2s ease',
              backgroundColor: spectrumValue > 25 && spectrumValue <= 50 ? '#3B82F6' : 'transparent',
              color: spectrumValue > 25 && spectrumValue <= 50 ? 'white' : '#6b7280'
            }}
          >
            Supportive
          </button>

          <button
            onClick={() => handleMarkerClick(62)}
            disabled={disabled}
            style={{
              background: 'none',
              border: 'none',
              cursor: disabled ? 'not-allowed' : 'pointer',
              padding: '0.25rem',
              borderRadius: '0.25rem',
              transition: 'background-color 0.2s ease',
              backgroundColor: spectrumValue > 50 && spectrumValue <= 75 ? '#F59E0B' : 'transparent',
              color: spectrumValue > 50 && spectrumValue <= 75 ? 'white' : '#6b7280'
            }}
          >
            Motivational
          </button>

          <button
            onClick={() => handleMarkerClick(87)}
            disabled={disabled}
            style={{
              background: 'none',
              border: 'none',
              cursor: disabled ? 'not-allowed' : 'pointer',
              padding: '0.25rem',
              borderRadius: '0.25rem',
              transition: 'background-color 0.2s ease',
              backgroundColor: spectrumValue > 75 ? '#8B5CF6' : 'transparent',
              color: spectrumValue > 75 ? 'white' : '#6b7280'
            }}
          >
            Analytical
          </button>
        </div>
      </div>

      {/* Sample Message Preview */}
      <div style={{
        backgroundColor: 'white',
        border: '1px solid #e5e7eb',
        borderRadius: '0.375rem',
        padding: '0.75rem',
        marginTop: '1rem'
      }}>
        <div style={{
          fontSize: '0.8rem',
          fontWeight: '500',
          color: '#374151',
          marginBottom: '0.5rem'
        }}>
          Sample AI Message:
        </div>
        <div style={{
          fontSize: '0.75rem',
          color: '#6b7280',
          fontStyle: 'italic',
          lineHeight: '1.4'
        }}>
          {getSampleMessage(currentStyle.style)}
        </div>
      </div>
    </div>
  );
};

// Sample messages for each style
const getSampleMessage = (style: string) => {
  const samples = {
    casual: "Nice job getting out there today! That 5-mile run looked really solid. How did it feel? Remember, consistency is what really builds fitness over time.",

    supportive: "Excellent work completing your training today! You're building great endurance with that 5-mile effort. Your body is adapting well to the consistent load. Keep up this fantastic progress!",

    motivational: "Strong execution on today's 5-mile run! You're hitting your targets consistently. Time to challenge yourself - let's aim for a slightly longer effort this weekend. Your fitness is trending upward!",

    analytical: "Training Analysis: 5.0mi completed at avg HR 145bpm (Zone 2). TRIMP: 68. ACWR: 1.1 (optimal range). Current divergence: +0.04 indicates efficient adaptation. Recommend maintaining current volume with 15% intensity increase next week."
  };
  return samples[style as keyof typeof samples] || samples.supportive;
};

export default CoachingStyleSpectrum;