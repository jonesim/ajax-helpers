from django.urls import path

from . import consumers

websocket_urlpatterns = [
    path('helpers/<str:slug>/', consumers.ConsumerHelper.as_asgi()),
]
