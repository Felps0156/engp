'''Task interface URL routes.'''

from django.urls import path

from .views import (
    TaskCompletedView,
    TaskCompleteView,
    TaskDeleteView,
    TaskInboxView,
    TaskMoveView,
    TaskPlanTodayView,
    TaskReopenView,
    TaskTodayView,
    TaskUpdateView,
    TaskWeekView,
)


app_name = 'tasks'

urlpatterns = [
    path('', TaskInboxView.as_view(), name='inbox'),
    path('hoje/', TaskTodayView.as_view(), name='today'),
    path('esta-semana/', TaskWeekView.as_view(), name='week'),
    path('concluidas/', TaskCompletedView.as_view(), name='completed'),
    path('<int:pk>/editar/', TaskUpdateView.as_view(), name='update'),
    path('<int:pk>/concluir/', TaskCompleteView.as_view(), name='complete'),
    path('<int:pk>/reabrir/', TaskReopenView.as_view(), name='reopen'),
    path('<int:pk>/hoje/', TaskPlanTodayView.as_view(), name='plan_today'),
    path('<int:pk>/mover/', TaskMoveView.as_view(), name='move'),
    path('<int:pk>/excluir/', TaskDeleteView.as_view(), name='delete'),
]
