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

logger = logging.getLogger(__name__)

def broadcast_update(action_type, data):
    """
    Broadcasts updates to all connected WebSocket clients
    
    Args:
        action_type (str): Type of action ('card_update' or 'delete')
        data (dict): Card data to broadcast
        
    Returns:
        None
    """
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
                    'IsExpired': bool
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
            })

        return JsonResponse({'gym_cards': gym_cards_data}, safe=False)

    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)

@csrf_exempt
def create_gym_card(request):
    """
    Creates a new gym card
    
    Args:
        request: HTTP POST request with JSON body containing:
            - title: str
            - description: str
            - expiration_date: datetime
            - priority: int (optional)
            
    Returns:
        JsonResponse: Created card details or error message
        Success: {
            'status': 'success',
            'message': str,
            'card': dict with card details
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
def delete_gym_card(request):
    """
    Deletes a gym card by ID
    
    Args:
        request: HTTP POST request with JSON body containing:
            - id: int (card ID)
            
    Returns:
        JsonResponse: Success or error message
        Success: {'status': 'success', 'message': 'Gym card deleted'}
        Error: {'status': 'error', 'message': str}
    """
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            card_id = data.get('id')
            logger.info(card_id)
            if card_id:
                gym_card = GymCard.objects.get(id=card_id)
                gym_card.delete()
                
                # Broadcast deletion
                broadcast_update('delete', {'id': card_id})
                
                return JsonResponse({'status': 'success', 'message': 'Gym card deleted'})
            return JsonResponse({'status': 'error', 'message': 'Gym card not found'}, status=404)
        except json.JSONDecodeError:
            return JsonResponse({'status': 'error', 'message': 'Invalid JSON'}, status=400)
    return JsonResponse({'status': 'error', 'message': 'Invalid request method'}, status=400)

@csrf_exempt
def update_gym_card(request):
    """
    Updates gym card status and priority
    
    Args:
        request: HTTP POST request with JSON body containing:
            - id: int (card ID)
            - status: str ('active', 'expired', 'deactivated')
            - priority: int (optional)
            
    Returns:
        JsonResponse: Success or error message
        Success: {'status': 'success', 'message': str}
        Error: {'status': 'error', 'message': str}
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
    """
    Sorts gym cards by specified criteria
    
    Args:
        request: HTTP POST request with JSON body containing:
            - sort_by: str ('date', 'status', or 'priority')
            
    Returns:
        JsonResponse: Sorted list of gym cards or error message
        Success: {'gym_cards': [sorted card objects]}
        Error: {'status': 'error', 'message': str}
    """
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
    """
    Searches gym cards by specified criteria
    
    Args:
        request: HTTP POST request with JSON body containing:
            - search_by: str (field name)
            - search_term: str (search value)
            
    Returns:
        JsonResponse: Matching gym cards or error message
        Success: {'gym_cards': [matching card objects]}
        Error: {'status': 'error', 'message': str}
    """
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
def get_gym_card(request):
    """
    Retrieves a single gym card by ID
    
    Args:
        request: HTTP POST request with JSON body containing:
            - id: int (card ID)
            
    Returns:
        JsonResponse: Card details or error message
        Success: {card object with all details}
        Error: {'status': 'error', 'message': str}
    """
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
def get_gym_card_by_id(request):
    """
    Alternative method to retrieve a single gym card by ID
    
    Args:
        request: HTTP POST request with JSON body containing:
            - id: int (card ID)
            
    Returns:
        JsonResponse: Card details or error message
        Success: {card object with all details}
        Error: {'status': 'error', 'message': str}
    """
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
    """
    Retrieves gym cards filtered by status
    
    Args:
        request: HTTP POST request with JSON body containing:
            - status: str/bool (card status)
            
    Returns:
        JsonResponse: List of matching cards or error message
        Success: {'gym_cards': [matching card objects]}
        Error: {'status': 'error', 'message': str}
    """
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
    """
    Retrieves gym cards filtered by priority level
    
    Args:
        request: HTTP POST request with JSON body containing:
            - priority: int
            
    Returns:
        JsonResponse: List of matching cards or error message
        Success: {'gym_cards': [matching card objects]}
        Error: {'status': 'error', 'message': str}
    """
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
    """
    Retrieves gym cards filtered by date added
    
    Args:
        request: HTTP POST request with JSON body containing:
            - date: datetime
            
    Returns:
        JsonResponse: List of matching cards or error message
        Success: {'gym_cards': [matching card objects]}
        Error: {'status': 'error', 'message': str}
    """
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
            - id: int (card ID)
            
    Returns:
        JsonResponse: Success or error message
        Success: {'status': 'success', 'message': 'Card marked as expired'}
        Error: {'status': 'error', 'message': str}
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
    """
    Renders the main index page
    
    Args:
        request: HTTP request object
        
    Returns:
        Rendered index.html template
    """
    return render(request, 'index.html')
