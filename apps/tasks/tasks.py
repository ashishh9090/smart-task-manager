"""
Celery asynchronous tasks for Task reminders.
"""
import logging
from datetime import timedelta
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings
from celery import shared_task
from .models import Task

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3)
def send_task_deadline_reminders(self) -> dict:
    """
    Periodic task to check for tasks due within the next 24 hours.
    Dispatches reminder emails to assignees who haven't yet received a reminder.
    """
    now = timezone.now()
    cutoff = now + timedelta(hours=24)

    # Query tasks due in next 24h that are not done and haven't had a reminder sent
    upcoming_tasks = Task.objects.filter(
        due_date__gte=now,
        due_date__lte=cutoff,
        reminder_sent_at__isnull=True,
        assignee__isnull=False,
    ).exclude(status=Task.STATUS_DONE).select_related('assignee', 'assignee__profile', 'project')

    sent_count = 0
    skipped_count = 0

    logger.info(f"Scanning for task deadline reminders: found {upcoming_tasks.count()} potential candidates.")

    for task in upcoming_tasks:
        assignee = task.assignee
        # Check if user enabled email notifications
        if hasattr(assignee, 'profile') and not assignee.profile.email_notifications:
            skipped_count += 1
            continue

        recipient_email = assignee.email
        if not recipient_email:
            skipped_count += 1
            continue

        subject = f"⏰ Reminder: Task '{task.title}' is due within 24 hours"
        message = (
            f"Hi {assignee.get_full_name() or assignee.username},\n\n"
            f"This is a friendly reminder that the task '{task.title}' in project '{task.project.title}' "
            f"is due on {task.due_date.strftime('%Y-%m-%d %H:%M UTC')}.\n\n"
            f"Priority: {task.get_priority_display()}\n"
            f"Status: {task.get_status_display()}\n"
            f"Description: {task.description or 'No description provided.'}\n\n"
            f"Best regards,\n"
            f"Smart Task Manager Team"
        )

        try:
            send_mail(
                subject=subject,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[recipient_email],
                fail_silently=False,
            )
            task.reminder_sent_at = timezone.now()
            task.save(update_fields=['reminder_sent_at'])
            sent_count += 1
            logger.info(f"Sent reminder for task #{task.id} to {recipient_email}")
        except Exception as exc:
            logger.error(f"Failed sending deadline reminder for task #{task.id}: {exc}")

    return {
        'status': 'completed',
        'reminders_sent': sent_count,
        'skipped': skipped_count,
        'timestamp': now.isoformat()
    }
