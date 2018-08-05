# chat/routing.py
from django.conf.urls import url

from . import pasur_interface

websocket_urlpatterns = [
    url(r'^ws/pasur/(?P<match_id>[^/]+)/$', pasur_interface.PasurInterface, name='pasur_game_ws'),
]
