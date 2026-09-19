from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver
from .models import Task, TaskActivity


@receiver(pre_save, sender=Task)
def track_task_field_changes(sender, instance: Task, **kwargs) -> None:
    """Cache previous field values to log in post_save."""
    if instance.pk:
        try:
            previous = Task.objects.get(pk=instance.pk)
            instance._previous_status = previous.status
            instance._previous_assignee_id = previous.assignee_id
        except Task.DoesNotExist:
            instance._previous_status = None
            instance._previous_assignee_id = None
    else:
        instance._previous_status = None
        instance._previous_assignee_id = None


@receiver(post_save, sender=Task)
def log_task_activity(sender, instance: Task, created: bool, **kwargs) -> None:
    """Create audit log entry for task creation and key updates."""
    if created:
        TaskActivity.objects.create(
            task=instance,
            user=instance.creator,
            action='created',
            note=f"Task created with status '{instance.get_status_display()}'"
        )
    else:
        # Check status change
        prev_status = getattr(instance, '_previous_status', None)
        if prev_status and prev_status != instance.status:
            TaskActivity.objects.create(
                task=instance,
                user=getattr(instance, '_actor', None) or instance.creator,
                action='status_changed',
                field_name='status',
                old_value=prev_status,
                new_value=instance.status,
                note=f"Status changed from {prev_status} to {instance.status}"
            )

        # Check assignee change
        prev_assignee_id = getattr(instance, '_previous_assignee_id', None)
        if prev_assignee_id != instance.assignee_id:
            old_name = str(prev_assignee_id) if prev_assignee_id else 'Unassigned'
            new_name = instance.assignee.username if instance.assignee else 'Unassigned'
            TaskActivity.objects.create(
                task=instance,
                user=getattr(instance, '_actor', None) or instance.creator,
                action='assignee_changed',
                field_name='assignee',
                old_value=old_name,
                new_value=new_name,
                note=f"Assignee changed to {new_name}"
            )
