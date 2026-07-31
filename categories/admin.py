from django.contrib import admin

from tenants.models import WorkspaceMembership

from .models import Category


def _visible_workspace_ids(request):
    return WorkspaceMembership.objects.filter(
        user=request.user,
        is_active=True,
        workspace__is_active=True,
    ).values_list('workspace_id', flat=True)


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'workspace',
        'color_token',
        'is_system',
        'is_active',
        'created_at',
    )
    list_filter = ('color_token', 'is_system', 'is_active')
    search_fields = ('name', 'slug', 'workspace__name')
    list_select_related = ('workspace',)
    readonly_fields = ('created_at', 'updated_at')
    ordering = ('workspace_id', 'name')

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
