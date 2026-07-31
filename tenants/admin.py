from django.contrib import admin

from .models import Workspace, WorkspaceMembership


def _visible_workspace_ids(request):
    return WorkspaceMembership.objects.filter(
        user=request.user,
        is_active=True,
        workspace__is_active=True,
    ).values_list('workspace_id', flat=True)


@admin.register(Workspace)
class WorkspaceAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'is_active', 'created_at', 'updated_at')
    list_filter = ('is_active',)
    search_fields = ('name', 'slug')
    readonly_fields = ('created_at', 'updated_at')
    ordering = ('name',)

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        if request.user.is_superuser:
            return queryset
        return queryset.filter(pk__in=_visible_workspace_ids(request))

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


@admin.register(WorkspaceMembership)
class WorkspaceMembershipAdmin(admin.ModelAdmin):
    list_display = (
        'workspace',
        'user',
        'role',
        'is_active',
        'created_at',
        'updated_at',
    )
    list_filter = ('role', 'is_active')
    search_fields = (
        'workspace__name',
        'workspace__slug',
        'user__email',
        'user__first_name',
        'user__last_name',
    )
    readonly_fields = ('created_at', 'updated_at')
    list_select_related = ('workspace', 'user')
    ordering = ('workspace_id', 'user_id')

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
