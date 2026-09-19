from django.contrib import admin
from .models import Project, ProjectMember


class ProjectMemberInline(admin.TabularInline):
    model = ProjectMember
    extra = 1
    autocomplete_fields = ['user']


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ('title', 'owner', 'status', 'created_at', 'updated_at')
    list_filter = ('status', 'created_at')
    search_fields = ('title', 'description', 'owner__username')
    inlines = [ProjectMemberInline]
    date_hierarchy = 'created_at'


@admin.register(ProjectMember)
class ProjectMemberAdmin(admin.ModelAdmin):
    list_display = ('user', 'project', 'role', 'joined_at')
    list_filter = ('role', 'joined_at')
    search_fields = ('user__username', 'project__title')
