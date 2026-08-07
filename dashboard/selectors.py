'''Read selectors used to compose the authenticated user's Home.'''

from django.db.models import Case, IntegerField, Value, When
from django.utils import timezone

from routines.models import RoutineOccurrence
from routines.services import ensure_today_routine_occurrences


HOME_ROUTINE_LIMIT = 5


def get_home_routine(*, workspace, occurrence_date=None):
    '''Ensure and return a compact, ordered view of today's routine.'''

    if workspace is None:
        return {
            'occurrences': (),
            'has_more': False,
            'date': occurrence_date or timezone.localdate(),
        }

    occurrence_date = occurrence_date or timezone.localdate()
    ensure_today_routine_occurrences(
        workspace=workspace,
        occurrence_date=occurrence_date,
    )
    queryset = (
        RoutineOccurrence.objects.for_tenant(workspace)
        .filter(occurrence_date=occurrence_date)
        .filter(routine_item__deleted_at__isnull=True)
        .select_related('routine_item')
        .annotate(
            status_order=Case(
                When(
                    status=RoutineOccurrence.Status.PENDING,
                    then=Value(0),
                ),
                When(
                    status=RoutineOccurrence.Status.COMPLETED,
                    then=Value(1),
                ),
                default=Value(2),
                output_field=IntegerField(),
            ),
        )
        .order_by(
            'status_order',
            'scheduled_time_snapshot',
            'title_snapshot',
            'pk',
        )
    )
    occurrences = list(queryset[: HOME_ROUTINE_LIMIT + 1])
    return {
        'occurrences': occurrences[:HOME_ROUTINE_LIMIT],
        'has_more': len(occurrences) > HOME_ROUTINE_LIMIT,
        'date': occurrence_date,
    }
