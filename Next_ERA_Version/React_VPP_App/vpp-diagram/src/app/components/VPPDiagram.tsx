"use client"; // Ensure it's a Client Component

import { useEffect, useState, useRef, useCallback, useMemo } from "react";
import ReactFlow, {
  ReactFlowProvider,
  type Node,
  type Edge,
  Background,
  Controls,
  ConnectionMode,
  MarkerType,
} from "reactflow";
import "reactflow/dist/style.css";
import elementsData from '../data/elements.json';
import demandResponseEvents from '../data/Demand_Response_Events.json';
import dynamic from 'next/dynamic';
import { SystemState, generateRandomSystemState, updateSystemForDR } from '../utils/systemState';
import LoadProfileChart from './LoadProfileChart';

// Create a client-only version of ReactFlow
const ReactFlowProvider = dynamic(
  () => import('reactflow').then(mod => mod.ReactFlowProvider),
  { ssr: false }
);

// Prevent SSR for the main component
const VPPDiagram = dynamic(() => Promise.resolve(VPPDiagramComponent), {
  ssr: false
});

// ✅ Header Component for Top Ribbon
const Header = dynamic(() => Promise.resolve(({ 
  isRunning, 
  onStart, 
  onStop, 
  onRestart,
  currentHour,
  onJumpToHour 
}) => (
  <div className="bg-blue-900 text-white flex items-center justify-between px-6 py-3">
    <div className="flex items-center gap-3">
      <img src="/logo.png" alt="DEMA Energy Logo" className="h-8" />
      <span className="text-lg font-bold">DEMA Energy</span>
    </div>
    <div className="flex items-center gap-4">
      {/* Add Simulation Hour display */}
      <div className="text-sm bg-blue-800 px-3 py-1 rounded">
        Simulation Hour: {currentHour}
      </div>
      
      {/* Jump to Hour controls */}
      <div className="flex items-center gap-2">
        <input
          type="number"
          min="0"
          max="8760"
          placeholder="Jump to hour..."
          className="px-2 py-1 rounded text-black text-sm w-32"
          onChange={(e) => onJumpToHour(parseInt(e.target.value))}
        />
        <button
          onClick={() => onJumpToHour()}
          className="px-3 py-1 rounded bg-yellow-500 hover:bg-yellow-600 text-sm"
        >
          Jump
        </button>
      </div>

      {/* Control buttons */}
      <div className="flex gap-2">
        <button
          onClick={onStart}
          disabled={isRunning}
          className={`px-4 py-1 rounded ${
            isRunning ? 'bg-gray-500' : 'bg-green-500 hover:bg-green-600'
          }`}
        >
          Start
        </button>
        <button
          onClick={onStop}
          disabled={!isRunning}
          className={`px-4 py-1 rounded ${
            !isRunning ? 'bg-gray-500' : 'bg-red-500 hover:bg-red-600'
          }`}
        >
          Stop
        </button>
        <button
          onClick={onRestart}
          className="px-4 py-1 rounded bg-blue-500 hover:bg-blue-600"
        >
          Restart
        </button>
      </div>
    </div>
    <span className="text-lg font-semibold">Virtual Power Plant</span>
  </div>
)), { ssr: false });

// **Standardized Resource Style**
const resourceStyle = {
  background: "rgba(46, 139, 87, 0.1)",
  border: "2px solid #2e8b57",
  borderRadius: "10px",
  padding: "10px",
  width: "180px",
  fontSize: "12px",
  textAlign: "center",
};

type ResourceData = {
  powerDraw: number;
  target: number;
  controllable: boolean;
  position: { x: number; y: number };
  monitoring?: { [key: string]: any };
  controls?: { [key: string]: any };
};

type ResourcesData = {
  [key: string]: ResourceData;
};

// Add these utility functions at the top level
const getDeviationColor = (deviationPercent: number) => {
  if (Math.abs(deviationPercent) <= 5) return '#22c55e'; // green
  if (Math.abs(deviationPercent) <= 10) return '#eab308'; // yellow
  return '#ef4444'; // red
};

const formatPower = (watts: number) => {
  if (Math.abs(watts) >= 1000) {
    return `${(watts / 1000).toFixed(1)} kW`;
  }
  return `${Math.round(watts)} W`;
};

// Add new components for the control panels
const ControlSlider = ({ label, value, min, max, unit, onChange }) => (
  <div className="flex flex-col gap-1">
    <div className="flex justify-between">
      <span className="text-xs font-semibold">{label}</span>
      <span className="font-mono text-xs">{value}{unit}</span>
    </div>
    <input 
      type="range" 
      min={min} 
      max={max} 
      value={value}
      onChange={onChange}
      className="w-full h-2 rounded-lg appearance-none cursor-pointer bg-gray-200"
    />
  </div>
);

const ToggleSwitch = ({ label, value, onChange }) => (
  <div className="flex items-center justify-between">
    <span className="text-xs font-semibold">{label}</span>
    <button 
      onClick={onChange}
      className={`px-3 py-1 rounded ${
        value ? 'bg-green-500 text-white' : 'bg-gray-300'
      }`}
    >
      {value ? 'ON' : 'OFF'}
    </button>
  </div>
);

// Update the title formatting function
const formatTitle = (id: string) => {
  switch (id.toLowerCase()) {
    case 'ev': return 'EV Charging';
    case 'hvac': return 'HVAC System';
    default: return id.charAt(0).toUpperCase() + id.slice(1);
  }
};

// Update the label formatting function
const formatLabel = (key: string) => {
  const specialCases: { [key: string]: string } = {
    'ev': 'EV',
    'hvac': 'HVAC',
    'preCooling': 'Pre-Cooling',
    'stateOfCharge': 'State of Charge',
    'chargingRate': 'Charging Rate',
    'chargingLimit': 'Charging Limit',
    'smartCharging': 'Smart Charging',
    'currentTemp': 'Current Temperature',
    'avgChargeLevel': 'Average Charge Level',
    'connectedVehicles': 'Connected Vehicles'
  };

  if (specialCases[key]) {
    return specialCases[key];
  }

  return key
    .replace(/([A-Z])/g, ' $1')
    .replace(/^./, str => str.toUpperCase())
    .trim();
};

