from urllib.parse import urlencode, urlsplit
from django.contrib.auth import login
from django.contrib.auth.models import Group
from django.contrib import messages
from django.db import transaction
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_http_methods
from .forms import RegistrationForm, ProfileForm
from .models import TournamentSettings, TournamentApplication, Stage, Sponsor, Match


def tournament_settings():
    # GET requests do not create database records. Defaults also work before editing admin.
    return TournamentSettings.objects.filter(pk=1).first() or TournamentSettings(pk=1)


def home(request):
    return render(request, 'home.html', {'tournament_settings': tournament_settings()})


def zxc(request):
    return render(request, 'zxc.html', {'tournament_settings': tournament_settings()})


def tournament(request):
    settings = tournament_settings()
    stages = list(Stage.objects.all())
    stage_content = [{'name': s.name, 'startsAt': s.starts_at.isoformat() if s.starts_at else None} for s in stages]
    if not stage_content:
        stage_content = [{'name': name, 'startsAt': None} for name in ['Приём заявок', 'Отбор', 'Матчи', 'Гранд-финал']]
    content = {
        'prize': settings.prize,
        'stages': stage_content,
        'sponsors': [{'name': s.name, 'logo': s.logo_url, 'url': s.url, 'presentation': s.presentation} for s in Sponsor.objects.all()],
        'contacts': [{'name': 'Telegram', 'url': settings.telegram_url}, {'name': 'Discord', 'url': settings.discord_url}],
    }
    parent = urlsplit('//' + request.get_host()).hostname
    embed = 'https://player.twitch.tv/?' + urlencode({'channel': settings.twitch_channel, 'parent': parent, 'autoplay': 'false', 'muted': 'true'})
    return render(request, 'tournament.html', {'tournament_settings': settings, 'fri_content': content, 'has_stage_dates': any(stage.starts_at for stage in stages), 'matches': Match.objects.select_related('team_a', 'team_b', 'stage'), 'twitch_embed_url': embed, 'twitch_url': 'https://www.twitch.tv/' + settings.twitch_channel})


@require_http_methods(['GET', 'POST'])
def register(request):
    if request.user.is_authenticated:
        return redirect('profile')
    form = RegistrationForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        with transaction.atomic():
            user = form.save()
            group, _ = Group.objects.get_or_create(name='Участники')
            user.groups.add(group)
        login(request, user)
        return redirect('profile_edit')
    return render(request, 'registration/register.html', {'form': form})


@never_cache
@login_required
def profile(request):
    applications = {item.competition: item for item in TournamentApplication.objects.filter(user=request.user)}
    return render(request, 'profile.html', {'application': applications.get('team'), 'zxc_application': applications.get('zxc')})


@never_cache
@login_required
@require_http_methods(['GET', 'POST'])
def profile_edit(request):
    form = ProfileForm(request.POST if request.method == 'POST' else None, instance=request.user)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Профиль сохранён.')
        return redirect('profile')
    return render(request, 'profile_edit.html', {'form': form})
