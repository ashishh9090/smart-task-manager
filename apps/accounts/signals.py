from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from .models import UserProfile


@receiver(post_save, sender=User)
def create_or_save_user_profile(sender, instance: User, created: bool, **kwargs) -> None:
    """
    Ensures that every User instance has a corresponding UserProfile.
    """
    if created:
        UserProfile.objects.create(user=instance)
    else:
        # Save profile if it exists, or create if missing (e.g. for existing users)
        UserProfile.objects.get_or_create(user=instance)
