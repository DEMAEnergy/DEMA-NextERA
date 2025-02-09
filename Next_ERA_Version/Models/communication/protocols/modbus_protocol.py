from typing import Dict, Any, Optional
from ..base_protocol import BaseProtocol
import asyncio
from pymodbus.client import ModbusTcpClient
from datetime import datetime

class ModbusProtocol(BaseProtocol):
    """Modbus protocol implementation"""
    
    def __init__(self, protocol_id: str, config: Dict[str, Any]):
        super().__init__(protocol_id, config)
        self.host = config['host']
        self.port = config.get('port', 502)
        self.unit_id = config.get('unit_id', 1)
        self.client = None
        self.register_map = config['register_map']
        
    async def connect(self) -> bool:
        try:
            self.client = ModbusTcpClient(self.host, port=self.port)
            connected = await self.client.connect()
            if connected:
                self.status = "connected"
                self.update_last_communication()
            return connected
        except Exception as e:
            return self.handle_error(e)
            
    async def disconnect(self) -> bool:
        try:
            if self.client:
                self.client.close()
                self.status = "disconnected"
            return True
        except Exception as e:
            return self.handle_error(e)
    
    async def send_command(self, command: str, params: Dict[str, Any]) -> Dict[str, Any]:
        try:
            if not self.client or not self.client.connected:
                await self.connect()
                
            register = self.register_map.get(command)
            if not register:
                raise ValueError(f"Unknown command: {command}")
                
            # Convert value based on register type
            value = params.get('value', 0)
            if register['type'] == 'holding':
                response = await self.client.write_register(
                    register['address'],
                    value,
                    unit=self.unit_id
                )
            elif register['type'] == 'coil':
                response = await self.client.write_coil(
                    register['address'],
                    bool(value),
                    unit=self.unit_id
                )
                
            self.update_last_communication()
            return {
                "success": not response.isError(),
                "timestamp": datetime.now(),
                "data": {"register": register['address'], "value": value}
            }
        except Exception as e:
            return self.handle_error(e)
    
    async def read_status(self) -> Dict[str, Any]:
        try:
            if not self.client or not self.client.connected:
                await self.connect()
                
            status_data = {}
            for name, register in self.register_map.items():
                if register['type'] == 'input':
                    response = await self.client.read_input_registers(
                        register['address'],
                        register.get('count', 1),
                        unit=self.unit_id
                    )
                elif register['type'] == 'holding':
                    response = await self.client.read_holding_registers(
                        register['address'],
                        register.get('count', 1),
                        unit=self.unit_id
                    )
                    
                if not response.isError():
                    status_data[name] = response.registers[0]
                    
            self.update_last_communication()
            return {
                "success": True,
                "timestamp": datetime.now(),
                "data": status_data
            }
        except Exception as e:
            return self.handle_error(e)
    
    async def subscribe_to_updates(self, callback: callable) -> bool:
        """
        Modbus doesn't support native subscriptions, so we implement polling
        """
        try:
            while self.status == "connected":
                status = await self.read_status()
                if status['success']:
                    await callback(status['data'])
                await asyncio.sleep(self.config.get('polling_interval', 1))
            return True
        except Exception as e:
            return self.handle_error(e) 