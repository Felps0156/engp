'''Request middleware for user-specific localization.'''

from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from django.utils import timezone

from .models import UserSettings


class UserTimezoneMiddleware:
    '''Activate a user's saved timezone for the duration of a request.'''

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        user = getattr(request, 'user', None)
        settings_obj = None
        if user is not None and user.is_authenticated:
            settings_obj = UserSettings.objects.filter(
                user_id=user.pk,
            ).only('timezone').first()

        if settings_obj is not None:
            try:
                timezone.activate(ZoneInfo(settings_obj.timezone))
            except (TypeError, ValueError, ZoneInfoNotFoundError):
                timezone.deactivate()
        else:
            timezone.deactivate()

        try:
            return self.get_response(request)
        finally:
            timezone.deactivate()
