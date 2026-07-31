'''Category list and mutation views.'''

from django.contrib import messages
from django.db import IntegrityError, transaction
from django.http import HttpResponseRedirect
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, ListView, UpdateView

from base.mixins import RoleRequiredMixin, TenantQuerysetMixin

from .forms import CategoryForm
from .models import Category


class CategoryListView(RoleRequiredMixin, TenantQuerysetMixin, ListView):
    '''List only active categories from the current workspace.'''

    model = Category
    template_name = 'categories/list.html'
    context_object_name = 'categories'

    def get_queryset(self):
        return super().get_queryset().filter(is_active=True)


class CategoryFormMixin(RoleRequiredMixin):
    '''Share tenant assignment and safe persistence between form views.'''

    form_class = CategoryForm
    template_name = 'categories/form.html'
    success_url = reverse_lazy('categories:list')
    success_message = 'Categoria salva.'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['workspace'] = self.request.tenant
        return kwargs

    def form_valid(self, form):
        form.instance.workspace = self.request.tenant
        try:
            with transaction.atomic():
                self.object = form.save()
        except IntegrityError:
            form.add_error('name', 'Já existe uma categoria com este nome.')
            return self.form_invalid(form)
        messages.success(self.request, self.success_message)
        return HttpResponseRedirect(self.get_success_url())


class CategoryCreateView(CategoryFormMixin, CreateView):
    '''Create a category in the active workspace.'''

    success_message = 'Categoria criada.'
    extra_context = {
        'page_title': 'Nova categoria',
        'page_description': 'Crie uma forma simples de organizar suas tarefas.',
        'submit_label': 'Criar categoria',
    }


class CategoryUpdateView(
    CategoryFormMixin,
    TenantQuerysetMixin,
    UpdateView,
):
    '''Edit a category only after scoping the lookup to the active workspace.'''

    model = Category
    success_message = 'Categoria atualizada.'
    extra_context = {
        'page_title': 'Editar categoria',
        'page_description': 'Ajuste o nome ou o token visual desta categoria.',
        'submit_label': 'Salvar alterações',
    }

    def get_queryset(self):
        return super().get_queryset().filter(is_active=True)


class CategoryDeleteView(
    RoleRequiredMixin,
    TenantQuerysetMixin,
    DeleteView,
):
    '''Delete a category through a scoped POST after client confirmation.'''

    model = Category
    success_url = reverse_lazy('categories:list')
    http_method_names = ('post', 'options')

    def get_queryset(self):
        return super().get_queryset().filter(is_active=True)

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        with transaction.atomic():
            self.object.delete()
        messages.success(request, 'Categoria excluída.')
        return HttpResponseRedirect(self.get_success_url())
