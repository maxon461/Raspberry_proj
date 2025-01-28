from django.http import JsonResponse, HttpResponseRedirect, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render
import json
import logging
from django.db import connection
from App.models import GymCard
from django.utils import timezone

logger = logging.getLogger(__name__)

@csrf_exempt
def get_gym_cards(request):
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

            gym_card = GymCard.objects.create(
                title=title,
                description=description,
                expiration_date=expiration_date,
                status=True,
                priority=priority
            )

            return JsonResponse({
                'status': 'success',
                'message': 'Gym card created successfully',
                'id': gym_card.id
            })

        except json.JSONDecodeError:
            return JsonResponse({
                'status': 'error',
                'message': 'Invalid JSON'
            }, status=400)
        except Exception as e:
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
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            card_id = data.get('id')
            logger.info(card_id)
            if card_id:
                gym_card = GymCard.objects.get(id=card_id)
                gym_card.delete()
                return JsonResponse({'status': 'success', 'message': 'Gym card deleted'})
            return JsonResponse({'status': 'error', 'message': 'Gym card not found'}, status=404)
        except json.JSONDecodeError:
            return JsonResponse({'status': 'error', 'message': 'Invalid JSON'}, status=400)
    return JsonResponse({'status': 'error', 'message': 'Invalid request method'}, status=400)

@csrf_exempt
def update_gym_card(request):
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
def get_gym_card(request):
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