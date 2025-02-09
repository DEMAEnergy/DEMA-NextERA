export type SystemState = {
  transmission: {
    voltage: number;
    frequency: number;
    loadFlow: number;
    dispatchSignal: string;
    requestedPower: number;
    powerFactor: number;
    harmonicDistortion: number;
    lineStability: number;
    congestionLevel: number;
    drEventStatus: {
      isActive: boolean;
      startTime: string;
      duration: number;
      targetReduction: number;
      currentReduction: number;
      participatingResources: number;
    };
  };
  distribution: {
    voltage: number;
    loading: number;
    temperature: number;
    powerQuality: number;
    activePower: number;
    reactivePower: number;
    flexibilityAvailable: number;
    feederLoading: number[];
    powerLosses: number;
    voltageImbalance: number;
    faultIndicators: {
      location: string;
      severity: 'normal' | 'warning' | 'critical';
    }[];
  };
  vpp: {
    controller: {
      status: string;
      controlMode: string;
      activeResources: number;
      responseTime: number;
      resourceAvailability: number;
      optimizationScore: number;
      lastCommand: {
        timestamp: string;
        type: string;
        status: string;
      };
    };
    optimizer: {
      algorithm: string;
      optimizationGoal: string;
      lastUpdate: string;
    };
    cloud: {
      aiStatus: string;
      dataStorage: number;
      predictions: string;
    };
  };
  resources: {
    [key: string]: {
      powerDraw: number;
      target: number;
      status: string;
      mode: string;
      reduction?: number;
      responseType?: string;
      performance: {
        responseTime: number;
        accuracyScore: number;
        stabilityIndex: number;
      };
      drMetrics?: {
        participationRate: number;
        reductionAccuracy: number;
        responseLatency: number;
      };
    };
  };
};

export const generateRandomSystemState = (): SystemState => {
  const isDRActive = Math.random() < 0.2;
  
  // Start with exactly 50 Hz for initial state
  return {
    transmission: {
      voltage: 132,  // Start at nominal
      frequency: 50, // Start at exactly 50 Hz
      loadFlow: 85,  // Start at nominal
      dispatchSignal: isDRActive ? "Reduction" : "Normal",
      requestedPower: isDRActive ? -(Math.random() * 3 + 1) : 0,  // 1-4 MW reduction
      powerFactor: 0.98,
      harmonicDistortion: 0.02,
      lineStability: 0.99,
      congestionLevel: 0.5,
      drEventStatus: {
        isActive: isDRActive,
        startTime: isDRActive ? new Date().toISOString() : "",
        duration: isDRActive ? Math.floor(Math.random() * 4) + 1 : 0,
        targetReduction: isDRActive ? Math.random() * 3 + 1 : 0,
        currentReduction: isDRActive ? Math.random() * 2 + 0.5 : 0,
        participatingResources: isDRActive ? Math.floor(Math.random() * 3) + 2 : 0,
      },
    },
    distribution: {
      voltage: 33 + (Math.random() * 1 - 0.5),
      loading: 75 + (Math.random() * 10 - 5),
      temperature: 42 + (Math.random() * 2 - 1),
      powerQuality: 98.5 + (Math.random() * 1 - 0.5),
      activePower: 12.4 + (Math.random() * 2 - 1),
      reactivePower: 2.1 + (Math.random() * 0.4 - 0.2),
      flexibilityAvailable: 10.0 + (Math.random() * 2 - 1),
      feederLoading: [0.7, 0.8, 0.9],
      powerLosses: 0.02,
      voltageImbalance: 0.01,
      faultIndicators: [
        { location: "Line 1", severity: "normal" },
        { location: "Line 2", severity: "warning" },
      ],
    },
    vpp: {
      controller: {
        status: "Normal",
        controlMode: "Automatic",
        activeResources: 5,
        responseTime: 0.5,
        resourceAvailability: 0.95,
        optimizationScore: 0.85,
        lastCommand: {
          timestamp: "30s ago",
          type: "Cost Minimization",
          status: "Completed",
        },
      },
      optimizer: {
        algorithm: "Cost Minimization",
        optimizationGoal: "Efficiency",
        lastUpdate: "30s ago",
      },
      cloud: {
        aiStatus: "Active",
        dataStorage: 85,
        predictions: "Updated",
      },
    },
    resources: {
      hvac: {
        powerDraw: 8000,
        target: 7500,
        status: "Normal",
        mode: "Standard",
      },
      ev: {
        powerDraw: 2500,
        target: 2300,
        status: "Normal",
        mode: "Standard",
      },
      battery: {
        powerDraw: 500,
        target: 600,
        status: "Normal",
        mode: "Standard",
      },
      solar: {
        powerDraw: 1200,
        target: 1500,
        status: "Normal",
        mode: "Standard",
      },
      wind: {
        powerDraw: 3000,
        target: 3200,
        status: "Normal",
        mode: "Standard",
      },
    },
  };
};

export const updateSystemForDR = (
  state: SystemState, 
  event: any, 
  selectedResources: any[]
): SystemState => {
  // Deep copy current state
  const newState = JSON.parse(JSON.stringify(state));
  
  try {
    // Update transmission state
    newState.transmission.dispatchSignal = "Reduction";
    newState.transmission.requestedPower = -event["Reduction Needed (MWh)"];
    
    // Update distribution state with safety check
    if (newState.distribution && typeof newState.distribution.flexibilityAvailable === 'number') {
      newState.distribution.flexibilityAvailable = Math.max(
        0, 
        newState.distribution.flexibilityAvailable - event["Reduction Needed (MWh)"]
      );
    }
    
    // Update VPP state
    newState.vpp.controller.status = "DR Active";
    newState.vpp.optimizer.optimizationGoal = "Load Reduction";
    
    // Update resources with safety check
    selectedResources.forEach(resource => {
      const resourceId = resource.name.toLowerCase().replace(' system', '');
      if (newState.resources[resourceId]) {
        newState.resources[resourceId].status = "Responding";
        newState.resources[resourceId].mode = "DR";
        newState.resources[resourceId].reduction = resource.capacity;
        newState.resources[resourceId].responseType = resource.type;
      }
    });
    
    return newState;
  } catch (error) {
    console.error('Error updating system state:', error);
    return state; // Return original state if update fails
  }
}; 