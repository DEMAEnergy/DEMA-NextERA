from typing import Dict, Any, Optional, Callable
from datetime import datetime
import asyncio
import random
from ..communication.base_protocol import BaseProtocol
from .base_simulator import BaseSimulator
from .state import ProtocolState

class SimulatedProtocolAdapter(BaseProtocol):
    """Adapter to make simulators work with communication protocols"""
    
    def __init__(self, simulator: BaseSimulator, protocol_id: str, config: Dict[str, Any]):
        super().__init__(protocol_id, config)
        self.simulator = simulator
        self.callbacks: Dict[str, Callable] = {}
        self.simulation_inputs = config.get('simulation_inputs', {})
        
        # Network simulation parameters
        self.latency = config.get('latency', 50)  # ms
        self.jitter = config.get('jitter', 10)  # ms
        self.packet_loss = config.get('packet_loss', 0.001)  # probability
        self.bandwidth = config.get('bandwidth', 1000)  # kbps
        self.error_rate = config.get('error_rate', 0.0001)  # probability
        
        # Protocol state
        self.state = ProtocolState(
            component_type="protocol",
            timestamp=datetime.now().timestamp(),
            mode="disconnected",
            parameters={
                'latency': self.latency,
                'packet_loss': self.packet_loss,
                'bandwidth': self.bandwidth
            }
        )
        
    async def connect(self) -> bool:
        """Simulate connection establishment with network effects"""
        try:
            # Simulate connection delay
            delay = self._calculate_delay(100)  # Larger delay for connection
            await asyncio.sleep(delay / 1000)  # Convert to seconds
            
            # Simulate connection failure
            if random.random() < self.error_rate:
                raise ConnectionError("Simulated connection failure")
                
            self.state.mode = "connected"
            self.state.timestamp = datetime.now().timestamp()
            self.update_last_communication()
            return True
        except Exception as e:
            return self.handle_error(e)
    
    async def disconnect(self) -> bool:
        """Simulate disconnection with network effects"""
        try:
            # Simulate disconnection delay
            delay = self._calculate_delay(50)
            await asyncio.sleep(delay / 1000)
            
            self.state.mode = "disconnected"
            self.state.timestamp = datetime.now().timestamp()
            return True
        except Exception as e:
            return self.handle_error(e)
    
    async def send_command(self, command: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Send command to simulator with network simulation"""
        try:
            # Check connection
            if self.state.mode != "connected":
                raise ConnectionError("Not connected")
                
            # Simulate packet loss
            if random.random() < self.packet_loss:
                raise TimeoutError("Simulated packet loss")
                
            # Calculate transmission delay based on message size
            message_size = len(str(params)) * 8  # Rough size in bits
            transmission_delay = self._calculate_transmission_delay(message_size)
            network_delay = self._calculate_delay(self.latency)
            total_delay = transmission_delay + network_delay
            
            await asyncio.sleep(total_delay / 1000)
            
            # Merge command parameters with simulation inputs
            inputs = {**self.simulation_inputs, **params}
            
            # Step simulator
            result = self.simulator.step(inputs)
            
            # Simulate response delay
            response_size = len(str(result)) * 8
            response_delay = self._calculate_transmission_delay(response_size)
            await asyncio.sleep(response_delay / 1000)
            
            self.update_last_communication()
            return {
                "success": True,
                "timestamp": datetime.now(),
                "data": result,
                "metrics": {
                    "latency": total_delay,
                    "message_size": message_size
                }
            }
        except Exception as e:
            return self.handle_error(e)
    
    async def read_status(self) -> Dict[str, Any]:
        """Read current simulator state with network simulation"""
        try:
            # Check connection
            if self.state.mode != "connected":
                raise ConnectionError("Not connected")
                
            # Simulate network delay
            delay = self._calculate_delay(self.latency)
            await asyncio.sleep(delay / 1000)
            
            state = self.simulator.get_state()
            self.update_last_communication()
            
            return {
                "success": True,
                "timestamp": datetime.now(),
                "data": state.to_dict(),
                "metrics": {
                    "latency": delay
                }
            }
        except Exception as e:
            return self.handle_error(e)
    
    async def subscribe_to_updates(self, callback: Callable) -> bool:
        """Subscribe to simulator updates with QoS simulation"""
        try:
            if self.state.mode != "connected":
                raise ConnectionError("Not connected")
                
            topic = f"simulator/{self.simulator.model.resource_id}/updates"
            self.callbacks[topic] = callback
            
            # Start periodic updates with network simulation
            asyncio.create_task(self._publish_updates(topic))
            return True
        except Exception as e:
            return self.handle_error(e)
            
    async def _publish_updates(self, topic: str):
        """Simulate periodic updates with network effects"""
        while self.state.mode == "connected":
            try:
                # Get current state
                state = self.simulator.get_state()
                
                # Simulate network effects
                if random.random() >= self.packet_loss:
                    delay = self._calculate_delay(self.latency)
                    await asyncio.sleep(delay / 1000)
                    
                    # Call callback with state and metrics
                    await self.callbacks[topic](state.to_dict(), {
                        "latency": delay,
                        "timestamp": datetime.now()
                    })
                    
                # Wait for next update
                await asyncio.sleep(1.0)  # 1 second update rate
            except Exception as e:
                self.handle_error(e)
                
    def _calculate_delay(self, base_latency: float) -> float:
        """Calculate network delay with jitter"""
        jitter_factor = random.uniform(-self.jitter, self.jitter)
        return max(1, base_latency + jitter_factor)
        
    def _calculate_transmission_delay(self, message_size: int) -> float:
        """Calculate transmission delay based on bandwidth"""
        return (message_size / (self.bandwidth * 1000)) * 1000  # Convert to ms
        
    def get_state(self) -> ProtocolState:
        """Get current protocol state"""
        return self.state
        
    def update_state(self, new_state: ProtocolState) -> None:
        """Update protocol state"""
        self.state = new_state
        
    def validate_state(self, state: ProtocolState) -> bool:
        """Validate protocol state"""
        return (state.mode in ["connected", "disconnected"] and
                isinstance(state.parameters, dict) and
                all(key in state.parameters for key in ['latency', 'packet_loss', 'bandwidth']))

class ProtocolSimulator:
    def __init__(self):
        self.protocol = None
        self.storage = None
        self.source = None
    
    def simulate(self, time_step):
        if not all([self.protocol, self.storage, self.source]):
            raise ValueError("Protocol, storage, and source must be initialized")
        
        # Simulation logic
        protocol_state = self.protocol.get_state()
        storage_state = self.storage.get_state()
        source_state = self.source.get_state()
        
        # Update states based on protocol rules
        new_states = self.protocol.compute_next_state(
            protocol_state,
            storage_state,
            source_state,
            time_step
        )
        
        # Apply new states
        self.storage.update_state(new_states['storage'])
        self.source.update_state(new_states['source']) 