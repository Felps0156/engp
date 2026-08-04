'''Weekly routine planning views and state actions.'''

from django.contrib import messages
from django.db import IntegrityError, transaction
from django.db.models import ProtectedError
from django.http import HttpResponseRedirect
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.views import View
from django.views.generic import CreateView, ListView, UpdateView
from django.views.generic.detail import SingleObjectMixin

from base.mixins import RoleRequiredMixin, TenantQuerysetMixin

from .forms import RoutineItemForm
from .models import WEEKDAY_CHOICES, WeeklyRoutineItem
from .services import (
    delete_routine_item,
    pause_routine_item,
    resume_routine_item,
)


class RoutineScopeMixin(RoleRequiredMixin, TenantQuerysetMixin):
    '''Apply active-workspace scoping to every routine item lookup.'''

    def get_queryset(self):
        return super().get_queryset().select_related('category', 'created_by')


class RoutineWeeklyView(RoutineScopeMixin, ListView):
    '''Render all seven weekdays with their recurring items.'''

    model = WeeklyRoutineItem
    template_name = 'routines/weekly.html'
    context_object_name = 'routine_items'

    def get_queryset(self):
        return super().get_queryset().order_by(
            '-is_active',
            'scheduled_time',
            'title',
            'pk',
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        items_by_day = {weekday: [] for weekday, _label in WEEKDAY_CHOICES}
        for item in context['routine_items']:
            for weekday in item.weekdays or []:
                if weekday in items_by_day:
                    items_by_day[weekday].append(item)

        today_weekday = timezone.localdate().weekday()
        context.update(
            {
                'week_days': tuple(
                    {
                        'value': weekday,
                        'label': label,
                        'items': items_by_day[weekday],
                        'is_today': weekday == today_weekday,
                    }
                    for weekday, label in WEEKDAY_CHOICES
                ),
                'today_label': dict(WEEKDAY_CHOICES)[today_weekday],
                'active_routine_count': self.get_queryset().filter(
                    is_active=True,
                ).count(),
                'page_title': 'Rotina semanal',
                'page_description': (
                    'Transforme o que se repete em um plano visual, leve e fácil '
                    'de ajustar.'
                ),
            },
        )
        return context


class RoutineFormMixin:
    '''Share tenant-aware form setup and persistence between create and edit.'''

    form_class = RoutineItemForm
    template_name = 'routines/form.html'
    success_url = reverse_lazy('routines:weekly')
    success_message = 'Item de rotina salvo.'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['workspace'] = self.request.tenant
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        form.instance.workspace = self.request.tenant
        if not form.instance.created_by_id:
            form.instance.created_by = self.request.user
        try:
            with transaction.atomic():
                self.object = form.save()
        except IntegrityError:
            form.add_error(
                None,
                'Não foi possível salvar a rotina. Revise os dados e tente novamente.',
            )
            return self.form_invalid(form)
        messages.success(self.request, self.success_message)
        return HttpResponseRedirect(self.get_success_url())

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.setdefault('page_title', 'Novo item de rotina')
        context.setdefault(
            'page_description',
            'Defina os dias e o ritmo sem transformar sua semana em um calendário complexo.',
        )
        context.setdefault('submit_label', 'Criar item')
        context['is_edit'] = bool(getattr(self.object, 'pk', None))
        return context


class RoutineCreateView(RoutineFormMixin, RoleRequiredMixin, CreateView):
    '''Create a recurring item in the active workspace.'''

    success_message = 'Item de rotina criado.'


class RoutineUpdateView(RoutineFormMixin, RoutineScopeMixin, UpdateView):
    '''Edit a recurring item without rewriting materialized snapshots.'''

    model = WeeklyRoutineItem
    success_message = 'Item de rotina atualizado.'
    extra_context = {
        'page_title': 'Editar item de rotina',
        'page_description': (
            'Ajuste o plano. Ocorrências já criadas preservam o histórico original.'
        ),
        'submit_label': 'Salvar alterações',
    }


class RoutineActionView(RoutineScopeMixin, SingleObjectMixin, View):
    '''Base POST-only view for workspace-scoped routine actions.'''

    model = WeeklyRoutineItem
    http_method_names = ('post', 'options')

    def get_success_url(self):
        return reverse('routines:weekly')


class RoutinePauseView(RoutineActionView):
    '''Pause future materialization of a routine item.'''

    def post(self, request, *args, **kwargs):
        item = self.get_object()
        was_active = item.is_active
        pause_routine_item(item=item, workspace=request.tenant)
        messages.success(
            request,
            'Item de rotina pausado.' if was_active else 'O item já estava pausado.',
        )
        return HttpResponseRedirect(self.get_success_url())


class RoutineResumeView(RoutineActionView):
    '''Reactivate a paused routine item.'''

    def post(self, request, *args, **kwargs):
        item = self.get_object()
        was_active = item.is_active
        resume_routine_item(item=item, workspace=request.tenant)
        messages.success(
            request,
            'Item de rotina reativado.' if not was_active else 'O item já estava ativo.',
        )
        return HttpResponseRedirect(self.get_success_url())


class RoutineDeleteView(RoutineActionView):
    '''Delete only items without materialized history.'''

    def post(self, request, *args, **kwargs):
        item = self.get_object()
        title = item.title
        try:
            delete_routine_item(item=item, workspace=request.tenant)
        except ProtectedError:
            messages.error(
                request,
                f'Não é possível excluir "{title}" porque ele já possui histórico. '
                'Pause o item para interromper novas ocorrências.',
            )
        else:
            messages.success(request, f'Item de rotina "{title}" excluído.')
        return HttpResponseRedirect(self.get_success_url())
