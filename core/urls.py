'''URL configuration for the ENGP project.'''

from django.contrib import admin
from django.urls import include, path

from core.views import health
from accounts.views import root


urlpatterns = [
    path('', root, name='home'),
    path('health/', health, name='health'),
    path('admin/', admin.site.urls),
    path('conta/', include('accounts.urls')),
]
