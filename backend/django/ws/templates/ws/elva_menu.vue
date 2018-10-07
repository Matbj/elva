{% verbatim vue_block %}
    <div id="elva_menu_app" class="pasur-menu-container" v-cloak>
        <transition-group name="matches" tag="div" class="pasur-menu-table">
            <div class="box pasur-menu-match-card" :key="'create game'"
                 onclick="window.location = elva_menu_config.ws_new_game_url">
                Create new game
            </div>
            <div class="box pasur-menu-match-card" v-if="!first_message_received" :key="'loading'">
                Loading games...
            </div>
                <div class="pasur-menu-match-card-outer" v-for="match in matches" :key="match.id">
                    <match :match="match" :set_location="set_location"/>
                </div>
        </transition-group>
    </div>
{% endverbatim vue_block %}
