'''Authentication forms with Portuguese labels and e-mail identity.'''

from zoneinfo import available_timezones

from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import AuthenticationForm, BaseUserCreationForm
from django.contrib.auth.forms import PasswordChangeForm
from django.core.exceptions import ValidationError

from .models import UserSettings


User = get_user_model()


def timezone_choices():
    '''Return all IANA zones with the product default shown first.'''

    preferred = ('America/Sao_Paulo', 'UTC')
    zones = sorted(available_timezones() - set(preferred))
    return [(zone, zone) for zone in (*preferred, *zones)]


class SignupForm(BaseUserCreationForm):
    '''Validate the public account creation form.'''

    class Meta:
        model = User
        fields = ('email', 'first_name', 'last_name')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['email'].label = 'E-mail'
        self.fields['email'].widget.attrs.update(
            {
                'autocomplete': 'email',
                'placeholder': 'voce@exemplo.com',
            },
        )
        self.fields['first_name'].label = 'Nome'
        self.fields['first_name'].widget.attrs.update(
            {
                'autocomplete': 'given-name',
                'placeholder': 'Como podemos chamar você?',
            },
        )
        self.fields['last_name'].label = 'Sobrenome'
        self.fields['last_name'].widget.attrs.update(
            {
                'autocomplete': 'family-name',
                'placeholder': 'Opcional',
            },
        )
        self.fields['password1'].label = 'Senha'
        self.fields['password2'].label = 'Confirme sua senha'

    def clean_email(self):
        email = User.objects.normalize_email(self.cleaned_data['email'])
        if User.objects.filter(email__iexact=email).exists():
            raise ValidationError('Já existe uma conta com este e-mail.')
        return email


class EmailAuthenticationForm(AuthenticationForm):
    '''Replace Django's username field with an explicit e-mail field.'''

    email = forms.EmailField(
        label='E-mail',
        widget=forms.EmailInput(
            attrs={
                'autocomplete': 'email',
                'autofocus': True,
                'placeholder': 'voce@exemplo.com',
            },
        ),
    )
    password = forms.CharField(
        label='Senha',
        strip=False,
        widget=forms.PasswordInput(
            attrs={
                'autocomplete': 'current-password',
                'placeholder': 'Sua senha',
            },
        ),
    )
    error_messages = {
        'invalid_login': 'E-mail ou senha inválidos.',
        'inactive': 'Esta conta está inativa.',
    }

    def __init__(self, request=None, *args, **kwargs):
        super().__init__(request, *args, **kwargs)
        self.fields.pop('username', None)
        self.username_field = User._meta.get_field(User.USERNAME_FIELD)

    def clean(self):
        email = self.cleaned_data.get('email')
        password = self.cleaned_data.get('password')

        if email is not None and password:
            from django.contrib.auth import authenticate

            self.user_cache = authenticate(
                self.request,
                email=User.objects.normalize_email(email),
                password=password,
            )
            if self.user_cache is None:
                raise self.get_invalid_login_error()
            self.confirm_login_allowed(self.user_cache)

        return self.cleaned_data


class ProfileSettingsForm(forms.ModelForm):
    '''Edit the personal name displayed throughout the application.'''

    class Meta:
        model = User
        fields = ('first_name', 'last_name')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['first_name'].label = 'Nome'
        self.fields['first_name'].widget.attrs.update(
            {
                'autocomplete': 'given-name',
                'placeholder': 'Como podemos chamar você?',
            },
        )
        self.fields['last_name'].label = 'Sobrenome'
        self.fields['last_name'].widget.attrs.update(
            {
                'autocomplete': 'family-name',
                'placeholder': 'Opcional',
            },
        )

    def clean_first_name(self):
        return self.cleaned_data['first_name'].strip()

    def clean_last_name(self):
        return self.cleaned_data['last_name'].strip()


class PreferencesSettingsForm(forms.ModelForm):
    '''Validate appearance, focus and localization preferences.'''

    class Meta:
        model = UserSettings
        fields = (
            'theme',
            'default_focus_minutes',
            'default_break_minutes',
            'focus_end_sound_enabled',
            'timezone',
            'date_format',
            'time_format',
        )
        widgets = {
            'default_focus_minutes': forms.NumberInput(
                attrs={'min': 1, 'max': 180, 'inputmode': 'numeric'},
            ),
            'default_break_minutes': forms.NumberInput(
                attrs={'min': 1, 'max': 60, 'inputmode': 'numeric'},
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['theme'].label = 'Tema'
        self.fields['default_focus_minutes'].label = 'Foco padrão (minutos)'
        self.fields['default_break_minutes'].label = 'Pausa padrão (minutos)'
        self.fields['focus_end_sound_enabled'].label = 'Tocar som ao encerrar o foco'
        self.fields['timezone'].label = 'Fuso horário'
        self.fields['timezone'].choices = timezone_choices()
        self.fields['date_format'].label = 'Formato de data'
        self.fields['time_format'].label = 'Formato de horário'


class EmailChangeForm(forms.Form):
    '''Require the current password before changing the account e-mail.'''

    new_email = forms.EmailField(
        label='Novo e-mail',
        widget=forms.EmailInput(
            attrs={
                'autocomplete': 'email',
                'placeholder': 'voce@exemplo.com',
            },
        ),
    )
    current_password = forms.CharField(
        label='Senha atual',
        strip=False,
        widget=forms.PasswordInput(
            attrs={'autocomplete': 'current-password'},
        ),
    )

    def __init__(self, *args, user, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user

    def clean_new_email(self):
        email = User.objects.normalize_email(self.cleaned_data['new_email'])
        if email == self.user.email:
            raise ValidationError('Informe um e-mail diferente do atual.')
        if User.objects.filter(email__iexact=email).exclude(pk=self.user.pk).exists():
            raise ValidationError('Já existe uma conta com este e-mail.')
        return email

    def clean_current_password(self):
        password = self.cleaned_data['current_password']
        if not self.user.check_password(password):
            raise ValidationError('A senha atual está incorreta.')
        return password


class AccountPasswordChangeForm(PasswordChangeForm):
    '''Apply Portuguese labels and browser hints to Django's native form.'''

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['old_password'].label = 'Senha atual'
        self.fields['old_password'].widget.attrs['autocomplete'] = 'current-password'
        self.fields['new_password1'].label = 'Nova senha'
        self.fields['new_password1'].widget.attrs['autocomplete'] = 'new-password'
        self.fields['new_password2'].label = 'Confirme a nova senha'
        self.fields['new_password2'].widget.attrs['autocomplete'] = 'new-password'
