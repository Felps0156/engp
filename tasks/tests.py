from datetime import date, timedelta

from django.core.exceptions import ValidationError
from django.test import RequestFactory, TestCase
from django.urls import reverse
from django.utils import timezone

from accounts.services import create_account
from categories.models import Category

from .admin import TaskAdmin
from .forms import TaskForm
from .models import Task
from .services import complete_task, move_task_to_column, reopen_task


class TaskTestMixin:
    def create_task(self, **overrides):
        data = {
            'workspace': self.workspace,
            'created_by': self.user,
            'title': 'Organizar a próxima ação',
        }
        data.update(overrides)
        return Task.objects.create(**data)


class TaskModelTests(TaskTestMixin, TestCase):
    def setUp(self):
        self.user, self.workspace = create_account(
            email='tasks@example.com',
            password='StrongPassword!123',
            first_name='Pessoa',
        )
        self.other_user, self.other_workspace = create_account(
            email='other-tasks@example.com',
            password='StrongPassword!123',
            first_name='Outra Pessoa',
        )
        self.category = Category.objects.get(
            workspace=self.workspace,
            slug='estudos',
        )

    def test_task_has_expected_defaults_and_normalizes_text(self):
        task = self.create_task(
            title='  Estudar Django  ',
            description='  Revisar os models.  ',
            category=self.category,
            due_date=date(2026, 8, 3),
            estimated_minutes=25,
        )

        self.assertEqual(task.title, 'Estudar Django')
        self.assertEqual(task.description, 'Revisar os models.')
        self.assertEqual(task.priority, Task.Priority.MEDIUM)
        self.assertEqual(task.status, Task.Status.PENDING)
        self.assertEqual(task.source, Task.Source.MANUAL)
        self.assertIsNone(task.completed_at)

    def test_category_must_belong_to_the_task_workspace(self):
        other_category = Category.objects.get(
            workspace=self.other_workspace,
            slug='estudos',
        )
        task = Task(
            workspace=self.workspace,
            created_by=self.user,
            title='Tarefa inválida',
            category=other_category,
        )

        with self.assertRaises(ValidationError) as raised:
            task.full_clean()

        self.assertIn('category', raised.exception.message_dict)


class TaskFormTests(TaskTestMixin, TestCase):
    def setUp(self):
        self.user, self.workspace = create_account(
            email='task-form@example.com',
            password='StrongPassword!123',
            first_name='Formulário',
        )
        self.other_user, self.other_workspace = create_account(
            email='other-task-form@example.com',
            password='StrongPassword!123',
            first_name='Outro Formulário',
        )

    def test_form_scopes_categories_and_assigns_workspace_on_save(self):
        own_category = Category.objects.get(
            workspace=self.workspace,
            slug='estudos',
        )
        other_category = Category.objects.get(
            workspace=self.other_workspace,
            slug='estudos',
        )
        form = TaskForm(
            data={
                'title': 'Planejar estudos',
                'description': 'Separar o próximo bloco.',
                'category': own_category.pk,
                'priority': Task.Priority.HIGH,
                'due_date': '2026-08-03',
                'estimated_minutes': '45',
            },
            workspace=self.workspace,
        )

        self.assertEqual(
            set(form.fields['category'].queryset),
            set(Category.objects.filter(workspace=self.workspace, is_active=True)),
        )
        self.assertNotIn(other_category, form.fields['category'].queryset)
        self.assertTrue(form.is_valid(), form.errors)
        task = form.save(commit=False)
        task.created_by = self.user
        task.save()

        self.assertEqual(task.workspace_id, self.workspace.pk)
        self.assertEqual(task.category_id, own_category.pk)

    def test_form_rejects_a_blank_title(self):
        form = TaskForm(data={'title': '   '}, workspace=self.workspace)

        self.assertFalse(form.is_valid())
        self.assertIn('title', form.errors)


