from django.contrib import admin

from categories.models import Category
from tenants.models import WorkspaceMembership

from .models import Task


def _visible_workspace_ids(request):
    return WorkspaceMembership.objects.filter(
        user=request.user,
        is_active=True,
        workspace__is_active=True,
    ).values_list('workspace_id', flat=True)


class TaskCategoryFilter(admin.SimpleListFilter):
    '''Expose only categories from workspaces visible to the admin user.'''

    title = 'categoria'
    parameter_name = 'category__id__exact'

    def lookups(self, request, model_admin):
        categories = Category.objects.filter(is_active=True)
        if not request.user.is_superuser:
            categories = categories.filter(
                workspace_id__in=_visible_workspace_ids(request),
            )
        return categories.order_by('name', 'pk').values_list('pk', 'name')

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(category_id=self.value())
        return queryset


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = (
        'title',
        'workspace',
        'created_by',
        'category',
        'priority',
        'status',
        'due_date',
        'completed_at',
        'source',
    )
    list_filter = ('status', 'priority', 'source', TaskCategoryFilter)
    search_fields = (
        'title',
        'description',
        'workspace__name',
        'created_by__email',
        'category__name',
    )
    list_select_related = ('workspace', 'created_by', 'category')
    readonly_fields = ('created_at', 'updated_at', 'completed_at')
    ordering = ('workspace_id', 'status', 'due_date', '-created_at')

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        if request.user.is_superuser:
            return queryset
        return queryset.filter(workspace_id__in=_visible_workspace_ids(request))

    def has_module_permission(self, request):
        if not request.user.is_active or not request.user.is_staff:
            return False
        return request.user.is_superuser or self.get_queryset(request).exists()

    def has_view_permission(self, request, obj=None):
        if not request.user.is_active or not request.user.is_staff:
            return False
        if request.user.is_superuser:
            return True
        if obj is None:
            return self.get_queryset(request).exists()
        return self.get_queryset(request).filter(pk=obj.pk).exists()

    def has_add_permission(self, request):
        return request.user.is_superuser

    def has_change_permission(self, request, obj=None):
        return request.user.is_superuser

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if not request.user.is_superuser:
            workspace_ids = _visible_workspace_ids(request)
            if db_field.name == 'workspace':
                kwargs['queryset'] = db_field.remote_field.model.objects.filter(
                    pk__in=workspace_ids,
                )
            elif db_field.name == 'category':
                kwargs['queryset'] = Category.objects.filter(
                    workspace_id__in=workspace_ids,
                    is_active=True,
                )
        return super().formfield_for_foreignkey(db_field, request, **kwargs)
