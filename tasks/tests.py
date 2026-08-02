from datetime import date

from django.core.exceptions import ValidationError
from django.test import RequestFactory, TestCase

from accounts.services import create_account
from categories.models import Category

from .admin import TaskAdmin
from .forms import TaskForm
from .models import Task
from .services import complete_task, reopen_task


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
