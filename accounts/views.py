'''Authentication views and the post-authentication landing page.'''

from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView as DjangoLoginView
from django.contrib.auth.views import LogoutView as DjangoLogoutView
from django.contrib.auth.views import PasswordResetConfirmView
from django.contrib.auth.views import PasswordResetDoneView
from django.contrib.auth.views import PasswordResetView
from django.contrib.auth.views import PasswordResetCompleteView
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.views.generic import FormView

from .forms import EmailAuthenticationForm, SignupForm
from .services import create_account


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
    '''Provide a stable post-login landing until the dashboard sprint.'''

    return render(request, 'accounts/home.html')


def root(request):
    if request.user.is_authenticated:
        return redirect('accounts:home')
    return redirect('accounts:login')
