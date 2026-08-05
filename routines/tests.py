from datetime import date, datetime, timedelta

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from accounts.services import create_account

from .analysis import build_month_analysis, parse_month
from .models import RoutineOccurrence, WeeklyRoutineItem
from .services import (
    delete_routine_item,
    generate_routine_occurrences,
    toggle_routine_occurrence,
)


class RoutineTestMixin:
    def create_item(self, **overrides):
        data = {
            'workspace': self.workspace,
            'created_by': self.user,
            'title': 'Leitura diária',
            'weekdays': list(range(7)),
            'starts_on': date(2026, 8, 1),
        }
        data.update(overrides)
        return WeeklyRoutineItem.objects.create(**data)

    def create_occurrence(self, item, occurrence_date, **overrides):
        data = {
            'workspace': item.workspace,
            'routine_item': item,
            'occurrence_date': occurrence_date,
            'title_snapshot': item.title,
            'priority_snapshot': item.priority,
        }
        data.update(overrides)
        return RoutineOccurrence.objects.create(**data)


class RoutineAnalysisTests(RoutineTestMixin, TestCase):
    def setUp(self):
        self.user, self.workspace = create_account(
            email='routine-analysis@example.com',
            password='StrongPassword!123',
            first_name='Análise',
        )

    def test_analysis_combines_definitions_and_real_occurrences(self):
        item = self.create_item()
        self.create_occurrence(
            item,
            date(2026, 8, 1),
            status=RoutineOccurrence.Status.COMPLETED,
            completed_at=timezone.now(),
        )

        analysis = build_month_analysis(
            items=[item],
            occurrences=RoutineOccurrence.objects.all(),
            month=date(2026, 8, 1),
            today=date(2026, 8, 4),
        )

        self.assertEqual(analysis['metrics']['habit_count'], 1)
        self.assertEqual(analysis['metrics']['average'], 3)
        self.assertEqual(analysis['metrics']['current_streak'], 0)
        self.assertEqual(analysis['metrics']['best_streak'], 1)
        self.assertEqual(analysis['rows'][0]['cells'][0]['status'], 'completed')
        self.assertEqual(analysis['rows'][0]['cells'][1]['status'], 'missing')
        self.assertEqual(analysis['rows'][0]['cells'][4]['status'], 'future')
        self.assertTrue(analysis['rows'][0]['cells'][4]['can_toggle'])
        self.assertEqual(analysis['weekly_summaries'][0]['completed'], 1)
        self.assertEqual(analysis['weekly_summaries'][0]['total'], 7)
        self.assertTrue(analysis['chart_area_path'])
        self.assertEqual([week['label'] for week in analysis['weeks']], [
            'S1',
            'S2',
            'S3',
            'S4',
            'S5',
        ])

    def test_analysis_handles_supported_date_boundaries(self):
        earliest = build_month_analysis(
            items=[],
            occurrences=[],
            month=date(1, 1, 1),
            today=date(1, 1, 1),
        )
        latest = build_month_analysis(
            items=[],
            occurrences=[],
            month=date(9999, 12, 1),
            today=date(9999, 12, 31),
        )

        self.assertEqual(earliest['previous_month'], '0001-01')
        self.assertEqual(latest['next_month'], '9999-12')
        self.assertEqual(
            parse_month('invalid', fallback=date(2026, 8, 4)),
            date(2026, 8, 1),
        )

    def test_radar_uses_real_completion_rates_when_three_habits_exist(self):
        items = [
            self.create_item(title=f'Hábito {index}')
            for index in range(3)
        ]

        analysis = build_month_analysis(
            items=items,
            occurrences=[],
            month=date(2026, 8, 1),
            today=date(2026, 8, 4),
        )

        self.assertIsNotNone(analysis['radar'])
        self.assertEqual(len(analysis['radar']['values']), 3)

    def test_deleted_habit_is_read_only_in_prior_month_and_hidden_after_deletion(self):
        item = self.create_item(
            is_active=False,
            deleted_at=timezone.make_aware(datetime(2026, 9, 5, 12)),
        )

        august = build_month_analysis(
            items=[item],
            occurrences=[],
            month=date(2026, 8, 1),
            today=date(2026, 9, 5),
        )
        september = build_month_analysis(
            items=[item],
            occurrences=[],
            month=date(2026, 9, 1),
            today=date(2026, 9, 5),
        )

        self.assertEqual(august['metrics']['habit_count'], 1)
        self.assertFalse(august['rows'][0]['cells'][0]['can_toggle'])
        self.assertEqual(september['metrics']['habit_count'], 0)


