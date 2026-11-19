from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings

from .access import COOKIE_NAME

KEY = 'k' * 20 + 'Secret-Invite-Key_42'
OTHER_KEY = 'z' * 40


@override_settings(FRI_ACCESS_KEY=KEY)
class AccessGateTests(TestCase):
    def enter(self):
        return self.client.get(f'/invite/{KEY}/')

    def test_everything_is_hidden_without_invite(self):
        for path in ('/', '/tournament/', '/zxc/', '/privacy/', '/accounts/login/', '/accounts/register/', '/support/', '/admin/', '/admin/login/'):
            response = self.client.get(path)
            self.assertEqual(response.status_code, 404, path)
            self.assertNotContains(response, 'FRI', status_code=404)
            self.assertEqual(response.headers['X-Robots-Tag'], 'noindex, nofollow')

    def test_posts_are_blocked_without_invite(self):
        get_user_model().objects.create_user('player@example.com', 'Long-Safe-Password-471!')
        response = self.client.post('/accounts/login/', {'username': 'player@example.com', 'password': 'Long-Safe-Password-471!'})
        self.assertEqual(response.status_code, 404)
        self.assertNotIn('_auth_user_id', self.client.session)

    def test_wrong_or_partial_keys_are_rejected(self):
        for path in ('/invite/', '/invite/wrong/', f'/invite/{KEY[:-1]}/', f'/invite/{KEY}x/', f'/invite/{KEY.upper()}/'):
            response = self.client.get(path)
            self.assertEqual(response.status_code, 404, path)
            self.assertNotIn(COOKIE_NAME, response.cookies)

    def test_invite_sets_cookie_and_redirects_home(self):
        response = self.enter()
        self.assertRedirects(response, '/', fetch_redirect_response=False)
        cookie = response.cookies[COOKIE_NAME]
        self.assertTrue(cookie['httponly'])
        self.assertEqual(cookie['samesite'], 'Lax')
        self.assertNotIn(KEY, cookie.value)
        for path in ('/', '/tournament/', '/privacy/', '/accounts/login/'):
            self.assertEqual(self.client.get(path).status_code, 200, path)

    def test_invite_without_trailing_slash_works(self):
        self.assertEqual(self.client.get(f'/invite/{KEY}').status_code, 302)

    def test_forged_cookie_is_rejected(self):
        self.client.cookies[COOKIE_NAME] = 'anything'
        self.assertEqual(self.client.get('/').status_code, 404)

    def test_rotating_key_revokes_old_cookies(self):
        self.enter()
        self.assertEqual(self.client.get('/').status_code, 200)
        with self.settings(FRI_ACCESS_KEY=OTHER_KEY):
            self.assertEqual(self.client.get('/').status_code, 404)

    def test_logout_keeps_site_access(self):
        user = get_user_model().objects.create_user('player@example.com', 'Long-Safe-Password-471!')
        self.enter()
        self.client.force_login(user)
        self.client.post('/accounts/logout/')
        self.assertEqual(self.client.get('/').status_code, 200)

    def test_gate_is_off_without_key(self):
        with self.settings(FRI_ACCESS_KEY=''):
            self.assertEqual(self.client.get('/').status_code, 200)
            self.assertEqual(self.client.get(f'/invite/{KEY}/').status_code, 404)
