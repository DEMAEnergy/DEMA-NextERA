# VPP Simulation Framework

## Overview
This simulation framework provides a comprehensive environment for modeling distributed energy resources (DER) and their interactions within a virtual power plant (VPP) system. The framework supports real-time simulation of various energy components, their control systems, and communication protocols.

## Core Components

### 1. Base Framework (`base_simulator.py`)
The foundation of the simulation framework is built on the `BaseSimulator` abstract class:

```python
class BaseSimulator(ABC):
    def step(self, inputs: Dict[str, Any]) -> Dict[str, Any]
    def reset(self) -> None
    def get_state(self) -> SimulationState
    def update_state(self, new_state: SimulationState) -> None
    def validate_state(self, state: SimulationState) -> bool
    def save_state(self, state: Dict[str, Any]) -> None
```

### 2. State Management (`state.py`)
Defines the state models for different components:

```python
@dataclass
class SimulationState:
    component_type: str
    timestamp: float

@dataclass
class StorageState(SimulationState):
    capacity: float
    current_charge: float
    charge_rate: float
    discharge_rate: float

@dataclass
class SourceState(SimulationState):
    max_power_output: float
    current_output: float
    availability: float
```

### 3. Resource Simulators

#### 3.1 Storage Systems (`storage_simulator.py`)
Simulates various energy storage technologies:

##### Battery Simulator
```python
class BatterySimulator(BaseSimulator):
    def __init__(self, model: Battery, config: Dict[str, Any]):
        self.temperature_model = config.get('temperature_model', 'constant')
        self.degradation_model = config.get('degradation_model', 'linear')
```

Configuration:
```python
battery_config = {
    'capacity': 100,              # kWh
    'max_charge_rate': 50,        # kW
    'max_discharge_rate': 50,     # kW
    'temperature_model': 'dynamic',
    'degradation_model': 'linear'
}
```

##### Thermal Storage Simulator
```python
class ThermalStorageSimulator(BaseSimulator):
    def __init__(self, model: ThermalStorage, config: Dict[str, Any]):
        self.heat_loss_model = config.get('heat_loss_model', 'linear')
```

#### 3.2 Power Sources (`source_simulator.py`)
Simulates renewable energy sources:

##### PV Simulator
```python
class PVSimulator(BaseSimulator):
    def __init__(self, model: PVSystem, config: Dict[str, Any]):
        self.cloud_impact = config.get('cloud_impact', True)
```

##### Wind Turbine Simulator
```python
class WindTurbineSimulator(BaseSimulator):
    def __init__(self, model: WindTurbine, config: Dict[str, Any]):
        self.turbulence_model = config.get('turbulence_model', 'simple')
```

#### 3.3 Load Systems (`load_simulator.py`)
Simulates various load types:

##### HVAC Simulator
```python
class HVACSimulator(BaseSimulator):
    def __init__(self, model: HVAC, config: Dict[str, Any]):
        self.thermal_model = config.get('thermal_model', 'simple')
```

##### Motor Simulator
```python
class MotorSimulator(BaseSimulator):
    def __init__(self, model: Motor, config: Dict[str, Any]):
        self.efficiency_model = config.get('efficiency_model', 'simple')
```

### 4. Grid Operation (`grid_operator_simulator.py`)
Simulates grid operator behavior and responses:

```python
class GridOperatorSimulator(BaseSimulator):
    def __init__(self, model: GridOperatorModel, config: Dict[str, Any]):
        self.noise_factors = config.get('noise_factors', {
            'frequency': 0.01,
            'voltage': 0.005,
            'load': 0.02
        })
```

### 5. Communication Layer

#### 5.1 Protocol Simulation (`protocol_simulator.py`)
Simulates communication protocols and network effects:

```python
class SimulatedProtocolAdapter(BaseProtocol):
    async def connect(self) -> bool
    async def disconnect(self) -> bool
    async def send_command(self, command: str, params: Dict[str, Any]) -> Dict[str, Any]
    async def read_status(self) -> Dict[str, Any]
```

