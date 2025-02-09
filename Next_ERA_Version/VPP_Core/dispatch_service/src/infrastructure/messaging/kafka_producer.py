import json
from typing import Any, Dict, Optional
from kafka import KafkaProducer as KafkaClient
from kafka.errors import KafkaError
from datetime import datetime
from ...core.models.optimization import DispatchSchedule

class KafkaProducer:
    """Kafka producer for publishing dispatch-related messages"""
    
    def __init__(self, bootstrap_servers: str):
        self.producer = KafkaClient(
            bootstrap_servers=bootstrap_servers,
            value_serializer=lambda v: json.dumps(v).encode('utf-8'),
            key_serializer=lambda k: k.encode('utf-8') if k else None
        )
        
    async def publish_schedule(self, schedule: DispatchSchedule) -> bool:
        """Publish dispatch schedule to Kafka"""
        try:
            # Convert schedule to dictionary
            schedule_dict = schedule.dict()
            
            # Add metadata
            message = {
                "type": "dispatch_schedule",
                "timestamp": datetime.utcnow().isoformat(),
                "schedule": schedule_dict
            }
            
            # Send message
            future = self.producer.send(
                topic="dispatch_schedules",
                key=schedule.schedule_id,
                value=message
            )
            
            # Wait for message to be sent
            future.get(timeout=10)
            return True
            
        except KafkaError as e:
            print(f"Failed to publish schedule: {str(e)}")
            return False
            
    async def publish_command(
        self,
        topic: str,
        key: str,
        value: Dict[str, Any]
    ) -> bool:
        """Publish command message to Kafka"""
        try:
            # Add metadata
            message = {
                "type": "command",
                "timestamp": datetime.utcnow().isoformat(),
                "payload": value
            }
            
            # Send message
            future = self.producer.send(
                topic=topic,
                key=key,
                value=message
            )
            
            # Wait for message to be sent
            future.get(timeout=10)
            return True
            
        except KafkaError as e:
            print(f"Failed to publish command: {str(e)}")
            return False
            
    def close(self):
        """Close Kafka producer"""
        if self.producer:
            self.producer.close() 