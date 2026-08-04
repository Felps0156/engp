'''Weekly routine URL routes.'''

from django.urls import path

from .views import (
    RoutineCreateView,
    RoutineDeleteView,
    RoutinePauseView,
    RoutineResumeView,
    RoutineUpdateView,
    RoutineWeeklyView,
)


app_name = 'routines'

urlpatterns = [
    path('', RoutineWeeklyView.as_view(), name='weekly'),
    path('novo/', RoutineCreateView.as_view(), name='create'),
    path('<int:pk>/editar/', RoutineUpdateView.as_view(), name='update'),
    path('<int:pk>/pausar/', RoutinePauseView.as_view(), name='pause'),
    path('<int:pk>/reativar/', RoutineResumeView.as_view(), name='resume'),
    path('<int:pk>/excluir/', RoutineDeleteView.as_view(), name='delete'),
]
