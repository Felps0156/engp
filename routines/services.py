'''Transactional services for routine state and occurrence generation.'''

from datetime import date, timedelta

from django.db import IntegrityError, transaction
from django.db.models import Q
from django.utils import timezone

from .models import (
    RoutineOccurrence,
    WeeklyRoutineItem,
)


def _locked_routine_item(*, item, workspace):
    '''Return a routine item only when it belongs to the supplied workspace.'''

    if workspace is None:
        raise ValueError('O workspace é obrigatório.')

    item_id = getattr(item, 'pk', item)
    if not item_id:
        raise WeeklyRoutineItem.DoesNotExist

    return WeeklyRoutineItem.objects.for_tenant(workspace).select_for_update().get(
        pk=item_id,
    )


@transaction.atomic
def pause_routine_item(*, item, workspace):
    '''Pause a routine item without touching already generated history.'''

    locked_item = _locked_routine_item(item=item, workspace=workspace)
    if locked_item.is_active:
        locked_item.is_active = False
        locked_item.save(update_fields=('is_active', 'updated_at'))
    return locked_item


@transaction.atomic
def resume_routine_item(*, item, workspace):
    '''Reactivate a routine item without duplicating existing occurrences.'''

    locked_item = _locked_routine_item(item=item, workspace=workspace)
    if not locked_item.is_active and locked_item.deleted_at is None:
        locked_item.is_active = True
        locked_item.save(update_fields=('is_active', 'updated_at'))
    return locked_item


@transaction.atomic
def delete_routine_item(*, item, workspace):
    '''Archive an item while preserving materialized history.'''

    locked_item = _locked_routine_item(item=item, workspace=workspace)
    if locked_item.deleted_at is None:
        locked_item.is_active = False
        locked_item.deleted_at = timezone.now()
        locked_item.save(
            update_fields=('is_active', 'deleted_at', 'updated_at'),
        )
    return locked_item


def _coerce_date(value, field_name):
    if isinstance(value, date):
        return value
    if isinstance(value, str):
        try:
            return date.fromisoformat(value)
        except ValueError as exc:
            raise ValueError(f'{field_name} deve estar no formato AAAA-MM-DD.') from exc
    raise ValueError(f'{field_name} deve ser uma data válida.')


def _occurrence_defaults(item):
    category = item.category
    return {
        'workspace': item.workspace,
        'scheduled_time_snapshot': item.scheduled_time,
        'title_snapshot': item.title,
        'category_snapshot': category.name if category else '',
        'category_color_token_snapshot': category.color_token if category else '',
        'estimated_minutes_snapshot': item.estimated_minutes,
        'priority_snapshot': item.priority,
        'status': RoutineOccurrence.Status.PENDING,
    }


@transaction.atomic
def generate_routine_occurrences(*, start_date, end_date, workspace=None):
    '''Materialize valid routine dates idempotently and preserve snapshots.'''

    start_date = _coerce_date(start_date, 'A data inicial')
    end_date = _coerce_date(end_date, 'A data final')
    if end_date < start_date:
        raise ValueError('A data final não pode ser anterior à data inicial.')

    items = WeeklyRoutineItem.objects.select_related('category', 'workspace').filter(
        workspace__is_active=True,
        is_active=True,
        deleted_at__isnull=True,
        starts_on__lte=end_date,
    ).filter(
        Q(ends_on__isnull=True) | Q(ends_on__gte=start_date),
    )
    if workspace is not None:
        items = items.filter(workspace=workspace)

    created_count = 0
    for item in items.order_by('workspace_id', 'pk'):
        current_date = max(start_date, item.starts_on)
        last_date = end_date
        if item.ends_on is not None:
            last_date = min(last_date, item.ends_on)

        defaults = _occurrence_defaults(item)
        while current_date <= last_date:
            try:
                with transaction.atomic():
                    _occurrence, created = (
                        RoutineOccurrence.objects.for_tenant(
                            item.workspace,
                        ).get_or_create(
                            routine_item=item,
                            occurrence_date=current_date,
                            defaults=defaults,
                        )
                    )
            except IntegrityError:
                created = False
            if created:
                created_count += 1
            current_date += timedelta(days=1)

    return created_count


@transaction.atomic
def toggle_routine_occurrence(*, item, workspace, occurrence_date):
    '''Toggle a dated occurrence, materializing a valid missing record if needed.'''

    occurrence_date = _coerce_date(occurrence_date, 'A data da ocorrência')
    locked_item = _locked_routine_item(item=item, workspace=workspace)
    if locked_item.deleted_at is not None:
        raise ValueError('Um hábito excluído não pode ser alterado.')
    if occurrence_date < locked_item.starts_on:
        raise ValueError('Este hábito ainda não existia na data informada.')
    if locked_item.ends_on and occurrence_date > locked_item.ends_on:
        raise ValueError('Este hábito não estava mais ativo na data informada.')
    occurrence = (
        RoutineOccurrence.objects.for_tenant(workspace)
        .select_for_update()
        .filter(routine_item=locked_item, occurrence_date=occurrence_date)
        .first()
    )
    if occurrence is None:
        is_valid_date = locked_item.is_active
        if not is_valid_date:
            raise ValueError('Esta rotina não estava agendada para a data informada.')
        occurrence = RoutineOccurrence.objects.create(
            routine_item=locked_item,
            occurrence_date=occurrence_date,
            **_occurrence_defaults(locked_item),
        )

    if occurrence.status == RoutineOccurrence.Status.COMPLETED:
        occurrence.status = RoutineOccurrence.Status.PENDING
        occurrence.completed_at = None
    else:
        occurrence.status = RoutineOccurrence.Status.COMPLETED
        occurrence.completed_at = timezone.now()
    occurrence.skipped_at = None
    occurrence.save(
        update_fields=('status', 'completed_at', 'skipped_at', 'updated_at'),
    )
    return occurrence
