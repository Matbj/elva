# chat/routing.py
from django.conf.urls import url

from ws.pasur_interface import PasurInterface
from ws.pasur_menu_interface import PasurMenuInterface

websocket_urlpatterns = [
    url(r'^ws/pasur/(?P<match_id>[^/]+)/$', PasurInterface, name='pasur_game_ws'),
    url(r'^ws/pasur/$', PasurMenuInterface, name='pasur_menu_ws'),
]
