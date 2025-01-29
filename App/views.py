from django.http import JsonResponse, HttpResponseRedirect, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render
import json
import logging
from django.db import connection
from App.models import GymCard
from django.utils import timezone
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
import paho.mqtt.client as mqtt
from datetime import datetime
import threading
import time
from django.core.cache import cache
from django.views.decorators.cache import cache_page
from django.conf import settings

logger = logging.getLogger(__name__)

def broadcast_update(action_type, data):
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        "gym_cards",
        {
            "type": "broadcast_update",
            "data": json.dumps({
                'type': action_type,
                'card': data
            })
        }
    )

def verify_mqtt_connection():
    """Helper function to verify MQTT broker is running"""
    try:
        # Create client with specific protocol version
        client = mqtt.Client(client_id="test_connection", protocol=mqtt.MQTTv311)
        client.loop_start()
        
        # Connect with timeout
        result = client.connect("localhost", 1883, 60)
        if result != 0:
            logger.error(f"MQTT Connect failed with result code: {result}")
            return False
            
        # Wait up to 3 seconds for connection
        for _ in range(30):
            if client.is_connected():
                client.loop_stop()
                client.disconnect()
                return True
            time.sleep(0.1)
            
        client.loop_stop()
        client.disconnect()
        return False
    except Exception as e:
        logger.error(f"MQTT Broker connection failed: {str(e)}")
        return False

@csrf_exempt
def get_gym_cards(request):
    """
    Retrieves all gym cards from database
    
    Args:
        request: HTTP request object
        
    Returns:
        JsonResponse: List of gym cards with their details
        {
            'gym_cards': [
                {
                    'id': int,
                    'Title': str,
                    'Description': str,
                    'DateAdded': datetime,
                    'ExpirationDate': datetime,
                    'Status': bool,
                    'Priority': int,
                    'IsExpired': bool,
                    'rfid_card_id': str
                },
                ...
            ]
        }
    """
    try:
        gym_cards = GymCard.objects.all()
        gym_cards_data = []

        for card in gym_cards:
            # Check if card is expired
            if not card.is_expired:
                now = timezone.now()
                expiration = card.expiration_date
                if now > expiration:
                    card.status = False
                    card.is_expired = True
                    card.save()

            gym_cards_data.append({
                'id': card.id,
                'Title': card.title,
                'Description': card.description,
                'DateAdded': card.date_added,
                'ExpirationDate': card.expiration_date,
                'Status': card.status,
                'Priority': card.priority,
                'IsExpired': card.is_expired,
                'rfid_card_id': card.rfid_card_id
            })

        return JsonResponse({'gym_cards': gym_cards_data}, safe=False)

    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)

@csrf_exempt
def create_gym_card(request):
    """
    Creates a new gym card in the database
    
    Args:
        request: HTTP POST request with JSON body containing:
            {
                'title': str,
                'description': str,
                'expiration_date': datetime,
                'priority': int
            }
            
    Returns:
        JsonResponse: Created card details or error message
        Success: {
            'status': 'success',
            'message': str,
            'card': {card_details}
        }
        Error: {
            'status': 'error',
            'message': str
        }
    """
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            title = data.get('title')
            description = data.get('description')
            expiration_date = data.get('expiration_date')
            priority = int(data.get('priority', 0))

            if not all([title, description, expiration_date]):
                return JsonResponse({
                    'status': 'error',
                    'message': 'Missing required fields'
                }, status=400)

            try:
                gym_card = GymCard.objects.create(
                    title=title,
                    description=description,
                    expiration_date=expiration_date,
                    status='true',  # Changed from 'true' to 'active'
                    priority=priority,
                    is_expired=False
                )

                # Prepare card data for broadcast
                card_data = {
                    'id': gym_card.id,
                    'Title': gym_card.title,
                    'Description': gym_card.description,
                    'Status': gym_card.status,
                    'DateAdded': gym_card.date_added.isoformat(),
                    'ExpirationDate': gym_card.expiration_date,
                    'Priority': gym_card.priority,
                    'IsExpired': gym_card.is_expired
                }

                # Broadcast the creation
                try:
                    broadcast_update('card_update', card_data)
                except Exception as e:
                    logger.error(f"Broadcast error: {e}")

                return JsonResponse({
                    'status': 'success',
                    'message': 'Gym card created successfully',
                    'card': card_data
                })

            except Exception as e:
                logger.error(f"Database error: {e}")
                return JsonResponse({
                    'status': 'error',
                    'message': str(e)
                }, status=500)

        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error: {e}")
            return JsonResponse({
                'status': 'error',
                'message': 'Invalid JSON format'
            }, status=400)
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            }, status=500)

    return JsonResponse({
        'status': 'error',
        'message': 'Invalid request method'
    }, status=405)

