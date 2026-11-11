from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_http_methods

from .forms import ReplyForm, TicketForm
from .models import Ticket


@never_cache
@login_required
@require_http_methods(['GET', 'POST'])
def index(request):
    form = TicketForm(request.POST if request.method == 'POST' else None)
    if request.method == 'POST' and form.is_valid():
        with transaction.atomic():
            ticket = form.save(commit=False)
            ticket.owner = request.user
            ticket.save()
            ticket.messages.create(author=request.user, body=form.cleaned_data['body'])
        return redirect('support:detail', pk=ticket.pk)
    tickets = Paginator(Ticket.objects.filter(owner=request.user), 20).get_page(request.GET.get('page'))
    return render(request, 'support/index.html', {'form': form, 'tickets': tickets})


@never_cache
@login_required
@require_http_methods(['GET', 'POST'])
def detail(request, pk):
    ticket = get_object_or_404(Ticket, pk=pk, owner=request.user)
    form = ReplyForm(request.POST if request.method == 'POST' else None)
    if request.method == 'POST' and form.is_valid():
        with transaction.atomic():
            # If the organizer closed the ticket after page load, do not append a message.
            is_open = Ticket.objects.filter(pk=pk, owner=request.user, status=Ticket.Status.OPEN).update(updated_at=timezone.now())
            if is_open:
                ticket.messages.create(author=request.user, body=form.cleaned_data['body'])
                return redirect('support:detail', pk=pk)
        ticket.refresh_from_db()
        form.add_error(None, 'Обращение уже закрыто. При необходимости создай новое.')
    return render(request, 'support/detail.html', {'ticket': ticket, 'thread': ticket.messages.all(), 'form': form})
