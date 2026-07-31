'''Authentication forms with Portuguese labels and e-mail identity.'''

from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import AuthenticationForm, BaseUserCreationForm
from django.core.exceptions import ValidationError


User = get_user_model()


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