@csrf_exempt
def create_gym_card_with_page(request):
    """
    Creates a new gym card with RFID card association
    """
    if request.method == 'POST':
        logger.info("Starting gym card creation with RFID...")
        try:
            # Try MQTT connection with retries
            logger.info("Verifying MQTT connection...")
            connected = False
            for attempt in range(3):
                logger.info(f"MQTT connection attempt {attempt + 1}/3")
                if verify_mqtt_connection():
                    connected = True
                    logger.info("MQTT connection successful")
                    break
                logger.warning(f"MQTT connection attempt {attempt + 1} failed, retrying...")
                time.sleep(1)
                
            if not connected:
                logger.error("Failed to connect to MQTT broker after 3 attempts")
                return JsonResponse({
                    'status': 'error',
                    'message': 'Unable to connect to MQTT broker after 3 attempts. Please check if Mosquitto service is running.'
                }, status=503)

            logger.info("Parsing request data...")
            data = json.loads(request.body)
            client = None
            
            # Validate required fields
            logger.info("Validating required fields...")
            if not all([data.get('title'), data.get('description'), data.get('expiration_date')]):
                logger.error("Missing required fields in request")
                return JsonResponse({
                    'status': 'error',
                    'message': 'Missing required fields'
                }, status=400)

            # Create the card first
            logger.info("Creating gym card in database...")
            gym_card = GymCard.objects.create(
                title=data['title'],
                description=data['description'],
                expiration_date=data['expiration_date'],
                priority=data.get('priority', 0),
                status='true',
                is_expired=False
            )
            logger.info(f"Gym card created with ID: {gym_card.id}")

            def mqtt_handler():
                nonlocal client
                retry_count = 0
                max_retries = 3
                logger.info("Starting MQTT handler...")

                while retry_count < max_retries:
                    try:
                        logger.info(f"Creating MQTT client (attempt {retry_count + 1}/{max_retries})")
                        client = mqtt.Client(
                            client_id=f"django_client_{timezone.now().timestamp()}", 
                            protocol=mqtt.MQTTv311
                        )
                        
                        def on_connect(client, userdata, flags, rc):
                            logger.info(f"MQTT on_connect callback triggered with result code: {rc}")
                            if rc != 0:
                                logger.error(f"Failed to connect to MQTT broker with code: {rc}")
                                raise Exception(f"MQTT connection failed with code {rc}")
                            logger.info("Successfully connected to MQTT broker")
                            client.subscribe("rfid/cards", qos=1)
                            logger.info("Subscribed to rfid/cards topic with QoS 1")

                        def on_disconnect(client, userdata, rc):
                            if rc != 0:
                                logger.error(f"Unexpected MQTT disconnection with code: {rc}")
                            else:
                                logger.info("MQTT client disconnected successfully")

                        def on_message(client, userdata, msg):
                            try:
                                logger.info(f"Received MQTT message on topic {msg.topic}")
                                logger.debug(f"Raw message payload: {msg.payload}")
                                received_data = json.loads(msg.payload.decode())
                                card_id = received_data.get('card_id')
                                logger.info(f"Extracted card_id: {card_id}")
                                
                                if card_id:
                                    logger.info(f"Processing RFID card: {card_id}")
                                    try:
                                        card = GymCard.objects.get(id=gym_card.id)
                                        logger.info(f"Found gym card {card.id}")
                                        card.rfid_card_id = card_id
                                        card.save()
                                        logger.info(f"Updated gym card {card.id} with RFID {card_id}")
                                        
                                        # Broadcast update
                                        logger.info("Broadcasting card update...")
                                        broadcast_update('card_update', {
                                            'id': card.id,
                                            'Title': card.title,
                                            'rfid_card_id': card_id,
                                            'Status': card.status
                                        })
                                        logger.info("Broadcast update sent successfully")
                                        
                                    except GymCard.DoesNotExist:
                                        logger.error(f"Gym card {gym_card.id} not found")
                                    except Exception as e:
                                        logger.error(f"Error updating card: {str(e)}")
                                    finally:
                                        logger.info("Disconnecting MQTT client")
                                        client.disconnect()
                                else:
                                    logger.error("No card_id in MQTT message")
                                    
                            except json.JSONDecodeError as e:
                                logger.error(f"Failed to decode MQTT message: {str(e)}")
                            except Exception as e:
                                logger.error(f"MQTT message processing error: {str(e)}")
                            finally:
                                client.disconnect()
                                # Invalidate cache after update
                                cache.delete('all_gym_cards')
                                cache.delete(f'gym_card_{gym_card.id}')

                        # ...rest of mqtt_handler implementation...
                        
                        logger.info("Setting up MQTT callbacks...")
                        client.on_connect = on_connect
                        client.on_message = on_message
                        client.on_disconnect = on_disconnect

                        logger.info("Connecting to MQTT broker...")
                        client.connect("localhost", 1883, 60)
                        client.loop_start()
                        logger.info("MQTT client loop started")
                        
                        # Run for maximum 30 seconds
                        logger.info("Setting up 30-second timeout")
                        def on_timeout():
                            logger.info("MQTT timeout reached")
                            try:
                                client.disconnect()
                                # Send timeout message through WebSocket
                                channel_layer = get_channel_layer()
                                async_to_sync(channel_layer.group_send)(
                                    "gym_cards",
                                    {
                                        "type": "broadcast_update",
                                        "data": json.dumps({
                                            'type': 'rfid_timeout',
                                            'card': {'id': gym_card.id}
                                        })
                                    }
                                )
                            except Exception as e:
                                logger.error(f"Error in timeout handler: {e}")

                        threading.Timer(30.0, on_timeout).start()
                        
                        # Keep the thread alive
                        while client.is_connected():
                            time.sleep(0.1)
                        
                        break
                        
                    except Exception as e:
                        retry_count += 1
                        logger.error(f"MQTT connection attempt {retry_count} failed: {str(e)}")
                        if client:
                            try:
                                client.disconnect()
                                logger.info("Disconnected failed MQTT client")
                            except:
                                pass
                        if retry_count >= max_retries:
                            logger.error("Max MQTT connection retries reached")
                            gym_card.delete()
                            logger.info(f"Deleted gym card {gym_card.id} due to MQTT connection failure")
                            raise Exception("Max MQTT connection retries reached")
                        time.sleep(1)

            logger.info("Starting MQTT handler thread...")
            thread = threading.Thread(target=mqtt_handler, daemon=True)
            thread.start()
            logger.info("MQTT handler thread started")
            
            return JsonResponse({
                'status': 'waiting_for_card',
                'card_id': gym_card.id,
                'message': 'Listening for RFID card...',
                'timeout': 30  # Add timeout value to response
            })
            
        except Exception as e:
            logger.error(f"Card creation error: {str(e)}", exc_info=True)
            if 'gym_card' in locals():
                logger.info(f"Cleaning up gym card {gym_card.id}")
                gym_card.delete()
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            }, status=500)
            
    logger.warning("Invalid request method for create_gym_card_with_page")
    return JsonResponse({
        'status': 'error',
        'message': 'Invalid request method'
    }, status=405)

