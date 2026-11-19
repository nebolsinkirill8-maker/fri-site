from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .forms import AdminUserCreationForm, AdminUserChangeForm, RateLimitedAdminAuthenticationForm
from django.db.models import Sum
from .models import User, TournamentSettings, TournamentApplication, Stage, Sponsor, Team, Match, PrizeContribution
from .application_admin import TournamentApplicationAdmin

admin.site.site_header = 'FRI — CRM организаторов'
admin.site.site_title = 'FRI Admin'
admin.site.login_form = RateLimitedAdminAuthenticationForm
admin.site.register(TournamentApplication, TournamentApplicationAdmin)


@admin.register(User)
class EmailUserAdmin(UserAdmin):
    add_form = AdminUserCreationForm
    form = AdminUserChangeForm
    list_display = ('email', 'nickname', 'is_staff', 'is_active')
    list_filter = ('groups', 'is_staff', 'is_active')
    ordering = ('email',)
    search_fields = ('email', 'nickname', 'telegram', 'discord', 'team_name', 'first_name', 'last_name')
    fieldsets = ((None, {'fields': ('email', 'password')}), ('Профиль', {'fields': ('first_name', 'last_name', 'nickname', 'telegram', 'discord', 'steam_url', 'team_name', 'mmr', 'position')}), ('Оборудование', {'fields': ('microphone', 'webcam')}), ('Доступ', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}), ('Даты', {'fields': ('last_login', 'date_joined', 'privacy_accepted_at', 'privacy_policy_version')}))
    readonly_fields = ('privacy_accepted_at', 'privacy_policy_version')
    add_fieldsets = ((None, {'classes': ('wide',), 'fields': ('email', 'password1', 'password2')}),)


@admin.register(TournamentSettings)
class TournamentSettingsAdmin(admin.ModelAdmin):
    readonly_fields = ('prize_total',)

    def has_add_permission(self, request):
        return super().has_add_permission(request) and not TournamentSettings.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(Stage)
class StageAdmin(admin.ModelAdmin):
    list_display = ('name', 'starts_at', 'position')
    list_editable = ('starts_at', 'position')


class PrizeContributionInline(admin.TabularInline):
    model = PrizeContribution
    fields = ('amount', 'status', 'note', 'created_at')
    readonly_fields = ('created_at',)
    extra = 0


@admin.register(Sponsor)
class SponsorAdmin(admin.ModelAdmin):
    search_fields = ('name',)
    list_display = ('name', 'gallery_slot', 'presentation', 'contributed')
    list_editable = ('presentation',)
    inlines = (PrizeContributionInline,)

    def get_queryset(self, request):
        return super().get_queryset(request).annotate(contributed_total=Sum('prize_contributions__amount'))

    @admin.display(description='Взнос в фонд', ordering='contributed_total')
    def contributed(self, obj):
        return obj.contributed_total or 0


@admin.register(Team)
class TeamAdmin(admin.ModelAdmin):
    search_fields = ('name',)
    filter_horizontal = ('players',)


@admin.register(Match)
class MatchAdmin(admin.ModelAdmin):
    list_display = ('title', 'team_a', 'team_b', 'stage', 'starts_at', 'result')
    list_filter = ('stage',)
    search_fields = ('title', 'team_a__name', 'team_b__name')
