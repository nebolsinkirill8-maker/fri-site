from django.test import TestCase
from django.urls import reverse
from .models import TournamentSettings


class PageIntegrationTests(TestCase):
    def test_dates_are_visible_for_both_tours_without_opening_intake(self):
        from datetime import date
        settings = TournamentSettings.objects.create(registration_starts_on=date(2026, 11, 13), registration_ends_on=date(2026, 11, 27), bracket_ready_on=date(2026, 12, 4))
        for name in ('tournament', 'zxc'):
            response = self.client.get(reverse(name))
            for text in ('13 ноября 2026', '27 ноября 2026', '4 декабря 2026'):
                self.assertContains(response, text)
        settings.refresh_from_db()
        self.assertFalse(settings.applications_open)
        self.assertFalse(settings.zxc_applications_open)

    def test_zxc_has_its_own_poster_and_does_not_open_registration(self):
        response = self.client.get(reverse('zxc'))
        self.assertContains(response, 'assets/zxc-lilies.jpg')
        self.assertContains(response, 'zxc.css')
        self.assertContains(response, 'Дуэли один на один в Dota 2.')
        self.assertContains(response, 'Набор ещё не открыт')
        self.assertNotContains(response, 'Подать заявку')
        self.assertNotContains(self.client.get(reverse('tournament')), 'zxc-lilies.jpg')

    def test_registration_uses_art_not_marketing_columns(self):
        response = self.client.get(reverse('register'))
        self.assertNotContains(response, 'registration-aside')
        self.assertNotContains(response, 'ТВОЙ ВЫХОД')
        self.assertNotContains(response, 'КАК ЭТО РАБОТАЕТ')
        self.assertContains(response, 'csrfmiddlewaretoken')

    def test_four_organizers_include_kirill(self):
        response = self.client.get(reverse('tournament'))
        self.assertContains(response, 'assets/kirill.png')
        self.assertContains(response, '<figcaption><strong>', count=4)
        self.assertContains(response, '<strong>Кирилл</strong><span>Соорганизатор</span>')
        self.assertContains(response, '<a href="https://discord.gg/qtRGBJMWg8" target="_blank" rel="noopener noreferrer">Discord FRI ↗</a>', html=True)

    def test_sponsors_orbit_uses_crm_content_and_apple(self):
        from .models import Sponsor
        Sponsor.objects.create(name='Тестовый партнёр', presentation='partner', url='https://example.com')
        response = self.client.get(reverse('tournament'))
        self.assertContains(response, 'data-sponsor-orbit')
        self.assertContains(response, 'assets/sponsor-apple.png')
        self.assertContains(response, 'sponsor-tier-partner')
        self.assertContains(response, 'Тестовый партнёр')
        self.assertNotContains(response, 'DUMBO')

    def test_public_routes_forms_contacts_and_encoding(self):
        for name in ('home', 'tournament', 'zxc', 'login', 'register'):
            response = self.client.get(reverse(name))
            self.assertEqual(response.status_code, 200, name)
            self.assertContains(response, 'https://t.me/firstrussianinternational')
            self.assertNotContains(response, '????')

    def test_home_choices_and_empty_tournament(self):
        response = self.client.get(reverse('home'))
        self.assertContains(response, 'Командный турнир')
        self.assertContains(response, 'ZXC 1 vs 1')
        response = self.client.get(reverse('tournament'))
        for old_claim in ('$20 000+', 'зимбабвийских', 'конец декабря'):
            self.assertNotContains(response, old_claim)
        self.assertContains(response, 'Приём заявок ещё не открыт')
        self.assertContains(response, 'Создание профиля не считается заявкой.')
        self.assertNotContains(response, 'id="prize-title"')
        self.assertNotContains(response, 'id="sponsors"')
        self.assertNotContains(response, 'Прогнозы за внутренние баллы')
        self.assertContains(response, '<details class="stream-preview">')
        self.assertNotContains(response, 'DUMBO')
        self.assertNotContains(response, 'travis-scott-dumbo.mp3')
        self.assertNotContains(response, 'id="soundtrack"')
        self.assertNotContains(response, 'runaway-mute')
        self.assertContains(response, '/static/django-content.js')
        self.assertNotContains(response, 'src="content.js"')

    def test_admin_edits_are_escaped_and_channel_label_follows_settings(self):
        TournamentSettings.objects.create(prize='Приз согласован', group_format='<script>alert(1)</script>', twitch_channel='another_channel')
        response = self.client.get(reverse('tournament'))
        self.assertContains(response, 'Приз согласован')
        self.assertContains(response, 'Смотреть another_channel на Twitch')
        self.assertContains(response, '&lt;script&gt;')
        self.assertNotContains(response, '<script>alert(1)</script>')
