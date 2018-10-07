const elva_menu = {};

elva_menu.webSocketBridge = new channels.WebSocketBridge();
elva_menu.webSocketBridge.connect(elva_menu_config.ws_menu_url);
elva_menu.webSocketBridge.socket.addEventListener('open', function() {
    console.log("Connected to WebSocket");
    if (elva_menu.app) {
        elva_menu.app.update_status();
    }
});
elva_menu.webSocketBridge.socket.addEventListener('close', function() {
    console.log("Disconnected from WebSocket");
    if (elva_menu.app) {
        elva_menu.app.update_status();
    }
});

elva_menu.webSocketBridge.listen(function(data) {
    console.log('Received data from server', data);
    elva_menu.app.matches = data.matches;
    elva_menu.app.first_message_received = true;
    elva_menu.app.update_status();
});

Vue.component('match', {
    'props': ["match", "set_location"],
    'template':
        '<div class="box pasur-menu-match-card" v-on:click="set_location(match.game_url)">' +
            '<p>{{match.status}} with players ' +
                '<span v-for="(player, index) in match.players">' +
                    '<span v-if="index !== match.players.length - 1 && index !== 0"> , </span>' +
                    '<span v-if="index === match.players.length - 1 && index !== 0"> and </span>' +
                    '<span class="tag is-info">{{ player }}</span>' +
                '</span>' +
            '</p>' +
            '<p><small>Last action {{ match.last_action }}</small></p>' +
        '</div>'
});

elva_menu.app = new Vue({
    el: '#elva_menu_app',
    data: {
        matches: [],
        first_message_received: false,
    },
    methods: {
        update_status: function () {

        },
        set_location: function (url) {
            window.location = url;
        }
    }
});
