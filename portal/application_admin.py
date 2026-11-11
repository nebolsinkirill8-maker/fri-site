from django.contrib import admin


class TournamentApplicationAdmin(admin.ModelAdmin):
    list_display = ('id', 'nickname', 'competition', 'team_name', 'user', 'status', 'created_at', 'updated_at')
    list_filter = ('competition', 'status', 'team_name')
    search_fields = ('nickname', 'user__email', 'telegram', 'discord', 'team_name')
    list_select_related = ('user',)
    readonly_fields = ('user', 'competition', 'nickname', 'steam_url', 'telegram', 'discord', 'team_name', 'resides_in_russia', 'is_student', 'mmr', 'position', 'comment', 'created_at', 'updated_at')
    fieldsets = (
        ('Решение', {'fields': ('status', 'decision_comment')}),
        ('Данные на момент подачи', {'fields': readonly_fields}),
    )

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
