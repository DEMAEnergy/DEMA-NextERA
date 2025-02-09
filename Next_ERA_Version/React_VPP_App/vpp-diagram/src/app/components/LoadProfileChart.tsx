import { useEffect, useState, useRef, useCallback, useMemo } from 'react';
import { Line } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  TimeScale,
} from 'chart.js';
import 'chartjs-adapter-date-fns';
import { parse } from 'papaparse';
import { loadProfileService, LoadProfileData } from '../services/loadProfileService';

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  TimeScale
);

interface LoadProfileChartProps {
  currentHour: number;
}

// Add this utility function at the top
const generateDREvents = (baseLoad: number[]) => {
  const totalHours = baseLoad.length; // 8760
  const targetDRHours = Math.floor(totalHours * 0.1); // 10% of the year
  const events: { start: number; end: number }[] = [];
  
  // Find peak load periods
  const loadWithIndex = baseLoad.map((load, index) => ({ load, index }));
  const sortedPeriods = loadWithIndex.sort((a, b) => b.load - a.load);
  
  // Take top 10% hours and group them into events
  const topHours = new Set(sortedPeriods.slice(0, targetDRHours).map(p => p.index));
  
  let currentEvent = null;
  for (let hour = 0; hour < totalHours; hour++) {
    if (topHours.has(hour)) {
      if (!currentEvent) {
        currentEvent = { start: hour, end: hour };
      } else {
        currentEvent.end = hour;
      }
    } else if (currentEvent) {
      events.push(currentEvent);
      currentEvent = null;
    }
  }
  
  return events;
};

const LoadProfileChart = ({ currentHour }: LoadProfileChartProps) => {
  const [chartData, setChartData] = useState<any>(null);
  const [maxLoad, setMaxLoad] = useState<number>(0);
  const chartRef = useRef(null);
  const detailChartRef = useRef(null);

  // Add month names for x-axis
  const monthNames = [
    'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
    'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'
  ];

  // Memoize chart data processing
  const processChartData = useCallback((baseLoad: number[]) => {
    const drEvents = generateDREvents(baseLoad);
    const withDR = baseLoad.map((value, hour) => {
      const isInDREvent = drEvents.some(event => 
        hour >= event.start && hour <= event.end
      );
      return isInDREvent ? value * 0.9 : value;
    });
    return { baseLoad, withDR, drEvents };
  }, []);

  // Subscribe to real-time updates
  useEffect(() => {
    // Initial data load
    loadProfileService.fetchLatestData()
      .then(initialData => {
        updateChartData(initialData);
      })
      .catch(error => {
        console.error('Error loading initial data:', error);
      });

    // Subscribe to real-time updates
    const unsubscribe = loadProfileService.subscribe(newData => {
      updateChartData(newData);
    });

    // Cleanup subscription
    return () => {
      unsubscribe();
    };
  }, []);

  // Update chart data when new data arrives
  const updateChartData = useCallback((data: LoadProfileData) => {
    const labels = Array.from({ length: data.baseLoad.length }, (_, i) => i);
    
    setChartData({
      labels,
      datasets: [
        {
          label: 'Base Load',
          data: data.baseLoad,
          borderColor: 'rgb(75, 192, 192)',
          backgroundColor: 'rgba(75, 192, 192, 0.1)',
          tension: 0.1,
          fill: true,
        },
        {
          label: 'With DR',
          data: data.withDR,
          borderColor: 'rgb(255, 99, 132)',
          backgroundColor: 'rgba(255, 99, 132, 0.1)',
          tension: 0.1,
          fill: true,
        }
      ],
    });
  }, []);

  // Update charts when currentHour changes
  useEffect(() => {
    if (chartRef.current) {
      chartRef.current.update('none'); // Use 'none' mode for better performance
    }
    if (detailChartRef.current) {
      detailChartRef.current.update('none');
    }
  }, [currentHour]);

  // Memoize chart options
  const yearChartOptions = useMemo(() => ({
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: 'top' as const,
      },
      title: {
        display: true,
        text: 'Annual System Load Profile',
      },
      tooltip: {
        mode: 'index' as const,
        intersect: false,
        callbacks: {
          title: (context) => {
            const hour = parseInt(context[0].label);
            const month = Math.floor(hour / 730);
            const dayOfMonth = Math.floor((hour % 730) / 24) + 1;
            const hourOfDay = hour % 24;
            return `${monthNames[month]} ${dayOfMonth}, Hour ${hourOfDay}`;
          },
          label: (context) => `${context.dataset.label}: ${parseInt(context.parsed.y).toLocaleString()} MW`,
        },
      },
    },
    scales: {
      x: {
        type: 'linear' as const,
        title: {
          display: true,
          text: 'Month',
        },
        ticks: {
          stepSize: 730,
          callback: (value) => monthNames[Math.floor(value / 730)],
        },
      },
      y: {
        type: 'linear' as const,
        title: {
          display: true,
          text: 'Load (MW)',
        },
        min: 0,
      },
    },
  }), []);

  const detailChartOptions = useMemo(() => ({
    ...yearChartOptions,
    plugins: {
      ...yearChartOptions.plugins,
      title: {
        display: true,
        text: '48-Hour Detailed View',
      },
    },
    scales: {
      x: {
        type: 'linear' as const,
        min: Math.max(0, currentHour - 24),
        max: Math.min(8760, currentHour + 24),
        title: {
          display: true,
          text: 'Hour',
        },
        ticks: {
          stepSize: 4,
          callback: (value) => {
            const hour = value % 24;
            return `${hour}:00`;
          },
        },
      },
      y: {
        type: 'linear' as const,
        title: {
          display: true,
          text: 'Load (MW)',
        },
        min: 0,
      },
    },
  }), [currentHour]);

  const timeIndicatorPlugin = {
    id: 'timeIndicator',
    beforeDraw: (chart) => {
      if (!chart || !chart.scales?.x) return;
      
      const ctx = chart.ctx;
      const xAxis = chart.scales.x;
      const yAxis = chart.scales.y;
      const x = xAxis.getPixelForValue(currentHour);
      
      ctx.save();
      ctx.beginPath();
      ctx.moveTo(x, yAxis.top);
      ctx.lineTo(x, yAxis.bottom);
      ctx.lineWidth = 2;
      ctx.strokeStyle = 'rgba(255, 0, 0, 0.75)';
      ctx.stroke();
      
      // Add current time label
      ctx.textAlign = 'center';
      ctx.fillStyle = 'rgba(255, 0, 0, 0.75)';
      const hour = currentHour % 24;
      ctx.fillText(`Current Hour: ${hour}:00`, x, yAxis.top - 10);
      
      ctx.restore();
    }
  };

  return (
    <div className="flex flex-col gap-4 p-4 bg-white border-t border-gray-200">
      {/* Full Year Chart */}
      <div className="h-48">
        {chartData && (
          <Line 
            ref={chartRef}
            data={chartData} 
            options={yearChartOptions}
            plugins={[timeIndicatorPlugin]}
          />
        )}
      </div>

      {/* Detailed 48-hour Chart */}
      <div className="h-48">
        {chartData && (
          <Line 
            ref={detailChartRef}
            data={chartData} 
            options={detailChartOptions}
            plugins={[timeIndicatorPlugin]}
          />
        )}
      </div>
    </div>
  );
};

export default LoadProfileChart; 