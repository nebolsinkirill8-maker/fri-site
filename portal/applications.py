from django import forms
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.shortcuts import redirect, render
from django.http import Http404
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_http_methods

from .models import TournamentApplication, TournamentSettings, validate_steam_url


class ApplicationForm(forms.Form):
    resides_in_russia = forms.BooleanField(label='Я проживаю в России')
    is_student = forms.BooleanField(label='Я учусь в школе или колледже')
    comment = forms.CharField(
        label='Комментарий организаторам',
        required=False,
        max_length=500,
        widget=forms.Textarea(attrs={'rows': 3}),
    )

    def __init__(self, *args, competition='team', **kwargs):
        super().__init__(*args, **kwargs)
        if competition == 'zxc':
            self.fields.pop('is_student')


def application_profile_ready(user):
    if not user.nickname.strip() or not user.steam_url or not user.telegram.strip() or not user.discord.strip():
        return False
    try:
        validate_steam_url(user.steam_url)
    except (ValidationError, ValueError):
        return False
    return True


@never_cache
@login_required
@require_http_methods(['GET', 'POST'])
def application(request, competition='team'):
    if competition not in TournamentApplication.Competition.values:
        raise Http404
    application_url = 'application' if competition == 'team' else 'zxc_application'
    user = request.user
    current = TournamentApplication.objects.filter(user=user, competition=competition).first()
    gate = 'applications_open' if competition == 'team' else 'zxc_applications_open'
    applications_open = TournamentSettings.objects.filter(pk=1, **{gate: True}).exists()
    profile_ready = application_profile_ready(user)
    can_apply = applications_open and profile_ready and current is None
    form = ApplicationForm(request.POST if request.method == 'POST' else None, competition=competition)
    status = 200

    if request.method == 'POST':
        if current is not None:
            return redirect(application_url)
        if not applications_open:
            status = 403
        elif not profile_ready:
            status = 400
        elif form.is_valid():
            TournamentApplication.objects.get_or_create(
                user=user, competition=competition,
                defaults={
                    'nickname': user.nickname.strip(),
                    'steam_url': user.steam_url,
                    'telegram': user.telegram,
                    'discord': user.discord.strip(),
                    'team_name': user.team_name.strip() if competition == 'team' else '',
                    'resides_in_russia': form.cleaned_data['resides_in_russia'],
                    'is_student': form.cleaned_data.get('is_student', False),
                    'mmr': user.mmr,
                    'position': user.position,
                    'comment': form.cleaned_data['comment'],
                },
            )
            return redirect(application_url)
        else:
            status = 400

    return render(request, 'application.html', {
        'application': current,
        'applications_open': applications_open,
        'can_apply': can_apply,
        'profile_ready': profile_ready,
        'form': form,
        'application_url': application_url,
        'competition': competition,
        'competition_label': TournamentApplication.Competition(competition).label,
    }, status=status)
