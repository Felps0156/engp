from django.contrib import admin

from categories.models import Category
from tenants.models import WorkspaceMembership

from .models import RoutineOccurrence, WeeklyRoutineItem


def _visible_workspace_ids(request):
    return WorkspaceMembership.objects.filter(
        user=request.user,
        is_active=True,
        workspace__is_active=True,
    ).values_list('workspace_id', flat=True)


class RoutineCategoryFilter(admin.SimpleListFilter):
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


class WorkspaceScopedAdminMixin:
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


@admin.register(WeeklyRoutineItem)
class WeeklyRoutineItemAdmin(WorkspaceScopedAdminMixin, admin.ModelAdmin):
    list_display = (
        'title',
        'workspace',
        'created_by',
        'category',
        'priority',
        'is_active',
        'starts_on',
        'ends_on',
    )
    list_filter = ('is_active', 'priority', RoutineCategoryFilter)
    search_fields = (
        'title',
        'workspace__name',
        'created_by__email',
        'category__name',
    )
    list_select_related = ('workspace', 'created_by', 'category')
    readonly_fields = ('created_at', 'updated_at')
    ordering = ('workspace_id', 'is_active', 'starts_on', 'title')


@admin.register(RoutineOccurrence)
class RoutineOccurrenceAdmin(WorkspaceScopedAdminMixin, admin.ModelAdmin):
    list_display = (
        'title_snapshot',
        'workspace',
        'routine_item',
        'occurrence_date',
        'status',
        'priority_snapshot',
    )
    list_filter = ('status', 'priority_snapshot', 'occurrence_date')
    search_fields = (
        'title_snapshot',
        'category_snapshot',
        'workspace__name',
        'routine_item__title',
    )
    list_select_related = ('workspace', 'routine_item')
    readonly_fields = (
        'workspace',
        'routine_item',
        'occurrence_date',
        'scheduled_time_snapshot',
        'title_snapshot',
        'category_snapshot',
        'category_color_token_snapshot',
        'estimated_minutes_snapshot',
        'priority_snapshot',
        'status',
        'completed_at',
        'skipped_at',
        'created_at',
        'updated_at',
    )
    ordering = ('workspace_id', '-occurrence_date', 'pk')

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