// Add new node rendering functions
const renderMonitoringValues = (monitoring: any) => (
  <div className="bg-gray-50/80 p-2 rounded">
    {Object.entries(monitoring).map(([key, value]) => (
      <div key={key} className="flex justify-between text-xs mb-1">
        <span className="font-semibold">{formatLabel(key)}:</span>
        <span className="font-mono">{value}</span>
      </div>
    ))}
  </div>
);

const renderControls = (controls: any) => (
  <div className="flex flex-col gap-2">
    {Object.entries(controls).map(([key, control]: [string, any]) => (
      <div key={key} className="bg-gray-50/80 p-2 rounded">
        {control.options ? (
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold">{formatLabel(key)}</span>
            <select 
              className="text-xs p-1 rounded border border-gray-300"
              value={control.value}
              onChange={() => {/* Add control logic */}}
            >
              {control.options.map((option: string) => (
                <option key={option} value={option}>
                  {formatLabel(option)}
                </option>
              ))}
            </select>
          </div>
        ) : (
          <ControlSlider
            label={formatLabel(key)}
            value={control.value}
            min={control.min}
            max={control.max}
            unit={control.unit}
            onChange={() => {/* Add control logic */}}
          />
        )}
      </div>
    ))}
  </div>
);

// Add new rendering function for combined sections
const renderCombinedSections = (sections: any) => (
  <div className="flex flex-col gap-4">
    {Object.entries(sections).map(([key, section]: [string, any]) => (
      <div key={key} className="flex flex-col gap-2">
        <div className="text-sm font-bold text-blue-900 border-b border-blue-200 pb-1">
          {section.label}
        </div>
        
        {/* Monitoring Section */}
        <div className="bg-white/80 rounded p-2">
          <div className="text-xs font-bold text-gray-600 mb-2">MONITORING</div>
          {renderMonitoringValues(section.monitoring)}
        </div>

        {/* Controls Section (if available) */}
        {section.controls && (
          <div className="bg-white/80 rounded p-2">
            <div className="text-xs font-bold text-gray-600 mb-2">CONTROL</div>
            {renderControls(section.controls)}
          </div>
        )}
      </div>
    ))}
  </div>
);

// Add a utility function for consistent time formatting
const formatEventTime = (date: Date) => {
  return date.toLocaleTimeString('en-US', {
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
    hour12: false
  });
};

// Add this type for node data
type NodeData = {
  label: string;
  sections?: {
    [key: string]: {
      label: string;
      monitoring?: {
        [key: string]: string | number;
      };
      controls?: {
        [key: string]: any;
      };
    };
  };
};

// Add new animation styles at the top
const pulseAnimation = `
  @keyframes pulse {
    0% { opacity: 0.6; }
    50% { opacity: 1; }
    100% { opacity: 0.6; }
  }
`;

const glowAnimation = `
  @keyframes glow {
    0% { box-shadow: 0 0 5px rgba(245, 158, 11, 0.5); }
    50% { box-shadow: 0 0 20px rgba(245, 158, 11, 0.8); }
    100% { box-shadow: 0 0 5px rgba(245, 158, 11, 0.5); }
  }
`;

// Add style tag to component
const StyleTag = () => (
  <style>
    {pulseAnimation}
    {glowAnimation}
  </style>
);

