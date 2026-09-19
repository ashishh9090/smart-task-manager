from django.urls import path
from . import views

app_name = 'tasks'

urlpatterns = [
    path('', views.task_list, name='list'),
    path('new/', views.task_create, name='create'),
    path('kanban/', views.kanban_board, name='kanban'),
    path('<int:pk>/', views.task_detail, name='detail'),
    path('<int:pk>/edit/', views.task_edit, name='edit'),
    path('<int:pk>/delete/', views.task_delete, name='delete'),
    path('<int:pk>/status/', views.task_update_status_api, name='update_status'),
]