class TaskServiceTests(TaskTestMixin, TestCase):
    def setUp(self):
        self.user, self.workspace = create_account(
            email='task-service@example.com',
            password='StrongPassword!123',
            first_name='Serviço',
        )
        self.other_user, self.other_workspace = create_account(
            email='other-task-service@example.com',
            password='StrongPassword!123',
            first_name='Outro Serviço',
        )

    def test_completion_is_idempotent_and_reopening_clears_timestamp(self):
        task = self.create_task()

        completed = complete_task(task=task, workspace=self.workspace)
        first_completed_at = completed.completed_at
        repeated = complete_task(task=task, workspace=self.workspace)

        self.assertEqual(completed.status, Task.Status.COMPLETED)
        self.assertIsNotNone(first_completed_at)
        self.assertEqual(repeated.completed_at, first_completed_at)

        reopened = reopen_task(task=task, workspace=self.workspace)
        self.assertEqual(reopened.status, Task.Status.PENDING)
        self.assertIsNone(reopened.completed_at)
        self.assertIsNone(reopen_task(task=task, workspace=self.workspace).completed_at)

    def test_service_cannot_mutate_a_task_from_another_workspace(self):
        task = self.create_task()

        with self.assertRaises(Task.DoesNotExist):
            complete_task(task=task, workspace=self.other_workspace)

        task.refresh_from_db()
        self.assertEqual(task.status, Task.Status.PENDING)

    def test_board_move_updates_column_state_and_order(self):
        first_task = self.create_task(
            title='Primeira tarefa',
            due_date=timezone.localdate(),
        )
        second_task = self.create_task(title='Segunda tarefa')

        move_task_to_column(
            task=second_task,
            workspace=self.workspace,
            column='today',
            before_task_id=first_task.pk,
        )

        second_task.refresh_from_db()
        first_task.refresh_from_db()
        self.assertEqual(second_task.status, Task.Status.PENDING)
        self.assertEqual(second_task.due_date, timezone.localdate())
        self.assertEqual(second_task.board_order, 0)
        self.assertEqual(first_task.board_order, 1)

        move_task_to_column(
            task=second_task,
            workspace=self.workspace,
            column='completed',
        )
        second_task.refresh_from_db()
        self.assertEqual(second_task.status, Task.Status.COMPLETED)
        self.assertIsNotNone(second_task.completed_at)


class TaskBoardViewTests(TaskTestMixin, TestCase):
    def setUp(self):
        self.user, self.workspace = create_account(
            email='task-board@example.com',
            password='StrongPassword!123',
            first_name='Quadro',
        )
        self.client.force_login(self.user)

    def test_board_exposes_four_non_overlapping_columns(self):
        today = timezone.localdate()
        inbox_task = self.create_task(title='Capturar sem data')
        week_task = self.create_task(
            title='Planejar para a semana',
            due_date=today + timedelta(days=2),
        )
        today_task = self.create_task(title='Executar hoje', due_date=today)
        overdue_task = self.create_task(
            title='Resolver atraso',
            due_date=today - timedelta(days=1),
        )
        completed_task = self.create_task(
            title='Tarefa feita',
            status=Task.Status.COMPLETED,
            completed_at=timezone.now(),
        )

        response = self.client.get(reverse('tasks:inbox'))

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['is_board'])
        columns = response.context['task_columns']
        self.assertEqual(
            [column['key'] for column in columns],
            ['inbox', 'week', 'today', 'completed'],
        )

        task_ids_by_column = {
            column['key']: {task.pk for task in column['tasks']}
            for column in columns
        }
        self.assertEqual(task_ids_by_column['inbox'], {inbox_task.pk})
        self.assertEqual(task_ids_by_column['week'], {week_task.pk})
        self.assertEqual(
            task_ids_by_column['today'],
            {today_task.pk, overdue_task.pk},
        )
        self.assertEqual(task_ids_by_column['completed'], {completed_task.pk})

    def test_week_view_keeps_today_only_in_today(self):
        today = timezone.localdate()
        self.create_task(title='Hoje', due_date=today)
        future_task = self.create_task(
            title='Depois de hoje',
            due_date=today + timedelta(days=1),
        )

        response = self.client.get(reverse('tasks:week'))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            [task.pk for task in response.context['page_obj'].object_list],
            [future_task.pk],
        )


class TaskAdminTests(TaskTestMixin, TestCase):
    def setUp(self):
        self.user, self.workspace = create_account(
            email='task-admin@example.com',
            password='StrongPassword!123',
            first_name='Admin',
        )
        self.other_user, self.other_workspace = create_account(
            email='other-task-admin@example.com',
            password='StrongPassword!123',
            first_name='Outro Admin',
        )
        self.user.is_staff = True
        self.user.save(update_fields=('is_staff', 'updated_at'))
        self.create_task()
        Task.objects.create(
            workspace=self.other_workspace,
            created_by=self.other_user,
            title='Não deve aparecer',
        )
        self.request = RequestFactory().get('/admin/tasks/task/')
        self.request.user = self.user

    def test_admin_queryset_is_filtered_by_active_membership(self):
        queryset = TaskAdmin(Task, admin_site=None).get_queryset(self.request)

        self.assertEqual(queryset.count(), 1)
        self.assertEqual(queryset.get().workspace_id, self.workspace.pk)
