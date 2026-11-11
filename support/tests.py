from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission
from django.test import Client, TestCase
from django.urls import reverse

from .models import MESSAGE_LIMIT, Ticket, TicketMessage


class SupportTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        User = get_user_model()
        cls.owner = User.objects.create_user('support-owner@example.com')
        cls.other = User.objects.create_user('support-other@example.com')
        cls.staff = User.objects.create_user('support-staff@example.com', is_staff=True)
        cls.staff.groups.add(Group.objects.get(name='Сотрудники'))
        cls.ticket = Ticket.objects.create(owner=cls.owner, subject='Личный вопрос')
        cls.initial = cls.ticket.messages.create(author=cls.owner, body='Приватное сообщение')
        cls.index_url = reverse('support:index')
        cls.detail_url = reverse('support:detail', args=[cls.ticket.pk])
        cls.admin_url = reverse('admin:support_ticket_change', args=[cls.ticket.pk])

    def test_anonymous_redirects_to_login_with_return_path(self):
        for url in (self.index_url, self.detail_url):
            self.assertRedirects(self.client.get(url), f'{reverse("login")}?next={url}')

    def test_other_account_cannot_list_view_or_reply_to_ticket(self):
        self.client.force_login(self.other)
        self.assertNotContains(self.client.get(self.index_url), self.ticket.subject)
        self.assertEqual(self.client.get(self.detail_url).status_code, 404)
        self.assertEqual(self.client.post(self.detail_url, {'body': 'Попытка ответа'}).status_code, 404)
        self.assertEqual(self.ticket.messages.count(), 1)
        self.assertEqual(self.client.get(self.admin_url).status_code, 302)

    def test_creation_sets_current_owner_and_author_and_escapes_content(self):
        self.client.force_login(self.owner)
        response = self.client.post(self.index_url, {
            'subject': 'Как подать заявку?', 'body': '<script>alert(1)</script>',
            'owner': self.other.pk, 'status': 'closed', 'author': self.staff.pk, 'from_staff': 'on',
        })
        ticket = Ticket.objects.get(subject='Как подать заявку?')
        self.assertEqual(ticket.owner, self.owner)
        self.assertEqual(ticket.status, Ticket.Status.OPEN)
        message = ticket.messages.get()
        self.assertEqual(message.author, self.owner)
        self.assertFalse(message.from_staff)
        self.assertRedirects(response, reverse('support:detail', args=[ticket.pk]))
        page = self.client.get(reverse('support:detail', args=[ticket.pk]))
        self.assertContains(page, '&lt;script&gt;alert(1)&lt;/script&gt;')
        self.assertIn('no-store', page.headers['Cache-Control'])

    def test_csrf_and_length_limits(self):
        client = Client(enforce_csrf_checks=True)
        client.force_login(self.owner)
        for url in (self.index_url, self.detail_url):
            self.assertEqual(client.post(url, {'subject': 'Вопрос', 'body': 'Текст'}).status_code, 403)
        self.client.force_login(self.owner)
        self.client.post(self.index_url, {'subject': 'x' * 121, 'body': 'Текст'})
        self.client.post(self.index_url, {'subject': 'Новая тема', 'body': 'x' * (MESSAGE_LIMIT + 1)})
        self.client.post(self.detail_url, {'body': 'x' * (MESSAGE_LIMIT + 1)})
        self.assertEqual(Ticket.objects.count(), 1)
        self.assertEqual(self.ticket.messages.count(), 1)

    def test_follow_up_only_on_open_ticket(self):
        self.client.force_login(self.owner)
        response = self.client.post(self.detail_url, {'body': 'Уточнение', 'author': self.staff.pk, 'from_staff': 'on'})
        self.assertRedirects(response, self.detail_url)
        message = self.ticket.messages.get(body='Уточнение')
        self.assertEqual(message.author, self.owner)
        self.assertFalse(message.from_staff)
        Ticket.objects.filter(pk=self.ticket.pk).update(status=Ticket.Status.CLOSED)
        response = self.client.post(self.detail_url, {'body': 'Запоздалое сообщение'})
        self.assertContains(response, 'Обращение уже закрыто.')
        self.assertEqual(self.ticket.messages.count(), 2)

    def admin_post(self, reply, status=Ticket.Status.OPEN):
        return self.client.post(self.admin_url, {
            'status': status, 'reply': reply, 'owner': self.other.pk, 'subject': 'Подмена темы',
            'messages-TOTAL_FORMS': '1', 'messages-INITIAL_FORMS': '1',
            'messages-0-id': self.initial.pk, 'messages-0-body': 'Подмена текста',
            'messages-0-author': self.other.pk, 'messages-0-DELETE': 'on', '_save': '1',
        })

    def test_staff_can_reply_and_close_without_modifying_original_message(self):
        self.client.force_login(self.staff)
        self.assertContains(self.client.get(self.admin_url), 'Ответ пользователю')
        response = self.admin_post('Ответ сотрудника', Ticket.Status.CLOSED)
        self.assertEqual(response.status_code, 302)
        self.ticket.refresh_from_db()
        self.assertEqual(self.ticket.status, Ticket.Status.CLOSED)
        self.assertEqual(self.ticket.owner, self.owner)
        self.assertEqual(self.ticket.subject, 'Личный вопрос')
        self.initial.refresh_from_db()
        self.assertEqual(self.initial.body, 'Приватное сообщение')
        reply = self.ticket.messages.get(from_staff=True)
        self.assertEqual(reply.author, self.staff)
        self.assertEqual(reply.body, 'Ответ сотрудника')
        self.assertContains(self.admin_post('Ответ после закрытия', Ticket.Status.CLOSED), 'сначала измени статус')
        self.client.force_login(self.owner)
        page = self.client.get(self.detail_url)
        self.assertContains(page, 'Ответ сотрудника')
        self.assertContains(page, 'Поддержка FRI')
        self.assertNotContains(page, self.staff.email)
        self.assertNotContains(page, 'Отправить сообщение')

    def test_admin_without_message_permission_cannot_reply(self):
        limited = get_user_model().objects.create_user('support-limited@example.com', is_staff=True)
        limited.user_permissions.add(Permission.objects.get(content_type__app_label='support', codename='change_ticket'))
        self.client.force_login(limited)
        self.assertNotContains(self.client.get(self.admin_url), 'Ответ пользователю')
        self.assertEqual(self.admin_post('Попытка ответа').status_code, 403)
        self.assertEqual(TicketMessage.objects.count(), 1)