#### 5.2 Protocol Factory (`protocol_factory.py`)
Creates appropriate protocol instances:

```python
class SimulationProtocolFactory:
    @classmethod
    def create_protocol(
        cls,
        resource_type: str,
        protocol_type: str,
        protocol_id: str,
        config: Dict[str, Any],
        simulation_mode: bool = False,
        model: Optional[Any] = None
    ) -> BaseProtocol
```

### 6. Resource Communication (`resource_communicator.py`)
Manages communication with simulated and real resources:

```python
class SimulationAwareResourceCommunicator(ResourceCommunicator):
    async def add_resource(
        self,
        resource_id: str,
        resource_type: str,
        protocol_type: str,
        config: Dict[str, Any],
        model: Optional[Any] = None,
        simulation_mode: Optional[bool] = None
    ) -> bool
```

## Usage Examples

### 1. Basic Component Simulation
```python
from Models.simulation.storage_simulator import BatterySimulator
from Models.Storage.battery import Battery

# Initialize battery
battery = Battery(capacity=100)
simulator = BatterySimulator(battery, {
    'temperature_model': 'dynamic',
    'degradation_model': 'linear'
})

# Run simulation step
result = simulator.step({
    'power_request': 50,
    'ambient_temperature': 25
})
```

### 2. Grid Operation Simulation
```python
from Models.simulation.grid_operator_simulator import GridOperatorSimulator
from Models.simulation.grid_operator_model import GridOperatorModel

# Initialize grid operator
model = GridOperatorModel("grid_1", {
    'grid_constraints': {
        'voltage_limits': {'min': 0.95, 'max': 1.05},
        'frequency_limits': {'min': 49.8, 'max': 50.2}
    }
})

simulator = GridOperatorSimulator(model, {
    'noise_factors': {
        'frequency': 0.01,
        'voltage': 0.005
    }
})

# Run simulation step
result = simulator.step({
    'load_forecast': 1000,
    'generation_forecast': 1200,
    'grid_events': []
})
```

### 3. Protocol Simulation
```python
from Models.simulation.protocol_simulator import SimulatedProtocolAdapter
from Models.simulation.storage_simulator import BatterySimulator

# Initialize components
battery = Battery(capacity=100)
simulator = BatterySimulator(battery, {})
protocol = SimulatedProtocolAdapter(simulator, "protocol_1", {
    'simulation_inputs': {
        'latency': 50,
        'packet_loss': 0.001
    }
})

# Send command through protocol
result = await protocol.send_command("charge", {
    'power': 50,
    'duration': 3600
})
```

## Error Handling

### 1. State Validation
```python
try:
    simulator.validate_state(new_state)
except ValueError as e:
    print(f"Invalid state: {e}")
```

### 2. Protocol Error Handling
```python
try:
    result = await protocol.send_command(command, params)
except CommunicationError as e:
    print(f"Communication error: {e}")
except TimeoutError as e:
    print(f"Command timed out: {e}")
```

## Data Collection and Analysis

### 1. State History
```python
history = simulator.get_history()
for state in history:
    print(f"Time: {state['timestamp']}")
    print(f"State: {state['state']}")
```

### 2. Performance Metrics
```python
metrics = simulator.calculate_metrics({
    'efficiency': True,
    'availability': True,
    'response_time': True
})
```

## Integration Guidelines

1. Always initialize simulators with appropriate configuration
2. Use type hints and validation for inputs
3. Handle errors appropriately
4. Monitor and log simulation states
5. Use the protocol factory for communication setup
6. Implement proper cleanup in reset methods

## Best Practices

1. Use appropriate models for different simulation needs
2. Configure noise factors realistically
3. Validate inputs and states
4. Handle edge cases and errors
5. Monitor simulation performance
6. Document configuration changes 