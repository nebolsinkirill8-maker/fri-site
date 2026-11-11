from django import forms

from .models import MESSAGE_LIMIT, Ticket


class ReplyForm(forms.Form):
    body = forms.CharField(label='Сообщение', max_length=MESSAGE_LIMIT, widget=forms.Textarea(attrs={'rows': 5}))


class TicketForm(forms.ModelForm):
    body = ReplyForm.base_fields['body']

    class Meta:
        model = Ticket
        fields = ('subject', 'body')
