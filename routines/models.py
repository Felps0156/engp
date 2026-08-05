'''Workspace-scoped weekly routines and their materialized occurrences.'''

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import F, Q
from django.utils import timezone

from base.models import TenantAwareModel


WEEKDAY_CHOICES = (
    (0, 'Segunda-feira'),
    (1, 'Terça-feira'),
    (2, 'Quarta-feira'),
    (3, 'Quinta-feira'),
    (4, 'Sexta-feira'),
    (5, 'Sábado'),
    (6, 'Domingo'),
)
VALID_WEEKDAYS = frozenset(value for value, _label in WEEKDAY_CHOICES)
VALID_WEEKDAY_STRINGS = frozenset(str(value) for value in VALID_WEEKDAYS)


def normalize_weekdays(value):
    '''Return a sorted list of unique weekday integers from 0 to 6.'''

    if value is None:
        return []
    if isinstance(value, str):
        value = [value]

    try:
        raw_weekdays = list(value)
    except TypeError as exc:
        raise ValueError('Informe os dias da semana em uma lista.') from exc

    weekdays = []
    for raw_weekday in raw_weekdays:
        if isinstance(raw_weekday, bool):
            raise ValueError('Os dias da semana informados são inválidos.')
        if isinstance(raw_weekday, int):
            weekday = raw_weekday
        elif (
            isinstance(raw_weekday, str)
            and raw_weekday.strip() in VALID_WEEKDAY_STRINGS
        ):
            weekday = int(raw_weekday)
        else:
            raise ValueError('Os dias da semana informados são inválidos.')
        if weekday not in VALID_WEEKDAYS:
            raise ValueError('Escolha somente dias entre segunda e domingo.')
        if weekday in weekdays:
            raise ValueError('Não repita dias na mesma rotina.')
        weekdays.append(weekday)

    return sorted(weekdays)


class WeeklyRoutineItem(TenantAwareModel):
    '''A recurring item that can materialize one occurrence per selected day.'''

    class Priority(models.TextChoices):
        LOW = 'low', 'Baixa'
        MEDIUM = 'medium', 'Média'
        HIGH = 'high', 'Alta'

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='routine_items',
        verbose_name='criada por',
    )
    title = models.CharField('título', max_length=180)
    category = models.ForeignKey(
        'categories.Category',
        on_delete=models.SET_NULL,
        related_name='routine_items',
        blank=True,
        null=True,
        verbose_name='categoria',
    )
    weekdays = models.JSONField('dias da semana', default=list)
    scheduled_time = models.TimeField(
        'horário planejado',
        blank=True,
        null=True,
    )
    estimated_minutes = models.PositiveSmallIntegerField(
        'estimativa em minutos',
        blank=True,
        null=True,
        validators=[MinValueValidator(1)],
    )
    priority = models.CharField(
        'prioridade',
        max_length=6,
        choices=Priority.choices,
        default=Priority.MEDIUM,
    )
    is_active = models.BooleanField('ativa', default=True)
    deleted_at = models.DateTimeField(
        'excluída em',
        blank=True,
        null=True,
        db_index=True,
    )
    starts_on = models.DateField(
        'início',
        default=timezone.localdate,
    )
    ends_on = models.DateField(
        'fim',
        blank=True,
        null=True,
    )

    class Meta:
        ordering = ('is_active', 'scheduled_time', 'title', 'pk')
        verbose_name = 'item de rotina semanal'
        verbose_name_plural = 'itens de rotina semanal'
        constraints = [
            models.CheckConstraint(
                condition=Q(priority__in=('low', 'medium', 'high')),
                name='routine_item_valid_priority',
            ),
            models.CheckConstraint(
                condition=Q(estimated_minutes__isnull=True)
                | Q(estimated_minutes__gte=1),
                name='routine_item_positive_est',
            ),
            models.CheckConstraint(
                condition=(
                    Q(ends_on__isnull=True) | Q(ends_on__gte=F('starts_on'))
                ),
                name='routine_item_valid_dates',
            ),
        ]
        indexes = [
            models.Index(
                fields=('workspace', 'is_active', 'starts_on'),
                name='routine_item_scope_active_idx',
            ),
            models.Index(
                fields=('workspace', 'starts_on', 'ends_on'),
                name='routine_item_scope_dates_idx',
            ),
        ]

    def clean(self):
        super().clean()
        self.title = (self.title or '').strip()

        errors = {}
        if not self.title:
            errors['title'] = 'Informe um título para a rotina.'

        try:
            self.weekdays = normalize_weekdays(self.weekdays)
        except ValueError as exc:
            errors['weekdays'] = str(exc)
        if not self.weekdays and 'weekdays' not in errors:
            errors['weekdays'] = 'Escolha ao menos um dia para a rotina.'

        if self.ends_on and self.starts_on and self.ends_on < self.starts_on:
            errors['ends_on'] = 'A data final deve ser igual ou posterior ao início.'

        if self.category_id and self.workspace_id:
            category_workspace_id = getattr(self.category, 'workspace_id', None)
            if category_workspace_id is None:
                category_model = self._meta.get_field(
                    'category',
                ).remote_field.model
                category_workspace_id = category_model.objects.filter(
                    pk=self.category_id,
                ).values_list('workspace_id', flat=True).first()
            if category_workspace_id != self.workspace_id:
                errors['category'] = 'A categoria deve pertencer ao mesmo workspace.'

        if self.created_by_id and self.workspace_id:
            from tenants.models import WorkspaceMembership

            if not WorkspaceMembership.objects.filter(
                workspace_id=self.workspace_id,
                user_id=self.created_by_id,
                is_active=True,
            ).exists():
                errors['created_by'] = (
                    'A pessoa criadora deve pertencer ao mesmo workspace.'
                )

        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        self.title = (self.title or '').strip()
        return super().save(*args, **kwargs)

    def __str__(self):
        return self.title


