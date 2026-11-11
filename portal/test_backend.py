from urllib.parse import parse_qs, urlsplit
from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from .models import TournamentSettings

User = get_user_model()


class AccountTests(TestCase):
    def test_register_creates_hashed_password_and_server_session(self):
        response = self.client.post(reverse('register'), {'email': 'PLAYER@Example.com', 'password1': 'Long-Safe-Password-471!', 'password2': 'Long-Safe-Password-471!'})
        self.assertRedirects(response, reverse('profile_edit'))
        user = User.objects.get()
        self.assertEqual(user.email, 'player@example.com')
        self.assertTrue(user.check_password('Long-Safe-Password-471!'))
        self.assertEqual(int(self.client.session['_auth_user_id']), user.pk)
        self.assertTrue(self.client.cookies['sessionid']['httponly'])

    def test_case_insensitive_email_uniqueness(self):
        User.objects.create_user('player@example.com', 'safe-pass')
        with transaction.atomic(), self.assertRaises(IntegrityError):
            User.objects.create_user('PLAYER@example.com', 'other-pass')

    def test_login_normalizes_email_and_logout_is_post_only(self):
        user = User.objects.create_user('player@example.com', 'Long-Safe-Password-471!')
        response = self.client.post(reverse('login'), {'username': 'PLAYER@EXAMPLE.COM', 'password': 'Long-Safe-Password-471!'})
        self.assertRedirects(response, reverse('profile'))
        self.assertEqual(int(self.client.session['_auth_user_id']), user.pk)
        self.assertEqual(self.client.get(reverse('logout')).status_code, 405)
        self.client.post(reverse('logout'))
        self.assertNotIn('_auth_user_id', self.client.session)

    def test_profile_requires_login(self):
        self.assertRedirects(self.client.get(reverse('profile')), reverse('login') + '?next=' + reverse('profile'))

    def test_csrf_required_on_registration_login_and_logout(self):
        client = Client(enforce_csrf_checks=True)
        for name in ('register', 'login', 'logout'):
            self.assertEqual(client.post(reverse(name), {}).status_code, 403)

    def test_nonstaff_cannot_access_admin(self):
        user = User.objects.create_user('player@example.com', 'safe-pass')
        self.client.force_login(user)
        self.assertEqual(self.client.get('/admin/').status_code, 302)

    def test_superuser_can_access_crm(self):
        user = User.objects.create_superuser('admin@example.com', 'safe-pass')
        self.client.force_login(user)
        for path in ('/admin/', '/admin/portal/user/', '/admin/portal/tournamentsettings/', '/admin/portal/team/', '/admin/portal/match/'):
            self.assertEqual(self.client.get(path).status_code, 200)


class TournamentTests(TestCase):
    def test_content_defaults_are_unconfirmed_and_contacts_are_real(self):
        response = self.client.get(reverse('tournament'))
        self.assertEqual(response.status_code, 200)
        content = response.context['fri_content']
        settings = response.context['tournament_settings']
        self.assertEqual(content['prize'], '')
        for field in ('group_format', 'playoff_format', 'main_event'):
            self.assertEqual(getattr(settings, field), '')
        self.assertTrue(all(s['startsAt'] is None for s in content['stages']))
        self.assertEqual(content['contacts'][0]['url'], 'https://t.me/firstrussianinternational')
        self.assertEqual(content['contacts'][1]['url'], 'https://discord.gg/qtRGBJMWg8')
        self.assertFalse(TournamentSettings.objects.exists())

    @override_settings(ALLOWED_HOSTS=['localhost', 'fri.example'])
    def test_twitch_parent_uses_validated_request_hostname_without_port(self):
        for host in ('localhost:8000', 'fri.example'):
            response = self.client.get(reverse('tournament'), HTTP_HOST=host)
            query = parse_qs(urlsplit(response.context['twitch_embed_url']).query)
            self.assertEqual(query['parent'], [host.split(':')[0]])
            self.assertEqual(query['channel'], ['ceo111kimikiru'])
        self.assertEqual(self.client.get(reverse('tournament'), HTTP_HOST='evil.example').status_code, 400)

    def test_admin_content_is_used(self):
        TournamentSettings.objects.create(prize='Подтверждено', group_format='Группы')
        response = self.client.get(reverse('tournament'))
        self.assertEqual(response.context['fri_content']['prize'], 'Подтверждено')

    def test_settings_admin_does_not_offer_second_record(self):
        user = User.objects.create_superuser('admin@example.com', 'safe-pass')
        self.client.force_login(user)
        self.assertEqual(self.client.get('/admin/portal/tournamentsettings/add/').status_code, 200)
        TournamentSettings.objects.create()
        self.assertEqual(self.client.get('/admin/portal/tournamentsettings/add/').status_code, 403)
        settings = TournamentSettings(prize='New')
        settings.save()
        self.assertEqual(TournamentSettings.objects.count(), 1)
