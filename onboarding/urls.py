'''Onboarding URL routes.'''

from django.urls import path

from .views import (
    AreasStepView,
    FocusStepView,
    NameStepView,
    OnboardingCompleteView,
    OnboardingSkipView,
    OnboardingStartView,
    RoutineStepView,
    TaskStepView,
)


app_name = 'onboarding'

urlpatterns = [
    path('', OnboardingStartView.as_view(), name='start'),
    path('nome/', NameStepView.as_view(), name='name'),
    path('areas/', AreasStepView.as_view(), name='areas'),
    path('foco/', FocusStepView.as_view(), name='focus'),
    path('primeira-tarefa/', TaskStepView.as_view(), name='task'),
    path('rotina/', RoutineStepView.as_view(), name='routine'),
    path('pular/', OnboardingSkipView.as_view(), name='skip'),
    path('concluido/', OnboardingCompleteView.as_view(), name='complete'),
]
