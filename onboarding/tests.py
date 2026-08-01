from django.test import TestCase

from accounts.models import UserSettings
from accounts.services import create_account
from categories.models import Category

from .models import OnboardingProgress


class OnboardingFlowTests(TestCase):
    def setUp(self):
        self.user, self.workspace = create_account(
            email='onboarding@example.com',
            password='StrongPassword!123',
            first_name='Pessoa',
        )
        self.client.force_login(self.user)

    def test_progress_is_resumable_and_completion_is_explicit(self):
        response = self.client.get('/onboarding/')
        self.assertRedirects(response, '/onboarding/nome/', fetch_redirect_response=False)

        response = self.client.post(
            '/onboarding/nome/',
            {'first_name': 'Pessoa Atualizada', 'last_name': ''},
        )
        self.assertRedirects(response, '/onboarding/areas/', fetch_redirect_response=False)

        studies = Category.objects.get(workspace=self.workspace, slug='estudos')
        response = self.client.post(
            '/onboarding/areas/',
            {
                'areas': [str(studies.pk)],
                'custom_areas': 'Leitura, leitura',
            },
        )
        self.assertRedirects(response, '/onboarding/foco/', fetch_redirect_response=False)
        self.assertEqual(
            Category.objects.filter(workspace=self.workspace).count(),
            5,
        )

        response = self.client.post(
            '/onboarding/foco/',
            {'default_focus_minutes': '50'},
        )
        self.assertRedirects(
            response,
            '/onboarding/primeira-tarefa/',
            fetch_redirect_response=False,
        )

        response = self.client.post(
            '/onboarding/primeira-tarefa/',
            {'title': 'Fazer a próxima ação', 'description': ''},
        )
        self.assertRedirects(response, '/onboarding/rotina/', fetch_redirect_response=False)

        response = self.client.get('/onboarding/rotina/')
        self.assertEqual(response.status_code, 200)
        progress = OnboardingProgress.objects.get(user=self.user)
        self.assertEqual(progress.current_step, OnboardingProgress.Step.ROUTINE)

        response = self.client.post(
            '/onboarding/rotina/',
            {'title': '', 'weekdays': [], 'scheduled_time': '', 'estimated_minutes': ''},
        )
        self.assertRedirects(response, '/onboarding/concluido/', fetch_redirect_response=False)
        self.assertFalse(UserSettings.objects.get(user=self.user).onboarding_completed)

        response = self.client.post('/onboarding/concluido/')
        self.assertRedirects(response, '/conta/', fetch_redirect_response=False)
        self.assertTrue(UserSettings.objects.get(user=self.user).onboarding_completed)
        self.assertEqual(
            OnboardingProgress.objects.get(user=self.user).current_step,
            OnboardingProgress.Step.COMPLETE,
        )

    def test_future_step_is_blocked_and_skip_finishes_once(self):
        response = self.client.get('/onboarding/rotina/')
        self.assertRedirects(response, '/onboarding/nome/', fetch_redirect_response=False)

        response = self.client.post('/onboarding/pular/')
        self.assertRedirects(response, '/onboarding/concluido/', fetch_redirect_response=False)
        progress = OnboardingProgress.objects.get(user=self.user)
        self.assertTrue(progress.is_skipped)
        self.assertTrue(UserSettings.objects.get(user=self.user).onboarding_completed)

        response = self.client.get('/onboarding/')
        self.assertRedirects(response, '/conta/', fetch_redirect_response=False)
