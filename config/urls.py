"""
URL Configuration for Smart Task Manager.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('apps.dashboard.urls', namespace='dashboard')),
    path('accounts/', include('apps.accounts.urls', namespace='accounts')),
    path('projects/', include('apps.projects.urls', namespace='projects')),
    path('tasks/', include('apps.tasks.urls', namespace='tasks')),
    path('api/v1/', include('apps.api.urls', namespace='api')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

handler403 = 'apps.accounts.views.error_403'
handler404 = 'apps.accounts.views.error_404'
handler500 = 'apps.accounts.views.error_500'
