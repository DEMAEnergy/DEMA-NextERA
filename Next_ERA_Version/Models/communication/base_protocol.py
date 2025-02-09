from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, Callable
from datetime import datetime
from enum import Enum
import asyncio
import logging

class ProtocolStatus(Enum):
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    ERROR = "error"
    MAINTENANCE = "maintenance"

class QualityOfService(Enum):
    AT_MOST_ONCE = 0    # Fire and forget
    AT_LEAST_ONCE = 1   # Guaranteed delivery
    EXACTLY_ONCE = 2    # Guaranteed single delivery

class ErrorType(Enum):
    CONNECTION = "connection_error"
    TIMEOUT = "timeout_error"
    VALIDATION = "validation_error"
    PROTOCOL = "protocol_error"
    AUTHENTICATION = "auth_error"
    PERMISSION = "permission_error"

class BaseProtocol(ABC):
    """Base class for all communication protocols"""
    
    def __init__(self, protocol_id: str, config: Dict[str, Any]):
        self.protocol_id = protocol_id
        self.config = config
        self.status = ProtocolStatus.DISCONNECTED
        self.last_communication = None
        self.retry_count = 0
        self.max_retries = config.get('max_retries', 3)
        self.timeout = config.get('timeout', 5.0)
        self.qos = QualityOfService(config.get('qos', 1))
        
        # Connection parameters
        self.reconnect_interval = config.get('reconnect_interval', 5.0)
        self.keepalive_interval = config.get('keepalive_interval', 60.0)
        
        # Security parameters
        self.username = config.get('username', None)
        self.password = config.get('password', None)
        self.ssl_context = config.get('ssl_context', None)
        
        # Performance metrics
        self.metrics = {
            'latency': 0.0,
            'packet_loss': 0.0,
            'throughput': 0.0,
            'error_rate': 0.0,
            'uptime': 0.0
        }
        
        # Setup logging
        self.logger = logging.getLogger(f"protocol.{protocol_id}")
        
        # Start monitoring tasks
        self._monitoring_task = None
        self._keepalive_task = None
        
    async def initialize(self) -> bool:
        """Initialize protocol and start monitoring"""
        try:
            # Start monitoring tasks
            self._monitoring_task = asyncio.create_task(self._monitor_connection())
            if self.keepalive_interval > 0:
                self._keepalive_task = asyncio.create_task(self._send_keepalive())
            return True
        except Exception as e:
            self.logger.error(f"Failed to initialize protocol: {e}")
            return False
            
    async def cleanup(self) -> None:
        """Clean up protocol resources"""
        try:
            # Cancel monitoring tasks
            if self._monitoring_task:
                self._monitoring_task.cancel()
            if self._keepalive_task:
                self._keepalive_task.cancel()
                
            # Disconnect if connected
            if self.status == ProtocolStatus.CONNECTED:
                await self.disconnect()
        except Exception as e:
            self.logger.error(f"Error during cleanup: {e}")
            
    @abstractmethod
    async def connect(self) -> bool:
        """Establish connection with the resource"""
        pass
    
    @abstractmethod
    async def disconnect(self) -> bool:
        """Disconnect from the resource"""
        pass
    
    @abstractmethod
    async def send_command(
        self, command: str, params: Dict[str, Any], timeout: Optional[float] = None
    ) -> Dict[str, Any]:
        """Send command to the resource"""
        pass
    
    @abstractmethod
    async def read_status(self, timeout: Optional[float] = None) -> Dict[str, Any]:
        """Read current status from the resource"""
        pass
    
    @abstractmethod
    async def subscribe_to_updates(
        self, callback: Callable, qos: Optional[QualityOfService] = None
    ) -> bool:
        """Subscribe to real-time updates from the resource"""
        pass
        
    async def _monitor_connection(self) -> None:
        """Monitor connection status and metrics"""
        while True:
            try:
                # Check connection status
                if self.status == ProtocolStatus.CONNECTED:
                    # Update metrics
                    await self._update_metrics()
                    
                    # Check last communication
                    if self.last_communication:
                        time_since_last = (datetime.now() - self.last_communication).total_seconds()
                        if time_since_last > self.timeout:
                            self.logger.warning("Communication timeout detected")
                            await self._handle_timeout()
                            
                elif self.status == ProtocolStatus.DISCONNECTED:
                    # Attempt reconnection
                    if self.retry_count < self.max_retries:
                        self.logger.info("Attempting reconnection...")
                        await self.connect()
                        
                # Update uptime metric
                if self.status == ProtocolStatus.CONNECTED:
                    self.metrics['uptime'] += 1
                    
                await asyncio.sleep(1.0)  # Check every second
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Error in connection monitoring: {e}")
                await asyncio.sleep(self.reconnect_interval)
                
    async def _send_keepalive(self) -> None:
        """Send periodic keepalive messages"""
        while True:
            try:
                if self.status == ProtocolStatus.CONNECTED:
                    await self.send_command("keepalive", {}, timeout=2.0)
                await asyncio.sleep(self.keepalive_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Error sending keepalive: {e}")
                
    async def _update_metrics(self) -> None:
        """Update protocol performance metrics"""
        try:
            # Measure latency
            start_time = datetime.now()
            response = await self.send_command("ping", {}, timeout=1.0)
            if response.get('success', False):
                latency = (datetime.now() - start_time).total_seconds() * 1000
                self.metrics['latency'] = latency
                
            # Update error rate
            total_commands = self.metrics.get('total_commands', 0)
            if total_commands > 0:
                self.metrics['error_rate'] = self.retry_count / total_commands
                
        except Exception as e:
            self.logger.error(f"Error updating metrics: {e}")
            
    async def _handle_timeout(self) -> None:
        """Handle communication timeout"""
        self.logger.warning("Handling communication timeout")
        self.status = ProtocolStatus.ERROR
        await self.disconnect()
        self.retry_count += 1
        
    def update_last_communication(self) -> None:
        """Update the timestamp of last successful communication"""
        self.last_communication = datetime.now()
        if self.status != ProtocolStatus.CONNECTED:
            self.status = ProtocolStatus.CONNECTED
            self.retry_count = 0
            
    def handle_error(self, error: Exception, error_type: ErrorType = ErrorType.PROTOCOL) -> Dict[str, Any]:
        """Handle communication errors"""
        self.retry_count += 1
        self.logger.error(f"{error_type.value}: {str(error)}")
        
        if self.retry_count >= self.max_retries:
            self.status = ProtocolStatus.ERROR
            
        return {
            "success": False,
            "error": str(error),
            "error_type": error_type.value,
            "retry_count": self.retry_count,
            "timestamp": datetime.now()
        }
        
    def reset_connection(self) -> None:
        """Reset connection state"""
        self.status = ProtocolStatus.DISCONNECTED
        self.retry_count = 0
        self.metrics['error_rate'] = 0.0
        self.logger.info("Connection state reset")
        
    def validate_response(
        self, response: Dict[str, Any], required_fields: Optional[list] = None
    ) -> bool:
        """Validate response from resource"""
        # Check basic response structure
        if not all(key in response for key in ['success', 'timestamp', 'data']):
            return False
            
        # Check additional required fields
        if required_fields:
            if not all(key in response['data'] for key in required_fields):
                return False
                
        # Validate timestamp
        try:
            if isinstance(response['timestamp'], str):
                datetime.fromisoformat(response['timestamp'].replace('Z', '+00:00'))
            elif not isinstance(response['timestamp'], datetime):
                return False
        except ValueError:
            return False
            
        return True
        
    def get_metrics(self) -> Dict[str, float]:
        """Get current protocol metrics"""
        return self.metrics.copy()
        
    def validate(self) -> bool:
        """Validate protocol configuration and state"""
        try:
            # Check required configuration
            if not self.protocol_id or not self.config:
                return False
                
            # Validate intervals
            if self.reconnect_interval <= 0 or self.timeout <= 0:
                return False
                
            # Validate security if enabled
            if self.username and not self.password:
                return False
            if self.ssl_context and not hasattr(self.ssl_context, 'wrap_socket'):
                return False
                
            return True
        except Exception:
            return False 