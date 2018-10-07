const elva = {};

elva.webSocketBridge = new channels.WebSocketBridge();
elva.webSocketBridge.connect(elva_config.ws_game_url);
elva.webSocketBridge.socket.addEventListener('open', function() {
    console.log("Connected to WebSocket");
    if (elva.app) {
        elva.app.update_status();
    }
});
elva.webSocketBridge.socket.addEventListener('close', function() {
    console.log("Disconnected from WebSocket");
    if (elva.app) {
        elva.app.update_status();
    }
});

class Card {
  constructor(id, rank, suit, color) {
    this.id = id;
    this.rank = rank;
    this.suit = suit;
    this.color = color;
    this.hidden = true;
  }
}
elva.card_json_to_card = function (card_json) {
    if (card_json === undefined || card_json === null) {
        return undefined;
    }
    return new Card(
        card_json.id,
        card_json.rank,
        elva.app.suits[card_json.suit],
        elva.app.suitColor[card_json.suit]);
};
elva.cards_json_to_cards = function(cards_json) {
    if (cards_json === undefined || cards_json === null) {
        return [];
    }
    return cards_json.map(function (card_json) { return elva.card_json_to_card(card_json)});
};
elva.webSocketBridge.listen(function(action, stream) {
    console.log(action, stream);
    console.log(action.game_status);
    let game_status = action.game_status;
    if (game_status !== undefined) {
        let player = game_status['player'];
        elva.app.game_phase = game_status.game_phase;
        elva.app.cards_on_board = elva.cards_json_to_cards(game_status['cards_on_board']);
        elva.app.number_of_cards_in_deck = game_status['number_of_cards_in_deck'];
        elva.app.cards_in_hand = elva.cards_json_to_cards(player.cards_in_hand);
        elva.app.number_of_cards_in_pile = player.number_of_cards_in_pile || 0;
        elva.app.opponents = game_status['opponents'];
        elva.app.player_in_turn = game_status['player_in_turn'];
        elva.app.number_of_cards_in_deck = game_status['number_of_cards_in_deck'];
        elva.app.no_player_has_cards_on_hand = game_status['no_player_has_cards_on_hand'];
        elva.app.last_played_card = elva.card_json_to_card(game_status.last_played_card);
        elva.app.last_collected_cards = elva.cards_json_to_cards(game_status['last_collected_cards']);
        elva.app.player_points = game_status['player_points'];
    }
    let message_box = $('#message');
    message_box.html(action['message']);
    elva.app.first_message_received = true;
    elva.app.update_status();
});

// INCLUDE vue resources to do the below thingy
//Vue.http.headers.common['X-CSRFToken'] = "{{ csrf_token }}";

Vue.component('card', {
    'props': ["card", "callback"],
    'template':
        '<div class="card" :class="card.color" ' +
        'v-on:click="callback(card.id)"  ' +
        'v-on:touchstart="$emit(\'card-touch\', 1, $event)" ' +
        'v-on:touchend="$emit(\'card-touch\', 0, $event)" ' +
        'v-on:mousedown="$emit(\'card-touch\', 1, $event)" ' +
        'v-on:mouseup="$emit(\'card-touch\', 0, $event)"' +
        '>' +
            '<span class="card__suit card__suit--top">{{ card.suit }}</span>' +
            '<span class="card__number">{{ card.rank }}</span>' +
            '<span class="card__suit card__suit--bottom">{{ card.suit }}</span>' +
        '</div>',
});

Vue.component('back_card', {
    'template': '<div class="card back" style="background-color: ghostwhite"></div>'
});

elva.app = new Vue({
    el: '#app',
    data: {
        first_message_received: false,
        ranks: ['A', '2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K'],
        suits: [
            '♠',
            '♥',
            '♣',
            '♦'
        ],
        suitColor: {
            0: 'black',
            1: 'red',
            2: 'black',
            3: 'red',
        },
        game_phase: '',
        cards_on_board: [],
        cards_in_hand: [],
        number_of_cards_in_pile: 0,
        number_of_cards_in_deck: 52,
        no_player_has_cards_on_hand: true,
        opponents: [],
        player_in_turn: '',
        selected_cards: [],
        player_identifier: elva_config.player_name,
        last_played_card: null,
        last_collected_cards: [],
        player_points: {},
        is_connected: false,
        warning_message: '',
    },
    methods: {
        highlight: function (on_or_off, event) {
            if (on_or_off && this.is_in_turn(elva_config.player_name)) {
                $(event.currentTarget).addClass('pressed_card');
            } else {
                $(event.currentTarget).removeClass('pressed_card');
            }
        },
        deal_cards: function () {
            elva.webSocketBridge.send({
                'message': 'Player requested deal cards',
                'player_action': elva_config.player_actions.DEAL_CARDS
            });
        },
        count_points: function () {
            elva.webSocketBridge.send({
                'message': 'Player requested count points',
                'player_action': elva_config.player_actions.COUNT_POINTS
            });
        },
        next_game: function () {
            elva.webSocketBridge.send({
                'message': 'Player requested go to next game',
                'player_action': elva_config.player_actions.NEXT_GAME
            });
        },
        play_card: function (card_id) {
            elva.webSocketBridge.send({
                'message': 'Player played a card',
                'player_action': elva_config.player_actions.PLAY_CARD,
                'played_card': card_id,
                'collect_cards': this.collected_cards
            });
        },
        is_in_turn: function (identifier) {
            if (identifier === this.player_in_turn && 'ongoing' === this.game_phase ) {
                return 'in_turn';
            } else {
                return '';
            }
        },
        select_card_for_collection: function (card_id) {
            if (this.selected_cards.includes(card_id)) {
                this.selected_cards = elva.app.selected_cards.filter(function (ci) {
                    return ci !== card_id;
                });
            } else {
                this.selected_cards.push(card_id);
            }
        },
        selected_class: function (card_id) {
            return this.selected_cards.includes(card_id) ? 'selected_card' : '';
        },
        opponent_class: function (index) {
            let opponent_top = 'opponent_top';
            let opponent_left = 'opponent_left';
            let opponent_right = 'opponent_right';
            if (this.opponents.length === 1) return opponent_top;
            else return [opponent_left, opponent_top, opponent_right][index];
        },
        update_status: function () {
            this.is_connected = elva.webSocketBridge.socket.readyState === elva.webSocketBridge.socket.OPEN;
            if (!this._isMounted) {
                this.warning_message = 'loading...';
            } else if (this.opponents.length === 0) {
                this.warning_message = "Invite opponent to the game";
            } else if (!this.is_connected) {
                this.warning_message = "You are not connected to the server, reconnecting...";
            } else {
                this.warning_message = '';
            }
        },
    },
    computed: {
        collected_cards: function () {
            let elva_app = this;
            let selected_cards = this.cards_on_board.filter(function (element) {
                return elva_app.selected_cards.includes(element.id);
            });
            this.selected_cards = selected_cards.map(function (element) {
                return element.id;
            });
            return this.selected_cards;
        },
        deal_cards_action_active: function () {
            return this.no_player_has_cards_on_hand
                && this.number_of_cards_in_deck > 0
                && ['pending', 'ongoing'].contains(this.game_phase)
                && this.opponents.length >= 1;
        },
        count_points_action_active: function () {
            return this.no_player_has_cards_on_hand &&
                this.number_of_cards_in_deck === 0 &&
                Object.keys(this.player_points).length === 0;
        },
        next_game_action_active: function () {
            return ['finished', 'cancelled'].contains(this.game_phase);
        },
    },
    mounted: function () {
        this.update_status();
    }
});
