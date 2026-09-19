from django.urls import path
from . import views

app_name = 'projects'

urlpatterns = [
    path('', views.project_list, name='list'),
    path('new/', views.project_create, name='create'),
    path('<int:pk>/', views.project_detail, name='detail'),
    path('<int:pk>/edit/', views.project_edit, name='edit'),
    path('<int:pk>/delete/', views.project_delete, name='delete'),
    path('<int:pk>/archive/', views.project_archive_toggle, name='archive_toggle'),
    path('<int:pk>/members/add/', views.project_member_add, name='member_add'),
    path('<int:pk>/members/<int:member_id>/remove/', views.project_member_remove, name='member_remove'),
]
