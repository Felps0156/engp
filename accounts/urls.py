'''Authentication URL routes.'''

from django.urls import path

from .views import (
    AccountPasswordResetCompleteView,
    AccountPasswordResetConfirmView,
    AccountPasswordResetDoneView,
    AccountPasswordResetView,
    LoginView,
    LogoutView,
    SignupView,
    account_home,
)


app_name = 'accounts'

urlpatterns = [
    path('', account_home, name='home'),
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('cadastro/', SignupView.as_view(), name='signup'),
    path(
        'senha/redefinir/',
        AccountPasswordResetView.as_view(),
        name='password_reset',
    ),
    path(
        'senha/redefinir/enviado/',
        AccountPasswordResetDoneView.as_view(),
        name='password_reset_done',
    ),
    path(
        'senha/redefinir/<uidb64>/<token>/',
        AccountPasswordResetConfirmView.as_view(),
        name='password_reset_confirm',
    ),
    path(
        'senha/redefinir/concluido/',
        AccountPasswordResetCompleteView.as_view(),
        name='password_reset_complete',
    ),
]
