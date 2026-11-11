from .models import TournamentSettings


def tournament_content(request):
    return {'tournament_settings': TournamentSettings.objects.filter(pk=1).first() or TournamentSettings(pk=1)}
