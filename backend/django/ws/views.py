import random

from django.contrib.auth import login
from django.contrib.auth.models import User
from django.shortcuts import render, redirect
from django.views import View

from game_engine import models
from game_engine.lib.pasur import STATUS
from ws.pasur_interface import PlayerActions
from ws.pasur_menu_interface import PasurMenuInterface


class PasurGameView(View):
    def get(self, request, match_id):
        if request.user.is_anonymous:
            if match_id:
                return redirect('create_user', match_id=match_id)
            else:
                return redirect('create_user_new_match')

        match = models.Match.objects.get(pk=match_id)
        game = match.get_latest_game()
        player, _ = models.Player.objects.get_or_create(name=request.user.username)
        if game and game.status == STATUS.pending:
            _, created = models.MatchPlayer.objects.get_or_create(
                match=match,
                player=player,
            )
            if created:
                PasurMenuInterface.notify_new_player_joined_game()

        return render(request, 'ws/elva.html', {
            'match_id': match.pk,
            'PlayerActions': PlayerActions,
            'player': player,
        })


class NewPasurGameView(View):
    def get(self, request):
        match = models.Match()
        match.save()
        models.Game(match=match).save()
        PasurMenuInterface.notify_new_game_was_created()
        return redirect(to='pasur_match', match_id=match.pk)


class PasurMenuView(View):

    def get(self, request):
        if request.user.is_anonymous:
            return redirect('create_user')
        matches = models.Match.objects.prefetch_related('game_players').order_by('-created')[0:10]
        return render(request, 'ws/elva_menu.html', context={
            'matches': matches,
        })


class CreateUserView(View):

    def get(self, request, match_id=None):
        return render(request, 'ws/create_account.html', context={'match_id': match_id})

    def post(self, request, match_id=None):
        new_username = request.POST.get('username', str(random.randint(0, 1e6)))
        user, _ = User.objects.get_or_create(username=new_username)
        login(request=request, user=user)
        if match_id:
            return redirect('pasur_match', match_id=match_id)
        else:
            return redirect('index')
