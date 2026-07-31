'''Workspace-scoped category model.'''

from django.core.exceptions import ValidationError
from django.db import models
from django.db.models.functions import Lower
from django.utils.text import slugify

from base.models import TenantAwareModel


class Category(TenantAwareModel):
    '''A reusable label for tasks and routine items in a workspace.'''

    class ColorToken(models.TextChoices):
        BRAND = 'brand-600', 'Azul principal'
        CYAN = 'cyan-200', 'Ciano'
        SUCCESS = 'success-600', 'Verde'
        WARNING = 'warning-600', 'Âmbar'
        DANGER = 'danger-600', 'Vermelho'

    name = models.CharField('nome', max_length=80)
    slug = models.SlugField('slug', max_length=80, allow_unicode=True)
    color_token = models.CharField(
        'token de cor',
        max_length=32,
        choices=ColorToken.choices,
        default=ColorToken.BRAND,
    )
    icon_key = models.CharField(
        'ícone',
        max_length=40,
        blank=True,
        default='',
    )
    is_system = models.BooleanField('padrão do sistema', default=False)
    is_active = models.BooleanField('ativa', default=True)

    class Meta:
        ordering = ('name', 'pk')
        verbose_name = 'categoria'
        verbose_name_plural = 'categorias'
        constraints = [
            models.UniqueConstraint(
                fields=('workspace', 'slug'),
                name='unique_workspace_category_slug',
            ),
            models.UniqueConstraint(
                Lower('name'),
                'workspace',
                name='unique_workspace_category_name_ci',
            ),
        ]
        indexes = [
            models.Index(
                fields=('workspace', 'is_active', 'name'),
                name='category_workspace_active_idx',
            ),
        ]

    def clean(self):
        super().clean()
        self.name = (self.name or '').strip()
        if not self.name:
            raise ValidationError({'name': 'Informe um nome para a categoria.'})
        if not slugify(self.name):
            raise ValidationError(
                {'name': 'Use ao menos uma letra ou número no nome.'},
            )
        if self.workspace_id:
            duplicate = type(self).objects.filter(
                workspace_id=self.workspace_id,
                name__iexact=self.name,
            )
            if self.pk:
                duplicate = duplicate.exclude(pk=self.pk)
            if duplicate.exists():
                raise ValidationError(
                    {'name': 'Já existe uma categoria com este nome.'},
                )

    def save(self, *args, **kwargs):
        self.name = (self.name or '').strip()
        self.slug = slugify(self.name)
        return super().save(*args, **kwargs)

    def __str__(self):
        return self.name
