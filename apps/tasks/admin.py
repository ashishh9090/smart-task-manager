from django.contrib import admin
from .models import Tag, Task, TaskActivity


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'color')
    search_fields = ('name', 'slug')
    prepopulated_fields = {'slug': ('name',)}


class TaskActivityInline(admin.TabularInline):
    model = TaskActivity
    extra = 0
    readonly_fields = ('user', 'action', 'field_name', 'old_value', 'new_value', 'note', 'created_at')
    can_delete = False


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ('title', 'project', 'assignee', 'status', 'priority', 'due_date', 'created_at')
    list_filter = ('status', 'priority', 'project', 'created_at', 'due_date')
    search_fields = ('title', 'description', 'assignee__username', 'project__title')
    filter_horizontal = ('tags',)
    inlines = [TaskActivityInline]
    date_hierarchy = 'created_at'


@admin.register(TaskActivity)
class TaskActivityAdmin(admin.ModelAdmin):
    list_display = ('task', 'user', 'action', 'field_name', 'created_at')
    list_filter = ('action', 'created_at')
    search_fields = ('task__title', 'user__username', 'note')
