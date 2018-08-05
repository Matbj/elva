import pytest

from game_engine import models
from game_engine.lib.pasur import STATUS

pytestmark = pytest.mark.django_db


@pytest.fixture('function')
def match():
    match = models.Match()
    match.save()
    return match


@pytest.fixture('function')
def game(match):
    game = models.Game(match=match)
    game.save()
    return game


@pytest.fixture('function')
def game_with_players(game: models.Game):
    players = [models.Player(name=f'Player {it}') for it in range(2)]
    for player in players:
        player.save()
        game_player = models.MatchPlayer(match=game.match, player=player)
        game_player.save()
    game.refresh_from_db()
    return game


def test_create_new_game_full_deck_remaining(game: models.Game):
    assert game.pasur.deck.card_count == 52


def test_get_game_from_db(game: models.Game):
    game_from_db = models.Game.objects.get(pk=game.pk)
    assert game_from_db.pasur.deck.card_count == 52


def test_start_game_with_players(game_with_players: models.Game):
    game_with_players.save()
    assert game_with_players.pasur.status == STATUS.pending
    game_with_players.pasur.deal_cards()
    assert game_with_players.pasur.status in [STATUS.ongoing,
                                              STATUS.cancelled]  # if start with two jacks


def test_get_players_from_game_with_players(game_with_players: models.Game):
    assert len(game_with_players.pasur.players) > 0


def test_get_card_in_game_and_then_another(game_with_players: models.Game):
    game_with_players.pasur.give_card_from_deck(
        to_card_holder=game_with_players.pasur.players[0],
    )
    game_with_players.pasur.give_card_from_deck(
        to_card_holder=game_with_players.pasur.players[0],
    )
    assert game_with_players.pasur.players[0].card_count == 2
    assert game_with_players.pasur.deck.remaining_cards() == 50
    assert game_with_players.pasur.players[1].card_count == 0

    game_with_players.save()
    game_with_players.refresh_from_db()
    assert game_with_players.pasur.players[0].card_count == 2
    assert game_with_players.pasur.deck.remaining_cards() == 50
    assert game_with_players.pasur.players[1].card_count == 0

    game_with_players.pasur.give_card_from_deck(
        to_card_holder=game_with_players.pasur.players[1],
    )
    assert game_with_players.pasur.deck.remaining_cards() == 49
    assert game_with_players.pasur.players[0].card_count == 2
    assert game_with_players.pasur.players[1].card_count == 1