@csrf_exempt
def delete_gym_card(request):
    """
    Deletes a gym card from the database
    
    Args:
        request: HTTP POST request with JSON body containing:
            {
                'id': int
            }
            
    Returns:
        JsonResponse: Success or error message
        Success: {
            'status': 'success',
            'message': 'Gym card deleted'
        }
        Error: {
            'status': 'error',
            'message': str
        }
    """
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            card_id = data.get('id')
            logger.info(f"Attempting to delete card {card_id}")
            
            if card_id:
                try:
                    gym_card = GymCard.objects.get(id=card_id)
                    # Store card info before deletion
                    card_info = {
                        'id': gym_card.id,
                        'Title': gym_card.title
                    }
                    gym_card.delete()
                    logger.info(f"Card {card_id} deleted successfully")
                    
                    # Send delete notification to all clients
                    message = {
                        'type': 'delete',
                        'card': {'id': card_id}  # Consistent format with other messages
                    }
                    
                    channel_layer = get_channel_layer()
                    async_to_sync(channel_layer.group_send)(
                        "gym_cards",
                        {
                            "type": "broadcast_update",
                            "data": json.dumps(message)
                        }
                    )
                    logger.info(f"Delete broadcast sent: {message}")
                    
                    # Invalidate cache
                    cache.delete('all_gym_cards')
                    cache.delete(f'gym_card_{card_id}')
                    
                    return JsonResponse({
                        'status': 'success',
                        'message': 'Gym card deleted',
                        'deleted_card': card_info
                    })
                except GymCard.DoesNotExist:
                    logger.error(f"Card {card_id} not found")
                    return JsonResponse({
                        'status': 'error',
                        'message': 'Gym card not found'
                    }, status=404)
            
            return JsonResponse({
                'status': 'error',
                'message': 'Card ID required'
            }, status=400)
            
        except json.JSONDecodeError:
            logger.error("Invalid JSON in delete request")
            return JsonResponse({
                'status': 'error',
                'message': 'Invalid JSON'
            }, status=400)
        except Exception as e:
            logger.error(f"Error deleting card: {str(e)}", exc_info=True)
            return JsonResponse({
                'status': 'error',
                'message': f'Error deleting card: {str(e)}'
            }, status=500)
    
    return JsonResponse({
        'status': 'error',
        'message': 'Invalid request method'
    }, status=405)

