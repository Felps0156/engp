'''Protected, resumable onboarding views.'''

from django.contrib import messages
from django.db import transaction
from django.shortcuts import redirect
from django.urls import reverse
from django.views import View
from django.views.generic import FormView, TemplateView

from accounts.services import get_or_create_user_settings
from base.mixins import RoleRequiredMixin
from categories.models import Category

from .forms import (
    OnboardingAreasForm,
    OnboardingFocusForm,
    OnboardingNameForm,
    OnboardingRoutineForm,
    OnboardingTaskForm,
)
from .models import OnboardingProgress
from .services import (
    STEP_ORDER,
    create_custom_categories,
    complete_onboarding,
    get_or_create_progress,
    save_step,
    skip_onboarding,
    step_index,
)


STEP_ROUTE_NAMES = {
    OnboardingProgress.Step.NAME: 'onboarding:name',
    OnboardingProgress.Step.AREAS: 'onboarding:areas',
    OnboardingProgress.Step.FOCUS: 'onboarding:focus',
    OnboardingProgress.Step.TASK: 'onboarding:task',
    OnboardingProgress.Step.ROUTINE: 'onboarding:routine',
    OnboardingProgress.Step.COMPLETE: 'onboarding:complete',
}

STEP_CONTENT = {
    OnboardingProgress.Step.NAME: {
        'kicker': '01 / Seu começo',
        'title': 'Como podemos chamar você?',
        'description': 'Vamos deixar o ENGP com a sua cara antes de organizar o restante.',
        'submit_label': 'Continuar para áreas',
    },
    OnboardingProgress.Step.AREAS: {
        'kicker': '02 / Seu contexto',
        'title': 'O que ocupa espaço no seu dia?',
        'description': 'Escolha algumas áreas para reconhecer rapidamente onde cada ação pertence.',
        'submit_label': 'Continuar para foco',
    },
    OnboardingProgress.Step.FOCUS: {
        'kicker': '03 / Seu ritmo',
        'title': 'Qual duração combina com seu foco?',
        'description': 'Defina um ponto de partida. Você poderá ajustar essa preferência quando quiser.',
        'submit_label': 'Continuar para primeira tarefa',
    },
    OnboardingProgress.Step.TASK: {
        'kicker': '04 / Próxima ação',
        'title': 'Tire uma coisa da cabeça.',
        'description': 'Capture uma tarefa real para o seu workspace começar com movimento, não com configuração.',
        'submit_label': 'Continuar para rotina',
    },
    OnboardingProgress.Step.ROUTINE: {
        'kicker': '05 / Se quiser',
        'title': 'Existe algo que se repete toda semana?',
        'description': 'Adicione um item de rotina agora ou deixe para organizar isso depois.',
        'submit_label': 'Ver meu ponto de partida',
    },
}


class OnboardingAccessMixin(RoleRequiredMixin):
    '''Require an active workspace and prevent completed users from repeating.'''

    onboarding_step = None

    def dispatch(self, request, *args, **kwargs):
        view_step = self.onboarding_step or getattr(self, 'step', None)
        if request.user.is_authenticated:
            self.user_settings = get_or_create_user_settings(user=request.user)
            self.progress = get_or_create_progress(user=request.user)

            if (
                self.user_settings.onboarding_completed
                and view_step != OnboardingProgress.Step.COMPLETE
            ):
                return redirect('accounts:home')

            if view_step == OnboardingProgress.Step.COMPLETE:
                if self.progress.current_step != OnboardingProgress.Step.COMPLETE:
                    return redirect(self.get_step_url(self.progress.current_step))
            elif view_step is not None:
                if step_index(view_step) > step_index(
                    self.progress.current_step,
                ):
                    return redirect(self.get_step_url(self.progress.current_step))

        return super().dispatch(request, *args, **kwargs)

    def get_step_url(self, step):
        '''Build a stable URL for a persisted onboarding step.'''

        return reverse(STEP_ROUTE_NAMES[step])


class OnboardingStartView(OnboardingAccessMixin, View):
    '''Redirect a user to the first incomplete step.'''

    def get(self, request, *args, **kwargs):
        return redirect(self.get_step_url(self.progress.current_step))


