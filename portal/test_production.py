from django.apps import apps
from django.contrib.auth import get_user_model
from django.contrib.staticfiles import finders
from django.test import RequestFactory, TestCase, override_settings
from django.urls import reverse
from django.views.defaults import server_error

from support.models import Ticket

from . import ratelimit

User = get_user_model()
PASSWORD = 'Long-Safe-Password-471!'


class LoginRateLimitTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user('player@example.com', PASSWORD)

    def login(self, password, email='player@example.com', **extra):
        return self.client.post(reverse('login'), {'username': email, 'password': password}, **extra)

    def test_account_is_locked_after_repeated_failures_even_with_correct_password(self):
        attempts, _ = ratelimit.LOGIN_PER_ACCOUNT
        for _ in range(attempts):
            self.login('wrong-password')
        response = self.login(PASSWORD)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Слишком много попыток входа')
        self.assertNotIn('_auth_user_id', self.client.session)

    def test_successful_login_resets_account_counter(self):
        attempts, _ = ratelimit.LOGIN_PER_ACCOUNT
        for _ in range(attempts - 1):
            self.login('wrong-password')
        self.assertEqual(self.login(PASSWORD).status_code, 302)
        self.client.logout()
        for _ in range(attempts - 1):
            self.login('wrong-password')
        self.assertEqual(self.login(PASSWORD).status_code, 302)

    def test_email_case_does_not_bypass_lock(self):
        attempts, _ = ratelimit.LOGIN_PER_ACCOUNT
        for index in range(attempts):
            self.login('wrong-password', email='PLAYER@example.com' if index % 2 else 'player@EXAMPLE.com')
        self.assertContains(self.login(PASSWORD), 'Слишком много попыток входа')

    def test_ip_is_limited_across_accounts(self):
        attempts, _ = ratelimit.LOGIN_PER_IP
        for index in range(attempts):
            self.login('wrong-password', email=f'spray{index}@example.com')
        self.assertContains(self.login(PASSWORD), 'Слишком много попыток входа')

    def test_admin_login_is_limited_too(self):
        User.objects.create_superuser('boss@example.com', PASSWORD)
        url = reverse('admin:login')
        attempts, _ = ratelimit.LOGIN_PER_ACCOUNT
        for _ in range(attempts):
            self.client.post(url, {'username': 'boss@example.com', 'password': 'wrong-password'})
        response = self.client.post(url, {'username': 'boss@example.com', 'password': PASSWORD})
        self.assertContains(response, 'Слишком много попыток входа')
        self.assertNotIn('_auth_user_id', self.client.session)

    @override_settings(FRI_CLIENT_IP_HEADER='HTTP_X_REAL_IP')
    def test_configured_proxy_header_separates_visitors(self):
        attempts, _ = ratelimit.LOGIN_PER_IP
        for index in range(attempts):
            self.login('wrong-password', email=f'spray{index}@example.com', HTTP_X_REAL_IP='203.0.113.5')
        self.assertContains(self.login(PASSWORD, HTTP_X_REAL_IP='203.0.113.5'), 'Слишком много попыток входа')
        self.assertEqual(self.login(PASSWORD, HTTP_X_REAL_IP='198.51.100.7').status_code, 302)

    def test_forwarded_header_is_ignored_without_configuration(self):
        attempts, _ = ratelimit.LOGIN_PER_IP
        for index in range(attempts):
            self.login('wrong-password', email=f'spray{index}@example.com', HTTP_X_REAL_IP=f'203.0.113.{index}')
        self.assertContains(self.login(PASSWORD, HTTP_X_REAL_IP='198.51.100.7'), 'Слишком много попыток входа')


