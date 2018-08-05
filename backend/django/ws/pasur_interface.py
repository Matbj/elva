import json
from django.db import transaction

from asgiref.sync import async_to_sync
from channels.generic.websocket import WebsocketConsumer
from django.contrib.auth.models import User
from django.db.models import Sum
from django.utils.html import escape
from djchoices import DjangoChoices, ChoiceItem

from game_engine import models
from game_engine.lib.card_holders import Player as PlayerCardHolder
from game_engine.lib.pasur import PasurIllegalAction, STATUS, Pasur


class PlayerActions(DjangoChoices):
    deal_cards = ChoiceItem()
    play_card = ChoiceItem()
    count_points = ChoiceItem()
    next_game = ChoiceItem()
    start_new_match = ChoiceItem()
    # undo_last_action = ChoiceItem()


class PasurInterface(WebsocketConsumer):

    def get_game_status(self, pasur: Pasur, game_id):
        player_ch: PlayerCardHolder = pasur.card_holders.get(self.player.name)

        game_status = {
            'game_phase': pasur.status,
            'player_in_turn': pasur.player_in_turn.identifier,
            'no_player_has_cards_on_hand': pasur.no_player_has_cards_on_hand,
            'cards_on_board': [
                {
                    'suit': card.suit,
                    'rank': card.rank,
                    'id': card.id,
                } for card in pasur.board.list_all_cards()
            ],
            'number_of_cards_in_deck': pasur.deck.card_count,
            'player': {
                'cards_in_hand': [
                    {
                        'suit': card.suit,
                        'rank': card.rank,
                        'id': card.id,
                    } for card in player_ch.list_in_hand_cards()
                ],
                'number_of_cards_in_pile': player_ch.card_count_collected(),
            } if player_ch else {},
            'opponents': [
                {
                    'name': opponent.identifier,
                    'card_count_in_hand': opponent.cards_count_hand(),
                    'card_count_in_pile': opponent.card_count_collected(),
                } for opponent in pasur.card_holders.get_players(exclude_player=player_ch)
            ],
            'last_played_card': {
                    'suit': pasur.last_played_card.suit,
                    'rank': pasur.last_played_card.rank,
                    'id': pasur.last_played_card.id,
                } if pasur.last_played_card else None,
            'last_collected_cards': [
                {
                    'suit': c.suit,
                    'rank': c.rank,
                    'id': c.id,
                } for c in pasur.last_collected_cards
            ],
            'player_points': self.get_points_status(pasur, game_id) if pasur.status == STATUS.finished else {},
        }
        return game_status

    def get_points_status(self, pasur: Pasur, game_id: int):
        points = {}
        for player in pasur.players:
            pms = models.GameMatchPlayerScore.objects\
                .filter(match_player__player__name=player.identifier)\
                .filter(match_player__match=self.match)
            points[player.identifier] = {
                'total': pms.aggregate(Sum('score')).get('score__sum', 0),
                'current_game': pms.filter(game_id=game_id).aggregate(Sum('score')).get('score__sum', 0)
            }
        return points

    def push_to_group(self, message, pasur, game_id):
        async_to_sync(self.channel_layer.group_send)(
            self.match_group_id,
            {
                'type': 'game_status',
                'message': message,
                'pasur': pasur.dump_json(),
                'game_id': game_id,
            }
        )

    # noinspection PyAttributeOutsideInit
    def connect(self):
        match_id = self.scope['url_route']['kwargs']['match_id']
        self.user: User = self.scope['user']
        self.match: models.Match = models.Match.objects.get(pk=match_id)
        self.player = models.Player.objects.get(name=self.user.username)

        self.match_group_id = 'game_%s' % self.match.pk

        # Join room group
        async_to_sync(self.channel_layer.group_add)(
            self.match_group_id,
            self.channel_name,
        )

        game = self.match.get_latest_game()
        self.push_to_group(
            message=f"Player joined {self.player.name}",
            pasur=game.pasur,
            game_id=game.pk,
        )
        self.accept()

    def disconnect(self, close_code):
        # Leave room group
        async_to_sync(self.channel_layer.group_discard)(
            self.match_group_id,
            self.channel_name,
        )

    # Receive message from WebSocket
    # noinspection PyMethodOverriding,PyAttributeOutsideInit
    def receive(self, text_data):
        text_data_json = json.loads(text_data)
        # message = text_data_json['message']
        player_action_name = text_data_json['player_action']

        with transaction.atomic():
            game = self.match.get_latest_game(select_for_update=True)
            try:
                if player_action_name == PlayerActions.deal_cards:
                    game.pasur.deal_cards()
                    game.save()
                    message = 'Cards dealed'
                elif player_action_name == PlayerActions.play_card:
                    player_ch: PlayerCardHolder = game.pasur.card_holders.get(self.player.name)
                    played_card = player_ch.get(card_id=text_data_json['played_card'])
                    collected_cards = [game.pasur.board.get(card_id) for card_id in text_data_json['collect_cards']]
                    game.pasur.play_card(player=player_ch, card=played_card, collect_cards=collected_cards)
                    game.save()
                    message = (
                        'Player played card {played_card}'.format(played_card=played_card) +
                        (' and picked up {collected_cards}'.format(
                            collected_cards=', '.join([f"{card}" for card in collected_cards])
                        ) if collected_cards else '')
                    )
                elif player_action_name == PlayerActions.count_points:
                    player_points = game.pasur.count_points()
                    game.save()
                    for player_identifier, score in player_points.items():
                        models.GameMatchPlayerScore.objects.get_or_create(
                            game=game,
                            match_player=models.MatchPlayer.objects.get(
                                match=self.match,
                                player__name=player_identifier),
                            score=score
                        )

                    message = 'Counted points: {}'.format(player_points)
                elif player_action_name == PlayerActions.next_game:
                    if game.status not in [STATUS.finished, STATUS.cancelled]:
                        raise PasurIllegalAction('Cannot go to next game before this game is finished or cancelled')
                    new_pasur = Pasur.create_new_game()
                    new_pasur.starter = game.pasur.players_in_play_order[1]
                    game = models.Game(match=self.match, pasur=new_pasur)
                    game.save()
                    message = 'New game started'
                else:
                    message = "UNKNOWN ACTION"
                # Send message to room group
                self.push_to_group(
                    message=message,
                    pasur=game.pasur,
                    game_id=game.pk,
                )
            except PasurIllegalAction as e:
                message = 'ERROR ({}): {}'.format(self.player.name, e)
                self.send(text_data=json.dumps({'message': escape(message)}))

    # Receive message from room group
    def game_status(self, event):
        message = event['message']
        pasur = Pasur.load_json(event['pasur'])
        game_id = event['game_id']

        # Send message to WebSocket
        self.send(text_data=json.dumps({
            'game_status': self.get_game_status(pasur=pasur, game_id=game_id),
            'message': escape(message),
        }))
