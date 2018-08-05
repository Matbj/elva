import random
from typing import List, Union, Type, Generic, TypeVar

# EXAMPLE DICT JSON:
_example = [
    {
        'card_id': 14,  # card zero is ace, card 12 is king (of first color, i.e. clubs). => card 14 == Diamond 2
        'collected': False,  # If card is "collected" by a player, only relevant if possessed by player.
        'identifier': 'Board',  # Who owns the card. Can either be 'Board', 'Deck',or a player.
    },
    # ... 52 cards in total
]

CLUBS = 'clubs'
DIAMONDS = 'diamonds'
HEARTS = 'hearts'
SPADES = 'spades'
COLORS = [SPADES, HEARTS, CLUBS, DIAMONDS]  # Same order as deck.js


class Card:
    def __init__(self, card_id, collected=False):
        if not (0 <= card_id <= 51):
            raise RuntimeError('Card is not valid: {}'.format(card_id))
        self.id = card_id
        self.collected = collected

    def __eq__(self, other):
        return self.id == other.id

    def __str__(self):
        return "<Card: {color}:{number}{collected}>".format(
            color=self.color,
            number=self.number,
            collected=' collected' if self.collected else '',
        )

    def __repr__(self):
        return self.__str__()

    def set_collected(self):
        """Card is now collected by a player"""
        self.collected = True

    @property
    def color(self):
        return COLORS[self.suit]

    @property
    def suit(self):
        return self.id // 13

    @property
    def number(self):
        return self.id % 13 + 1

    @property
    def rank(self):
        return {
            1: 'A',
            11: 'J',
            12: 'Q',
            13: 'K'}.get(self.number, self.number)


class CardHolder:
    def __init__(self, identifier):
        self._cards: List[Card] = []
        self.identifier = identifier

    def add_card(self, card: Card):
        if card not in self._cards:
            self._cards.append(card)
        else:
            raise RuntimeError('Card already in the deck: {}'.format(card))

    @property
    def card_count(self):
        return len(self._cards)

    def __eq__(self, other: Union[Type["CardHolder"], "CardHolder", str]):
        if isinstance(other, CardHolder):
            return self.identifier == other.identifier
        if isinstance(other, type):
            return self.identifier == other.__name__
        else:
            return self.identifier == other

    def move_card(self, card: Card, to_card_holder: "CardHolder"):
        if card not in self._cards:
            raise RuntimeError('CardHolder tried to play a card not owned')
        to_card_holder.add_card(card)
        self._cards.remove(card)

    def list_all_cards(self):
        return self._cards.copy()  # Do not allow tampering with _cards

    def has_knight(self):
        for card in self._cards:
            if card.number == 11:
                return True
        return False

    def clubs_count(self):
        count = 0
        for card in self.list_all_cards():
            if card.color == CLUBS:
                count += 1
        return count

    def __str__(self):
        return f'<{self.__class__.__name__}: {self.identifier} ({self.card_count} cards)>'

    def __repr__(self):
        return str(self)

    def get(self, card_id):
        for card in self._cards:
            if card.id == card_id:
                return card


class Player(CardHolder):
    def __init__(self, player_id):
        super(Player, self).__init__(identifier=player_id)

    def cards_count_hand(self):
        count = 0
        for card in self._cards:
            if not card.collected:
                count += 1
        return count

    def card_count_collected(self):
        return self.card_count - self.cards_count_hand()

    def list_collected_cards(self):
        return [c for c in self._cards if c.collected]

    def list_in_hand_cards(self):
        return [c for c in self._cards if not c.collected]


class Board(CardHolder):
    def __init__(self):
        super(Board, self).__init__(identifier=self.__class__.__name__)

    def get_cards_on_board(self):
        return self._cards


class Deck(CardHolder):
    def __init__(self):
        super(Deck, self).__init__(identifier=self.__class__.__name__)

    @staticmethod
    def generate_fresh_set_of_cards() -> "Deck":
        deck = Deck()
        for it in range(52):
            deck.add_card(
                Card(
                    card_id=it,
                    collected=False,
                ))
        return deck

    def remaining_cards(self):
        return len(self._cards)

    def __str__(self):
        return "<Deck with {} cards remaining>".format(self.remaining_cards())

    def pop_card(self, to_card_holder: CardHolder):
        self.move_card(self._cards[random.randint(0, len(self._cards) - 1)], to_card_holder=to_card_holder)


T = TypeVar('T')


class CardHolderList(list, Generic[T]):
    def __init__(self, *args):
        super(CardHolderList, self).__init__(args)

    def get(self, identifier, default=None) -> T:
        try:
            return self[self.index(identifier)]
        except ValueError:
            return default

    def get_or_create(self, identifier) -> T:
        try:
            return self[self.index(identifier)]
        except ValueError:
            new = CardHolder(identifier=identifier)
            self.append(new)
            return new

    def get_players(self, exclude_player=None) -> "CardHolderList":
        return CardHolderList(*[player for player in self if isinstance(player, Player) and player != exclude_player])

    def get_card(self, card_id):
        for p in self:
            for c in p.list_all_cards():
                if c.id == card_id:
                    return c
        # raise RuntimeError('Did not find card that was supposed to be here')
        return None