class RoutineOccurrence(TenantAwareModel):
    '''A dated routine snapshot that preserves the values used at generation.'''

    class Status(models.TextChoices):
        PENDING = 'pending', 'Pendente'
        COMPLETED = 'completed', 'Concluída'
        SKIPPED = 'skipped', 'Pulada'

    routine_item = models.ForeignKey(
        WeeklyRoutineItem,
        on_delete=models.PROTECT,
        related_name='occurrences',
        verbose_name='item de rotina',
    )
    occurrence_date = models.DateField('data da ocorrência')
    scheduled_time_snapshot = models.TimeField(
        'horário preservado',
        blank=True,
        null=True,
    )
    title_snapshot = models.CharField('título preservado', max_length=180)
    category_snapshot = models.CharField(
        'categoria preservada',
        max_length=80,
        blank=True,
        default='',
    )
    category_color_token_snapshot = models.CharField(
        'cor da categoria preservada',
        max_length=32,
        blank=True,
        default='',
    )
    estimated_minutes_snapshot = models.PositiveSmallIntegerField(
        'estimativa preservada em minutos',
        blank=True,
        null=True,
        validators=[MinValueValidator(1)],
    )
    priority_snapshot = models.CharField(
        'prioridade preservada',
        max_length=6,
        choices=WeeklyRoutineItem.Priority.choices,
    )
    status = models.CharField(
        'status',
        max_length=9,
        choices=Status.choices,
        default=Status.PENDING,
    )
    completed_at = models.DateTimeField(
        'concluída em',
        blank=True,
        null=True,
    )
    skipped_at = models.DateTimeField(
        'pulada em',
        blank=True,
        null=True,
    )

    class Meta:
        ordering = ('occurrence_date', 'scheduled_time_snapshot', 'pk')
        verbose_name = 'ocorrência de rotina'
        verbose_name_plural = 'ocorrências de rotina'
        constraints = [
            models.UniqueConstraint(
                fields=('routine_item', 'occurrence_date'),
                name='unique_routine_item_date',
            ),
            models.CheckConstraint(
                condition=Q(status__in=('pending', 'completed', 'skipped')),
                name='routine_occ_valid_status',
            ),
            models.CheckConstraint(
                condition=Q(priority_snapshot__in=('low', 'medium', 'high')),
                name='routine_occ_valid_priority',
            ),
            models.CheckConstraint(
                condition=Q(estimated_minutes_snapshot__isnull=True)
                | Q(estimated_minutes_snapshot__gte=1),
                name='routine_occ_positive_est',
            ),
        ]
        indexes = [
            models.Index(
                fields=('workspace', 'occurrence_date', 'status'),
                name='routine_occ_scope_status_idx',
            ),
        ]

    def clean(self):
        super().clean()
        self.title_snapshot = (self.title_snapshot or '').strip()
        errors = {}

        if not self.title_snapshot:
            errors['title_snapshot'] = 'A ocorrência precisa de um título preservado.'

        if self.routine_item_id and self.workspace_id:
            item_workspace_id = getattr(self.routine_item, 'workspace_id', None)
            if item_workspace_id is None:
                item_workspace_id = WeeklyRoutineItem.objects.filter(
                    pk=self.routine_item_id,
                ).values_list('workspace_id', flat=True).first()
            if item_workspace_id != self.workspace_id:
                errors['routine_item'] = (
                    'O item de rotina deve pertencer ao mesmo workspace.'
                )

        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        self.title_snapshot = (self.title_snapshot or '').strip()
        return super().save(*args, **kwargs)

    def __str__(self):
        return f'{self.title_snapshot} / {self.occurrence_date:%d/%m/%Y}'
