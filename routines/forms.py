'''Forms for weekly routine planning.'''

from django import forms
from django.core.exceptions import ValidationError
from django.db.models import Q
from django.utils import timezone

from categories.models import Category

from .models import WeeklyRoutineItem


class RoutineItemForm(forms.ModelForm):
    '''Validate recurring routine input while keeping it tenant-aware.'''

    class Meta:
        model = WeeklyRoutineItem
        fields = (
            'title',
            'category',
            'scheduled_time',
            'estimated_minutes',
            'priority',
        )
        widgets = {
            'title': forms.TextInput(
                attrs={
                    'autocomplete': 'off',
                    'placeholder': 'Ex.: Caminhar pela manhã',
                    'maxlength': 180,
                },
            ),
            'scheduled_time': forms.TimeInput(
                format='%H:%M',
                attrs={'type': 'time'},
            ),
            'estimated_minutes': forms.NumberInput(
                attrs={'min': 1, 'inputmode': 'numeric'},
            ),
        }

    def __init__(self, *args, workspace=None, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.workspace = workspace or getattr(self.instance, 'workspace', None)
        self.user = user
        self.instance.weekdays = list(range(7))

        if self.workspace is not None and not self.instance.workspace_id:
            self.instance.workspace = self.workspace
        if self.user is not None and not self.instance.created_by_id:
            self.instance.created_by = self.user

        categories = Category.objects.filter(
            workspace=self.workspace,
            is_active=True,
        )
        if self.instance.category_id:
            categories = Category.objects.filter(
                workspace=self.workspace,
            ).filter(Q(is_active=True) | Q(pk=self.instance.category_id))
        self.fields['category'].queryset = categories.order_by('name', 'pk')

        labels = {
            'title': 'Nome do hábito',
            'category': 'Categoria',
            'scheduled_time': 'Horário (opcional)',
            'estimated_minutes': 'Duração estimada (minutos)',
            'priority': 'Prioridade',
        }
        for field_name, label in labels.items():
            if field_name in self.fields:
                self.fields[field_name].label = label
        if 'category' in self.fields:
            self.fields['category'].empty_label = 'Sem categoria'

    def clean_title(self):
        title = self.cleaned_data['title'].strip()
        if not title:
            raise ValidationError('Informe um título para a rotina.')
        return title

    def clean_category(self):
        category = self.cleaned_data.get('category')
        if category is not None and self.workspace is not None:
            workspace_id = getattr(self.workspace, 'pk', self.workspace)
            if category.workspace_id != workspace_id:
                raise ValidationError(
                    'A categoria deve pertencer ao mesmo workspace.',
                )
        return category

    def save(self, commit=True):
        item = super().save(commit=False)
        item.weekdays = list(range(7))
        if not item.pk:
            item.starts_on = timezone.localdate().replace(day=1)
            item.ends_on = None
        if commit:
            item.save()
        return item


class RoutineQuickCreateForm(RoutineItemForm):
    '''Minimal daily-habit form used by the in-page creation dialog.'''

    class Meta(RoutineItemForm.Meta):
        fields = ('title', 'category')