class RegistrationTests(TestCase):
    def register(self, email, **extra):
        data = {'email': email, 'password1': PASSWORD, 'password2': PASSWORD, 'privacy_consent': 'on', **extra}
        return self.client.post(reverse('register'), data)

    def test_privacy_consent_is_required_and_recorded(self):
        response = self.client.post(reverse('register'), {'email': 'a@example.com', 'password1': PASSWORD, 'password2': PASSWORD})
        self.assertEqual(response.status_code, 200)
        self.assertFalse(User.objects.exists())
        self.assertContains(response, 'Без согласия на обработку персональных данных')
        self.assertContains(response, f'href="{reverse("privacy")}"')
        self.register('a@example.com')
        user = User.objects.get()
        self.assertIsNotNone(user.privacy_accepted_at)
        from .models import PRIVACY_POLICY_VERSION
        self.assertEqual(user.privacy_policy_version, PRIVACY_POLICY_VERSION)

    def test_registrations_per_ip_are_limited(self):
        allowed, _ = ratelimit.REGISTRATIONS_PER_IP
        for index in range(allowed):
            self.assertEqual(self.register(f'player{index}@example.com').status_code, 302)
            self.client.logout()
        response = self.register('one-too-many@example.com')
        self.assertEqual(response.status_code, 429)
        self.assertContains(response, 'слишком много регистраций', status_code=429)
        self.assertEqual(User.objects.count(), allowed)

    def test_privacy_page_is_public_and_linked_from_footer(self):
        response = self.client.get(reverse('privacy'))
        self.assertContains(response, '152-ФЗ')
        self.assertContains(self.client.get(reverse('home')), f'href="{reverse("privacy")}"')
        self.assertContains(self.client.get(reverse('tournament')), f'href="{reverse("privacy")}"')

    def test_admin_can_create_user_without_player_consent(self):
        admin_user = User.objects.create_superuser('boss@example.com', PASSWORD)
        self.client.force_login(admin_user)
        response = self.client.post(reverse('admin:portal_user_add'), {'email': 'staff-made@example.com', 'password1': PASSWORD, 'password2': PASSWORD, '_save': '1'})
        self.assertEqual(response.status_code, 302)
        self.assertIsNone(User.objects.get(email='staff-made@example.com').privacy_accepted_at)


class SupportRateLimitTests(TestCase):
    def test_new_tickets_per_user_are_limited(self):
        user = User.objects.create_user('player@example.com', PASSWORD)
        self.client.force_login(user)
        allowed, _ = ratelimit.TICKETS_PER_USER
        for index in range(allowed):
            self.assertEqual(self.client.post(reverse('support:index'), {'subject': f'Вопрос {index}', 'body': 'Текст'}).status_code, 302)
        response = self.client.post(reverse('support:index'), {'subject': 'Спам', 'body': 'Текст'})
        self.assertEqual(response.status_code, 429)
        self.assertContains(response, 'Слишком много новых обращений', status_code=429)
        self.assertEqual(Ticket.objects.count(), allowed)
        other = User.objects.create_user('other@example.com', PASSWORD)
        self.client.force_login(other)
        self.assertEqual(self.client.post(reverse('support:index'), {'subject': 'Вопрос', 'body': 'Текст'}).status_code, 302)


class HardeningTests(TestCase):
    def test_content_security_policy_header(self):
        policy = self.client.get(reverse('home')).headers['Content-Security-Policy']
        self.assertIn("script-src 'self'", policy)
        self.assertIn('frame-src https://player.twitch.tv', policy)
        self.assertIn("frame-ancestors 'none'", policy)

    def test_custom_404_page(self):
        response = self.client.get('/no-such-page/')
        self.assertContains(response, 'Такой страницы нет', status_code=404)
        self.assertContains(response, 'href="/"', status_code=404)

    def test_custom_500_page_renders_without_request_context(self):
        response = server_error(RequestFactory().get('/'))
        self.assertEqual(response.status_code, 500)
        self.assertIn('Что-то сломалось на нашей стороне', response.content.decode())

    def test_legacy_and_unused_files_are_not_collected(self):
        # collectstatic passes the staticfiles app's ignore_patterns to every finder.
        patterns = apps.get_app_config('staticfiles').ignore_patterns
        collected = {path for finder in finders.get_finders() for path, _ in finder.list(patterns)}
        for hidden in ('index.html', 'design-log.md', 'content.js', 'assets/travis-scott-dumbo.mp3', 'screenshots/FRI-desktop-full.png', 'assets/zxc-shadow-fiend-slow.webm'):
            self.assertNotIn(hidden, collected)
        for needed in ('site.js', 'django-content.js', 'legal.css', 'assets/zxc-shadow-fiend-seamless.webm', 'assets/kirill.png', 'assets/onest.ttf'):
            self.assertIn(needed, collected)
