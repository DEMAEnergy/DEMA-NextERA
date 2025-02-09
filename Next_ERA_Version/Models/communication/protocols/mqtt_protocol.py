from typing import Dict, Any, Optional
from ..base_protocol import BaseProtocol
import asyncio
import json
from asyncio_mqtt import Client, MqttError
from datetime import datetime

class MQTTProtocol(BaseProtocol):
    """MQTT protocol implementation"""
    
    def __init__(self, protocol_id: str, config: Dict[str, Any]):
        super().__init__(protocol_id, config)
        self.broker = config['broker']
        self.port = config.get('port', 1883)
        self.username = config.get('username')
        self.password = config.get('password')
        self.topic_prefix = config.get('topic_prefix', 'vpp')
        self.client = None
        self.subscriptions = {}
        
    async def connect(self) -> bool:
        try:
            self.client = Client(
                hostname=self.broker,
                port=self.port,
                username=self.username,
                password=self.password
            )
            await self.client.connect()
            self.status = "connected"
            self.update_last_communication()
            return True
        except Exception as e:
            return self.handle_error(e)
            
    async def disconnect(self) -> bool:
        try:
            if self.client:
                await self.client.disconnect()
                self.status = "disconnected"
            return True
        except Exception as e:
            return self.handle_error(e)
    
    async def send_command(self, command: str, params: Dict[str, Any]) -> Dict[str, Any]:
        try:
            if not self.client:
                await self.connect()
                
            topic = f"{self.topic_prefix}/command/{command}"
            message = {
                "timestamp": datetime.now().isoformat(),
                "command": command,
                "params": params
            }
            
            await self.client.publish(topic, json.dumps(message))
            self.update_last_communication()
            
            return {
                "success": True,
                "timestamp": datetime.now(),
                "data": {"topic": topic, "message": message}
            }
        except Exception as e:
            return self.handle_error(e)
    
    async def read_status(self) -> Dict[str, Any]:
        try:
            if not self.client:
                await self.connect()
                
            # Request status update
            request_topic = f"{self.topic_prefix}/status/request"
            response_topic = f"{self.topic_prefix}/status/response"
            
            # Create a future to store the response
            response_future = asyncio.Future()
            
            async def message_handler(message):
                try:
                    data = json.loads(message.payload)
                    response_future.set_result(data)
                except Exception as e:
                    response_future.set_exception(e)
            
            # Subscribe to response topic
            await self.client.subscribe(response_topic)
            self.subscriptions[response_topic] = message_handler
            
            # Send status request
            await self.client.publish(request_topic, json.dumps({
                "timestamp": datetime.now().isoformat()
            }))
            
            # Wait for response with timeout
            try:
                response = await asyncio.wait_for(response_future, timeout=5.0)
                self.update_last_communication()
                return {
                    "success": True,
                    "timestamp": datetime.now(),
                    "data": response
                }
            except asyncio.TimeoutError:
                return self.handle_error(Exception("Status request timeout"))
            finally:
                # Cleanup subscription
                await self.client.unsubscribe(response_topic)
                self.subscriptions.pop(response_topic, None)
                
        except Exception as e:
            return self.handle_error(e)
    
    async def subscribe_to_updates(self, callback: callable) -> bool:
        try:
            if not self.client:
                await self.connect()
                
            topic = f"{self.topic_prefix}/updates/#"
            
            async def message_handler(message):
                try:
                    data = json.loads(message.payload)
                    await callback(data)
                except Exception as e:
                    self.handle_error(e)
            
            await self.client.subscribe(topic)
            self.subscriptions[topic] = message_handler
            
            # Keep subscription active
            while self.status == "connected":
                await asyncio.sleep(1)
                
            return True
        except Exception as e:
            return self.handle_error(e)
            
    async def _handle_messages(self):
        """Internal message handling loop"""
        async with self.client.messages() as messages:
            async for message in messages:
                handler = self.subscriptions.get(message.topic)
                if handler:
                    await handler(message) 