class RoutineOccurrenceServiceTests(RoutineTestMixin, TestCase):
    def setUp(self):
        self.user, self.workspace = create_account(
            email='routine-service@example.com',
            password='StrongPassword!123',
            first_name='Serviço',
        )
        self.other_user, self.other_workspace = create_account(
            email='other-routine-service@example.com',
            password='StrongPassword!123',
            first_name='Outro Serviço',
        )

    def test_toggle_materializes_completion_and_then_reopens_it(self):
        today = timezone.localdate()
        item = self.create_item(
            starts_on=today,
            weekdays=[today.weekday()],
        )

        completed = toggle_routine_occurrence(
            item=item,
            workspace=self.workspace,
            occurrence_date=today,
        )

        self.assertEqual(completed.status, RoutineOccurrence.Status.COMPLETED)
        self.assertIsNotNone(completed.completed_at)
        self.assertEqual(RoutineOccurrence.objects.count(), 1)

        reopened = toggle_routine_occurrence(
            item=item,
            workspace=self.workspace,
            occurrence_date=today,
        )
        self.assertEqual(reopened.status, RoutineOccurrence.Status.PENDING)
        self.assertIsNone(reopened.completed_at)
        self.assertEqual(RoutineOccurrence.objects.count(), 1)

    def test_generation_materializes_every_day(self):
        start = date(2026, 8, 3)
        self.create_item(starts_on=start, weekdays=[start.weekday()])

        created = generate_routine_occurrences(
            start_date=start,
            end_date=start + timedelta(days=2),
            workspace=self.workspace,
        )

        self.assertEqual(created, 3)
        self.assertEqual(RoutineOccurrence.objects.count(), 3)

    def test_toggle_accepts_future_and_rejects_cross_workspace_changes(self):
        today = timezone.localdate()
        item = self.create_item(
            starts_on=today,
            weekdays=list(range(7)),
        )

        future = toggle_routine_occurrence(
            item=item,
            workspace=self.workspace,
            occurrence_date=today + timedelta(days=1),
        )
        self.assertEqual(future.status, RoutineOccurrence.Status.COMPLETED)
        with self.assertRaises(WeeklyRoutineItem.DoesNotExist):
            toggle_routine_occurrence(
                item=item,
                workspace=self.other_workspace,
                occurrence_date=today,
            )

    def test_delete_archives_item_and_preserves_occurrences(self):
        today = timezone.localdate()
        item = self.create_item(starts_on=today.replace(day=1))
        self.create_occurrence(item, today)

        archived = delete_routine_item(item=item, workspace=self.workspace)

        self.assertIsNotNone(archived.deleted_at)
        self.assertFalse(archived.is_active)
        self.assertTrue(WeeklyRoutineItem.objects.filter(pk=item.pk).exists())
        self.assertTrue(RoutineOccurrence.objects.filter(routine_item=item).exists())
        with self.assertRaisesMessage(ValueError, 'excluído'):
            toggle_routine_occurrence(
                item=item,
                workspace=self.workspace,
                occurrence_date=today,
            )

    def test_toggle_rejects_dates_before_habit_start(self):
        starts_on = timezone.localdate().replace(day=1)
        item = self.create_item(starts_on=starts_on)

        with self.assertRaisesMessage(ValueError, 'ainda não existia'):
            toggle_routine_occurrence(
                item=item,
                workspace=self.workspace,
                occurrence_date=starts_on - timedelta(days=1),
            )