// Add this new component for the Grid Operations display
const GridOperationsDisplay = ({ systemState }) => {
  const isDRActive = systemState.transmission.dispatchSignal === "Reduction";
  
  console.log("GridOperationsDisplay rendering with state:", {
    voltage: systemState.transmission.voltage,
    frequency: systemState.transmission.frequency,
    loadFlow: systemState.transmission.loadFlow
  });

  useEffect(() => {
    console.log('Grid Operations Display - Current frequency:', systemState.transmission.frequency);
  }, [systemState.transmission.frequency]);

  return (
    <div className="flex flex-col gap-4">
      {/* DR Status Banner */}
      <div className={`
        ${isDRActive ? 'bg-orange-500' : 'bg-green-500'} 
        text-white px-4 py-2 rounded-t-lg -mx-3 -mt-3 font-bold text-center
        transition-all duration-300
      `}>
        Demand Response Status: {isDRActive ? 'ACTIVE' : 'INACTIVE'}
      </div>

      {/* Transmission Network Section */}
      <div className="bg-blue-50 rounded-lg p-4">
        <h3 className="text-blue-900 font-bold mb-2">Transmission Network</h3>
        <div className="bg-white rounded p-3">
          <div className="text-sm font-bold mb-2">MONITORING</div>
          <div className="grid gap-2">
            <div className="flex justify-between items-center">
              <span className="text-gray-600">Voltage:</span>
              <span className={`font-mono ${
                Math.abs(systemState.transmission.voltage - 132) > 2 ? 'text-red-600' : 'text-blue-700'
              }`}>
                {systemState.transmission.voltage.toFixed(2)} kV
              </span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-gray-600">Frequency:</span>
              <span className={`font-mono ${
                Math.abs(systemState.transmission.frequency - 50) > 0.03 ? 'text-red-600' : 'text-blue-700'
              }`}>
                {systemState.transmission.frequency.toFixed(3)} Hz
              </span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-gray-600">Load Flow:</span>
              <span className="font-mono text-blue-700">
                {systemState.transmission.loadFlow.toFixed(1)} MW
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* Grid Dispatch Section */}
      <div className="bg-blue-50 rounded-lg p-4">
        <h3 className="text-blue-900 font-bold mb-2">Grid Dispatch</h3>
        <div className="bg-white rounded p-3">
          <div className="text-sm font-bold mb-2">MONITORING</div>
          <div className="grid gap-2">
            <div className="flex justify-between items-center">
              <span className="text-gray-600">Dispatch Signal:</span>
              <span className={`font-mono ${isDRActive ? 'text-orange-600 font-bold' : 'text-blue-700'}`}>
                {systemState.transmission.dispatchSignal}
              </span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-gray-600">Requested Power:</span>
              <span className={`font-mono ${isDRActive ? 'text-orange-600 font-bold' : 'text-blue-700'}`}>
                {systemState.transmission.requestedPower.toFixed(1)} MW
              </span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-gray-600">Event Duration:</span>
              <span className={`font-mono ${isDRActive ? 'text-orange-600 font-bold' : 'text-blue-700'}`}>
                {isDRActive ? `${systemState.transmission.drEventStatus.duration} hours` : 'N/A'}
              </span>
            </div>
          </div>
        </div>

        {/* Control Section */}
        <div className="mt-3">
          <div className="text-sm font-bold mb-2">CONTROL</div>
          <div className="grid gap-3">
            <div className="flex justify-between items-center">
              <span className="text-gray-600">Demand Response:</span>
              <select 
                className={`px-2 py-1 rounded ${isDRActive ? 'bg-orange-100 border-orange-500' : 'bg-gray-100'}`}
                value={isDRActive ? 'active' : 'inactive'}
                disabled={true}
              >
                <option value="active">Active</option>
                <option value="inactive">Inactive</option>
              </select>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-gray-600">Response Type:</span>
              <select 
                className={`px-2 py-1 rounded ${isDRActive ? 'bg-orange-100 border-orange-500' : 'bg-gray-100'}`}
                value="emergency"
                disabled={true}
              >
                <option value="emergency">Emergency</option>
                <option value="economic">Economic</option>
                <option value="planned">Planned</option>
              </select>
            </div>
            <div className="flex flex-col gap-1">
              <span className="text-gray-600">Target Reduction:</span>
              <input 
                type="range" 
                min="0" 
                max="5" 
                step="0.1"
                value={Math.abs(systemState.transmission.requestedPower)}
                disabled={true}
                className="w-full"
              />
              <div className="flex justify-between text-xs text-gray-500">
                <span>0 MW</span>
                <span>{Math.abs(systemState.transmission.requestedPower).toFixed(1)} MW</span>
                <span>5 MW</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

function VPPDiagramComponent() {
  const [resourceData, setResourceData] = useState<ResourcesData>({
    solar: {
      powerDraw: 1200,
      target: 1500,
      controllable: false,
      position: elementsData.hierarchy.level4_resources.solar.position,
      controls: {
        curtailment: {
          value: 0,
          min: 0,
          max: 100,
          unit: "%"
        }
      }
    },
    wind: {
      powerDraw: 3000,
      target: 3200,
      controllable: true,
      position: elementsData.hierarchy.level4_resources.wind.position,
      controls: {
        curtailment: {
          value: 0,
          min: 0,
          max: 100,
          unit: "%"
        }
      }
    },
    battery: {
      powerDraw: 500,
      target: 600,
      controllable: true,
      position: elementsData.hierarchy.level4_resources.battery.position,
      controls: {
        chargingRate: {
          value: 50,
          min: 0,
          max: 100,
          unit: "%"
        },
        stateOfCharge: {
          value: 75,
          min: 20,
          max: 90,
          unit: "%"
        }
      }
    },
    hvac: {
      powerDraw: 8000,
      target: 7500,
      controllable: true,
      position: elementsData.hierarchy.level4_resources.hvac.position,
      controls: {
        temperature: {
          value: 22,
          min: 20,
          max: 26,
          unit: "°C"
        },
        preCooling: {
          value: false,
          schedule: "14:00-17:00"
        }
      },
      monitoring: {
        currentTemp: 22.5,
        humidity: 45,
        occupancy: true
      }
    },
    ev: {
      powerDraw: 2500,
      target: 2300,
      controllable: true,
      position: elementsData.hierarchy.level4_resources.ev.position,
      controls: {
        chargingLimit: {
          value: 7.4,
          min: 3.7,
          max: 11,
          unit: "kW"
        },
        smartCharging: {
          value: true,
          schedule: "22:00-06:00"
        }
      },
      monitoring: {
        connectedVehicles: 3,
        avgChargeLevel: 65
      }
    }
  });
  const [eventLog, setEventLog] = useState<string[]>([]);
  const [isRunning, setIsRunning] = useState(false);
  const [currentHour, setCurrentHour] = useState(0);
  const simulationInterval = useRef(null);
  const [jumpToHourValue, setJumpToHourValue] = useState<number | null>(null);
  const [hasError, setHasError] = useState(false);
  const [systemState, setSystemState] = useState<SystemState>(() => {
    console.log("Initializing system state");
    const initialState = generateRandomSystemState();
    console.log("Initial state:", initialState);
    return initialState;
  });
  const [allNodes, setAllNodes] = useState<Node[]>([]);

  // **Simulate Data Updates Every 5 Seconds**
  useEffect(() => {
    const interval = setInterval(() => {
      if (!isRunning) {
        setSystemState(prevState => {
          const newState = generateRandomSystemState();
          // Preserve DR-related states if active
          if (prevState.transmission.dispatchSignal === "Reduction") {
            return {
              ...newState,
              transmission: prevState.transmission,
              vpp: prevState.vpp,
              resources: prevState.resources,
            };
          }
          return newState;
        });
      }
    }, 5000);
    return () => clearInterval(interval);
  }, [isRunning]);

  // **Helper to Compute Deviation**
  const getResourceDeviation = (id: string) => {
    const { powerDraw, target } = resourceData[id];
    const deviationValue = powerDraw - target;
    const deviationPercent = ((deviationValue / target) * 100).toFixed(1);
    return { deviationValue, deviationPercent };
  };

  // **Generate Resource Nodes**
  const resourceNodes: Node[] = Object.entries(resourceData).map(([id, data]) => {
    const { deviationValue, deviationPercent } = getResourceDeviation(id);
    const deviationPercentNum = parseFloat(deviationPercent);
    
    return {
      id,
      type: "default",
      data: {
        label: (
          <div className="flex flex-col gap-2">
            {/* Title Bar */}
            <div className="bg-blue-900 text-white py-1 px-2 rounded-t-lg font-bold text-center -mt-2.5 -mx-2.5 mb-1">
              {formatTitle(id)}
            </div>

            {/* Monitoring Panel */}
            <div className="flex flex-col gap-2">
              <div className="text-xs font-bold text-gray-600 mb-1">MONITORING</div>
              
              {/* Power Reading */}
              <div className="grid grid-cols-2 gap-1">
                <div className="text-xs font-semibold bg-gray-100 p-1 rounded">Power Draw</div>
                <div className="bg-black text-green-400 font-mono p-1 rounded text-right">
                  {formatPower(data.powerDraw)}
                </div>
              </div>

              {/* Target Reading */}
              <div className="grid grid-cols-2 gap-1">
                <div className="text-xs font-semibold bg-gray-100 p-1 rounded">Target</div>
                <div className="bg-gray-700 text-white font-mono p-1 rounded text-right">
                  {formatPower(data.target)}
                </div>
              </div>

              {/* Deviation Box */}
              <div className="border-2 rounded p-1" style={{ borderColor: getDeviationColor(deviationPercentNum) }}>
                <div className="text-xs font-semibold mb-1">Deviation</div>
                <div className="grid grid-cols-2 gap-1 text-sm">
                  <div className="font-mono" style={{ color: getDeviationColor(deviationPercentNum) }}>
                    {formatPower(deviationValue)}
                  </div>
                  <div className="font-mono text-right" style={{ color: getDeviationColor(deviationPercentNum) }}>
                    {deviationPercent}%
                  </div>
                </div>
              </div>

              {/* Resource-specific monitoring */}
              {data.monitoring && (
                <div className="bg-gray-50 p-2 rounded">
                  {Object.entries(data.monitoring).map(([key, value]) => (
                    <div key={key} className="flex justify-between text-xs">
                      <span className="font-semibold">{formatLabel(key)}:</span>
                      <span className="font-mono">{value}</span>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* Divider */}
            <div className="border-t border-gray-200 my-2"></div>

            {/* Control Panel */}
            {data.controls && (
              <div className="flex flex-col gap-2">
                <div className="text-xs font-bold text-gray-600 mb-1">CONTROL</div>
                
                {Object.entries(data.controls).map(([key, control]) => (
                  <div key={key} className="bg-gray-50 p-2 rounded">
                    {typeof control.value === 'boolean' ? (
                      <ToggleSwitch
                        label={formatLabel(key)}
                        value={control.value}
                        onChange={() => {/* Add control logic */}}
                      />
                    ) : (
                      <ControlSlider
                        label={formatLabel(key)}
                        value={control.value}
                        min={control.min}
                        max={control.max}
                        unit={control.unit}
                        onChange={() => {/* Add control logic */}}
                      />
                    )}
                    {control.schedule && (
                      <div className="text-xs mt-1 text-gray-500">
                        Schedule: {control.schedule}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>
        ),
      },
      position: data.position,
      style: {
        ...elementsData.styles.resource,
        width: 250,
      },
    };
  });

  // Update the level nodes creation
  const level1Nodes = [
    {
      id: elementsData.hierarchy.level1_transmission.gridOperations.id,
      type: "default",
      data: {
        label: (
          <div className="flex flex-col gap-2">
            <div className="bg-sky-800 text-white py-1 px-2 rounded-t-lg font-bold text-center -mt-2.5 -mx-2.5 mb-1">
              {elementsData.hierarchy.level1_transmission.gridOperations.label}
            </div>
            {renderCombinedSections(elementsData.hierarchy.level1_transmission.gridOperations.sections)}
          </div>
        ),
      },
      position: elementsData.hierarchy.level1_transmission.gridOperations.position,
      style: elementsData.styles.gridOps,
    }
  ];

  const level2Nodes = [
    {
      id: elementsData.hierarchy.level2_distribution.distributionOps.id,
      type: "default",
      data: {
        label: (
          <div className="flex flex-col gap-2">
            <div className="bg-sky-800 text-white py-1 px-2 rounded-t-lg font-bold text-center -mt-2.5 -mx-2.5 mb-1">
              {elementsData.hierarchy.level2_distribution.distributionOps.label}
            </div>
            {renderCombinedSections(elementsData.hierarchy.level2_distribution.distributionOps.sections)}
          </div>
        ),
      },
      position: elementsData.hierarchy.level2_distribution.distributionOps.position,
      style: elementsData.styles.distOps,
    }
  ];

  const level3Nodes = Object.values(elementsData.hierarchy.level3_vpp.components).map((item: any) => ({
    id: item.id,
    type: "default",
    data: {
      label: (
        <div className="flex flex-col gap-2">
          <div className="bg-blue-900 text-white py-1 px-2 rounded-t-lg font-bold text-center -mt-2.5 -mx-2.5 mb-1">
            {item.label}
          </div>
          <div className="flex flex-col gap-2">
            {renderMonitoringValues(item.monitoring)}
            {item.controls && (
              <>
                <div className="border-t border-gray-200 my-2"></div>
                <div className="text-xs font-bold text-gray-600 mb-1">CONTROL</div>
                {renderControls(item.controls)}
              </>
            )}
          </div>
        </div>
      ),
    },
    position: item.position,
    style: elementsData.styles.vppComponent,
  }));

  // Update the edges creation
  const levelEdges: Edge[] = [
    // Grid to Distribution
    {
      id: 'grid-dist',
      source: 'gridOperations',
      target: 'distributionOps',
      type: 'smoothstep',
      animated: true,
      style: { stroke: '#0369a1' },
    },
    // Distribution to VPP Controller
    {
      id: 'dist-controller',
      source: 'distributionOps',
      target: 'controller',
      type: 'smoothstep',
      animated: true,
      style: { stroke: '#1e3a8a' },
    },
    // VPP internal connections
    {
      id: 'controller-optimizer',
      source: 'controller',
      target: 'optimizer',
      type: 'smoothstep',
      animated: true,
      style: { stroke: '#1e3a8a' },
    },
    {
      id: 'optimizer-cloud',
      source: 'optimizer',
      target: 'cloud',
      type: 'smoothstep',
      animated: true,
      style: { stroke: '#1e3a8a' },
    },
  ];

  // Update the resource edges generation function
  const generateResourceEdges = (nodes: Node[]): Edge[] => {
    const resourceNodes = nodes.filter(node => 
      node.type === 'default' && 
      ['solar', 'wind', 'battery', 'hvac', 'ev'].includes(node.id)
    );

    console.log('Found resource nodes:', resourceNodes.map(n => n.id));

    return resourceNodes.map((node) => ({
      id: `controller-${node.id}`,
      source: 'controller',
      target: node.id,
      type: 'smoothstep',
      animated: true,
      style: { stroke: '#2e8b57' },
      markerEnd: {
        type: MarkerType.ArrowClosed,
        color: '#2e8b57',
      },
    }));
  };

  // Update the edges memoization
  const edges = useMemo(() => {
    const resourceEdges = generateResourceEdges(allNodes);
    console.log('Generated resource edges:', resourceEdges);
    return [...levelEdges, ...resourceEdges];
  }, [allNodes]);

  // Update startSimulation with error handling
  const startSimulation = () => {
    if (!isRunning) {
      setIsRunning(true);
      setHasError(false);
      simulationInterval.current = setInterval(() => {
        try {
          setCurrentHour(prev => {
            const nextHour = prev + 1;
            console.log('Simulation hour:', nextHour);
            
            // Validate that we still have valid nodes
            if (!allNodes || allNodes.length === 0) {
              console.error('No nodes found in simulation');
              stopSimulation();
              setHasError(true);
              return prev;
            }

            if (nextHour >= 8760) {
              stopSimulation();
              return prev;
            }

            // Safely process the hour
            try {
              processHour(nextHour);
            } catch (error) {
              console.error('Error processing hour:', error);
              setEventLog(prev => [
                `[${formatEventTime(new Date())}] Error processing hour ${nextHour}: ${error.message}`,
                ...prev
              ]);
            }

            return nextHour;
          });
        } catch (error) {
          console.error('Simulation error:', error);
          stopSimulation();
          setHasError(true);
        }
      }, 1000);
    }
  };

  const stopSimulation = () => {
    setIsRunning(false);
    if (simulationInterval.current) {
      clearInterval(simulationInterval.current);
    }
  };

  const restartSimulation = () => {
    stopSimulation();
    setCurrentHour(0);
    setEventLog([]);
    // Reset any other simulation state here
  };

  const processHour = (hour: number) => {
    if (!demandResponseEvents || !Array.isArray(demandResponseEvents)) {
      console.error('Demand response data not properly loaded');
      return;
    }

    console.log('Current hour:', hour);
    console.log('Available events:', demandResponseEvents);

    const event = demandResponseEvents.find(e => 
      e && typeof e.Start === 'number' && 
      typeof e.End === 'number' && 
      hour >= e.Start && hour <= e.End
    );

    if (event) {
      console.log('Found event:', event);

      const hourlyDetail = event["Hourly Details"]?.find(d => d && d.Hour === hour);
      if (hourlyDetail) {
        const timestamp = formatEventTime(new Date());
        
        // First, analyze and select resources
        const selectedResources = analyzeAndSelectResources(hourlyDetail["Reduction Needed (MWh)"]);
        
        // Then update system state with the selected resources
        setSystemState(prevState => updateSystemForDR(prevState, hourlyDetail, selectedResources));
        
        // Now log the event and continue with the sequence
        setEventLog(prev => [
          `[${timestamp}] SEC Command Center - Demand Response Event Initiated`,
          `[${timestamp}] ├─ Event Duration: ${event["Duration (hours)"]} hours`,
          `[${timestamp}] ├─ Reduction Target: ${hourlyDetail["Reduction Needed (MWh)"]} MWh`,
          `[${timestamp}] ├─ Projected Load: ${hourlyDetail["Projected Load (MWh)"]} MWh`,
          `[${timestamp}] └─ Start Hour: ${hour}`,
          ...prev
        ]);

        // Continue with DEMA VPP Response
        setTimeout(() => {
          const t1 = formatEventTime(new Date());
          setEventLog(prev => [
            `[${t1}] DEMA VPP - Processing Demand Response Request`,
            `[${t1}] ├─ Request Received and Validated`,
            `[${t1}] ├─ Analyzing Available Resources`,
            `[${t1}] └─ Optimization Engine Started`,
            ...prev
          ]);
          
          // Resource Selection and Optimization logging
          setTimeout(() => {
            const t2 = formatEventTime(new Date());
            setEventLog(prev => [
              `[${t2}] Optimization Engine - Resource Selection Complete`,
              `[${t2}] ├─ Selected Resources: ${selectedResources.map(r => r.name).join(', ')}`,
              `[${t2}] └─ Total Capacity Available: ${selectedResources.reduce((sum, r) => sum + r.capacity, 0).toFixed(2)} MWh`,
              ...prev
            ]);

            // Dispatch Control Signals
            dispatchControlSignals(selectedResources, t2);
          }, 1000);
        }, 500);
      }
    } else {
      console.log('No event found for hour:', hour);
    }
  };

  const analyzeAndSelectResources = (reductionNeeded: number) => {
    // Simulate resource selection based on availability and capacity
    return [
      { name: 'HVAC System', capacity: reductionNeeded * 0.4, type: 'demand' },
      { name: 'EV Charging', capacity: reductionNeeded * 0.3, type: 'demand' },
      { name: 'Battery Storage', capacity: reductionNeeded * 0.3, type: 'supply' }
    ];
  };

  const dispatchControlSignals = (resources: any[], timestamp: string) => {
    resources.forEach((resource, index) => {
      setTimeout(() => {
        const t = formatEventTime(new Date());
        
        // Resource acknowledgment
        setEventLog(prev => [
          `[${t}] ${resource.name} - Control Signal Received`,
          `[${t}] ├─ Target Reduction: ${resource.capacity.toFixed(2)} MWh`,
          `[${t}] └─ Response Type: ${resource.type === 'demand' ? 'Demand Reduction' : 'Supply Increase'}`,
          ...prev
        ]);

        // Resource action confirmation
        setTimeout(() => {
          const t2 = formatEventTime(new Date());
          setEventLog(prev => [
            `[${t2}] ${resource.name} - Action Confirmed`,
            `[${t2}] ├─ Status: Active`,
            `[${t2}] └─ Mode: Demand Response`,
            ...prev
          ]);
        }, 500);
      }, index * 300);
    });

    // Final confirmation after all resources respond
    setTimeout(() => {
      const t = formatEventTime(new Date());
      setEventLog(prev => [
        `[${t}] DEMA VPP - Demand Response Implementation Complete`,
        `[${t}] ├─ All Resources Confirmed`,
        `[${t}] ├─ Smart Meter Validation Started`,
        `[${t}] └─ Monitoring Active`,
        ...prev
      ]);
    }, resources.length * 300 + 1000);
  };

  // Add jump to hour handler
  const handleJumpToHour = (hour?: number) => {
    if (hour !== undefined) {
      setJumpToHourValue(hour);
      return;
    }
    
    if (jumpToHourValue === null) return;
    
    if (jumpToHourValue < 0 || jumpToHourValue > 8760) {
      const timestamp = formatEventTime(new Date());
      setEventLog(prev => [
        `[${timestamp}] Invalid hour value. Please enter a number between 0 and 8760.`,
        ...prev
      ]);
      return;
    }

    if (isRunning) {
      stopSimulation();
    }

    setCurrentHour(jumpToHourValue);
    processHour(jumpToHourValue);
    
    const timestamp = formatEventTime(new Date());
    setEventLog(prev => [
      `[${timestamp}] Jumped to hour ${jumpToHourValue}`,
      ...prev
    ]);
  };

  // Add recovery function
  const recoverSimulation = () => {
    setHasError(false);
    restartSimulation();
  };

  // Clean up interval on unmount
  useEffect(() => {
    return () => {
      if (simulationInterval.current) {
        clearInterval(simulationInterval.current);
      }
    };
  }, []);

  // Add function to update node data based on system state
  const updateNodeData = (nodes: Node[]) => {
    return nodes.map(node => {
      const newNode = { ...node };
      
      switch (node.type) {
        case 'gridOps':
          // Update transmission node data
          newNode.data = {
            ...node.data,
            label: <GridOperationsDisplay systemState={systemState} />
          };
          break;

        case 'distOps':
          // Update distribution node data
          newNode.data = {
            ...node.data,
            sections: {
              substation: {
                label: 'Main Distribution Substation',
                monitoring: {
                  voltage: `${systemState.distribution.voltage.toFixed(1)}kV`,
                  loading: `${systemState.distribution.loading.toFixed(1)}%`,
                  temperature: `${systemState.distribution.temperature.toFixed(1)}°C`,
                },
              },
              distribution: {
                label: 'Distribution Network',
                monitoring: {
                  powerQuality: `${systemState.distribution.powerQuality.toFixed(1)}%`,
                  activePower: `${systemState.distribution.activePower.toFixed(1)} MW`,
                  reactivePower: `${systemState.distribution.reactivePower.toFixed(1)} MVAr`,
                },
              },
            },
          };
          break;

        case 'vppComponent':
          // Update VPP component data
          const vppSection = node.id === 'controller' ? 'controller' :
                           node.id === 'optimizer' ? 'optimizer' : 'cloud';
          newNode.data = {
            ...node.data,
            monitoring: systemState.vpp[vppSection],
          };
          break;

        case 'resource':
          // Update resource data
          if (systemState.resources[node.id]) {
            newNode.data = {
              ...node.data,
              powerDraw: systemState.resources[node.id].powerDraw,
              target: systemState.resources[node.id].target,
              status: systemState.resources[node.id].status,
              mode: systemState.resources[node.id].mode,
              reduction: systemState.resources[node.id].reduction,
              responseType: systemState.resources[node.id].responseType,
            };
          }
          break;
      }

      // Add visual indicators for DR events
      if (systemState.transmission.dispatchSignal === "Reduction") {
        newNode.style = {
          ...newNode.style,
          borderColor: '#f59e0b',
          borderWidth: 3,
          background: node.type === 'gridOps' ? 
            'linear-gradient(to right, rgba(251, 146, 60, 0.2), rgba(251, 146, 60, 0.3))' :
            newNode.style?.background,
        };

        if (node.type === 'resource' && systemState.resources[node.id]?.mode === "DR") {
          newNode.style = {
            ...newNode.style,
            background: 'rgba(251, 146, 60, 0.2)',
          };
        }
      }

      return newNode;
    });
  };

  // 1. Initialize nodes once
  useEffect(() => {
    const initialNodes = [
      ...level1Nodes,
      ...level2Nodes,
      ...level3Nodes,
      ...resourceNodes
    ];
    setAllNodes(initialNodes);
  }, []); // Empty dependency array since these are static

  // 2. Update nodes when system state changes
  const updateNodesWithSystemState = useCallback((nodes: Node[]) => {
    console.log("Updating nodes with system state");
    return nodes.map(node => {
      const newNode = { ...node };
      
      switch (node.type) {
        case 'gridOps':
          console.log("Updating gridOps node");
          newNode.data = {
            ...node.data,
            label: <GridOperationsDisplay systemState={systemState} />
          };
          break;

        case 'distOps':
          // Update distribution node data
          newNode.data = {
            ...node.data,
            sections: {
              substation: {
                label: 'Main Distribution Substation',
                monitoring: {
                  voltage: `${systemState.distribution.voltage.toFixed(1)}kV`,
                  loading: `${systemState.distribution.loading.toFixed(1)}%`,
                  temperature: `${systemState.distribution.temperature.toFixed(1)}°C`,
                },
              },
              distribution: {
                label: 'Distribution Network',
                monitoring: {
                  powerQuality: `${systemState.distribution.powerQuality.toFixed(1)}%`,
                  activePower: `${systemState.distribution.activePower.toFixed(1)} MW`,
                  reactivePower: `${systemState.distribution.reactivePower.toFixed(1)} MVAr`,
                },
              },
            },
          };
          break;

        case 'vppComponent':
          // Update VPP component data
          const vppSection = node.id === 'controller' ? 'controller' :
                           node.id === 'optimizer' ? 'optimizer' : 'cloud';
          newNode.data = {
            ...node.data,
            monitoring: systemState.vpp[vppSection],
          };
          break;

        case 'resource':
          // Update resource data
          if (systemState.resources[node.id]) {
            newNode.data = {
              ...node.data,
              powerDraw: systemState.resources[node.id].powerDraw,
              target: systemState.resources[node.id].target,
              status: systemState.resources[node.id].status,
              mode: systemState.resources[node.id].mode,
              reduction: systemState.resources[node.id].reduction,
              responseType: systemState.resources[node.id].responseType,
            };
          }
          break;
      }

      // Add visual indicators for DR events
      if (systemState.transmission.dispatchSignal === "Reduction") {
        newNode.style = {
          ...newNode.style,
          borderColor: '#f59e0b',
          borderWidth: 3,
          background: node.type === 'gridOps' ? 
            'linear-gradient(to right, rgba(251, 146, 60, 0.2), rgba(251, 146, 60, 0.3))' :
            newNode.style?.background,
        };

        if (node.type === 'resource' && systemState.resources[node.id]?.mode === "DR") {
          newNode.style = {
            ...newNode.style,
            background: 'rgba(251, 146, 60, 0.2)',
          };
        }
      }

      return newNode;
    });
  }, [systemState]); // No dependencies since this is just a transformation function

  useEffect(() => {
    if (allNodes.length > 0) {
      console.log("Nodes exist, updating with new system state");
      const updatedNodes = updateNodesWithSystemState(allNodes);
      console.log("Updated nodes:", updatedNodes);
      setAllNodes(updatedNodes);
    }
  }, [systemState, updateNodesWithSystemState]); // Only depend on systemState changes

  // Update the system state update effect
  useEffect(() => {
    if (isRunning) return;

    console.log("Setting up system state interval");
    const interval = setInterval(() => {
      setSystemState(prevState => {
        // Generate small random variations
        const voltageVariation = (Math.random() * 0.4 - 0.2); // ±0.2 kV
        const frequencyVariation = (Math.random() * 0.02 - 0.01); // ±0.01 Hz
        const loadFlowVariation = (Math.random() * 0.4 - 0.2); // ±0.2 MW

        // Get current values
        const currentVoltage = prevState.transmission.voltage;
        const currentFrequency = prevState.transmission.frequency;
        const currentLoadFlow = prevState.transmission.loadFlow;

        // Calculate new values with bounds
        const newVoltage = Math.min(134, Math.max(130, currentVoltage + voltageVariation));
        const newFrequency = Math.min(50.1, Math.max(49.9, currentFrequency + frequencyVariation));
        const newLoadFlow = Math.min(95, Math.max(75, currentLoadFlow + loadFlowVariation));

        console.log('Updating frequency from', currentFrequency, 'to', newFrequency);

        return {
          ...prevState,
          transmission: {
            ...prevState.transmission,
            voltage: newVoltage,
            frequency: newFrequency,
            loadFlow: newLoadFlow,
          }
        };
      });
    }, 500);

    return () => clearInterval(interval);
  }, [isRunning]);

  // Add a useEffect to log system state changes
  useEffect(() => {
    console.log("System state updated:", systemState);
  }, [systemState]);

  // 4. Simulation cleanup
  useEffect(() => {
    return () => {
      if (simulationInterval.current) {
        clearInterval(simulationInterval.current);
      }
    };
  }, []);

  // Move node style calculation to a memoized function
  const getNodeStyle = useCallback((node: Node, isDRActive: boolean, isResponding: boolean) => {
    const baseStyle = {
      ...node.style,
      transition: 'all 0.3s ease-in-out',
    };

    if (isDRActive) {
      return {
        ...baseStyle,
        borderColor: '#f59e0b',
        borderWidth: 3,
        animation: 'glow 2s infinite',
        background: node.type === 'gridOps' ? 
          'linear-gradient(45deg, rgba(251, 146, 60, 0.2), rgba(251, 146, 60, 0.3))' :
          isResponding ? 'rgba(251, 146, 60, 0.15)' :
          baseStyle.background,
      };
    }

    return baseStyle;
  }, []);

  // Update node rendering
  const renderNodeContent = (node: Node) => {
    const data = node.data as NodeData;
    const isDRActive = systemState.transmission.dispatchSignal === "Reduction";
    const isResourceResponding = node.type === 'resource' && 
      systemState.resources[node.id]?.mode === "DR";
    
    return (
      <div className={`p-4 relative ${
        isDRActive ? 'dr-active' : ''
      } ${
        isResourceResponding ? 'dr-responding' : ''
      }`}>
        {/* DR Status Indicator */}
        {isDRActive && (node.type === 'gridOps' || isResourceResponding) && (
          <div className="absolute -top-2 -right-2 flex items-center gap-1">
            <div className="animate-ping absolute h-3 w-3 rounded-full bg-orange-400 opacity-75"></div>
            <div className="relative h-3 w-3 rounded-full bg-orange-500"></div>
            <span className="bg-orange-500 text-white px-2 py-1 text-xs rounded-md shadow-lg" 
                  style={{ animation: 'pulse 2s infinite' }}>
              {node.type === 'gridOps' ? 'DR Event Active' : 'Responding'}
            </span>
          </div>
        )}

        {/* Node Content with Enhanced Monitoring */}
        <div className={`
          rounded-lg p-3 
          ${isDRActive ? 'transition-all duration-500' : ''}
          ${isResourceResponding ? 'bg-orange-50' : ''}
        `}>
          <h3 className="font-bold mb-2 flex items-center gap-2">
            {data.label}
            {isDRActive && (
              <span className="text-xs bg-orange-100 text-orange-800 px-2 py-1 rounded-full">
                {getStatusText(node)}
              </span>
            )}
          </h3>

          {/* Enhanced Monitoring Sections */}
          {data.sections && Object.entries(data.sections).map(([key, section]) => (
            <div key={key} className="mb-4">
              <h4 className="font-semibold text-sm mb-1 flex items-center gap-2">
                {section.label}
                {getStatusIndicator(section)}
              </h4>
              {section.monitoring && (
                <div className="bg-white/50 p-2 rounded transition-all duration-300">
                  {Object.entries(section.monitoring).map(([k, v]) => (
                    <MonitoringValue 
                      key={k} 
                      label={k} 
                      value={v} 
                      isHighlighted={isValueSignificant(k, v)}
                    />
                  ))}
                </div>
              )}
            </div>
          ))}

          {/* Resource-specific DR metrics */}
          {isResourceResponding && (
            <div className="mt-3 bg-orange-100 p-2 rounded-lg border border-orange-200">
              <h4 className="text-xs font-bold text-orange-800 mb-1">DR Metrics</h4>
              <div className="grid grid-cols-2 gap-2">
                <MetricBox 
                  label="Reduction" 
                  value={`${systemState.resources[node.id].reduction?.toFixed(1)} MWh`}
                />
                <MetricBox 
                  label="Response" 
                  value={systemState.resources[node.id].responseType || 'N/A'}
                />
              </div>
            </div>
          )}
        </div>
      </div>
    );
  };

  // Add helper components for enhanced visualization
  const MonitoringValue = ({ label, value, isHighlighted }) => (
    <div className={`
      flex justify-between text-xs p-1 rounded
      ${isHighlighted ? 'bg-yellow-100 font-semibold' : ''}
      transition-all duration-300
    `}>
      <span>{formatLabel(label)}:</span>
      <span className={`
        font-mono
        ${isHighlighted ? 'text-orange-600' : ''}
      `}>
        {value}
      </span>
    </div>
  );

  const MetricBox = ({ label, value }) => (
    <div className="bg-white/50 p-2 rounded text-xs">
      <div className="text-orange-800 font-semibold">{label}</div>
      <div className="font-mono text-orange-900">{value}</div>
    </div>
  );

  const getStatusIndicator = (section) => {
    if (!section.monitoring) return null;
    
    // Add status indicators based on monitoring values
    const status = calculateSectionStatus(section.monitoring);
    return (
      <span className={`
        w-2 h-2 rounded-full
        ${status === 'critical' ? 'bg-red-500 animate-pulse' : 
          status === 'warning' ? 'bg-yellow-500' : 
          'bg-green-500'}
      `} />
    );
  };

  return (
    <div className="w-full min-h-screen bg-background flex flex-col">
      {/* Fixed Header */}
      <div className="sticky top-0 z-50">
        <Header 
          isRunning={isRunning}
          onStart={startSimulation}
          onStop={stopSimulation}
          onRestart={restartSimulation}
          currentHour={currentHour}
          onJumpToHour={handleJumpToHour}
        />
      </div>

      {hasError ? (
        <div className="flex-1 flex items-center justify-center bg-red-50">
          <div className="text-center">
            <h2 className="text-xl font-bold text-red-600 mb-4">
              An error occurred in the simulation
            </h2>
            <button
              onClick={recoverSimulation}
              className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600"
            >
              Recover Simulation
            </button>
          </div>
        </div>
      ) : (
        <div className="flex-1 flex flex-col overflow-auto">
          {/* ReactFlow section with fixed height */}
          <div className="h-[600px] flex">
            <ReactFlowProvider>
              <div className="flex-1 relative">
                {allNodes.length > 0 ? (
                  <ReactFlow
                    nodes={allNodes}
                    edges={edges}
                    onNodeClick={(event, node) => {
                      try {
                        const timestamp = formatEventTime(new Date());
                        setEventLog((prevLog) => [
                          `[${timestamp}] User clicked on ${node.id}`,
                          ...prevLog
                        ].slice(0, 10));
                      } catch (error) {
                        console.error('Error handling node click:', error);
                      }
                    }}
                    connectionMode={ConnectionMode.Loose}
                    fitView
                    attributionPosition="bottom-right"
                    onError={(error) => {
                      console.error('ReactFlow error:', error);
                      setHasError(true);
                    }}
                    nodesConnectable={false}
                    nodesDraggable={false}
                    minZoom={0.5}
                    maxZoom={1.5}
                    defaultViewport={{ x: 0, y: 0, zoom: 0.8 }}
                  >
                    <Background color="#aaa" gap={16} />
                    <Controls />
                  </ReactFlow>
                ) : (
                  <div className="flex items-center justify-center h-full">
                    <p className="text-gray-500">Loading diagram elements...</p>
                  </div>
                )}
              </div>
            </ReactFlowProvider>

            {/* Event Log Sidebar with fixed header */}
            <div className="w-64 bg-gray-100 border-l border-gray-300 flex flex-col">
              <div className="sticky top-0 bg-white border-b border-gray-200 z-40">
                <h2 className="text-lg font-bold p-4">Event Log</h2>
              </div>
              <div className="flex-1 p-4 overflow-y-auto">
                {eventLog.length > 0 ? (
                  <div className="flex flex-col gap-2">
                    {eventLog.map((event, index) => (
                      <div 
                        key={index} 
                        className="text-xs bg-white p-2 border border-gray-300 rounded shadow-sm hover:shadow-md transition-shadow"
                      >
                        {event}
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-xs text-gray-500">No events yet...</p>
                )}
              </div>
            </div>
          </div>

          {/* Charts section */}
          <LoadProfileChart currentHour={currentHour} />
        </div>
      )}
    </div>
  );
}

// Export the non-SSR version
export default VPPDiagram;
