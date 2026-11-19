from .models import TournamentApplication, TournamentSettings


def tournament_content(request):
    context = {'tournament_settings': TournamentSettings.objects.filter(pk=1).first() or TournamentSettings(pk=1)}
    match = request.resolver_match
    cabinet = match and (match.namespace == 'support' or match.url_name in (
        'profile', 'profile_edit', 'application', 'zxc_application',
    ))
    if cabinet and request.user.is_authenticated:
        context['fri_accepted'] = request.user.tournament_applications.filter(
            status=TournamentApplication.Status.ACCEPTED,
        ).exists()
    return context
