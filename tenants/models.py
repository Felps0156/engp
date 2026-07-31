'''Workspace and membership models.'''

from django.conf import settings
from django.db import models

from base.models import BaseModel, TenantAwareModel


class Workspace(BaseModel):
    '''A personal or shared product workspace.'''

    name = models.CharField('nome', max_length=120)
    slug = models.SlugField('slug', max_length=120, unique=True)
    is_active = models.BooleanField('ativo', default=True)

    class Meta:
        ordering = ('name',)
        verbose_name = 'workspace'
        verbose_name_plural = 'workspaces'

    def __str__(self):
        return self.name


class WorkspaceMembership(TenantAwareModel):
    '''User membership and role inside a workspace.'''

    class Role(models.TextChoices):
        OWNER = 'owner', 'Owner'
        MEMBER = 'member', 'Member'

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='workspace_memberships',
        verbose_name='usuário',
    )
    role = models.CharField(
        'papel',
        max_length=10,
        choices=Role.choices,
        default=Role.MEMBER,
    )
    is_active = models.BooleanField('ativa', default=True)

    class Meta:
        ordering = ('workspace_id', 'user_id')
        verbose_name = 'membership de workspace'
        verbose_name_plural = 'memberships de workspace'
        constraints = [
            models.UniqueConstraint(
                fields=['workspace', 'user'],
                name='unique_workspace_membership_user',
            ),
            models.CheckConstraint(
                condition=models.Q(role__in=['owner', 'member']),
                name='workspace_membership_valid_role',
            ),
        ]
        indexes = [
            models.Index(
                fields=['workspace', 'user', 'is_active'],
                name='workspace_member_scope_idx',
            ),
            models.Index(
                fields=['user', 'is_active'],
                name='workspace_member_user_idx',
            ),
        ]

    def __str__(self):
        return f'{self.workspace} / {self.user}'
