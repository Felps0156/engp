'''Shared abstract models.'''

from django.db import models

from base.managers import TenantManager


class BaseModel(models.Model):
    '''Base model with timestamps shared by persisted domain models.'''

    created_at = models.DateTimeField('criado em', auto_now_add=True)
    updated_at = models.DateTimeField('atualizado em', auto_now=True)

    class Meta:
        abstract = True
        ordering = ('-created_at',)


class TenantAwareModel(BaseModel):
    '''Abstract model for records isolated by workspace.'''

    workspace = models.ForeignKey(
        'tenants.Workspace',
        on_delete=models.CASCADE,
        db_index=True,
        verbose_name='workspace',
    )

    objects = TenantManager()

    class Meta:
        abstract = True
        indexes = [models.Index(fields=['workspace'])]
