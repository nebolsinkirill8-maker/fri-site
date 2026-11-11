from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.test import Client, TestCase
from django.urls import reverse

from .models import TournamentApplication, TournamentSettings


class TournamentApplicationTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            'player@example.com',
            'example-pass',
            nickname='Player',
            steam_url='https://steamcommunity.com/id/example',
            telegram='@example_player',
            discord='example_player',
            team_name='Example Team',
            mmr=0,
            position='1',
        )
        self.other = get_user_model().objects.create_user('other@example.com', 'example-pass')
        self.url = reverse('application')

    def open_intake(self):
        TournamentSettings.objects.update_or_create(pk=1, defaults={'applications_open': True})

    def submit(self, **post_data):
        self.open_intake()
        self.client.force_login(self.user)
        self.assertRedirects(self.client.post(self.url, {'resides_in_russia': True, 'is_student': True, **post_data}), self.url)
        return TournamentApplication.objects.get(user=self.user)

    def test_anonymous_request_requires_login(self):
        self.assertRedirects(self.client.get(self.url), reverse('login') + '?next=' + self.url)
        self.assertRedirects(self.client.post(self.url), reverse('login') + '?next=' + self.url)

    def test_closed_intake_and_incomplete_profile_cannot_submit(self):
        self.client.force_login(self.user)
        self.assertFalse(self.client.get(self.url).context['applications_open'])
        self.assertEqual(self.client.post(self.url).status_code, 403)
        self.open_intake()
        self.client.force_login(self.other)
        self.assertFalse(self.client.get(self.url).context['profile_ready'])
        self.assertEqual(self.client.post(self.url).status_code, 400)
        self.assertFalse(TournamentApplication.objects.exists())

    def test_submission_is_pending_and_cannot_inject_fields(self):
        item = self.submit(
            status='accepted', user=self.other.pk, nickname='Injected',
            decision_comment='Injected', comment='Мой комментарий',
        )
        self.assertEqual(item.status, TournamentApplication.Status.PENDING)
        self.assertEqual(item.nickname, self.user.nickname)
        self.assertEqual(item.steam_url, self.user.steam_url)
        self.assertEqual(item.telegram, self.user.telegram)
        self.assertEqual(item.discord, 'example_player')
        self.assertEqual(item.team_name, 'Example Team')
        self.assertEqual(item.mmr, 0)
        self.assertEqual(item.position, '1')
        self.assertEqual(item.decision_comment, '')
        self.assertEqual(item.comment, 'Мой комментарий')
        response = self.client.get(self.url)
        self.assertContains(response, 'В обработке')
        self.assertIn('no-store', response['Cache-Control'])
        self.assertContains(self.client.get(reverse('profile')), 'В обработке')

    def test_duplicate_is_idempotent_and_profile_changes_do_not_modify_snapshot(self):
        item = self.submit(comment='Первое сообщение')
        self.assertRedirects(
            self.client.post(reverse('profile_edit'), {'nickname': 'New nickname'}),
            reverse('profile'),
        )
        self.assertRedirects(self.client.post(self.url, {'comment': 'Замена'}), self.url)
        self.user.refresh_from_db()
        item.refresh_from_db()
        self.assertEqual(TournamentApplication.objects.count(), 1)
        self.assertEqual(self.user.nickname, 'New nickname')
        self.assertEqual(item.nickname, 'Player')
        self.assertEqual(item.steam_url, 'https://steamcommunity.com/id/example')
        self.assertEqual(item.comment, 'Первое сообщение')

    def test_two_competitions_have_independent_gates_and_statuses(self):
        team = self.submit(competition='zxc')
        self.assertEqual(team.competition, 'team')
        zxc_url = reverse('zxc_application')
        self.assertEqual(self.client.post(zxc_url, {'resides_in_russia': True}).status_code, 403)
        TournamentSettings.objects.filter(pk=1).update(zxc_applications_open=True, applications_open=False)
        self.assertRedirects(self.client.post(zxc_url, {'resides_in_russia': True, 'competition': 'team', 'status': 'accepted'}), zxc_url)
        zxc = TournamentApplication.objects.get(user=self.user, competition='zxc')
        self.assertEqual(zxc.status, 'pending')
        self.assertTrue(zxc.resides_in_russia)
        self.assertFalse(zxc.is_student)
        self.assertEqual(zxc.team_name, '')
        self.assertRedirects(self.client.post(zxc_url, {'resides_in_russia': True}), zxc_url)
        self.assertEqual(TournamentApplication.objects.filter(user=self.user).count(), 2)
        team.status = 'accepted'
        team.save()
        zxc.refresh_from_db()
        self.assertEqual(zxc.status, 'pending')

    def test_required_declarations_and_contact_fields(self):
        self.open_intake()
        self.client.force_login(self.user)
        for data in ({}, {'resides_in_russia': True}, {'is_student': True}):
            self.assertEqual(self.client.post(self.url, data).status_code, 400)
        self.assertFalse(TournamentApplication.objects.exists())
        self.user.discord = ''
        self.user.save()
        self.assertEqual(self.client.post(self.url, {'resides_in_russia': True, 'is_student': True}).status_code, 400)
        self.assertFalse(TournamentApplication.objects.exists())

    def test_other_account_cannot_read_application(self):
        item = self.submit(comment='Приватный комментарий')
        item.decision_comment = 'Приватный ответ'
        item.save()
        self.client.force_login(self.other)
        response = self.client.get(self.url, {'user': self.user.pk, 'application': item.pk})
        self.assertIsNone(response.context['application'])
        self.assertNotContains(response, 'Приватный')

    def test_csrf_and_comment_length(self):
        self.open_intake()
        csrf_client = Client(enforce_csrf_checks=True)
        csrf_client.force_login(self.user)
        self.assertEqual(csrf_client.post(self.url).status_code, 403)
        self.client.force_login(self.user)
        self.assertEqual(self.client.post(self.url, {'comment': 'x' * 501}).status_code, 400)
        self.assertFalse(TournamentApplication.objects.exists())

    def test_staff_decision_is_visible_and_cannot_change_owner_or_snapshot(self):
        item = self.submit()
        staff = get_user_model().objects.create_user('staff@example.com', 'example-pass', is_staff=True)
        staff.groups.add(Group.objects.get(name='Сотрудники'))
        admin_url = reverse('admin:portal_tournamentapplication_change', args=[item.pk])
        self.assertEqual(self.client.get(admin_url).status_code, 302)
        self.client.force_login(staff)
        self.assertEqual(self.client.get(admin_url).status_code, 200)
        self.assertEqual(self.client.get(reverse('admin:portal_tournamentapplication_add')).status_code, 403)
        self.assertEqual(self.client.get(reverse('admin:portal_tournamentapplication_delete', args=[item.pk])).status_code, 403)
        for status, label in (
            (TournamentApplication.Status.ACCEPTED, 'Принята'),
            (TournamentApplication.Status.REJECTED, 'Отказ'),
        ):
            self.client.force_login(staff)
            self.assertEqual(self.client.post(admin_url, {
                'status': status,
                'decision_comment': 'Решение организатора',
                'user': self.other.pk,
                'nickname': 'Injected',
            }).status_code, 302)
            item.refresh_from_db()
            self.assertEqual(item.status, status)
            self.assertEqual(item.user_id, self.user.pk)
            self.assertEqual(item.nickname, 'Player')
            self.client.force_login(self.user)
            response = self.client.get(self.url)
            self.assertContains(response, label)
            self.assertContains(response, 'Решение организатора')
            self.assertContains(self.client.get(reverse('profile')), f'data-status="{status}"')

    def test_application_status_is_still_visible_when_intake_closes(self):
        item = self.submit()
        TournamentSettings.objects.filter(pk=1).update(applications_open=False)
        self.assertContains(self.client.get(self.url), 'В обработке')
        self.assertContains(self.client.get(reverse('profile')), f'Открыть заявку №{item.pk}')
