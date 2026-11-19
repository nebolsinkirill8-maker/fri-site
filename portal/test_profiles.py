from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.test import TestCase
from django.urls import reverse
from .forms import ProfileForm

User = get_user_model()


class ProfileTests(TestCase):
    def test_account_flow_pages_use_designed_surfaces(self):
        response = self.client.get(reverse('register'))
        self.assertContains(response, 'flow.css')
        self.client.force_login(self.user)
        for route in ('application', 'zxc_application'):
            response = self.client.get(reverse(route))
            self.assertContains(response, 'application-layout')
            self.assertContains(response, 'application-guide')
            self.assertContains(response, 'flow.css')
        response = self.client.get(reverse('support:index'))
        self.assertContains(response, 'support.css')

    def test_dashboard_status_badges_and_contextual_actions(self):
        from .models import TournamentApplication
        self.client.force_login(self.user)
        application = TournamentApplication.objects.create(
            user=self.user, nickname='Player', steam_url='https://steamcommunity.com/id/player_test/')
        for status in ('pending', 'accepted', 'rejected'):
            application.status = status
            application.save()
            response = self.client.get(reverse('profile'))
            self.assertContains(response, 'class="application-badge"')
            self.assertContains(response, f'data-status="{status}"')
            self.assertContains(response, reverse('application'))
            self.assertNotContains(response, 'player-shortcuts')
            self.assertContains(response, reverse('profile_edit'))
            self.assertContains(response, reverse('support:index'))

    def test_equipment_answers_are_required_validated_and_saved(self):
        user = User.objects.create_user('equipment@example.com', 'StrongPassword-245!')
        self.client.force_login(user)
        self.assertRedirects(self.client.post(reverse('profile_edit'), {'microphone': 'yes', 'webcam': 'no'}), reverse('profile'))
        user.refresh_from_db()
        self.assertEqual(user.microphone, 'yes')
        self.assertEqual(user.webcam, 'no')
        response = self.client.get(reverse('profile_edit'))
        self.assertEqual(response.context['form']['microphone'].value(), 'yes')
        self.assertFalse(ProfileForm(data={'microphone': 'unexpected'}, instance=user).is_valid())
        self.assertFalse(ProfileForm(data={}, instance=user).is_valid())
        self.assertContains(self.client.get(reverse('profile')), 'Веб-камера')

    def setUp(self):
        self.user = User.objects.create_user('player@example.com', 'StrongPassword-245!')

    def test_edit_requires_login(self):
        response = self.client.get(reverse('profile_edit'))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse('login'), response.url)

    def test_save_only_own_profile_fields(self):
        other = User.objects.create_user('other@example.com', 'StrongPassword-245!')
        self.client.force_login(self.user)
        response = self.client.post(reverse('profile_edit'), {'microphone': 'yes', 'webcam': 'no', 'nickname': 'Игрок', 'telegram': '@player_test', 'steam_url': 'https://steamcommunity.com/id/player_test/', 'mmr': '4500', 'position': '2', 'id': other.pk, 'email': 'changed@example.com', 'is_staff': True, 'is_superuser': True, 'groups': [Group.objects.get(name='Сотрудники').pk]})
        self.assertRedirects(response, reverse('profile'))
        self.user.refresh_from_db()
        other.refresh_from_db()
        self.assertEqual(self.user.nickname, 'Игрок')
        self.assertEqual(self.user.mmr, 4500)
        self.assertEqual(self.user.email, 'player@example.com')
        self.assertFalse(self.user.is_staff)
        self.assertFalse(self.user.is_superuser)
        self.assertFalse(self.user.groups.exists())
        self.assertEqual(other.nickname, '')

    def test_optional_fields_can_be_left_empty(self):
        form = ProfileForm(data={'microphone': 'no', 'webcam': 'no'}, instance=self.user)
        self.assertTrue(form.is_valid(), form.errors)
        form.save()
        self.user.refresh_from_db()
        self.assertIsNone(self.user.mmr)

    def test_team_name_is_staff_owned_and_equipment_cannot_be_skipped(self):
        self.user.team_name = 'Assigned by staff'
        self.user.save()
        form = ProfileForm(data={'discord': 'my.discord', 'team_name': 'Player override', 'microphone': 'no', 'webcam': 'yes'}, instance=self.user)
        self.assertNotIn('team_name', form.fields)
        self.assertTrue(form.is_valid(), form.errors)
        form.save()
        self.user.refresh_from_db()
        self.assertEqual(self.user.team_name, 'Assigned by staff')
        self.assertEqual(self.user.discord, 'my.discord')
        for data in ({}, {'microphone': 'yes'}, {'webcam': 'no'}, {'microphone': 'invalid', 'webcam': 'yes'}):
            self.assertFalse(ProfileForm(data=data, instance=self.user).is_valid())
        self.client.force_login(self.user)
        response = self.client.post(reverse('profile_edit'), {'microphone': 'yes'})
        self.assertEqual(response.status_code, 200)
        self.assertIn('webcam', response.context['form'].errors)
        self.assertNotContains(response, 'name="team_name"')

    def test_invalid_profile_fields(self):
        for data in ({'telegram': 'bad!'}, {'mmr': '-1'}, {'mmr': '20001'}, {'position': '9'}):
            self.assertFalse(ProfileForm(data=data, instance=self.user).is_valid(), data)
        for url in ('https://evil.example/id/player', 'http://steamcommunity.com/id/player', 'https://steamcommunity.com.evil/id/player', 'https://user:pass@steamcommunity.com/id/player', 'https://steamcommunity.com/id/player?x=1', 'https://steamcommunity.com/id/player#x', 'https://steamcommunity.com/'):
            self.assertFalse(ProfileForm(data={'steam_url': url}, instance=self.user).is_valid(), url)

    def test_register_enters_optional_second_step_and_group(self):
        response = self.client.post(reverse('register'), {'email': 'new@example.com', 'password1': 'StrongPassword-245!', 'password2': 'StrongPassword-245!', 'privacy_consent': 'on'})
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('profile_edit'))
        user = User.objects.get(email='new@example.com')
        self.assertTrue(user.groups.filter(name='Участники').exists())
        self.assertFalse(user.is_staff)

    def test_staff_group_is_least_privilege(self):
        participants = Group.objects.get(name='Участники')
        self.assertEqual(participants.permissions.count(), 0)
        self.user.groups.add(Group.objects.get(name='Сотрудники'))
        self.user.is_staff = True
        self.user.save()
        self.client.force_login(self.user)
        self.assertTrue(self.user.has_perm('portal.change_tournamentsettings'))
        self.assertTrue(self.user.has_perm('portal.view_user'))
        self.assertFalse(self.user.has_perm('portal.change_user'))
        self.assertFalse(self.user.has_perm('auth.change_group'))
        self.assertEqual(self.client.get('/admin/portal/user/').status_code, 200)
        self.assertEqual(self.client.post(f'/admin/portal/user/{self.user.pk}/change/', {'is_superuser': 'on'}).status_code, 403)
        self.user.refresh_from_db()
        self.assertFalse(self.user.is_superuser)
