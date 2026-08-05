'''Weekly routine planning views and state actions.'''

from django.contrib import messages
from django.db import IntegrityError, transaction
from django.http import HttpResponseRedirect
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.views import View
from django.views.generic import CreateView, ListView, UpdateView
from django.views.generic.detail import SingleObjectMixin

from base.mixins import RoleRequiredMixin, TenantQuerysetMixin

from .analysis import build_month_analysis, month_bounds, parse_month
from .forms import RoutineItemForm, RoutineQuickCreateForm
from .models import RoutineOccurrence, WeeklyRoutineItem
from .services import (
    delete_routine_item,
    pause_routine_item,
    resume_routine_item,
    toggle_routine_occurrence,
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
        today = timezone.localdate()
        selected_month = parse_month(self.request.GET.get('month'), fallback=today)
        month_start, month_end = month_bounds(selected_month)
        occurrences = RoutineOccurrence.objects.for_tenant(
            self.request.tenant,
        ).filter(
            occurrence_date__range=(month_start, month_end),
        )
        context.update(
            {
                'analysis': build_month_analysis(
                    items=context['routine_items'],
                    occurrences=occurrences,
                    month=selected_month,
                    today=today,
                ),
                'quick_form': kwargs.get('quick_form') or RoutineQuickCreateForm(
                    workspace=self.request.tenant,
                    user=self.request.user,
                ),
                'open_create_dialog': kwargs.get('open_create_dialog', False),
                'page_title': 'Rotina semanal',
                'page_description': (
                    'Visualize sua consistência, registre conclusões e ajuste o '
                    'ritmo ao longo do mês.'
                ),
            },
        )
        return context

    def post(self, request, *args, **kwargs):
        self.object_list = self.get_queryset()
        form = RoutineQuickCreateForm(
            request.POST,
            workspace=request.tenant,
            user=request.user,
        )
        if form.is_valid():
            try:
                with transaction.atomic():
                    form.save()
            except IntegrityError:
                form.add_error(
                    None,
                    'Não foi possível criar o hábito. Tente novamente.',
                )
            else:
                messages.success(request, 'Hábito criado.')
                month = timezone.localdate().strftime('%Y-%m')
                url = reverse('routines:weekly')
                return HttpResponseRedirect(f'{url}?month={month}')
        context = self.get_context_data(
            object_list=self.object_list,
            quick_form=form,
            open_create_dialog=True,
        )
        return self.render_to_response(context)


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
    '''Archive an item without changing previous monthly history.'''

    def post(self, request, *args, **kwargs):
        item = self.get_object()
        title = item.title
        delete_routine_item(item=item, workspace=request.tenant)
        messages.success(request, f'Hábito "{title}" excluído.')
        return HttpResponseRedirect(self.get_success_url())


class RoutineOccurrenceToggleView(RoutineActionView):
    '''Toggle one routine completion using a tenant-scoped POST action.'''

    def get_success_url(self):
        month = self.request.POST.get('month', '')
        url = reverse('routines:weekly')
        return f'{url}?month={month}' if month else url

    def post(self, request, *args, **kwargs):
        item = self.get_object()
        try:
            toggle_routine_occurrence(
                item=item,
                workspace=request.tenant,
                occurrence_date=request.POST.get('date'),
            )
        except ValueError as exc:
            messages.error(request, str(exc))
        return HttpResponseRedirect(self.get_success_url())
