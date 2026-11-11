from django import forms
from django.contrib import admin
from django.core.exceptions import PermissionDenied

from .models import MESSAGE_LIMIT, Ticket, TicketMessage


class TicketAdminForm(forms.ModelForm):
    reply = forms.CharField(label='Ответ пользователю', max_length=MESSAGE_LIMIT, required=False, widget=forms.Textarea(attrs={'rows': 5}))

    def clean(self):
        cleaned = super().clean()
        if cleaned.get('reply') and self.instance.status == Ticket.Status.CLOSED and cleaned.get('status') == Ticket.Status.CLOSED:
            self.add_error('reply', 'Чтобы ответить на закрытое обращение, сначала измени статус на «Открыто».')
        return cleaned


class TicketMessageInline(admin.TabularInline):
    model = TicketMessage
    fields = ('author', 'from_staff', 'body', 'created_at')
    readonly_fields = fields
    extra = 0
    can_delete = False

    def has_add_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False


@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
    form = TicketAdminForm
    inlines = (TicketMessageInline,)
    list_display = ('id', 'subject', 'owner', 'status', 'updated_at')
    list_filter = ('status',)
    list_select_related = ('owner',)
    search_fields = ('subject', 'owner__email')
    readonly_fields = ('owner', 'subject', 'created_at', 'updated_at')

    def get_fields(self, request, obj=None):
        fields = ('owner', 'subject', 'status', 'created_at', 'updated_at')
        if self.has_change_permission(request, obj) and request.user.has_perm('support.add_ticketmessage'):
            return (*fields, 'reply')
        return fields

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def save_model(self, request, obj, form, change):
        reply = form.cleaned_data.get('reply')
        if reply and not request.user.has_perm('support.add_ticketmessage'):
            raise PermissionDenied
        super().save_model(request, obj, form, change)
        if reply:
            obj.messages.create(author=request.user, body=reply, from_staff=True)
