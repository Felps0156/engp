'''Forms for weekly routine planning.'''

from django import forms
from django.core.exceptions import ValidationError
from django.db.models import Q

from categories.models import Category

from .models import WEEKDAY_CHOICES, WeeklyRoutineItem, normalize_weekdays


class RoutineItemForm(forms.ModelForm):
    '''Validate recurring routine input while keeping it tenant-aware.'''

    weekdays = forms.MultipleChoiceField(
        label='Dias da semana',
        choices=tuple((str(value), label) for value, label in WEEKDAY_CHOICES),
        widget=forms.CheckboxSelectMultiple,
        required=True,
    )

    class Meta:
        model = WeeklyRoutineItem
        fields = (
            'title',
            'category',
            'weekdays',
            'scheduled_time',
            'estimated_minutes',
            'priority',
            'starts_on',
            'ends_on',
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
            'starts_on': forms.DateInput(
                format='%Y-%m-%d',
                attrs={'type': 'date'},
            ),
            'ends_on': forms.DateInput(
                format='%Y-%m-%d',
                attrs={'type': 'date'},
            ),
        }

    def __init__(self, *args, workspace=None, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.workspace = workspace or getattr(self.instance, 'workspace', None)
        self.user = user

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

        self.fields['title'].label = 'Nome do item'
        self.fields['category'].label = 'Categoria'
        self.fields['category'].empty_label = 'Sem categoria'
        self.fields['scheduled_time'].label = 'Horário (opcional)'
        self.fields['estimated_minutes'].label = 'Duração estimada (minutos)'
        self.fields['priority'].label = 'Prioridade'
        self.fields['starts_on'].label = 'Válida a partir de'
        self.fields['ends_on'].label = 'Válida até (opcional)'

        if self.instance.pk:
            self.initial['weekdays'] = [
                str(weekday) for weekday in self.instance.weekdays or []
            ]

    def clean_title(self):
        title = self.cleaned_data['title'].strip()
        if not title:
            raise ValidationError('Informe um título para a rotina.')
        return title

    def clean_weekdays(self):
        try:
            return normalize_weekdays(self.cleaned_data.get('weekdays') or [])
        except ValueError as exc:
            raise ValidationError(str(exc)) from exc

    def clean_category(self):
        category = self.cleaned_data.get('category')
        if category is not None and self.workspace is not None:
            workspace_id = getattr(self.workspace, 'pk', self.workspace)
            if category.workspace_id != workspace_id:
                raise ValidationError(
                    'A categoria deve pertencer ao mesmo workspace.',
                )
        return category

    def clean(self):
        cleaned_data = super().clean()
        starts_on = cleaned_data.get('starts_on')
        ends_on = cleaned_data.get('ends_on')
        if starts_on and ends_on and ends_on < starts_on:
            self.add_error(
                'ends_on',
                'A data final deve ser igual ou posterior ao início.',
            )
        return cleaned_data
