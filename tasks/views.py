'''Task list, planning and state mutation views.'''

from datetime import timedelta

from django.contrib import messages
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import redirect
from django.urls import reverse
from django.utils import timezone
from django.utils.http import url_has_allowed_host_and_scheme
from django.views import View
from django.views.generic import ListView, UpdateView
from django.views.generic.detail import SingleObjectMixin

from base.mixins import PerPageMixin, RoleRequiredMixin, TenantQuerysetMixin

from .forms import QuickTaskForm, TaskFilterForm, TaskForm, TaskMoveForm
from .models import Task
from .services import complete_task, move_task, move_task_to_column, reopen_task


def _safe_next_url(request, candidate, fallback):
    '''Keep redirects inside the current application host.'''

    if candidate and url_has_allowed_host_and_scheme(
        candidate,
        allowed_hosts={request.get_host()},
        require_https=request.is_secure(),
    ):
        return candidate
    return fallback


class TaskScopeMixin(RoleRequiredMixin, TenantQuerysetMixin):
    '''Apply membership and workspace scoping to every task lookup.'''

    def get_queryset(self):
        return super().get_queryset().select_related('category', 'created_by')


class TaskListView(TaskScopeMixin, PerPageMixin, ListView):
    '''Render task lists and the four-column planning board.'''

    model = Task
    template_name = 'tasks/list.html'
    context_object_name = 'tasks'
    paginate_by = 10
    per_page_default = 10
    per_page_query_params = ('category', 'priority')
    http_method_names = ('get', 'post', 'options')

    view_key = 'inbox'
    page_title = 'Caixa de entrada'
    page_description = 'Capture tudo o que precisa de uma próxima ação antes de decidir quando fazer.'
    empty_title = 'Sua caixa de entrada está limpa.'
    empty_description = 'Capture uma tarefa rápida aqui e planeje a data quando estiver pronto.'
    board_page_size = 10

    def get_task_view_definitions(self):
        return (
            {
                'key': 'inbox',
                'label': 'Caixa de entrada',
                'kicker': 'Sem data',
                'empty_title': 'Entrada limpa',
                'empty_description': 'Capture uma tarefa para decidir a data depois.',
            },
            {
                'key': 'week',
                'label': 'Esta semana',
                'kicker': 'Próximos dias',
                'empty_title': 'Semana livre',
                'empty_description': 'Mova uma tarefa para os próximos dias para vê-la aqui.',
            },
            {
                'key': 'today',
                'label': 'Hoje',
                'kicker': 'Atenção agora',
                'empty_title': 'Nada para hoje',
                'empty_description': 'Planeje uma tarefa para hoje quando quiser trazê-la para este espaço.',
            },
            {
                'key': 'completed',
                'label': 'Feitos',
                'kicker': 'Histórico',
                'empty_title': 'Nenhuma tarefa feita',
                'empty_description': 'As tarefas concluídas aparecerão aqui para uma revisão rápida.',
            },
        )

    def get_filter_form(self):
        if not hasattr(self, 'filter_form'):
            self.filter_form = TaskFilterForm(
                self.request.GET or None,
                workspace=self.request.tenant,
            )
        return self.filter_form

    def get_view_url(self, view_key):
        url = reverse(f'tasks:{view_key}')
        query_params = self.request.GET.copy()
        query_params.pop('page', None)
        query = query_params.urlencode()
        return f'{url}?{query}' if query else url

    def get_view_queryset(self, view_key):
        queryset = super().get_queryset()
        today = timezone.localdate()

        if view_key == 'inbox':
            queryset = queryset.filter(
                status=Task.Status.PENDING,
                due_date__isnull=True,
            )
        elif view_key == 'today':
            queryset = queryset.filter(
                status=Task.Status.PENDING,
                due_date__lte=today,
            )
        elif view_key == 'week':
            queryset = queryset.filter(
                status=Task.Status.PENDING,
                due_date__range=(
                    today + timedelta(days=1),
                    today + timedelta(days=6),
                ),
            )
        elif view_key == 'completed':
            queryset = queryset.filter(status=Task.Status.COMPLETED)

        filter_form = self.get_filter_form()
        if filter_form.is_valid():
            category = filter_form.cleaned_data.get('category')
            priority = filter_form.cleaned_data.get('priority')
            if category is not None:
                queryset = queryset.filter(category=category)
            if priority:
                queryset = queryset.filter(priority=priority)

        if view_key == 'completed':
            return queryset.order_by('board_order', '-completed_at', '-pk')
        return queryset.order_by('board_order', 'due_date', '-created_at', '-pk')

    def get_queryset(self):
        return self.get_view_queryset(self.view_key)

    def get_board_columns(self):
        columns = []
        for definition in self.get_task_view_definitions():
            queryset = self.get_view_queryset(definition['key'])
            total = queryset.count()
            columns.append(
                {
                    **definition,
                    'url': self.get_view_url(definition['key']),
                    'tasks': queryset[:self.board_page_size],
                    'total': total,
                    'has_more': total > self.board_page_size,
                },
            )
        return columns

    def post(self, request, *args, **kwargs):
        '''Handle quick capture without leaving the current task view.'''

        self.quick_form = QuickTaskForm(request.POST)
        if self.quick_form.is_valid():
            task = self.quick_form.save(commit=False)
            task.workspace = request.tenant
            task.created_by = request.user
            task.source = Task.Source.MANUAL
            task.save()
            messages.success(request, 'Tarefa capturada.')
            fallback = reverse(f'tasks:{self.view_key}')
            return redirect(
                _safe_next_url(request, request.POST.get('next'), fallback),
            )

        self.object_list = self.get_queryset()
        return self.render_to_response(self.get_context_data(), status=400)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        query_params = self.request.GET.copy()
        query_params.pop('page', None)
        return_url = self.request.get_full_path()
        quick_return_url = (
            return_url
            if self.view_key == 'inbox'
            else reverse('tasks:inbox')
        )
        task_view_definitions = self.get_task_view_definitions()
        context.update(
            {
                'page_title': self.page_title,
                'page_description': self.page_description,
                'current_view': self.view_key,
                'today': timezone.localdate(),
                'filter_form': self.get_filter_form(),
                'quick_form': getattr(self, 'quick_form', QuickTaskForm()),
                'return_url': return_url,
                'quick_return_url': quick_return_url,
                'has_filters': bool(
                    self.request.GET.get('category')
                    or self.request.GET.get('priority')
                ),
                'pagination_query': query_params.urlencode(),
                'empty_title': self.empty_title,
                'empty_description': self.empty_description,
                'is_board': self.view_key == 'inbox',
                'task_columns': self.get_board_columns()
                if self.view_key == 'inbox'
                else (),
                'task_views': tuple(
                    {
                        'key': definition['key'],
                        'label': definition['label'],
                        'url': self.get_view_url(definition['key']),
                    }
                    for definition in task_view_definitions
                ),
            },
        )
        return context


