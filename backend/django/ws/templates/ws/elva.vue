{% verbatim vue_block %}
<div id="app" class="room" v-cloak>

    <div v-for="(opponent, index) in opponents" class="opponent-space"
         :class="[opponent_class(index), is_in_turn(opponent.name)]">
        <transition-group tag="div" name="opponent" class="hand opponent">
            <back_card v-for="card_id in opponent.card_count_in_hand" :key="card_id"/>
        </transition-group>
        <div class="hand-name">{{opponent.name}}</div>
    </div>
    <div class="middle">
        <div class="deck">
            <back_card></back_card>
            <div class="deck-count">{{ number_of_cards_in_deck }}</div>
        </div>
        <transition-group tag="div" name="board" class="board">
            <card v-for="card in cards_on_board" :key="card.id"
                  :card="card"
                  :callback="select_card_for_collection"
                  :class="selected_class(card.id)"
            />
        </transition-group>
        <div class="buttons" v-if="count_points_action_active || deal_cards_action_active || next_game_action_active">
            <button class="button"
                    v-on:click="count_points()"
                    :disabled="!count_points_action_active">
                Count points
            </button>
            <button class="button"
                    v-on:click="deal_cards()"
                    :disabled="!deal_cards_action_active">
                Deal cards
            </button>
            <button class="button"
                    v-on:click="next_game()"
                    :disabled="!next_game_action_active">
                Next game
            </button>
        </div>
        <div class="last-play">
            <div class="last-card">
                <card v-bind:key="last_played_card.id"
                      :card="last_played_card"
                      v-if="last_played_card"
                />
            </div>
            <div v-for="card in last_collected_cards" class="last-collected-cards">
                <card v-bind:key="card.id"
                      :card="card"
                />
            </div>
        </div>
        <div class="score-table">
            <div class="score" v-for="(score, player) in player_points">
                {{ player }}: {{score.current_game}} ({{score.total}})<br/>
            </div>
        </div>
        <!--<div id="message"></div>-->
    </div>
    <div class="player-space player" :class="is_in_turn(player_identifier)">
        <transition-group tag="div" name="hand" class="hand">
            <card v-for="card in cards_in_hand" v-bind:key="card.id"
                  :card="card"
                  :callback="play_card"
                  v-on:card-touch="highlight"
            />
        </transition-group>
        <div class="hand-name">{{player_identifier}}</div>
    </div>

</div>
{% endverbatim vue_block %}
