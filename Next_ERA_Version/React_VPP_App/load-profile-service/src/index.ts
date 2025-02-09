import express from 'express';
import { WebSocketServer } from 'ws';
import cors from 'cors';
import fs from 'fs/promises';
import path from 'path';

const app = express();
const wss = new WebSocketServer({ port: 8080 });

app.use(cors());

interface LoadProfileData {
  timestamp: number;
  baseLoad: number[];
  withDR: number[];
}

// Cache for load profile data
let loadProfileData: LoadProfileData | null = null;

// Load data from CSV file
async function loadData(): Promise<void> {
  try {
    const csvPath = path.join(__dirname, '../data/Saudi_Demand_by_Group_and_Region.csv');
    const data = await fs.readFile(csvPath, 'utf-8');
    const rows = data.split('\n').slice(1); // Skip header
    const baseLoad = rows.map(row => parseFloat(row.split(',')[1]));
    
    // Calculate DR impact (10% reduction during peak hours)
    const withDR = baseLoad.map((value: number, hour: number) => {
      const timeOfDay = hour % 24;
      const isPeakHour = timeOfDay >= 9 && timeOfDay <= 21;
      return value * (isPeakHour ? 0.9 : 1);
    });

    loadProfileData = {
      timestamp: Date.now(),
      baseLoad,
      withDR
    };
  } catch (error) {
    console.error('Error loading data:', error);
    // Fallback to generated data if file read fails
    loadProfileData = generateRandomData();
  }
}

function generateRandomData(): LoadProfileData {
  return {
    timestamp: Date.now(),
    baseLoad: Array(8760).fill(0).map(() => Math.random() * 40000),
    withDR: Array(8760).fill(0).map(() => Math.random() * 35000),
  };
}

// Initialize data
loadData();

// REST endpoint
app.get('/api/load-profile', (req, res) => {
  res.json(loadProfileData || generateRandomData());
});

// WebSocket handling
wss.on('connection', (ws) => {
  console.log('Client connected');

  // Send initial data
  if (loadProfileData) {
    ws.send(JSON.stringify(loadProfileData));
  }

  // Simulate real-time updates every minute
  const interval = setInterval(() => {
    if (ws.readyState === ws.OPEN && loadProfileData) {
      // Add small random variations to the data
      const variation = 0.05; // 5% variation
      const updatedData: LoadProfileData = {
        timestamp: Date.now(),
        baseLoad: loadProfileData.baseLoad.map((value: number) => 
          value * (1 + (Math.random() * variation - variation/2))
        ),
        withDR: loadProfileData.withDR.map((value: number) => 
          value * (1 + (Math.random() * variation - variation/2))
        )
      };
      ws.send(JSON.stringify(updatedData));
    }
  }, 60000);

  ws.on('close', () => {
    clearInterval(interval);
  });
});

app.listen(3001, () => {
  console.log('REST server running on port 3001');
});
console.log('WebSocket server running on port 8080'); 