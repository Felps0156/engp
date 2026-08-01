'''Forms for the guided onboarding steps.'''

from django import forms
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator

from accounts.models import UserSettings
from categories.models import Category


User = get_user_model()


class OnboardingNameForm(forms.ModelForm):
    '''Collect the name used in greetings and the personal workspace.'''

    class Meta:
        model = User
        fields = ('first_name', 'last_name')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['first_name'].label = 'Nome'
        self.fields['first_name'].required = True
        self.fields['first_name'].widget.attrs.update(
            {
                'autocomplete': 'given-name',
                'placeholder': 'Como podemos chamar você?',
                'maxlength': 150,
            },
        )
        self.fields['last_name'].label = 'Sobrenome'
        self.fields['last_name'].widget.attrs.update(
            {
                'autocomplete': 'family-name',
                'placeholder': 'Opcional',
                'maxlength': 150,
            },
        )

    def clean_first_name(self):
        name = self.cleaned_data['first_name'].strip()
        if not name:
            raise ValidationError('Informe seu nome para continuar.')
        return name

    def clean_last_name(self):
        return self.cleaned_data['last_name'].strip()


class OnboardingAreasForm(forms.Form):
    '''Select existing categories and optionally add new workspace areas.'''

    areas = forms.ModelMultipleChoiceField(
        label='Áreas principais',
        queryset=Category.objects.none(),
        required=False,
        widget=forms.CheckboxSelectMultiple,
    )
    custom_areas = forms.CharField(
        label='Adicionar outras áreas',
        required=False,
        max_length=500,
        widget=forms.Textarea(
            attrs={
                'rows': 3,
                'placeholder': 'Ex.: Projetos pessoais, leitura\nUma por linha ou separadas por vírgula',
            },
        ),
    )

    def __init__(self, *args, workspace=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.workspace = workspace
        self.fields['areas'].queryset = Category.objects.filter(
            workspace=workspace,
            is_active=True,
        ).order_by('name', 'pk')

    def clean_custom_areas(self):
        raw_value = self.cleaned_data.get('custom_areas', '')
        names = []
        seen = set()
        for raw_name in raw_value.replace(';', '\n').replace(',', '\n').splitlines():
            name = raw_name.strip()
            key = name.casefold()
            if name and key not in seen:
                if len(name) > 80:
                    raise ValidationError('Cada área pode ter no máximo 80 caracteres.')
                names.append(name)
                seen.add(key)
        return names

    def clean(self):
        cleaned_data = super().clean()
        selected = cleaned_data.get('areas')
        custom_areas = cleaned_data.get('custom_areas') or []
        if not selected and not custom_areas:
            raise ValidationError('Selecione ou adicione ao menos uma área.')
        return cleaned_data


class OnboardingFocusForm(forms.ModelForm):
    '''Set the default focus duration using the existing preference model.'''

    class Meta:
        model = UserSettings
        fields = ('default_focus_minutes',)
        widgets = {
            'default_focus_minutes': forms.NumberInput(
                attrs={
                    'min': 1,
                    'max': 180,
                    'inputmode': 'numeric',
                    'placeholder': '25',
                },
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['default_focus_minutes'].label = 'Duração padrão do foco'
        self.fields['default_focus_minutes'].help_text = 'Entre 1 e 180 minutos. Você poderá ajustar depois.'


class OnboardingTaskForm(forms.Form):
    '''Capture the first actionable task before the task domain is introduced.'''

    title = forms.CharField(
        label='Qual é a próxima ação?',
        max_length=180,
        widget=forms.TextInput(
            attrs={
                'autocomplete': 'off',
                'placeholder': 'Ex.: Marcar consulta com o dentista',
                'maxlength': 180,
            },
        ),
    )
    description = forms.CharField(
        label='Detalhes (opcional)',
        required=False,
        widget=forms.Textarea(
            attrs={
                'rows': 4,
                'placeholder': 'Algum contexto que ajude você a começar?',
            },
        ),
    )

    def clean_title(self):
        title = self.cleaned_data['title'].strip()
        if not title:
            raise ValidationError('Informe uma primeira tarefa para continuar.')
        return title

    def clean_description(self):
        return self.cleaned_data['description'].strip()


class OnboardingRoutineForm(forms.Form):
    '''Optionally capture a weekly routine item for later routine generation.'''

    WEEKDAY_CHOICES = (
        ('0', 'Segunda-feira'),
        ('1', 'Terça-feira'),
        ('2', 'Quarta-feira'),
        ('3', 'Quinta-feira'),
        ('4', 'Sexta-feira'),
        ('5', 'Sábado'),
        ('6', 'Domingo'),
    )

    title = forms.CharField(
        label='Nome do item de rotina',
        required=False,
        max_length=180,
        widget=forms.TextInput(
            attrs={
                'autocomplete': 'off',
                'placeholder': 'Ex.: Caminhar pela manhã',
                'maxlength': 180,
            },
        ),
    )
    weekdays = forms.MultipleChoiceField(
        label='Dias da semana',
        required=False,
        choices=WEEKDAY_CHOICES,
        widget=forms.CheckboxSelectMultiple,
    )
    scheduled_time = forms.TimeField(
        label='Horário (opcional)',
        required=False,
        input_formats=('%H:%M',),
        widget=forms.TimeInput(
            format='%H:%M',
            attrs={'type': 'time'},
        ),
    )
    estimated_minutes = forms.IntegerField(
        label='Duração estimada (opcional)',
        required=False,
        validators=(MinValueValidator(1), MaxValueValidator(180)),
        widget=forms.NumberInput(
            attrs={
                'min': 1,
                'max': 180,
                'inputmode': 'numeric',
                'placeholder': '25',
            },
        ),
    )

    def clean_title(self):
        return self.cleaned_data['title'].strip()

    def clean(self):
        cleaned_data = super().clean()
        title = cleaned_data.get('title', '')
        weekdays = cleaned_data.get('weekdays') or []
        if title and not weekdays:
            self.add_error('weekdays', 'Escolha ao menos um dia para a rotina.')
        if not title:
            cleaned_data['weekdays'] = []
            cleaned_data['scheduled_time'] = None
            cleaned_data['estimated_minutes'] = None
        return cleaned_data
