from django.conf import settings
from django.core.validators import MaxLengthValidator
from django.db import models


MESSAGE_LIMIT = 3000


class Ticket(models.Model):
    class Status(models.TextChoices):
        OPEN = 'open', 'Открыто'
        CLOSED = 'closed', 'Закрыто'

    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='support_tickets', verbose_name='Пользователь')
    subject = models.CharField('Тема', max_length=120)
    status = models.CharField('Статус', max_length=6, choices=Status.choices, default=Status.OPEN)
    created_at = models.DateTimeField('Создано', auto_now_add=True)
    updated_at = models.DateTimeField('Обновлено', auto_now=True)

    class Meta:
        ordering = ('-updated_at', '-pk')
        verbose_name = 'Обращение'
        verbose_name_plural = 'Обращения'

    def __str__(self):
        return f'#{self.pk}: {self.subject}'


class TicketMessage(models.Model):
    ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE, related_name='messages', verbose_name='Обращение')
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, verbose_name='Автор')
    from_staff = models.BooleanField('Ответ поддержки', default=False)
    body = models.TextField('Сообщение', validators=[MaxLengthValidator(MESSAGE_LIMIT)])
    created_at = models.DateTimeField('Отправлено', auto_now_add=True)

    class Meta:
        ordering = ('created_at', 'pk')
        verbose_name = 'Сообщение'
        verbose_name_plural = 'Сообщения'
