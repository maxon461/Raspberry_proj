from django.contrib import admin
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from App import views  # Update import to use App views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.index, name='index'),
    path('create_gym_card/', views.create_gym_card, name='create_gym_card'),
    path('get_gym_cards/', views.get_gym_cards, name='get_gym_cards'),
    path('delete_gym_card/', views.delete_gym_card, name='delete_gym_card'),
    path('update_gym_card/', views.update_gym_card, name='update_gym_card'),
    path('sort_gym_card/', views.sort_gym_card, name='sort_gym_card'),
    path('search_gym_card/', views.search_gym_card, name='search_gym_card'),
    path('get_gym_card/', views.get_gym_card, name='get_gym_card'),
    path('get_gym_card_by_id/', views.get_gym_card_by_id, name='get_gym_card_by_id'),
    path('get_gym_card_by_status/', views.get_gym_card_by_status, name='get_gym_card_by_status'),
    path('get_gym_card_by_priority/', views.get_gym_card_by_priority, name='get_gym_card_by_priority'),
    path('get_gym_card_by_date/', views.get_gym_card_by_date, name='get_gym_card_by_date'),
    path('mark_card_expired/', views.mark_card_expired, name='mark_card_expired'),
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)