class RoutineWeeklyViewTests(RoutineTestMixin, TestCase):
    def setUp(self):
        self.user, self.workspace = create_account(
            email='routine-view@example.com',
            password='StrongPassword!123',
            first_name='Painel',
        )
        self.other_user, self.other_workspace = create_account(
            email='other-routine-view@example.com',
            password='StrongPassword!123',
            first_name='Outro Painel',
        )
        self.client.force_login(self.user)

    def test_weekly_page_exposes_selected_month_analysis(self):
        self.create_item()

        response = self.client.get(reverse('routines:weekly'), {'month': '2026-08'})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['analysis']['month_value'], '2026-08')
        self.assertEqual(response.context['analysis']['metrics']['habit_count'], 1)
        self.assertContains(response, 'Registro diário')
        self.assertContains(response, 'Evolução diária da consistência')
        self.assertContains(response, 'Agosto de 2026')

    def test_toggle_endpoint_persists_completion_and_keeps_month(self):
        today = timezone.localdate()
        item = self.create_item(
            starts_on=today,
            weekdays=[today.weekday()],
        )
        month = today.strftime('%Y-%m')

        response = self.client.post(
            reverse('routines:toggle-occurrence', args=[item.pk]),
            {'date': today.isoformat(), 'month': month},
        )

        self.assertRedirects(
            response,
            f"{reverse('routines:weekly')}?month={month}",
            fetch_redirect_response=False,
        )
        occurrence = RoutineOccurrence.objects.get(routine_item=item)
        self.assertEqual(occurrence.status, RoutineOccurrence.Status.COMPLETED)

    def test_toggle_endpoint_cannot_access_another_workspace_item(self):
        today = timezone.localdate()
        other_item = WeeklyRoutineItem.objects.create(
            workspace=self.other_workspace,
            created_by=self.other_user,
            title='Rotina de outro workspace',
            starts_on=today,
            weekdays=[today.weekday()],
        )

        response = self.client.post(
            reverse('routines:toggle-occurrence', args=[other_item.pk]),
            {'date': today.isoformat()},
        )

        self.assertEqual(response.status_code, 404)
        self.assertFalse(RoutineOccurrence.objects.exists())

    def test_quick_create_adds_a_daily_habit_without_leaving_the_page(self):
        current_month = timezone.localdate().replace(day=1)
        month_value = current_month.strftime('%Y-%m')
        response = self.client.post(
            reverse('routines:weekly'),
            {'title': 'Beber água', 'category': '', 'month': '2020-01'},
        )

        self.assertRedirects(
            response,
            f"{reverse('routines:weekly')}?month={month_value}",
            fetch_redirect_response=False,
        )
        item = WeeklyRoutineItem.objects.get(title='Beber água')
        self.assertEqual(item.weekdays, list(range(7)))
        self.assertEqual(item.starts_on, current_month)

        previous_month = current_month - timedelta(days=1)
        previous_response = self.client.get(
            reverse('routines:weekly'),
            {'month': previous_month.strftime('%Y-%m')},
        )
        self.assertEqual(
            previous_response.context['analysis']['metrics']['habit_count'],
            0,
        )

    def test_invalid_quick_create_reopens_the_dialog_with_errors(self):
        response = self.client.post(
            reverse('routines:weekly'),
            {'title': '   ', 'category': '', 'month': '2026-08'},
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['open_create_dialog'])
        self.assertContains(response, 'data-open="true"')
        self.assertContains(response, 'Informe um título para a rotina.')

    def test_delete_endpoint_requires_ui_confirmation_and_archives_item(self):
        today = timezone.localdate()
        item = self.create_item(starts_on=today.replace(day=1))
        page = self.client.get(
            reverse('routines:weekly'),
            {'month': today.strftime('%Y-%m')},
        )
        self.assertContains(page, 'data-confirm-delete=')

        response = self.client.post(reverse('routines:delete', args=[item.pk]))

        self.assertRedirects(
            response,
            reverse('routines:weekly'),
            fetch_redirect_response=False,
        )
        item.refresh_from_db()
        self.assertIsNotNone(item.deleted_at)
        self.assertFalse(item.is_active)
