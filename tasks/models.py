'''Workspace-scoped task model.'''

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models

from base.models import TenantAwareModel


class Task(TenantAwareModel):
    '''An actionable item owned by a workspace and created by a user.'''

    class Status(models.TextChoices):
        PENDING = 'pending', 'Pendente'
        COMPLETED = 'completed', 'Concluída'

    class Priority(models.TextChoices):
        LOW = 'low', 'Baixa'
        MEDIUM = 'medium', 'Média'
        HIGH = 'high', 'Alta'

    class Source(models.TextChoices):
        MANUAL = 'manual', 'Manual'
        ONBOARDING = 'onboarding', 'Onboarding'
        AI = 'ai', 'IA'

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='tasks',
        verbose_name='criada por',
    )
    title = models.CharField('título', max_length=180)
    description = models.TextField('descrição', blank=True, default='')
    category = models.ForeignKey(
        'categories.Category',
        on_delete=models.SET_NULL,
        related_name='tasks',
        blank=True,
        null=True,
        verbose_name='categoria',
    )
    priority = models.CharField(
        'prioridade',
        max_length=6,
        choices=Priority.choices,
        default=Priority.MEDIUM,
    )
    due_date = models.DateField(
        'data planejada',
        blank=True,
        null=True,
    )
    completed_at = models.DateTimeField(
        'concluída em',
        blank=True,
        null=True,
    )
    status = models.CharField(
        'status',
        max_length=9,
        choices=Status.choices,
        default=Status.PENDING,
    )
    estimated_minutes = models.PositiveSmallIntegerField(
        'estimativa em minutos',
        blank=True,
        null=True,
        validators=[MinValueValidator(1)],
    )
    board_order = models.PositiveIntegerField(
        'ordem no quadro',
        default=0,
    )
    source = models.CharField(
        'origem',
        max_length=10,
        choices=Source.choices,
        default=Source.MANUAL,
    )

    class Meta:
        ordering = ('-created_at',)
        verbose_name = 'tarefa'
        verbose_name_plural = 'tarefas'
        constraints = [
            models.CheckConstraint(
                condition=models.Q(status__in=('pending', 'completed')),
                name='task_valid_status',
            ),
            models.CheckConstraint(
                condition=models.Q(priority__in=('low', 'medium', 'high')),
                name='task_valid_priority',
            ),
            models.CheckConstraint(
                condition=models.Q(source__in=('manual', 'onboarding', 'ai')),
                name='task_valid_source',
            ),
            models.CheckConstraint(
                condition=models.Q(estimated_minutes__isnull=True)
                | models.Q(estimated_minutes__gte=1),
                name='task_positive_estimate',
            ),
        ]
        indexes = [
            models.Index(
                fields=('workspace', 'status', 'due_date'),
                name='task_workspace_status_due_idx',
            ),
            models.Index(
                fields=('workspace', 'completed_at'),
                name='task_workspace_completed_idx',
            ),
        ]

    def clean(self):
        super().clean()
        self.title = (self.title or '').strip()
        self.description = (self.description or '').strip()

        errors = {}
        if not self.title:
            errors['title'] = 'Informe um título para a tarefa.'

        if self.category_id and self.workspace_id:
            category_workspace_id = getattr(self.category, 'workspace_id', None)
            if category_workspace_id is None:
                category_workspace_id = type(self).category.field.related_model.objects.filter(
                    pk=self.category_id,
                ).values_list('workspace_id', flat=True).first()
            if category_workspace_id != self.workspace_id:
                errors['category'] = 'A categoria deve pertencer ao mesmo workspace.'

        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        self.title = (self.title or '').strip()
        self.description = (self.description or '').strip()
        return super().save(*args, **kwargs)

    def __str__(self):
        return self.title
