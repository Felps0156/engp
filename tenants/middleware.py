'''Resolve and clean up the active workspace for each request.'''

from base.managers import current_tenant

from .models import WorkspaceMembership


ACTIVE_WORKSPACE_SESSION_KEY = 'active_workspace_id'


class TenantMiddleware:
    '''Attach an active workspace and membership to authenticated requests.'''

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        tenant = None
        membership = None
        user = getattr(request, 'user', None)

        if user is not None and user.is_authenticated:
            memberships = WorkspaceMembership.objects.select_related(
                'workspace',
            ).filter(
                user=user,
                is_active=True,
                workspace__is_active=True,
            )
            active_workspace_id = getattr(
                request,
                'session',
                {},
            ).get(ACTIVE_WORKSPACE_SESSION_KEY)
            if active_workspace_id:
                membership = memberships.filter(
                    workspace_id=active_workspace_id,
                ).first()
            if membership is None:
                membership = memberships.order_by(
                    'workspace_id',
                    'pk',
                ).first()
            if membership is not None:
                tenant = membership.workspace

        request.tenant = tenant
        request.membership = membership
        token = current_tenant.set(tenant)
        try:
            return self.get_response(request)
        finally:
            current_tenant.reset(token)
