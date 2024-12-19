from django.urls import re_path
from . import views

websocket_urlpatterns = [
    re_path(r"ws/chat/$", views.ChatConsumer.as_asgi()),
]
