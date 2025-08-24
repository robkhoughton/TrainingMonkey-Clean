// chartTheme.ts
export interface ChartTheme {
  colors: {
    primary: string;
    secondary: string;
    warning: string;
    danger: string;
    dark: string;
    accent: string;
    trimp: string;
    background: string;
    success: string; // Added for success states
  };
  lineStyles: {
    regular: {
      strokeWidth: number;
    };
    thin: {
      strokeWidth: number;
    };
    dashed: {
      strokeWidth: number;
      strokeDasharray: string;
    };
  };
  barStyles: {
    narrow: {
      width: number;
      opacity: number;
    };
    regular: {
      width: number;
      opacity: number;
    };
    wide: {
      width: number;
      opacity: number;
    };
  };
  chartSizes: {
    small: {
      height: number;
    };
    medium: {
      height: number;
    };
    large: {
      height: number;
    };
  };
  // FIXED: Reference area styles with proper opacity values
  referenceAreas: {
    optimal: {
      fillOpacity: string;
      strokeOpacity: number;
      strokeWidth: number;
      fontSize: number;
    };
    risk: {
      fillOpacity: string;
      strokeOpacity: number;
      strokeWidth: number;
      fontSize: number;
    };
    moderate: {
      fillOpacity: string;
      strokeOpacity: number;
      strokeWidth: number;
      fontSize: number;
    };
    efficient: {
      fillOpacity: string;
      strokeOpacity: number;
      strokeWidth: number;
      fontSize: number;
    };
  };
  // Add tooltip styles
  tooltip: {
    width: string;
    fontSize: number;
    labelFontSize: number;
    padding: string;
  };
}

const defaultTheme: ChartTheme = {
  colors: {
    primary: '#3498db',
    secondary: '#2ecc71',
    warning: '#f39c12',
    danger: '#c0392b',
    dark: '#2c3e50',
    accent: '#9b59b6',
    trimp: '#e84393',
    background: '#f9fafb',
    success: '#10b981', // Added for success states
  },
  lineStyles: {
    regular: {
      strokeWidth: 3,
    },
    thin: {
      strokeWidth: 2,
    },
    dashed: {
      strokeWidth: 2,
      strokeDasharray: '5 5',
    },
  },
  barStyles: {
    narrow: {
      width: 8,
      opacity: 1.0,
    },
    regular: {
      width: 24,
      opacity: 1.0,
    },
    wide: {
      width: 36,
      opacity: 1.0,
    },
  },
  chartSizes: {
    small: {
      height: 250,
    },
    medium: {
      height: 300,
    },
    large: {
      height: 400,
    },
  },
  // FIXED: Reference area styles with proper hex opacity values for Recharts
  referenceAreas: {
    optimal: {
      fillOpacity: '40',  // Hex opacity for balanced/optimal zones
      strokeOpacity: 0.6,
      strokeWidth: 2,
      fontSize: 11,
    },
    risk: {
      fillOpacity: '40',  // Hex opacity for high risk zones
      strokeOpacity: 0.4,
      strokeWidth: 1,
      fontSize: 11,
    },
    moderate: {
      fillOpacity: '40',  // Hex opacity for moderate risk zones
      strokeOpacity: 0.4,
      strokeWidth: 1,
      fontSize: 11,
    },
    efficient: {
      fillOpacity: '40',  // Hex opacity for efficient zones
      strokeOpacity: 0.4,
      strokeWidth: 1,
      fontSize: 11,
    },
  },
  // Tooltip styles
  tooltip: {
    width: '240px',
    fontSize: 12,
    labelFontSize: 14,
    padding: '12px',
  },
};

export default defaultTheme;