class TaskInboxView(TaskListView):
    '''Show pending tasks without a planned date.'''

    view_key = 'inbox'


class TaskTodayView(TaskListView):
    '''Show pending tasks due today or overdue.'''

    view_key = 'today'
    page_title = 'Hoje'
    page_description = 'Uma lista curta do que pede sua atenção agora, incluindo o que ficou para trás.'
    empty_title = 'Nada planejado para hoje.'
    empty_description = 'Planeje uma tarefa da caixa de entrada para começar a transformar intenção em ação.'


class TaskWeekView(TaskListView):
    '''Show pending tasks for the next seven days.'''

    view_key = 'week'
    page_title = 'Esta semana'
    page_description = 'Veja os próximos sete dias sem transformar planejamento em um calendário complexo.'
    empty_title = 'Sua semana ainda está aberta.'
    empty_description = 'Mova tarefas para uma data desta semana para criar um plano leve e executável.'


class TaskCompletedView(TaskListView):
    '''Show completed task history ordered by completion time.'''

    view_key = 'completed'
    page_title = 'Feitos'
    page_description = 'Seu histórico recente de ações finalizadas, pronto para uma revisão rápida.'
    empty_title = 'Ainda não há tarefas feitas.'
    empty_description = 'Quando você finalizar uma tarefa, ela aparecerá aqui para mostrar seu progresso.'


