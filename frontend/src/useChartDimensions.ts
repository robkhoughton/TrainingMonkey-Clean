// Update to useChartDimensions.ts
import { useState, useEffect } from 'react';
import defaultTheme, { ChartTheme } from './chartTheme';

interface ChartDimensions {
  width: number;
  height: number;
  majorTickInterval: number;  // Renamed from tickInterval
  showMinorTicks: boolean;    // Whether to show minor ticks
  minorTickHeight: number;    // Height of minor ticks
  majorTickHeight: number;    // Height of major ticks
  barSize: number;
}

export function useChartDimensions(
  dateRange: string,
  theme: ChartTheme = defaultTheme
): ChartDimensions {
  const [dimensions, setDimensions] = useState<ChartDimensions>({
    width: 1000,
    height: 300,
    majorTickInterval: 2,
    showMinorTicks: true,
    minorTickHeight: 3,
    majorTickHeight: 6,
    barSize: 8,
  });

  useEffect(() => {
    const days = parseInt(dateRange, 10);
    const baseWidth = Math.min(window.innerWidth - 48, 1200);

    let width = baseWidth;
    if (days <= 7) width = Math.min(baseWidth, 800);
    if (days <= 14) width = Math.min(baseWidth, 900);

    let height = theme.chartSizes.medium.height;
    if (days >= 60) height = theme.chartSizes.large.height;
    if (days <= 7) height = theme.chartSizes.small.height;

    // Determine major tick interval based on date range
    let majorTickInterval = 0;  // Show all ticks by default
    if (days > 14 && days <= 30) majorTickInterval = 1;  // Every other day
    if (days > 30 && days <= 60) majorTickInterval = 3;  // Every fourth day
    if (days > 60) majorTickInterval = 7;  // Weekly

    // Show minor ticks for reasonable date ranges
    const showMinorTicks = days <= 60;

    // Adjust tick height based on date range
    const minorTickHeight = days <= 14 ? 4 : 3;
    const majorTickHeight = days <= 14 ? 7 : 6;

    let barSize = theme.barStyles.regular.width;
    if (days > 30) barSize = theme.barStyles.narrow.width;
    if (days <= 7) barSize = theme.barStyles.wide.width;

    setDimensions({
      width,
      height,
      majorTickInterval,
      showMinorTicks,
      minorTickHeight,
      majorTickHeight,
      barSize,
    });
  }, [dateRange, theme]);

  // Add window resize listener
  useEffect(() => {
    const handleResize = () => {
      const days = parseInt(dateRange, 10);
      const baseWidth = Math.min(window.innerWidth - 48, 1200);

      let width = baseWidth;
      if (days <= 7) width = Math.min(baseWidth, 800);
      if (days <= 14) width = Math.min(baseWidth, 900);

      setDimensions(prev => ({
        ...prev,
        width,
      }));
    };

    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, [dateRange]);

  return dimensions;
}