'''Template context for account-wide preferences.'''

from .models import UserSettings


def user_settings(request):
    '''Expose the authenticated user's theme without creating records.'''

    settings_obj = None
    theme = UserSettings.Theme.LIGHT

    if getattr(request, 'user', None) is not None and request.user.is_authenticated:
        settings_obj = UserSettings.objects.filter(
            user_id=request.user.pk,
        ).first()
        if settings_obj is not None:
            theme = settings_obj.theme

    return {
        'user_settings': settings_obj,
        'user_theme': theme,
    }
