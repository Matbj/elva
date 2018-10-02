import json
from typing import Union, List

from djchoices import DjangoChoices, ChoiceItem

from game_engine.lib.card_holders import Deck, Card, Board, Player, CardHolder, CardHolderList, CLUBS, DIAMONDS


class STATUS(DjangoChoices):
    pending = ChoiceItem()
    ongoing = ChoiceItem()
    finished = ChoiceItem()
    cancelled = ChoiceItem()


CLUBS_WIN_POINT = 7
CLUBS_TWO_POINT = 2
DIAMONDS_TEN_POINT = 3
ACE_POINT = 1
JACK_POINT = 1
SUR_POINT = 5


class PasurIllegalAction(Exception):
    pass


class Pasur:

    def __init__(
            self,
            card_holders: CardHolderList[CardHolder],
            starter: Player=None,
            surs: List[CardHolder]=None,
            last_collector: CardHolder=None,
            last_played_card: Card=None,
            last_collected_cards: List[Card]=None,
            status=None,
    ):
        self.card_holders = card_holders
        self.starter = starter
        self.surs = surs or []
        self.status = status or STATUS.pending
        self.last_collector: Player = last_collector
        self.last_played_card = last_played_card
        self.last_collected_cards = last_collected_cards or []
        if not (Board in card_holders and Deck in card_holders):
            raise SyntaxError('There has to be a Deck and a Board in the player set')

    @staticmethod
    def create_new_game() -> "Pasur":
        deck = Deck.generate_fresh_set_of_cards()
        return Pasur(card_holders=CardHolderList(deck, Board()))

    @staticmethod
    def load_json(data: Union[str, dict]) -> "Pasur":
        if isinstance(data, str):
            data = json.loads(data)
        players = CardHolderList(Deck(), Board())
        for identifier in data.get('players', []):
            if identifier not in players:
                players.append(Player(player_id=identifier))

        for card_dict in data.get('cards', []):
            card = Card(
                card_id=card_dict['card_id'],
                collected=card_dict['collected'],
            )
            identifier = card_dict['identifier']
            players.get_or_create(identifier).add_card(card)

        starter = players.get(data.get('starter'))

        surs = []
        for p in data.get('surs', []):
            surs.append(players.get(p))

        if data.get('last_collector'):
            last_collector = players.get(identifier=data['last_collector'])
        else:
            last_collector = None

        if data.get('last_played_card'):
            last_played_card = players.get_card(card_id=data['last_played_card'])
        else:
            last_played_card = None

        last_collected_cards = []
        for c in data.get('last_collected_cards', []):
            last_collected_cards.append(players.get_card(card_id=c))

        status = data.get('status')

        return Pasur(
            card_holders=players,
            starter=starter,
            surs=surs,
            last_collector=last_collector,
            last_played_card=last_played_card,
            last_collected_cards=last_collected_cards,
            status=status,
        )

    def dump_json(self):
        cards = []
        for card_holder in self.card_holders:
            for card in card_holder.list_all_cards():
                cards.append({
                    'card_id': card.id,
                    'collected': card.collected,
                    'identifier': card_holder.identifier,
                })

        output = {
            'cards': cards,
            'players': [p.identifier for p in self.players],
            'surs': [p.identifier for p in self.surs],
            'last_collector': self.last_collector.identifier if self.last_collector else None,
            'last_played_card': self.last_played_card.id if self.last_played_card else None,
            'last_collected_cards': [c.id for c in self.last_collected_cards],
            'status': self.status,
            'starter': self.starter.identifier if self.starter else None,
        }
        return json.dumps(output)

    @property
    def deck(self) -> Deck:
        # noinspection PyTypeChecker
        return self.card_holders.get(Deck)

    @property
    def board(self) -> Board:
        # noinspection PyTypeChecker
        return self.card_holders.get(Board)

    @property
    def players(self) -> CardHolderList[Player]:
        return CardHolderList(*[player for player in self.card_holders if isinstance(player, Player)])

    @property
    def starting_player(self) -> Player:
        if self.starter:
            return self.starter
        else:
            return self.players[0]

    @property
    def players_in_play_order(self):
        starting_player = self.starting_player
        players = self.players
        starter_index = players.index(starting_player)
        remaining_players = players[starter_index+1:] + players[0:starter_index]
        return [starting_player] + remaining_players

    @property
    def player_in_turn(self) -> Player:
        players_in_play_order = self.players_in_play_order
        for p in players_in_play_order[1:]:
            if p.cards_count_hand() > players_in_play_order[0].cards_count_hand():
                return p
        return players_in_play_order[0]

    @property
    def no_player_has_cards_on_hand(self):
        for p in self.players:
            if p.cards_count_hand() > 0:
                return False
        return True

    def add_player(self, player: Player):
        if player not in self.card_holders:
            self.card_holders.append(player)

    def give_card_from_deck(self, to_card_holder: Union[Player, Board]):
        self.deck.pop_card(to_card_holder=to_card_holder)

    def deal_cards(self):
        deal_to = self.players

        if not (2 <= len(deal_to) <= 4):
            raise PasurIllegalAction('Need to be 2-4 players to play')

        for player in deal_to:
            if player.cards_count_hand() > 0:
                raise PasurIllegalAction('Not allowed to deal cards while a player still has cards in hand')

        if self.deck.remaining_cards() == 0:
            self.status = STATUS.finished
            return

        if self.deck.remaining_cards() == 52:
            deal_to.append(self.board)
            self.status = STATUS.ongoing

        for ch in deal_to:
            for _ in range(4):
                self.give_card_from_deck(to_card_holder=ch)
            if isinstance(ch, Board):
                if self.board.has_knight():
                    knight = [c for c in self.board.list_all_cards() if c.number == 11][0]
                    self.board.move_card(card=knight, to_card_holder=self.deck)
                    self.give_card_from_deck(to_card_holder=self.board)
                    if self.board.has_knight():
                        self.terminate_game()

    def play_card(self, player: Player, card: Card, collect_cards: List[Card]=None):
        if self.player_in_turn != player:
            raise PasurIllegalAction('Player not in turn')
        if not self.validate_move(card=card, collect_cards=collect_cards):
            raise PasurIllegalAction('Move not allowed')
        player.move_card(card=card, to_card_holder=self.board)
        self.last_played_card = card
        if collect_cards:
            self.board.move_card(card=card, to_card_holder=player)
            card.set_collected()
            for c in collect_cards:
                self.board.move_card(card=c, to_card_holder=player)
                c.set_collected()
            self.last_collector = player
            self.last_collected_cards = collect_cards

            if self.board.card_count == 0 and card.number != 11 and self.deck.card_count > 0:
                self.surs.append(player)
        else:
            self.last_collected_cards = []

    def terminate_game(self):
        self.status = STATUS.cancelled

    def validate_move(self, card: Card, collect_cards: List[Card]=None):
        if collect_cards:
            if card.number <= 10:
                card_sum = card.number
                for cc in collect_cards:
                    if cc not in self.board.list_all_cards():
                        raise PasurIllegalAction('Not allowed collect card that is not on the board')
                    if cc.number > 10:
                        return False
                    card_sum += cc.number
                return card_sum == 11
            if card.number == 11:
                for c in self.board.list_all_cards():
                    if c.number > 11:
                        if c in collect_cards:
                            return False
                    elif c not in collect_cards:
                        return False
                return True
            if card.number >= 12:
                return len(collect_cards) == 1 and collect_cards[0].number == card.number
        else:
            # Player tried to not collect any cards, see if can find a possible way to collect cards.
            if card.number <= 10:
                if _find_possible_11(current_sum=card.number, cards=self.board.list_all_cards()):
                    return False
            if card.number == 11:
                for c in self.board.list_all_cards():
                    if c.number <= 10:
                        return False
            if card.number >= 12:
                for c in self.board.list_all_cards():
                    if c.number == card.number:
                        return False
        return True

    def count_points(self):
        if self.deck.remaining_cards() > 0:
            raise PasurIllegalAction('Cannot count points, deck has cards left.')
        for player in self.players:
            if player.cards_count_hand() > 0:
                raise PasurIllegalAction('Cannot count points, player still has cards left.')
        for card in self.board.list_all_cards():
            self.board.move_card(card=card, to_card_holder=self.last_collector)
            card.set_collected()

        if self.last_collector:
            for card in self.board.list_all_cards():
                self.board.move_card(card=card, to_card_holder=self.last_collector)

        player_points = {player.identifier: 0 for player in self.players}
        clubs_rank = sorted(self.players, key=lambda p: p.clubs_count(), reverse=True)
        if clubs_rank[0].clubs_count() != clubs_rank[1].clubs_count():  # Two top clubs owners has different clubs count
            player_points[clubs_rank[0].identifier] += CLUBS_WIN_POINT

        for player in self.players:
            for card in player.list_all_cards():
                if card.number == 1:
                    player_points[player.identifier] += ACE_POINT
                elif card.number == 11:
                    player_points[player.identifier] += JACK_POINT
                elif card.number == 2 and card.color == CLUBS:
                    player_points[player.identifier] += CLUBS_TWO_POINT
                elif card.number == 10 and card.color == DIAMONDS:
                    player_points[player.identifier] += DIAMONDS_TEN_POINT

        if self.surs:
            surs_per_player = {player.identifier: 0 for player in self.players}
            for player in self.surs:
                surs_per_player[player.identifier] += 1

            lowest_sur_count = min(surs_per_player.values())
            for player_identifier, sur_count in surs_per_player.items():
                player_points[player_identifier] += (sur_count - lowest_sur_count) * SUR_POINT

        self.status = STATUS.finished

        return player_points


def _find_possible_11(current_sum, cards: List[Card]):
    if current_sum == 11:
        return True
    elif current_sum > 11:
        return False
    elif cards:
        for c in cards:
            if _find_possible_11(
                    current_sum=current_sum + c.number,
                    cards=[c2 for c2 in cards if c2 != c]
            ):
                return True
        return False
    return False
