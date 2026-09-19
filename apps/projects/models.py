from django.db import models
from django.contrib.auth.models import User
from django.urls import reverse


class Project(models.Model):
    """
    Project model containing tasks, with role-based member permissions.
    """
    STATUS_ACTIVE = 'active'
    STATUS_ARCHIVED = 'archived'
    STATUS_COMPLETED = 'completed'

    STATUS_CHOICES = [
        (STATUS_ACTIVE, 'Active'),
        (STATUS_ARCHIVED, 'Archived'),
        (STATUS_COMPLETED, 'Completed'),
    ]

    title = models.CharField(max_length=200)
    description = models.TextField(blank=True, default='')
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='owned_projects')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_ACTIVE)
    color = models.CharField(max_length=20, default='#4f46e5', help_text="Hex color code for UI accents")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at', 'title']
        verbose_name = 'Project'
        verbose_name_plural = 'Projects'

    def __str__(self) -> str:
        return self.title

    def get_absolute_url(self) -> str:
        return reverse('projects:detail', kwargs={'pk': self.pk})

    def is_member(self, user: User) -> bool:
        """Check if a given user is an owner or member of this project."""
        if not user or not user.is_authenticated:
            return False
        if self.owner_id == user.id or user.is_superuser:
            return True
        return self.memberships.filter(user=user).exists()

    def get_user_role(self, user: User) -> str | None:
        """Return the role of the user within this project."""
        if not user or not user.is_authenticated:
            return None
        if self.owner_id == user.id or user.is_superuser:
            return 'admin'
        membership = self.memberships.filter(user=user).first()
        return membership.role if membership else None

    def can_edit(self, user: User) -> bool:
        """Admins and Owners can edit project details."""
        role = self.get_user_role(user)
        return role in ('admin',)

    def can_manage_tasks(self, user: User) -> bool:
        """Admins and Members can create/edit tasks. Viewers have read-only access."""
        role = self.get_user_role(user)
        return role in ('admin', 'member')


class ProjectMember(models.Model):
    """
    Through model defining user membership and roles in a Project.
    """
    ROLE_ADMIN = 'admin'
    ROLE_MEMBER = 'member'
    ROLE_VIEWER = 'viewer'

    ROLE_CHOICES = [
        (ROLE_ADMIN, 'Project Admin'),
        (ROLE_MEMBER, 'Member'),
        (ROLE_VIEWER, 'Viewer'),
    ]

    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='memberships')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='project_memberships')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default=ROLE_MEMBER)
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('project', 'user')
        ordering = ['role', 'user__username']
        verbose_name = 'Project Member'
        verbose_name_plural = 'Project Members'

    def __str__(self) -> str:
        return f"{self.user.username} ({self.get_role_display()}) in {self.project.title}"
