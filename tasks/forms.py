'''Forms for workspace-scoped tasks.'''

from django import forms
from django.core.exceptions import ValidationError
from django.db.models import Q

from categories.models import Category

from .models import Task


class TaskForm(forms.ModelForm):
    '''Validate task input without exposing tenant ownership to the client.'''

    class Meta:
        model = Task
        fields = (
            'title',
            'description',
            'category',
            'priority',
            'due_date',
            'estimated_minutes',
        )
        widgets = {
            'title': forms.TextInput(
                attrs={
                    'autocomplete': 'off',
                    'placeholder': 'Ex.: Marcar consulta com o dentista',
                    'maxlength': 180,
                },
            ),
            'description': forms.Textarea(
                attrs={
                    'rows': 4,
                    'placeholder': 'Algum contexto que ajude você a começar?',
                },
            ),
            'due_date': forms.DateInput(
                format='%Y-%m-%d',
                attrs={'type': 'date'},
            ),
            'estimated_minutes': forms.NumberInput(
                attrs={'min': 1, 'inputmode': 'numeric'},
            ),
        }

    def __init__(self, *args, workspace=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.workspace = workspace or getattr(self.instance, 'workspace', None)

        if self.workspace is not None and not self.instance.workspace_id:
            self.instance.workspace = self.workspace

        categories = Category.objects.filter(
            workspace=self.workspace,
            is_active=True,
        )
        if self.instance.category_id:
            categories = Category.objects.filter(
                workspace=self.workspace,
            ).filter(Q(is_active=True) | Q(pk=self.instance.category_id))
        self.fields['category'].queryset = categories.order_by('name', 'pk')

        self.fields['title'].label = 'Título'
        self.fields['description'].label = 'Descrição'
        self.fields['category'].label = 'Categoria'
        self.fields['category'].empty_label = 'Sem categoria'
        self.fields['priority'].label = 'Prioridade'
        self.fields['due_date'].label = 'Data planejada'
        self.fields['estimated_minutes'].label = 'Estimativa (minutos)'

    def clean_title(self):
        title = self.cleaned_data['title'].strip()
        if not title:
            raise ValidationError('Informe um título para a tarefa.')
        return title

    def clean_description(self):
        return self.cleaned_data['description'].strip()

    def clean_category(self):
        category = self.cleaned_data.get('category')
        if category is not None and self.workspace is not None:
            workspace_id = getattr(self.workspace, 'pk', self.workspace)
            if category.workspace_id != workspace_id:
                raise ValidationError(
                    'A categoria deve pertencer ao mesmo workspace.',
                )
        return category

    def clean_estimated_minutes(self):
        estimated_minutes = self.cleaned_data.get('estimated_minutes')
        if estimated_minutes is not None and estimated_minutes < 1:
            raise ValidationError('A estimativa deve ser maior que zero.')
        return estimated_minutes
