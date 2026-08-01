'''Authentication views and the post-authentication landing page.'''

from django.contrib import messages
from django.contrib.auth import login, update_session_auth_hash
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView as DjangoLoginView
from django.contrib.auth.views import LogoutView as DjangoLogoutView
from django.contrib.auth.views import PasswordResetConfirmView
from django.contrib.auth.views import PasswordResetDoneView
from django.contrib.auth.views import PasswordResetView
from django.contrib.auth.views import PasswordResetCompleteView
from django.db import IntegrityError, transaction
from django.shortcuts import redirect, render
from django.urls import reverse, reverse_lazy
from django.views.generic import FormView, TemplateView

from .forms import (
    AccountPasswordChangeForm,
    EmailAuthenticationForm,
    EmailChangeForm,
    PreferencesSettingsForm,
    ProfileSettingsForm,
    SignupForm,
)
from .models import User
from .services import create_account, get_or_create_user_settings


class SignupView(FormView):
    '''Create the account and its initial workspace in one transaction.'''

    form_class = SignupForm
    template_name = 'registration/signup.html'
    success_url = reverse_lazy('accounts:home')

    def form_valid(self, form):
        user, _workspace = create_account(
            email=form.cleaned_data['email'],
            password=form.cleaned_data['password1'],
            first_name=form.cleaned_data.get('first_name', ''),
            last_name=form.cleaned_data.get('last_name', ''),
        )
        login(self.request, user)
        messages.success(
            self.request,
            'Sua conta e seu workspace pessoal foram criados.',
        )
        return super().form_valid(form)


class LoginView(DjangoLoginView):
    '''Authenticate with the native Django session using e-mail.'''

    authentication_form = EmailAuthenticationForm
    template_name = 'registration/login.html'
    redirect_authenticated_user = True

    def get_success_url(self):
        user_settings = get_or_create_user_settings(user=self.request.user)
        if not user_settings.onboarding_completed:
            return reverse('onboarding:start')
        return super().get_success_url()

    def form_valid(self, form):
        user = form.get_user()
        messages.success(
            self.request,
            f'Bem-vindo de volta, {user.get_short_name() or user.email}.',
        )
        return super().form_valid(form)


class LogoutView(DjangoLogoutView):
    '''End sessions through the POST-only native Django logout view.'''

    next_page = reverse_lazy('accounts:login')
    template_name = 'registration/logged_out.html'

    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        messages.success(request, 'Você saiu da sua conta.')
        return response


class AccountPasswordResetView(PasswordResetView):
    '''Use Django's password reset flow with ENGP templates.'''

    template_name = 'registration/password_reset_form.html'
    email_template_name = 'registration/password_reset_email.txt'
    html_email_template_name = 'registration/password_reset_email.html'
    subject_template_name = 'registration/password_reset_subject.txt'
    success_url = reverse_lazy('accounts:password_reset_done')
    title = 'Recuperar senha'


class AccountPasswordResetDoneView(PasswordResetDoneView):
    template_name = 'registration/password_reset_done.html'
    title = 'E-mail enviado'


class AccountPasswordResetConfirmView(PasswordResetConfirmView):
    template_name = 'registration/password_reset_confirm.html'
    success_url = reverse_lazy('accounts:password_reset_complete')
    title = 'Criar nova senha'


class AccountPasswordResetCompleteView(PasswordResetCompleteView):
    template_name = 'registration/password_reset_complete.html'
    title = 'Senha atualizada'


@login_required
def account_home(request):
    '''Send users through onboarding before showing the account landing page.'''

    user_settings = get_or_create_user_settings(user=request.user)
    if not user_settings.onboarding_completed:
        return redirect('onboarding:start')

    return render(request, 'accounts/home.html')


def settings_context(request):
    '''Build the settings page forms for the current authenticated user.'''

    user_settings = get_or_create_user_settings(user=request.user)
    return {
        'user_settings': user_settings,
        'profile_form': ProfileSettingsForm(instance=request.user),
        'preferences_form': PreferencesSettingsForm(instance=user_settings),
        'email_form': EmailChangeForm(user=request.user),
        'password_form': AccountPasswordChangeForm(user=request.user),
    }


class AccountSettingsView(LoginRequiredMixin, TemplateView):
    '''Display account, preference and security forms in one screen.'''

    template_name = 'accounts/settings.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(settings_context(self.request))
        return context


class SettingsFormView(LoginRequiredMixin, FormView):
    '''Render a bound settings section alongside the other settings forms.'''

    template_name = 'accounts/settings.html'
    http_method_names = ('post', 'options')
    success_url = reverse_lazy('accounts:settings')
    form_context_name = 'form'
    success_message = 'Configurações atualizadas.'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        bound_form = context.pop('form', None)
        context.update(settings_context(self.request))
        if bound_form is not None:
            context[self.form_context_name] = bound_form
        return context

    def form_valid(self, form):
        messages.success(self.request, self.success_message)
        return super().form_valid(form)


class ProfileSettingsView(SettingsFormView):
    '''Update the authenticated user's display name.'''

    form_class = ProfileSettingsForm
    form_context_name = 'profile_form'
    success_message = 'Seu nome foi atualizado.'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['instance'] = self.request.user
        return kwargs

    def form_valid(self, form):
        form.save()
        return super().form_valid(form)


class PreferencesSettingsView(SettingsFormView):
    '''Update theme, focus defaults, sound and localization preferences.'''

    form_class = PreferencesSettingsForm
    form_context_name = 'preferences_form'
    success_message = 'Suas preferências foram atualizadas.'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['instance'] = get_or_create_user_settings(user=self.request.user)
        return kwargs

    def form_valid(self, form):
        form.save()
        return super().form_valid(form)


class EmailSettingsView(SettingsFormView):
    '''Change the account e-mail after checking the current password.'''

    form_class = EmailChangeForm
    form_context_name = 'email_form'
    success_message = 'Seu e-mail foi atualizado.'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        try:
            with transaction.atomic():
                user = User.objects.select_for_update().get(
                    pk=self.request.user.pk,
                )
                if not user.check_password(form.cleaned_data['current_password']):
                    form.add_error(
                        'current_password',
                        'A senha atual está incorreta.',
                    )
                    return self.form_invalid(form)
                user.email = form.cleaned_data['new_email']
                user.save(update_fields=('email', 'updated_at'))
        except IntegrityError:
            form.add_error(
                'new_email',
                'Já existe uma conta com este e-mail.',
            )
            return self.form_invalid(form)

        return super().form_valid(form)


class PasswordSettingsView(SettingsFormView):
    '''Change the password while preserving the current authenticated session.'''

    form_class = AccountPasswordChangeForm
    form_context_name = 'password_form'
    success_message = 'Sua senha foi alterada.'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        user = form.save()
        update_session_auth_hash(self.request, user)
        return super().form_valid(form)


def root(request):
    if request.user.is_authenticated:
        return redirect('accounts:home')
    return redirect('accounts:login')
