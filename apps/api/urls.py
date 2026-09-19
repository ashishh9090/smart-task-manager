from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

app_name = 'api'

router = DefaultRouter()
router.register(r'projects', views.ProjectViewSet, basename='project')
router.register(r'tasks', views.TaskViewSet, basename='task')
router.register(r'tags', views.TagViewSet, basename='tag')

urlpatterns = [
    path('', include(router.urls)),
    path('auth/profile/', views.UserProfileView.as_view(), name='user-profile'),
    path('dashboard/stats/', views.DashboardStatsView.as_view(), name='dashboard-stats'),
]
