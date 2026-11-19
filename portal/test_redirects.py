from urllib.parse import urlencode
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse


class RegistrationDestinationTests(TestCase):
    destination = '/accounts/zxc-application/'

    def test_registration_errors_and_profile_save_preserve_destination(self):
        data = {'email': 'next@example.test', 'password1': 'Secure-Fri-824!', 'password2': 'wrong', 'privacy_consent': 'on', 'next': self.destination}
        response = self.client.post(reverse('register'), data)
        self.assertEqual(response.context['next'], self.destination)
        self.assertContains(response, 'name="next"')
        data['password2'] = data['password1']
        response = self.client.post(reverse('register'), data)
        self.assertEqual(response.url, reverse('profile_edit') + '?' + urlencode({'next': self.destination}))
        response = self.client.post(reverse('profile_edit'), {'next': self.destination})
        self.assertEqual(response.context['next'], self.destination)
        response = self.client.post(reverse('profile_edit'), {'microphone': 'yes', 'webcam': 'no', 'next': self.destination})
        self.assertEqual(response.url, self.destination)

    def test_links_between_auth_pages_preserve_destination(self):
        for route, other in [('login', 'register'), ('register', 'login')]:
            response = self.client.get(reverse(route), {'next': self.destination})
            self.assertContains(response, reverse(other) + '?next=' + self.destination)

    def test_unsafe_destinations_are_ignored(self):
        user = get_user_model().objects.create_user('unsafe@example.test', 'Secure-Fri-824!')
        for destination in ['https://evil.test/', '//evil.test/', '/\\evil.test/', 'javascript:alert(1)']:
            response = self.client.get(reverse('register'), {'next': destination})
            self.assertEqual(response.context['next'], '')
            self.client.force_login(user)
            response = self.client.post(reverse('profile_edit'), {'microphone': 'yes', 'webcam': 'no', 'next': destination})
            self.assertEqual(response.url, reverse('profile'))
            self.client.logout()

    def test_direct_profile_save_does_not_reuse_previous_destination(self):
        user = get_user_model().objects.create_user('direct@example.test', 'Secure-Fri-824!')
        self.client.force_login(user)
        self.client.get(reverse('profile_edit'), {'next': self.destination})
        response = self.client.post(reverse('profile_edit'), {'microphone': 'yes', 'webcam': 'no'})
        self.assertEqual(response.url, reverse('profile'))
