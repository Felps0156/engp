'''Transactional task state services.'''

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
