from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .forms import AdminUserCreationForm, AdminUserChangeForm
from .models import User, TournamentSettings, TournamentApplication, Stage, Sponsor, Team, Match
from .application_admin import TournamentApplicationAdmin

admin.site.site_header = 'FRI — CRM организаторов'
admin.site.site_title = 'FRI Admin'
admin.site.register(TournamentApplication, TournamentApplicationAdmin)


@admin.register(User)
class EmailUserAdmin(UserAdmin):
    add_form = AdminUserCreationForm
    form = AdminUserChangeForm
    list_display = ('email', 'nickname', 'is_staff', 'is_active')
    list_filter = ('groups', 'is_staff', 'is_active')
    ordering = ('email',)
    search_fields = ('email', 'nickname', 'telegram', 'discord', 'team_name', 'first_name', 'last_name')
    fieldsets = ((None, {'fields': ('email', 'password')}), ('Профиль', {'fields': ('first_name', 'last_name', 'nickname', 'telegram', 'discord', 'steam_url', 'team_name', 'mmr', 'position')}), ('Доступ', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}), ('Даты', {'fields': ('last_login', 'date_joined')}))
    add_fieldsets = ((None, {'classes': ('wide',), 'fields': ('email', 'password1', 'password2')}),)


@admin.register(TournamentSettings)
class TournamentSettingsAdmin(admin.ModelAdmin):
    def has_add_permission(self, request):
        return super().has_add_permission(request) and not TournamentSettings.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(Stage)
class StageAdmin(admin.ModelAdmin):
    list_display = ('name', 'starts_at', 'position')
    list_editable = ('starts_at', 'position')


@admin.register(Sponsor)
class SponsorAdmin(admin.ModelAdmin):
    search_fields = ('name',)
    list_display = ('name', 'presentation')
    list_editable = ('presentation',)


@admin.register(Team)
class TeamAdmin(admin.ModelAdmin):
    search_fields = ('name',)
    filter_horizontal = ('players',)


@admin.register(Match)
class MatchAdmin(admin.ModelAdmin):
    list_display = ('title', 'team_a', 'team_b', 'stage', 'starts_at', 'result')
    list_filter = ('stage',)
    search_fields = ('title', 'team_a__name', 'team_b__name')
