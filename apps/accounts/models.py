from django.db import models
from django.contrib.auth.models import User
import urllib.parse


class UserProfile(models.Model):
    """
    Profile extension for the standard Django User model.
    Stores additional metadata such as avatar, job role, and preferences.
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    avatar = models.ImageField(upload_to='avatars/', null=True, blank=True)
    bio = models.TextField(blank=True, default='', max_length=500)
    job_title = models.CharField(max_length=100, blank=True, default='')
    department = models.CharField(max_length=100, blank=True, default='')
    email_notifications = models.BooleanField(
        default=True,
        help_text="Receive email notifications for deadlines and assignments."
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'User Profile'
        verbose_name_plural = 'User Profiles'
        ordering = ['user__username']

    def __str__(self) -> str:
        return f"{self.user.username}'s profile"

    @property
    def display_name(self) -> str:
        """Return the user's full name or fallback to username."""
        full_name = self.user.get_full_name()
        return full_name if full_name.strip() else self.user.username

    @property
    def avatar_url(self) -> str:
        """
        Return the uploaded avatar URL or a dynamic SVG avatar from ui-avatars.com.
        """
        if self.avatar and hasattr(self.avatar, 'url'):
            return self.avatar.url
        name = urllib.parse.quote(self.display_name)
        return f"https://ui-avatars.com/api/?name={name}&background=4f46e5&color=fff&size=128"