@csrf_exempt
def update_gym_card(request):
    """
    Updates gym card status and priority
    
    Args:
        request: HTTP POST request with JSON body containing:
            {
                'id': int,
                'status': str,
                'priority': int (optional)
            }
            
    Returns:
        JsonResponse: Success or error message
        Success: {
            'status': 'success',
            'message': str
        }
        Error: {
            'status': 'error',
            'message': str
        }
    """
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            card_id = data.get('id')
            status = data.get('status')

            if card_id and status is not None:
                try:
                    gym_card = GymCard.objects.get(id=card_id)
                    # Set status and handle related fields
                    if status == 'active':
                        gym_card.status = status
                        gym_card.is_expired = False  # Reset expired status
                    elif status in ['expired', 'deactivated']:
                        gym_card.status = status
                        gym_card.is_expired = True
                    else:
                        gym_card.status = status

                    if 'priority' in data:
                        gym_card.priority = data['priority']
                        
                    gym_card.save()
                    
                    # Broadcast the update
                    channel_layer = get_channel_layer()
                    async_to_sync(channel_layer.group_send)(
                        "gym_cards",
                        {
                            "type": "broadcast_update",
                            "data": json.dumps({
                                'type': 'card_update',
                                'card': {
                                    'id': gym_card.id,
                                    'Title': gym_card.title,
                                    'Description': gym_card.description,
                                    'Status': gym_card.status,
                                    'DateAdded': gym_card.date_added.isoformat(),
                                    'ExpirationDate': gym_card.expiration_date.isoformat(),
                                    'Priority': gym_card.priority,
                                    'IsExpired': gym_card.is_expired
                                }
                            })
                        }
                    )
                    
                    # Invalidate cache after update
                    cache.delete('all_gym_cards')
                    cache.delete(f'gym_card_{card_id}')
                    
                    return JsonResponse({
                        'status': 'success',
                        'message': f'Gym card {status}'
                    })
                except GymCard.DoesNotExist:
                    return JsonResponse({
                        'status': 'error',
                        'message': 'Gym card not found'
                    }, status=404)

            return JsonResponse({
                'status': 'error',
                'message': 'Invalid card or status'
            }, status=400)
        except json.JSONDecodeError:
            return JsonResponse({
                'status': 'error',
                'message': 'Invalid JSON'
            }, status=400)
    return JsonResponse({
        'status': 'error',
        'message': 'Invalid request method'
    }, status=400)

