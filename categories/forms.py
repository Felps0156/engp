'''Forms for workspace categories.'''

from django import forms
from django.core.exceptions import ValidationError

from .models import Category


class CategoryForm(forms.ModelForm):
    '''Validate a category without exposing its tenant in client input.'''

    class Meta:
        model = Category
        fields = ('name', 'color_token')
        widgets = {
            'name': forms.TextInput(
                attrs={
                    'autocomplete': 'off',
                    'placeholder': 'Ex.: Saúde, estudos, projetos...',
                    'maxlength': 80,
                },
            ),
        }

    def __init__(self, *args, workspace=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.workspace = workspace or getattr(self.instance, 'workspace', None)
        if self.workspace is not None and not self.instance.workspace_id:
            self.instance.workspace = self.workspace
        self.fields['name'].label = 'Nome da categoria'
        self.fields['color_token'].label = 'Cor'

    def clean_name(self):
        name = self.cleaned_data['name'].strip()
        if not name:
            raise ValidationError('Informe um nome para a categoria.')
        categories = Category.objects.filter(
            workspace=self.workspace,
            name__iexact=name,
        )
        if self.instance.pk:
            categories = categories.exclude(pk=self.instance.pk)
        if categories.exists():
            raise ValidationError('Já existe uma categoria com este nome.')
        return name
