'''Persistence for the user's onboarding progress.'''

from django.conf import settings
from django.db import models

from base.models import BaseModel


class OnboardingProgress(BaseModel):
    '''Store resumable onboarding state independently from user preferences.'''

    class Step(models.TextChoices):
        NAME = 'name', 'Nome'
        AREAS = 'areas', 'Áreas'
        FOCUS = 'focus', 'Foco padrão'
        TASK = 'task', 'Primeira tarefa'
        ROUTINE = 'routine', 'Rotina'
        COMPLETE = 'complete', 'Concluído'

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='onboarding_progress',
        verbose_name='usuário',
    )
    current_step = models.CharField(
        'etapa atual',
        max_length=16,
        choices=Step.choices,
        default=Step.NAME,
    )
    completed_steps = models.JSONField(
        'etapas concluídas',
        default=list,
    )
    data = models.JSONField(
        'dados do onboarding',
        default=dict,
    )
    is_skipped = models.BooleanField('foi pulado', default=False)
    completed_at = models.DateTimeField(
        'concluído em',
        blank=True,
        null=True,
    )
    skipped_at = models.DateTimeField(
        'pulado em',
        blank=True,
        null=True,
    )

    class Meta:
        ordering = ('user_id',)
        verbose_name = 'progresso do onboarding'
        verbose_name_plural = 'progressos do onboarding'

    def __str__(self):
        return f'{self.user} / {self.get_current_step_display()}'
