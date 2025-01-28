from channels.generic.websocket import AsyncWebsocketConsumer
from channels.exceptions import StopConsumer
import json
import logging

logger = logging.getLogger(__name__)

class GymCardConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        try:
            self.group_name = "gym_cards"
            # Join room group
            await self.channel_layer.group_add(
                self.group_name,
                self.channel_name
            )
            await self.accept()
            logger.info(f"WebSocket connected: {self.channel_name}")
        except Exception as e:
            logger.error(f"WebSocket connection error: {str(e)}")
            raise StopConsumer()

    async def disconnect(self, close_code):
        try:
            # Leave room group
            await self.channel_layer.group_discard(
                self.group_name,
                self.channel_name
            )
            logger.info(f"WebSocket disconnected: {self.channel_name}")
        except Exception as e:
            logger.error(f"WebSocket disconnection error: {str(e)}")

    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
            logger.info(f"Received message: {data}")
        except Exception as e:
            logger.error(f"WebSocket receive error: {str(e)}")

    async def gym_card_update(self, event):
        try:
            await self.send(text_data=json.dumps(event['data']))
            logger.info(f"Message sent to {self.channel_name}: {event['data']}")
        except Exception as e:
            logger.error(f"WebSocket send error: {str(e)}")
            
    async def gym_card_dot_update(self, event):
        """Handler for gym_card.update messages"""
        try:
            # Ensure we're sending the complete data structure
            message = {
                'action': event['data']['action'],
                'data': {
                    'id': event['data']['data']['id'],
                    'status': event['data']['data']['status'],
                    'is_expired': event['data']['data']['is_expired'],
                    'priority': event['data']['data']['priority']
                }
            }
            await self.send(text_data=json.dumps(message))
            logger.info(f"Message sent to {self.channel_name}: {message}")
        except Exception as e:
            logger.error(f"WebSocket send error: {str(e)}")
