from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    re_path(r'ws/gym_cards/$', consumers.GymCardConsumer.as_asgi()),
]
