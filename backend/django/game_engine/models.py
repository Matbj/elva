from django.contrib.postgres.fields import JSONField
from django.db import models
from django.db.models import Sum
from djchoices import DjangoChoices, ChoiceItem

from game_engine.lib.card_holders import Deck, Player as PasurPlayer
from game_engine.lib.pasur import Pasur, STATUS, MAX_PLAYER_COUNT


class GameModel(models.Model):

    class Meta:
        abstract = True

    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)


# noinspection PyPep8Naming
class MATCH_STATUS(DjangoChoices):
    joinable = ChoiceItem()
    ongoing = ChoiceItem()
    finished = ChoiceItem()


class Match(GameModel):
    def get_latest_game(self, select_for_update=False) -> "Game":
        if select_for_update:
            query = self.games.select_for_update()
        else:
            query = self.games
        return query.latest('created')

    def status(self):
        games = self.games.order_by('-modified')
        if len(games) <= 1 and games[0].status == STATUS.pending and self.game_players.count() <= MAX_PLAYER_COUNT:
            return MATCH_STATUS.joinable
        elif self.has_a_player_reached_goal(current_game=games[0]):
            return MATCH_STATUS.finished
        else:
            return MATCH_STATUS.ongoing

    def has_a_player_reached_goal(self, current_game=None):
        for player, values in self.count_player_points(current_game=current_game or self.get_latest_game()).items():
            try:
                if values['total'] >= MAX_PLAYER_COUNT:
                    return True
            except Exception as e:
                print(e)
        return False

    def count_player_points(self, current_game: "Game"=None):
        current_game = current_game or self.get_latest_game()
        points = {}
        for player in self.game_players.all():
            pms = GameMatchPlayerScore.objects \
                .filter(match_player__player__name=player.player.name) \
                .filter(match_player__match=self)
            points[player.player.name] = {
                'total': pms.aggregate(Sum('score')).get('score__sum') or 0,
                'current_game': pms.filter(game_id=current_game.id).aggregate(Sum('score')).get('score__sum') or 0
            }
        return points


class GameField(JSONField):
    description = "A field to save decks as jsonb in postgres db, but acts like a Deck-object"

    def to_python(self, value):
        value = super(GameField, self).to_python(value)
        if isinstance(value, Deck):
            return value

        if value is None:
            return value

        return Pasur.load_json(value)

    def get_prep_value(self, value: Pasur):
        return super(GameField, self).get_prep_value(value.dump_json())

    def from_db_value(self, value, *_):
        return self.to_python(value)

    def formfield(self, **kwargs):
        raise NotImplementedError('This is not yet supported')


class Game(GameModel):

    status = models.CharField(max_length=30, choices=STATUS.choices, default=STATUS.pending)
    pasur: Pasur = GameField()
    match = models.ForeignKey(to=Match, on_delete=models.CASCADE, related_name='games')

    def __init__(self, *args, **kwargs):
        super(Game, self).__init__(*args, **kwargs)
        if self.id is None and self.pasur is None:
            self.pasur: Pasur = Pasur.create_new_game()

        for player in self.match.game_players.order_by('created'):  # type: MatchPlayer
            self.pasur.add_player(player=player.player.get_pasur_player())

        self.pasur.status = self.status

    def save(self, *args, **kwargs):
        self.status = self.pasur.status
        super(Game, self).save(*args, **kwargs)


class Player(GameModel):
    name = models.CharField(max_length=120, unique=True, blank=False)

    def get_pasur_player(self):
        return PasurPlayer(player_id=self.name)


class MatchPlayer(GameModel):
    match = models.ForeignKey(Match, on_delete=models.CASCADE, related_name='game_players')
    player = models.ForeignKey(Player, on_delete=models.CASCADE)


class GameMatchPlayerScore(GameModel):
    game = models.ForeignKey(to=Game, on_delete=models.CASCADE)
    match_player = models.ForeignKey(to=MatchPlayer, on_delete=models.CASCADE)
    score = models.IntegerField(default=0)
