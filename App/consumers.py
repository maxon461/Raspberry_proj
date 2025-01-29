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
        """Handle incoming WebSocket messages"""
        try:
            text_data_json = json.loads(text_data)
            logger.debug(f"Received WebSocket message: {text_data_json}")
            
            # Handle different message types here if needed
            message_type = text_data_json.get('type')
            if message_type:
                await self.channel_layer.group_send(
                    "gym_cards",
                    {
                        "type": "broadcast_update",
                        "data": text_data
                    }
                )
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in WebSocket message: {e}")
        except Exception as e:
            logger.error(f"Error processing WebSocket message: {e}")

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

    async def broadcast_update(self, event):
        """Handler for broadcast_update messages"""
        try:
            logger.info(f"Received broadcast event: {event}")
            message_data = json.loads(event["data"])
            
            # Ensure message format is consistent
            formatted_message = {
                'type': message_data['type'],
                'data': message_data['card']
            }
            
            # Send the update to the WebSocket
            await self.send(text_data=json.dumps(formatted_message))
            
            # Log based on message type
            if message_data['type'] == 'delete':
                logger.info(f"Delete notification sent for card ID: {message_data['card']['id']}")
            elif message_data['type'] == 'rfid_timeout':
                logger.info(f"RFID timeout notification sent for card {message_data['card']['id']}")
            else:
                logger.info(f"Update sent to client {self.channel_name}")
                
        except Exception as e:
            logger.error(f"Error broadcasting message: {e}", exc_info=True)
