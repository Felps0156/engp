'''Transactional task state services.'''

from datetime import timedelta

from django.db import transaction
from django.utils import timezone

from .models import Task


def _locked_task(*, task, workspace):
    '''Return the task only when it belongs to the supplied workspace.'''

    if workspace is None:
        raise ValueError('O workspace é obrigatório.')

    task_id = getattr(task, 'pk', task)
    if not task_id:
        raise Task.DoesNotExist

    return Task.objects.for_tenant(workspace).select_for_update().get(pk=task_id)


@transaction.atomic
def complete_task(*, task, workspace):
    '''Complete a task once and preserve the first completion timestamp.'''

    locked_task = _locked_task(task=task, workspace=workspace)
    if locked_task.status == Task.Status.COMPLETED:
        return locked_task

    locked_task.status = Task.Status.COMPLETED
    locked_task.completed_at = timezone.now()
    locked_task.save(update_fields=('status', 'completed_at', 'updated_at'))
    return locked_task


@transaction.atomic
def reopen_task(*, task, workspace):
    '''Reopen a task once and clear its completion timestamp.'''

    locked_task = _locked_task(task=task, workspace=workspace)
    if locked_task.status == Task.Status.PENDING and locked_task.completed_at is None:
        return locked_task

    locked_task.status = Task.Status.PENDING
    locked_task.completed_at = None
    locked_task.save(update_fields=('status', 'completed_at', 'updated_at'))
    return locked_task


@transaction.atomic
def move_task(*, task, workspace, due_date):
    '''Move a task to a planned date without bypassing tenant locking.'''

    locked_task = _locked_task(task=task, workspace=workspace)
    locked_task.due_date = due_date
    locked_task.save(update_fields=('due_date', 'updated_at'))
    return locked_task


@transaction.atomic
def move_task_to_column(*, task, workspace, column, before_task_id=None):
    '''Move and position a task inside one of the planning board columns.'''

    today = timezone.localdate()
    column_dates = {
        'inbox': None,
        'week': today + timedelta(days=1),
        'today': today,
    }
    valid_columns = {*column_dates, 'completed'}
    if column not in valid_columns:
        raise ValueError('A coluna informada é inválida.')

    locked_task = _locked_task(task=task, workspace=workspace)
    target_queryset = Task.objects.for_tenant(workspace).select_for_update()

    if column == 'completed':
        target_queryset = target_queryset.filter(status=Task.Status.COMPLETED)
    else:
        target_queryset = target_queryset.filter(status=Task.Status.PENDING)
        if column == 'inbox':
            target_queryset = target_queryset.filter(due_date__isnull=True)
        elif column == 'week':
            target_queryset = target_queryset.filter(
                due_date__range=(today + timedelta(days=1), today + timedelta(days=6)),
            )
        else:
            target_queryset = target_queryset.filter(due_date__lte=today)

    target_tasks = list(
        target_queryset.exclude(pk=locked_task.pk).order_by(
            'board_order',
            'created_at',
            'pk',
        ),
    )
    before_index = len(target_tasks)
    if before_task_id:
        for index, target_task in enumerate(target_tasks):
            if target_task.pk == before_task_id:
                before_index = index
                break
    target_tasks.insert(before_index, locked_task)

    if column == 'completed':
        locked_task.status = Task.Status.COMPLETED
        if locked_task.completed_at is None:
            locked_task.completed_at = timezone.now()
    else:
        locked_task.status = Task.Status.PENDING
        locked_task.completed_at = None
        locked_task.due_date = column_dates[column]

    original_orders = {
        target_task.pk: target_task.board_order
        for target_task in target_tasks
    }
    for index, target_task in enumerate(target_tasks):
        target_task.board_order = index
        if target_task.pk == locked_task.pk:
            target_task.save(
                update_fields=(
                    'status',
                    'completed_at',
                    'due_date',
                    'board_order',
                    'updated_at',
                ),
            )
        elif target_task.board_order != original_orders[target_task.pk]:
            target_task.save(update_fields=('board_order', 'updated_at'))

    return locked_task
