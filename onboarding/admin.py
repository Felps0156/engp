'''Admin registration for onboarding progress.'''

from django.contrib import admin

from .models import OnboardingProgress


@admin.register(OnboardingProgress)
class OnboardingProgressAdmin(admin.ModelAdmin):
    list_display = ('user', 'current_step', 'is_skipped', 'completed_at', 'updated_at')
    list_filter = ('current_step', 'is_skipped')
    search_fields = ('user__email', 'user__first_name', 'user__last_name')
    readonly_fields = ('created_at', 'updated_at', 'completed_at', 'skipped_at')
