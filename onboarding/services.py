'''Transactional services for the onboarding flow.'''

from django.db import IntegrityError, transaction
from django.utils import timezone

from accounts.services import get_or_create_user_settings
from categories.models import Category

from .models import OnboardingProgress


STEP_ORDER = (
    OnboardingProgress.Step.NAME,
    OnboardingProgress.Step.AREAS,
    OnboardingProgress.Step.FOCUS,
    OnboardingProgress.Step.TASK,
    OnboardingProgress.Step.ROUTINE,
)


def get_or_create_progress(*, user):
    '''Return the single resumable progress record for a user.'''

    progress, _created = OnboardingProgress.objects.get_or_create(user=user)
    return progress


def step_index(step):
    '''Return the ordered position of a step, including the final state.'''

    if step == OnboardingProgress.Step.COMPLETE:
        return len(STEP_ORDER)
    try:
        return STEP_ORDER.index(step)
    except ValueError:
        return 0


def next_step(step):
    '''Return the next route step after a regular onboarding step.'''

    index = step_index(step) + 1
    if index >= len(STEP_ORDER):
        return OnboardingProgress.Step.COMPLETE
    return STEP_ORDER[index]


@transaction.atomic
def save_step(*, progress, step, data):
    '''Merge a completed step and advance without regressing existing progress.'''

    stored_data = dict(progress.data or {})
    stored_data.update(data)

    completed_steps = list(progress.completed_steps or [])
    if step not in completed_steps:
        completed_steps.append(step)

    candidate_step = next_step(step)
    if step_index(candidate_step) > step_index(progress.current_step):
        progress.current_step = candidate_step

    progress.data = stored_data
    progress.completed_steps = completed_steps
    progress.save(
        update_fields=(
            'current_step',
            'completed_steps',
            'data',
            'updated_at',
        ),
    )
    return progress


@transaction.atomic
def complete_onboarding(*, user, skipped=False):
    '''Mark both progress and user settings as complete atomically.'''

    progress = OnboardingProgress.objects.select_for_update().get(user=user)
    user_settings = get_or_create_user_settings(user=user)
    now = timezone.now()

    progress.current_step = OnboardingProgress.Step.COMPLETE
    progress.completed_at = progress.completed_at or now
    progress.is_skipped = progress.is_skipped or skipped
    if skipped and progress.skipped_at is None:
        progress.skipped_at = now
    progress.save(
        update_fields=(
            'current_step',
            'completed_at',
            'is_skipped',
            'skipped_at',
            'updated_at',
        ),
    )

    if not user_settings.onboarding_completed:
        user_settings.onboarding_completed = True
        user_settings.save(update_fields=('onboarding_completed', 'updated_at'))

    return progress


@transaction.atomic
def skip_onboarding(*, user):
    '''Finish onboarding immediately while retaining the current answers.'''

    return complete_onboarding(user=user, skipped=True)


@transaction.atomic
def create_custom_categories(*, workspace, names):
    '''Create onboarding areas idempotently and return existing or new records.'''

    categories = []
    for name in names:
        normalized_name = name.strip()
        if not normalized_name:
            continue

        category = Category.objects.filter(
            workspace=workspace,
            name__iexact=normalized_name,
        ).first()
        if category is None:
            try:
                with transaction.atomic():
                    category = Category.objects.create(
                        workspace=workspace,
                        name=normalized_name,
                        color_token=Category.ColorToken.BRAND,
                    )
            except IntegrityError:
                category = Category.objects.get(
                    workspace=workspace,
                    name__iexact=normalized_name,
                )
        categories.append(category)
    return categories