class OnboardingStepView(OnboardingAccessMixin, FormView):
    '''Shared form flow for each persisted onboarding step.'''

    step = None
    template_name = 'onboarding/step.html'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        if self.step == OnboardingProgress.Step.NAME:
            kwargs['instance'] = self.request.user
        elif self.step == OnboardingProgress.Step.AREAS:
            kwargs['workspace'] = self.request.tenant
        elif self.step == OnboardingProgress.Step.FOCUS:
            kwargs['instance'] = self.user_settings
        elif self.step in (
            OnboardingProgress.Step.TASK,
            OnboardingProgress.Step.ROUTINE,
        ):
            kwargs['initial'] = self.get_saved_initial()
        return kwargs

    def get_saved_initial(self):
        '''Restore the current step's values after a pause or a revisit.'''

        data = self.progress.data or {}
        if self.step == OnboardingProgress.Step.TASK:
            saved = data.get('first_task') or data.get('task') or {}
            return {
                'title': saved.get('title', ''),
                'description': saved.get('description', ''),
            }
        if self.step == OnboardingProgress.Step.ROUTINE:
            saved = data.get('routine') or data.get('weekly_routine_item') or {}
            return {
                'title': saved.get('title', ''),
                'weekdays': saved.get('weekdays', []),
                'scheduled_time': saved.get('scheduled_time', ''),
                'estimated_minutes': saved.get('estimated_minutes'),
            }
        return {}

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        step_position = step_index(self.step)
        content = STEP_CONTENT[self.step]
        progress_items = []
        current_position = step_index(self.progress.current_step)
        completed_steps = self.progress.completed_steps or []

        for position, step in enumerate(STEP_ORDER):
            if step in completed_steps or position < current_position:
                state = 'completed'
            elif step == self.step:
                state = 'current'
            else:
                state = 'upcoming'
            progress_items.append(
                {
                    'label': OnboardingProgress.Step(step).label,
                    'number': position + 1,
                    'state': state,
                    'url': self.get_step_url(step),
                    'can_visit': position <= current_position,
                },
            )

        context.update(
            {
                'progress': self.progress,
                'onboarding_step': self.step,
                'step_number': step_position + 1,
                'total_steps': len(STEP_ORDER),
                'progress_percent': int((step_position + 1) / len(STEP_ORDER) * 100),
                'progress_items': progress_items,
                'step_kicker': content['kicker'],
                'step_title': content['title'],
                'step_description': content['description'],
                'submit_label': content['submit_label'],
                'previous_url': (
                    self.get_step_url(STEP_ORDER[step_position - 1])
                    if step_position > 0
                    else None
                ),
            },
        )
        return context

    def form_valid(self, form):
        with transaction.atomic():
            data = self.persist_form(form)
            save_step(progress=self.progress, step=self.step, data=data)

        if self.step == OnboardingProgress.Step.ROUTINE:
            return redirect('onboarding:complete')
        return redirect(self.get_step_url(self.progress.current_step))

    def persist_form(self, form):
        '''Persist the domain value and return the progress payload for the step.'''

        if self.step == OnboardingProgress.Step.NAME:
            user = form.save()
            return {
                'profile': {
                    'first_name': user.first_name,
                    'last_name': user.last_name,
                },
            }

        if self.step == OnboardingProgress.Step.AREAS:
            selected_categories = list(form.cleaned_data['areas'])
            custom_categories = create_custom_categories(
                workspace=self.request.tenant,
                names=form.cleaned_data.get('custom_areas', []),
            )
            categories = []
            seen_ids = set()
            for category in (*selected_categories, *custom_categories):
                if category.pk not in seen_ids:
                    categories.append(category)
                    seen_ids.add(category.pk)
            return {
                'areas': [category.pk for category in categories],
                'area_ids': [category.pk for category in categories],
                'area_names': [category.name for category in categories],
                'area_slugs': [category.slug for category in categories],
            }

        if self.step == OnboardingProgress.Step.FOCUS:
            settings_obj = form.save()
            return {
                'focus': {
                    'default_focus_minutes': settings_obj.default_focus_minutes,
                },
            }

        if self.step == OnboardingProgress.Step.TASK:
            task_data = {
                'title': form.cleaned_data['title'],
                'description': form.cleaned_data['description'],
                'source': 'onboarding',
            }
            return {'first_task': task_data, 'task': task_data}

        routine_data = {
            'title': form.cleaned_data['title'],
            'weekdays': form.cleaned_data['weekdays'],
            'scheduled_time': (
                form.cleaned_data['scheduled_time'].isoformat()
                if form.cleaned_data['scheduled_time']
                else None
            ),
            'estimated_minutes': form.cleaned_data['estimated_minutes'],
            'source': 'onboarding',
        }
        return {
            'routine': routine_data,
            'weekly_routine_item': routine_data,
        }


class NameStepView(OnboardingStepView):
    step = OnboardingProgress.Step.NAME
    form_class = OnboardingNameForm


class AreasStepView(OnboardingStepView):
    step = OnboardingProgress.Step.AREAS
    form_class = OnboardingAreasForm


class FocusStepView(OnboardingStepView):
    step = OnboardingProgress.Step.FOCUS
    form_class = OnboardingFocusForm


class TaskStepView(OnboardingStepView):
    step = OnboardingProgress.Step.TASK
    form_class = OnboardingTaskForm


class RoutineStepView(OnboardingStepView):
    step = OnboardingProgress.Step.ROUTINE
    form_class = OnboardingRoutineForm


class OnboardingSkipView(OnboardingAccessMixin, View):
    '''Allow the user to leave the guided flow through an explicit POST.'''

    http_method_names = ('post', 'options')

    def post(self, request, *args, **kwargs):
        skip_onboarding(user=request.user)
        messages.success(
            request,
            'Tudo bem deixar o restante para depois. Seu workspace está pronto.',
        )
        return redirect('onboarding:complete')


class OnboardingCompleteView(OnboardingAccessMixin, TemplateView):
    '''Show the final summary and persist the explicit completion action.'''

    onboarding_step = OnboardingProgress.Step.COMPLETE
    template_name = 'onboarding/complete.html'
    http_method_names = ('get', 'post', 'options')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        data = self.progress.data or {}
        area_ids = data.get('area_ids') or data.get('areas') or []
        categories = Category.objects.filter(
            workspace=self.request.tenant,
            pk__in=area_ids,
            is_active=True,
        ).order_by('name', 'pk')
        context.update(
            {
                'progress': self.progress,
                'categories': categories,
                'first_task': data.get('first_task') or data.get('task'),
                'routine': data.get('routine') or data.get('weekly_routine_item'),
            },
        )
        return context

    def post(self, request, *args, **kwargs):
        complete_onboarding(user=request.user)
        messages.success(
            request,
            'Onboarding concluído. Seu workspace está pronto para o próximo passo.',
        )
        return redirect('accounts:home')