@csrf_exempt
def sort_gym_card(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            sort_by = data.get('sort_by')
            gym_cards = GymCard.objects.all()
            gym_cards_data = []

            for card in gym_cards:
                gym_cards_data.append({
                    'id': card.id,
                    'Title': card.title,
                    'Description': card.description,
                    'DateAdded': card.date_added,
                    'ExpirationDate': card.expiration_date,
                    'Status': card.status,
                    'Priority': card.priority,
                })

            if sort_by == 'date':
                gym_cards_data = sorted(gym_cards_data, key=lambda x: x['DateAdded'])
            elif sort_by == 'status':
                gym_cards_data = sorted(gym_cards_data, key=lambda x: x['Status'])
            elif sort_by == 'priority':
                gym_cards_data = sorted(gym_cards_data, key=lambda x: x['Priority'])
            else:
                return JsonResponse({'status': 'error', 'message': 'Invalid sort_by parameter'}, status=400)

            return JsonResponse({'gym_cards': gym_cards_data}, safe=False)
        except json.JSONDecodeError:
            return JsonResponse({'status': 'error', 'message': 'Invalid JSON'}, status=400)
    return JsonResponse({'status': 'error', 'message': 'Invalid request method'}, status=400)

@csrf_exempt
def search_gym_card(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            search_by = data.get('search_by')
            search_term = data.get('search_term')
            gym_cards = GymCard.objects.all()
            gym_cards_data = []

            for card in gym_cards:
                gym_cards_data.append({
                    'id': card.id,
                    'Title': card.title,
                    'Description': card.description,
                    'DateAdded': card.date_added,
                    'ExpirationDate': card.expiration_date,
                    'Status': card.status,
                    'Priority': card.priority,
                })

            search_results = []
            for card in gym_cards_data:
                if search_by in card and search_term in card[search_by]:
                    search_results.append(card)

            return JsonResponse({'gym_cards': search_results}, safe=False)
        except json.JSONDecodeError:
            return JsonResponse({'status': 'error', 'message': 'Invalid JSON'}, status=400)
    return JsonResponse({'status': 'error', 'message': 'Invalid request method'}, status=400)

@csrf_exempt
@cache_page(5)  # Cache for 5 seconds
def get_gym_card(request):
    """
    Get gym card(s) from database with caching
    
    Methods:
        GET: Returns all cards or specific card if ID provided in query params
        POST: Returns specific card by ID in request body
    """
    if request.method == 'GET':
        try:
            card_id = request.GET.get('id')
            cache_key = f'gym_card_{card_id}' if card_id else 'all_gym_cards'
            
            # Try to get data from cache first
            cached_data = cache.get(cache_key)
            if cached_data:
                logger.debug(f"Returning cached data for key: {cache_key}")
                return JsonResponse(cached_data, safe=False)
            
            if card_id:
                try:
                    gym_card = GymCard.objects.get(id=card_id)
                    data = {
                        'id': gym_card.id,
                        'Title': gym_card.title,
                        'Description': gym_card.description,
                        'DateAdded': gym_card.date_added,
                        'ExpirationDate': gym_card.expiration_date,
                        'Status': gym_card.status,
                        'Priority': gym_card.priority,
                        'rfid_card_id': gym_card.rfid_card_id,
                        'IsExpired': gym_card.is_expired
                    }
                    # Cache for 5 seconds
                    cache.set(cache_key, data, 5)
                    return JsonResponse(data)
                except GymCard.DoesNotExist:
                    return JsonResponse({
                        'status': 'error',
                        'message': 'Gym card not found'
                    }, status=404)
            else:
                gym_cards = GymCard.objects.all()
                data = {
                    'gym_cards': [{
                        'id': card.id,
                        'Title': card.title,
                        'Description': card.description,
                        'DateAdded': card.date_added,
                        'ExpirationDate': card.expiration_date,
                        'Status': card.status,
                        'Priority': card.priority,
                        'rfid_card_id': card.rfid_card_id,
                        'IsExpired': card.is_expired
                    } for card in gym_cards]
                }
                # Cache for 5 seconds
                cache.set(cache_key, data, 5)
                return JsonResponse(data, safe=False)
                
        except Exception as e:
            logger.error(f"Error in get_gym_card GET: {str(e)}")
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            }, status=500)
        except json.JSONDecodeError:
            return JsonResponse({
                'status': 'error',
                'message': 'Invalid JSON'
            }, status=400)
    
    return JsonResponse({
        'status': 'error',
        'message': 'Method not allowed'
    }, status=405)

