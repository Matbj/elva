import json

from asgiref.sync import async_to_sync
from channels.generic.websocket import WebsocketConsumer
from channels.layers import get_channel_layer
from django.contrib.auth.models import User
from django.contrib.humanize.templatetags.humanize import naturaltime
from django.urls import reverse
from django.utils.text import capfirst

from game_engine import models

MENU_CHANNEL_NAME = 'pasur_menu_group'


class PasurMenuInterface(WebsocketConsumer):

    # noinspection PyAttributeOutsideInit
    def connect(self):
        self.user: User = self.scope['user']
        self.player, _ = models.Player.objects.get_or_create(name=self.user.username)
        self.group_name = MENU_CHANNEL_NAME

        # Join room group
        async_to_sync(self.channel_layer.group_add)(
            self.group_name,
            self.channel_name,
        )

        self.accept()
        self.push_to_group()

    def disconnect(self, close_code):
        # Leave room group
        async_to_sync(self.channel_layer.group_discard)(
            self.group_name,
            self.channel_name,
        )

    # Receive message from WebSocket
    # noinspection PyMethodOverriding,PyAttributeOutsideInit
    def receive(self, text_data):
        pass

    def push_to_group(self):
        async_to_sync(self.channel_layer.group_send)(
            self.group_name,
            {
                'type': 'menu_update',
                'matches': [{
                    'id': match.pk,
                    'game_url': reverse('pasur_match', args=[match.id]),
                    'players': [player.player.name for player in match.game_players.all()],
                    'status': capfirst(match.status()),
                    'last_action': naturaltime(match.get_latest_game().modified)
                } for match in models.Match.objects.prefetch_related('game_players').order_by('-created')][0:10],
            }
        )

    def menu_update(self, event):
        matches = event['matches']
        self.send(text_data=json.dumps({'matches': matches}))

    def force_update(self, _):
        self.push_to_group()

    @staticmethod
    def notify_new_game_was_created():
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            MENU_CHANNEL_NAME,
            {"type": "force_update"},
        )

    @staticmethod
    def notify_new_player_joined_game():
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            MENU_CHANNEL_NAME,
            {"type": "force_update"},
        )
