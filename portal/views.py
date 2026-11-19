from urllib.parse import urlencode, urlsplit
from django.contrib.auth import login
from django.contrib.auth.models import Group
from django.contrib import messages
from django.db import transaction
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_http_methods
from . import ratelimit
from .forms import RegistrationForm, ProfileForm
from .models import PRIVACY_POLICY_VERSION, TournamentSettings, TournamentApplication, Stage, Sponsor, Match


def tournament_settings():
    # GET requests do not create database records. Defaults also work before editing admin.
    return TournamentSettings.objects.filter(pk=1).first() or TournamentSettings(pk=1)


@never_cache
def home(request):
    return render(request, 'home.html', {'tournament_settings': tournament_settings()})


def zxc(request):
    return render(request, 'zxc.html', {'tournament_settings': tournament_settings()})


@never_cache
def tournament(request):
    settings = tournament_settings()
    stages = list(Stage.objects.all())
    stage_content = [{'name': s.name, 'startsAt': s.starts_at.isoformat() if s.starts_at else None} for s in stages]
    if not stage_content:
        stage_content = [{'name': name, 'startsAt': None} for name in ['Приём заявок', 'Отбор', 'Матчи', 'Гранд-финал']]
    prize_total = settings.prize_total()
    content = {
        # Grouped digits with plain spaces: site.js animates the label glyph by glyph.
        'prize': f'${prize_total:,}'.replace(',', ' ') if prize_total else settings.prize,
        'stages': stage_content,
        'sponsors': [{'name': s.name, 'logo': s.logo_url, 'url': s.url, 'presentation': s.presentation} for s in Sponsor.objects.all()],
        'contacts': [{'name': 'Telegram', 'url': settings.telegram_url}, {'name': 'Discord', 'url': settings.discord_url}],
    }
    parent = urlsplit('//' + request.get_host()).hostname
    embed = 'https://player.twitch.tv/?' + urlencode({'channel': settings.twitch_channel, 'parent': parent, 'autoplay': 'false', 'muted': 'true'})
    frames = {s.gallery_slot: s for s in Sponsor.objects.filter(gallery_slot__range=(1, 6))}
    return render(request, 'tournament.html', {'tournament_settings': settings, 'fri_content': content, 'prize_total': prize_total, 'gallery_frames': [frames.get(slot) for slot in range(1, 7)], 'has_stage_dates': any(stage.starts_at for stage in stages), 'matches': Match.objects.select_related('team_a', 'team_b', 'stage'), 'twitch_embed_url': embed, 'twitch_url': 'https://www.twitch.tv/' + settings.twitch_channel})


def safe_next(request):
    destination = request.POST.get('next', request.GET.get('next', '')).strip()
    if destination.startswith('/') and url_has_allowed_host_and_scheme(destination, allowed_hosts=set()):
        return destination
    return ''


@require_http_methods(['GET', 'POST'])
def register(request):
    next_url = safe_next(request)
    if request.user.is_authenticated:
        return redirect(next_url or 'profile')
    form = RegistrationForm(request.POST or None)
    ip = ratelimit.client_ip(request)
    status = 200
    if request.method == 'POST' and ratelimit.is_limited('register-ip', ip, ratelimit.REGISTRATIONS_PER_IP):
        form.is_valid()
        form.add_error(None, ratelimit.REGISTRATION_LOCKED_MESSAGE)
        status = 429
    elif request.method == 'POST' and form.is_valid():
        from django.utils.timezone import now
        with transaction.atomic():
            user = form.save(commit=False)
            user.privacy_accepted_at = now()
            user.privacy_policy_version = PRIVACY_POLICY_VERSION
            if form.cleaned_data['media_fields']:
                user.media_consent = {
                    'version': 1,
                    'fields': form.cleaned_data['media_fields'],
                    'recorded_at': now().isoformat(),
                }
            user.save()
            group, _ = Group.objects.get_or_create(name='Участники')
            user.groups.add(group)
        ratelimit.hit('register-ip', ip, ratelimit.REGISTRATIONS_PER_IP)
        login(request, user)
        destination = reverse('profile_edit')
        if next_url:
            destination += '?' + urlencode({'next': next_url})
        return redirect(destination)
    return render(request, 'registration/register.html', {'form': form, 'next': next_url}, status=status)


def privacy(request):
    return render(request, 'privacy.html', {'policy_version': PRIVACY_POLICY_VERSION})


@never_cache
@login_required
def profile(request):
    applications = {item.competition: item for item in TournamentApplication.objects.filter(user=request.user)}
    return render(request, 'profile.html', {'application': applications.get('team'), 'zxc_application': applications.get('zxc')})


@never_cache
@login_required
@require_http_methods(['GET', 'POST'])
def profile_edit(request):
    next_url = safe_next(request)
    old_photo = request.user.photo.name
    form = ProfileForm(request.POST if request.method == 'POST' else None, request.FILES if request.method == 'POST' else None, instance=request.user)
    if request.method == 'POST' and form.is_valid():
        form.save()
        if old_photo and old_photo != request.user.photo.name:
            request.user.photo.storage.delete(old_photo)
        messages.success(request, 'Профиль сохранён.')
        return redirect(next_url or 'profile')
    return render(request, 'profile_edit.html', {'form': form, 'next': next_url})


@never_cache
@login_required
@require_http_methods(['GET'])
def profile_photo(request):
    from django.http import FileResponse, Http404
    if not request.user.photo:
        raise Http404
    try:
        response = FileResponse(request.user.photo.open('rb'), content_type='image/jpeg')
    except FileNotFoundError:
        raise Http404
    response['X-Content-Type-Options'] = 'nosniff'
    return response
