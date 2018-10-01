from typing import List

import pytest
from mock import patch

from game_engine.lib.card_holders import Player, Card
from game_engine.lib.pasur import Pasur, _find_possible_11


@pytest.fixture()
def pasur():
    return Pasur.create_new_game()


@pytest.fixture()
def pasur_with_two_players(pasur: Pasur):
    pasur.add_player(Player('1'))
    pasur.add_player(Player('2'))
    return pasur


def test_give_cards_to_player(pasur_with_two_players: Pasur):
    player = pasur_with_two_players.player_in_turn
    for _ in range(52):
        pasur_with_two_players.give_card_from_deck(to_card_holder=player)
    assert player.card_count == 52
    assert pasur_with_two_players.deck.card_count == 0
    with pytest.raises(Exception):
        pasur_with_two_players.give_card_from_deck(to_card_holder=player)


def test_deal_cards_to_player(pasur_with_two_players: Pasur):
    pasur_with_two_players.deal_cards()
    assert len(pasur_with_two_players.board.list_all_cards()) == 4
    assert pasur_with_two_players.deck.card_count == 52-4-4*len(pasur_with_two_players.players)
    for player in pasur_with_two_players.players:
        assert player.card_count == 4


@pytest.mark.parametrize('card_value_on_hand, expected', [
    (1, False),
    (2, True),
    (3, True),
    (4, False),
    (5, True),
    (6, True),
    (7, False),
    (8, False),
    (9, False),
    (10, True),
])
def test_find_possible_11(card_value_on_hand, expected: bool):
    assert _find_possible_11(current_sum=card_value_on_hand, cards=[
        Card(1 - 1),
        Card(5 - 1),
        Card(12 - 1),
        Card(11 - 1),
        Card(8 - 1),
    ]) is expected


def test_play_card_no_collect(pasur_with_two_players: Pasur):
    player = pasur_with_two_players.players[0]
    with patch_card_pop_sequence(pasur=pasur_with_two_players,
                                 sequence=[
                                     8, 1, 9, 2,  # player 1
                                     4, 5, 6, 7,  # player 2
                                     3, 14, 27, 40,  # board
                                 ]):
        pasur_with_two_players.deal_cards()
    pasur_with_two_players.play_card(
        player=player,
        card=player.list_all_cards()[0],
    )


def test_play_card_collect_3_8(pasur_with_two_players: Pasur):
    player = pasur_with_two_players.players[0]
    with patch_card_pop_sequence(pasur=pasur_with_two_players,
                                 sequence=[
                                     7, 1, 9, 3,  # player 1
                                     4, 5, 6, 8,  # player 2
                                     2, 14, 27, 40,  # board
                                 ]):
        pasur_with_two_players.deal_cards()
    pasur_with_two_players.play_card(
        player=player,
        card=player.list_all_cards()[0],
        collect_cards=[pasur_with_two_players.board.list_all_cards()[0]]
    )
    assert player.card_count_collected() == 2
    assert Card(7) in [c for c in player.list_all_cards() if c.collected]
    assert Card(2) in [c for c in player.list_all_cards() if c.collected]


def test_play_card_collect_king(pasur_with_two_players: Pasur):
    player = pasur_with_two_players.players[0]
    with patch_card_pop_sequence(pasur=pasur_with_two_players,
                                 sequence=[
                                     12, 1, 9, 3,  # player 1
                                     4, 5, 6, 8,  # player 2
                                     25, 2, 27, 40,  # board
                                 ]):
        pasur_with_two_players.deal_cards()
    pasur_with_two_players.play_card(
        player=player,
        card=player.list_all_cards()[0],
        collect_cards=[pasur_with_two_players.board.list_all_cards()[0]]
    )
    assert player.card_count_collected() == 2
    assert Card(12) in [c for c in player.list_all_cards() if c.collected]
    assert Card(25) in [c for c in player.list_all_cards() if c.collected]


def test_play_card_collect_3_6_2(pasur_with_two_players: Pasur):
    player = pasur_with_two_players.players[0]
    with patch_card_pop_sequence(pasur=pasur_with_two_players,
                                 sequence=[
                                     2, 7, 9, 3,  # player 1
                                     4, 27, 6, 8,  # player 2
                                     5, 1, 25, 40,  # board
                                 ]):
        pasur_with_two_players.deal_cards()
    pasur_with_two_players.play_card(
        player=player,
        card=player.list_all_cards()[0],
        collect_cards=pasur_with_two_players.board.list_all_cards()[0:2]
    )
    assert player.card_count_collected() == 3
    assert Card(1) in [c for c in player.list_all_cards() if c.collected]
    assert Card(2) in [c for c in player.list_all_cards() if c.collected]
    assert Card(5) in [c for c in player.list_all_cards() if c.collected]


def patch_card_pop_sequence(pasur: Pasur, sequence: List[int]):
    sq = sequence.copy()

    def return_numbers(*_, **__):
        card_to_fake = sq.pop(0)
        for index, card in enumerate(pasur.deck.list_all_cards()):
            if card.id == card_to_fake:
                return index
    return patch(
        target='game_engine.lib.card_holders.random.randint',
        side_effect=return_numbers,
    )
