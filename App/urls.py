from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('api/get_gym_cards/', views.get_gym_cards, name='get_gym_cards'),
    path('api/create_gym_card/', views.create_gym_card, name='create_gym_card'),
    path('api/delete_gym_card/', views.delete_gym_card, name='delete_gym_card'),
    path('api/update_gym_card/', views.update_gym_card, name='update_gym_card'),
    path('api/sort_gym_card/', views.sort_gym_card, name='sort_gym_card'),
    path('api/search_gym_card/', views.search_gym_card, name='search_gym_card'),
    path('api/get_gym_card/', views.get_gym_card, name='get_gym_card'),
    path('api/get_gym_card_by_id/', views.get_gym_card_by_id, name='get_gym_card_by_id'),
    path('api/get_gym_card_by_status/', views.get_gym_card_by_status, name='get_gym_card_by_status'),
    path('api/get_gym_card_by_priority/', views.get_gym_card_by_priority, name='get_gym_card_by_priority'),
    path('api/get_gym_card_by_date/', views.get_gym_card_by_date, name='get_gym_card_by_date'),
    path('api/mark_card_expired/', views.mark_card_expired, name='mark_card_expired'),
    path('api/create_gym_card_with_page/', views.create_gym_card_with_page, name='create_gym_card_with_page'),
]
