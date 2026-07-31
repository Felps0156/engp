'''Reusable class-based-view mixins.'''

from django.contrib.auth.mixins import AccessMixin
from django.core.exceptions import PermissionDenied

from base.managers import current_tenant


class TenantQuerysetMixin:
    '''Scope a class-based view queryset to the active workspace.'''

    def get_queryset(self):
        queryset = super().get_queryset()
        request = getattr(self, 'request', None)
        tenant = getattr(request, 'tenant', None) or current_tenant.get()
        if tenant is None:
            return queryset.none()
        return queryset.for_tenant(tenant)


class RoleRequiredMixin(AccessMixin):
    '''Require an active membership and, optionally, one of its roles.'''

    allowed_roles = ()

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()

        tenant = getattr(request, 'tenant', None)
        if tenant is None:
            raise PermissionDenied('Usuário sem membership ativa.')

        membership = getattr(request, 'membership', None)
        if (
            membership is None
            or membership.workspace_id != tenant.pk
            or not membership.is_active
        ):
            from tenants.models import WorkspaceMembership

            membership = WorkspaceMembership.objects.filter(
                workspace=tenant,
                user=request.user,
                is_active=True,
            ).first()

        if membership is None:
            raise PermissionDenied('Usuário sem membership ativa.')

        if self.allowed_roles:
            allowed_roles = self.allowed_roles
            if isinstance(allowed_roles, str):
                allowed_roles = (allowed_roles,)
            if membership.role not in allowed_roles:
                raise PermissionDenied('Papel não autorizado.')

        request.membership = membership
        return super().dispatch(request, *args, **kwargs)


class PerPageMixin:
    '''Allow a bounded page size through the ``per_page`` query parameter.'''

    per_page_default = 10
    per_page_choices = (10, 20, 50, 100, 200)
    per_page_query_params = ()

    def get_paginate_by(self, queryset):
        per_page = self.request.GET.get('per_page')
        if per_page and per_page.isdigit():
            value = int(per_page)
            if value in self.per_page_choices:
                return value
        return getattr(self, 'paginate_by', None) or self.per_page_default

    def get_pagination_params(self):
        return {
            key: value
            for key in self.per_page_query_params
            if (value := self.request.GET.get(key))
        }

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['per_page_choices'] = self.per_page_choices
        context['current_per_page'] = self.get_paginate_by(None)
        context['pagination_params'] = self.get_pagination_params()
        return context
