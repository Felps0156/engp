'''Transactional account creation services.'''

from uuid import uuid4

from django.db import transaction
from django.utils.text import slugify

from tenants.models import Workspace, WorkspaceMembership

from .models import User, UserSettings


@transaction.atomic
def create_account(*, email, password, first_name='', last_name=''):
    '''Create a user and its personal owner workspace atomically.'''

    user = User.objects.create_user(
        email=email,
        password=password,
        first_name=first_name,
        last_name=last_name,
    )
    display_name = user.get_short_name() or 'pessoal'
    workspace_name = f'Workspace de {display_name}'[:120]
    workspace_slug = slugify(workspace_name) or 'workspace-pessoal'
    workspace_slug = f'{workspace_slug[:108]}-{uuid4().hex[:10]}'
    workspace = Workspace.objects.create(
        name=workspace_name,
        slug=workspace_slug,
    )
    WorkspaceMembership.objects.create(
        workspace=workspace,
        user=user,
        role=WorkspaceMembership.Role.OWNER,
    )
    UserSettings.objects.create(user=user)
    return user, workspace


def get_or_create_user_settings(*, user):
    '''Return account settings, creating them for legacy users when needed.'''

    settings_obj, _created = UserSettings.objects.get_or_create(user=user)
    return settings_obj
