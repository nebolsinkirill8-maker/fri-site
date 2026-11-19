from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.test import TestCase
from django.urls import reverse

from .models import PrizeContribution, Sponsor, TournamentSettings

User = get_user_model()


class PrizeFundTests(TestCase):
    def tournament(self):
        return self.client.get(reverse('tournament'))

    def test_fund_is_hidden_when_empty(self):
        response = self.tournament()
        self.assertNotContains(response, 'id="prize-title"')
        self.assertNotContains(response, 'зимбабвийских')

    def test_total_is_base_plus_all_contributions_and_follows_changes(self):
        TournamentSettings.objects.create(prize_base=5000)
        alpha = Sponsor.objects.create(name='Альфа')
        beta = Sponsor.objects.create(name='Бета')
        pledged = PrizeContribution.objects.create(sponsor=alpha, amount=10000, status='pledged')
        PrizeContribution.objects.create(sponsor=beta, amount=2500, status='received')
        response = self.tournament()
        self.assertEqual(response.context['fri_content']['prize'], '$17 500')
        self.assertContains(response, '<p id="prize-value">$17 500</p>', html=True)
        self.assertContains(response, 'в зимбабвийских долларах')

        pledged.amount = 4000
        pledged.save()
        self.assertEqual(self.tournament().context['fri_content']['prize'], '$11 500')

        beta.delete()
        self.assertEqual(self.tournament().context['fri_content']['prize'], '$9 000')

    def test_individual_contributions_are_not_public(self):
        sponsor = Sponsor.objects.create(name='Секретный спонсор', gallery_slot=1)
        PrizeContribution.objects.create(sponsor=sponsor, amount=777, note='договор №5')
        response = self.tournament()
        self.assertContains(response, '$777')
        self.assertNotContains(response, 'договор №5')
        self.assertNotIn('amount', str(response.context['fri_content']['sponsors']))
        self.assertNotContains(response, 'Обещан')

    def test_manual_text_is_fallback_then_caption(self):
        settings = TournamentSettings.objects.create(prize='и мерч от партнёров')
        response = self.tournament()
        self.assertContains(response, '<p id="prize-value">и мерч от партнёров</p>', html=True)
        self.assertNotContains(response, 'зимбабвийских')
        settings.prize_base = 1000
        settings.save()
        response = self.tournament()
        self.assertContains(response, '<p id="prize-value">$1 000</p>', html=True)
        self.assertContains(response, '<p class="prize-caption">и мерч от партнёров</p>', html=True)

    def test_staff_manage_contributions_inside_sponsor_card(self):
        staff = User.objects.create_user('staff@example.com', 'Long-Safe-Password-471!', is_staff=True)
        staff.groups.add(Group.objects.get(name='Сотрудники'))
        sponsor = Sponsor.objects.create(name='Альфа')
        self.client.force_login(staff)
        url = reverse('admin:portal_sponsor_change', args=[sponsor.pk])
        self.assertContains(self.client.get(url), 'Взносы в призовой фонд')
        response = self.client.post(url, {
            'name': 'Альфа', 'description': '', 'logo_url': '', 'url': '', 'presentation': 'standard', 'gallery_slot': '',
            'prize_contributions-TOTAL_FORMS': '1', 'prize_contributions-INITIAL_FORMS': '0',
            'prize_contributions-0-amount': '3000', 'prize_contributions-0-status': 'received', 'prize_contributions-0-note': '',
            '_save': '1',
        })
        self.assertEqual(response.status_code, 302)
        self.assertEqual(self.tournament().context['fri_content']['prize'], '$3 000')
        self.assertContains(self.client.get(reverse('admin:portal_sponsor_changelist')), '3000')

    def test_negative_amount_is_rejected(self):
        admin_user = User.objects.create_superuser('boss@example.com', 'Long-Safe-Password-471!')
        sponsor = Sponsor.objects.create(name='Альфа')
        self.client.force_login(admin_user)
        response = self.client.post(reverse('admin:portal_sponsor_change', args=[sponsor.pk]), {
            'name': 'Альфа', 'presentation': 'standard',
            'prize_contributions-TOTAL_FORMS': '1', 'prize_contributions-INITIAL_FORMS': '0',
            'prize_contributions-0-amount': '-500', 'prize_contributions-0-status': 'pledged',
            '_save': '1',
        })
        self.assertEqual(response.status_code, 200)
        self.assertFalse(PrizeContribution.objects.exists())