@csrf_exempt
def get_gym_card_by_id(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            card_id = data.get('id')
            if card_id:
                gym_card = GymCard.objects.get(id=card_id)
                return JsonResponse({
                    'id': gym_card.id,
                    'Title': gym_card.title,
                    'Description': gym_card.description,
                    'DateAdded': gym_card.date_added,
                    'ExpirationDate': gym_card.expiration_date,
                    'Status': gym_card.status,
                    'Priority': gym_card.priority,
                })
            return JsonResponse({'status': 'error', 'message': 'Gym card not found'}, status=404)
        except GymCard.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Gym card not found'}, status=404)
        except json.JSONDecodeError:
            return JsonResponse({'status': 'error', 'message': 'Invalid JSON'}, status=400)
    return JsonResponse({'status': 'error', 'message': 'Invalid request method'}, status=400)

@csrf_exempt
def get_gym_card_by_status(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            status = data.get('status')
            gym_cards = GymCard.objects.filter(status=status)
            gym_cards_data = []

            for card in gym_cards:
                gym_cards_data.append({
                    'id': card.id,
                    'Title': card.title,
                    'Description': card.description,
                    'DateAdded': card.date_added,
                    'ExpirationDate': card.expiration_date,
                    'Status': card.status,
                    'Priority': card.priority,
                })

            return JsonResponse({'gym_cards': gym_cards_data}, safe=False)
        except json.JSONDecodeError:
            return JsonResponse({'status': 'error', 'message': 'Invalid JSON'}, status=400)
    return JsonResponse({'status': 'error', 'message': 'Invalid request method'}, status=400)

@csrf_exempt
def get_gym_card_by_priority(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            priority = data.get('priority')
            gym_cards = GymCard.objects.filter(priority=priority)
            gym_cards_data = []

            for card in gym_cards:
                gym_cards_data.append({
                    'id': card.id,
                    'Title': card.title,
                    'Description': card.description,
                    'DateAdded': card.date_added,
                    'ExpirationDate': card.expiration_date,
                    'Status': card.status,
                    'Priority': card.priority,
                })

            return JsonResponse({'gym_cards': gym_cards_data}, safe=False)
        except json.JSONDecodeError:
            return JsonResponse({'status': 'error', 'message': 'Invalid JSON'}, status=400)
    return JsonResponse({'status': 'error', 'message': 'Invalid request method'}, status=400)

@csrf_exempt
def get_gym_card_by_date(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            date = data.get('date')
            gym_cards = GymCard.objects.filter(date_added=date)
            gym_cards_data = []

            for card in gym_cards:
                gym_cards_data.append({
                    'id': card.id,
                    'Title': card.title,
                    'Description': card.description,
                    'DateAdded': card.date_added,
                    'ExpirationDate': card.expiration_date,
                    'Status': card.status,
                    'Priority': card.priority,
                })

            return JsonResponse({'gym_cards': gym_cards_data}, safe=False)
        except json.JSONDecodeError:
            return JsonResponse({'status': 'error', 'message': 'Invalid JSON'}, status=400)
    return JsonResponse({'status': 'error', 'message': 'Invalid request method'}, status=400)

@csrf_exempt
def mark_card_expired(request):
    """
    Marks a gym card as expired
    
    Args:
        request: HTTP POST request with JSON body containing:
            {
                'id': int
            }
            
    Returns:
        JsonResponse: Success or error message
        Success: {
            'status': 'success',
            'message': 'Card marked as expired'
        }
        Error: {
            'status': 'error',
            'message': str
        }
    """
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            card_id = data.get('id')
            
            if card_id:
                try:
                    gym_card = GymCard.objects.get(id=card_id)
                    gym_card.status = False
                    gym_card.is_expired = True
                    gym_card.save()
                    return JsonResponse({
                        'status': 'success',
                        'message': 'Card marked as expired'
                    })
                except GymCard.DoesNotExist:
                    return JsonResponse({
                        'status': 'error',
                        'message': 'Card not found'
                    }, status=404)
            
            return JsonResponse({
                'status': 'error',
                'message': 'Invalid card ID'
            }, status=400)
        except json.JSONDecodeError:
            return JsonResponse({
                'status': 'error',
                'message': 'Invalid JSON'
            }, status=400)
    return JsonResponse({
        'status': 'error',
        'message': 'Invalid request method'
    }, status=405)

def index(request):
    return render(request, 'index.html')
