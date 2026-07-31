'''Querysets, managers and request-scoped tenant context.'''

from contextvars import ContextVar

from django.db import models


current_tenant: ContextVar[object | None] = ContextVar(
    'current_tenant',
    default=None,
)


class TenantQuerySet(models.QuerySet):
    '''Query helpers for records that belong to a workspace.'''

    def for_tenant(self, workspace):
        '''Return only records belonging to the supplied workspace.'''

        workspace_id = getattr(workspace, 'pk', workspace)
        if not workspace_id:
            return self.none()
        return self.filter(workspace_id=workspace_id)


class TenantManager(models.Manager.from_queryset(TenantQuerySet)):
    '''Manager exposing the explicit workspace scoping API.'''

    def for_tenant(self, workspace):
        return self.get_queryset().for_tenant(workspace)
