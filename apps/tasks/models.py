from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.utils.text import slugify
from django.urls import reverse
from datetime import timedelta
from apps.projects.models import Project


class Tag(models.Model):
    """
    Categorization tag for tasks with customized display color.
    """
    name = models.CharField(max_length=50, unique=True)
    slug = models.SlugField(max_length=60, unique=True, blank=True)
    color = models.CharField(max_length=20, default='#6366f1', help_text="Hex color code (e.g. #3b82f6)")

    class Meta:
        ordering = ['name']
        verbose_name = 'Tag'
        verbose_name_plural = 'Tags'

    def __str__(self) -> str:
        return self.name

    def save(self, *args, **kwargs) -> None:
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class Task(models.Model):
    """
    Task model representing an actionable item inside a project.
    """
    STATUS_TODO = 'todo'
    STATUS_IN_PROGRESS = 'in_progress'
    STATUS_REVIEW = 'review'
    STATUS_DONE = 'done'

    STATUS_CHOICES = [
        (STATUS_TODO, 'To Do'),
        (STATUS_IN_PROGRESS, 'In Progress'),
        (STATUS_REVIEW, 'In Review'),
        (STATUS_DONE, 'Done'),
    ]

    PRIORITY_LOW = 'low'
    PRIORITY_MEDIUM = 'medium'
    PRIORITY_HIGH = 'high'
    PRIORITY_URGENT = 'urgent'

    PRIORITY_CHOICES = [
        (PRIORITY_LOW, 'Low'),
        (PRIORITY_MEDIUM, 'Medium'),
        (PRIORITY_HIGH, 'High'),
        (PRIORITY_URGENT, 'Urgent'),
    ]

    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, default='')
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='tasks')
    creator = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_tasks')
    assignee = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_tasks')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_TODO)
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default=PRIORITY_MEDIUM)
    due_date = models.DateTimeField(null=True, blank=True)
    tags = models.ManyToManyField(Tag, blank=True, related_name='tasks')
    is_archived = models.BooleanField(default=False)
    reminder_sent_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-priority', 'due_date', '-created_at']
        verbose_name = 'Task'
        verbose_name_plural = 'Tasks'

    def __str__(self) -> str:
        return f"[{self.project.title}] {self.title}"

    def get_absolute_url(self) -> str:
        return reverse('tasks:detail', kwargs={'pk': self.pk})

    @property
    def is_overdue(self) -> bool:
        if self.due_date and self.status != self.STATUS_DONE:
            return self.due_date < timezone.now()
        return False

    @property
    def is_due_soon(self) -> bool:
        """Due within the next 24 hours."""
        if self.due_date and self.status != self.STATUS_DONE:
            now = timezone.now()
            return now <= self.due_date <= now + timedelta(hours=24)
        return False

    @property
    def status_badge_class(self) -> str:
        mapping = {
            self.STATUS_TODO: 'bg-secondary',
            self.STATUS_IN_PROGRESS: 'bg-primary',
            self.STATUS_REVIEW: 'bg-warning text-dark',
            self.STATUS_DONE: 'bg-success',
        }
        return mapping.get(self.status, 'bg-secondary')

    @property
    def priority_badge_class(self) -> str:
        mapping = {
            self.PRIORITY_LOW: 'badge-priority-low',
            self.PRIORITY_MEDIUM: 'badge-priority-medium',
            self.PRIORITY_HIGH: 'badge-priority-high',
            self.PRIORITY_URGENT: 'badge-priority-urgent',
        }
        return mapping.get(self.priority, 'badge-priority-medium')


class TaskActivity(models.Model):
    """
    Audit log documenting history, status transitions, and actions performed on a task.
    """
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='activities')
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='task_activities')
    action = models.CharField(max_length=50)
    field_name = models.CharField(max_length=50, blank=True, default='')
    old_value = models.TextField(blank=True, default='')
    new_value = models.TextField(blank=True, default='')
    note = models.TextField(blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Task Activity'
        verbose_name_plural = 'Task Activities'

    def __str__(self) -> str:
        user_str = self.user.username if self.user else 'System'
        return f"{user_str} {self.action} on {self.task.title} at {self.created_at:%Y-%m-%d %H:%M}"