class TaskUpdateView(TaskScopeMixin, UpdateView):
    '''Edit a task only after resolving it inside the active workspace.'''

    model = Task
    form_class = TaskForm
    template_name = 'tasks/form.html'
    http_method_names = ('get', 'post', 'options')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['workspace'] = self.request.tenant
        return kwargs

    def get_next_url(self):
        candidate = self.request.POST.get('next') or self.request.GET.get('next')
        return _safe_next_url(
            self.request,
            candidate,
            reverse('tasks:inbox'),
        )

    def get_success_url(self):
        return self.get_next_url()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            {
                'page_title': 'Editar tarefa',
                'page_description': 'Ajuste o contexto, a prioridade ou a data sem perder a próxima ação.',
                'next_url': self.get_next_url(),
            },
        )
        return context

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, 'Tarefa atualizada.')
        return response


class TaskActionView(TaskScopeMixin, SingleObjectMixin, View):
    '''Base POST-only view for idempotent task state actions.'''

    model = Task
    http_method_names = ('post', 'options')

    def get_return_url(self):
        return _safe_next_url(
            self.request,
            self.request.POST.get('next'),
            reverse('tasks:inbox'),
        )


class PendingTaskActionView(TaskActionView):
    '''Limit planning actions to tasks that are still pending.'''

    def get_queryset(self):
        return super().get_queryset().filter(status=Task.Status.PENDING)


class TaskCompleteView(TaskActionView):
    '''Complete a task through the transactional service.'''

    def post(self, request, *args, **kwargs):
        task = self.get_object()
        complete_task(task=task, workspace=request.tenant)
        messages.success(request, 'Tarefa concluída.')
        return HttpResponseRedirect(self.get_return_url())


class TaskReopenView(TaskActionView):
    '''Reopen a completed task through the transactional service.'''

    def post(self, request, *args, **kwargs):
        task = self.get_object()
        reopen_task(task=task, workspace=request.tenant)
        messages.success(request, 'Tarefa reaberta.')
        return HttpResponseRedirect(self.get_return_url())


class TaskPlanTodayView(PendingTaskActionView):
    '''Plan a pending task for the user's current local date.'''

    def post(self, request, *args, **kwargs):
        task = self.get_object()
        move_task(
            task=task,
            workspace=request.tenant,
            due_date=timezone.localdate(),
        )
        messages.success(request, 'Tarefa planejada para hoje.')
        return HttpResponseRedirect(self.get_return_url())


class TaskMoveView(PendingTaskActionView):
    '''Move a task to a validated planned date.'''

    def post(self, request, *args, **kwargs):
        task = self.get_object()
        form = TaskMoveForm(request.POST)
        if not form.is_valid():
            messages.error(request, 'Informe uma data válida para mover a tarefa.')
            return HttpResponseRedirect(self.get_return_url())

        move_task(
            task=task,
            workspace=request.tenant,
            due_date=form.cleaned_data['due_date'],
        )
        messages.success(request, 'Data da tarefa atualizada.')
        return HttpResponseRedirect(self.get_return_url())


class TaskDragView(TaskActionView):
    '''Move a task between board columns and persist its position.'''

    def post(self, request, *args, **kwargs):
        task = self.get_object()
        before_task_id = request.POST.get('before_task_id') or None
        if before_task_id:
            try:
                before_task_id = int(before_task_id)
            except (TypeError, ValueError):
                return HttpResponse(status=400)

        try:
            move_task_to_column(
                task=task,
                workspace=request.tenant,
                column=request.POST.get('column', ''),
                before_task_id=before_task_id,
            )
        except ValueError:
            return HttpResponse(status=400)

        return HttpResponse(status=204)


class TaskDeleteView(TaskActionView):
    '''Delete a task through an explicit POST confirmation.'''

    def post(self, request, *args, **kwargs):
        task = self.get_object()
        title = task.title
        task.delete()
        messages.success(request, f'Tarefa "{title}" excluída.')
        return HttpResponseRedirect(self.get_return_url())
