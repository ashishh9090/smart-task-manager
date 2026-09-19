from django.test import TestCase
from django.contrib.auth.models import User
from django.utils import timezone
from django.core import mail
from datetime import timedelta
from apps.projects.models import Project, ProjectMember
from apps.tasks.models import Task
from apps.tasks.tasks import send_task_deadline_reminders


class CeleryReminderTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='remind_user',
            email='remind@example.com',
            password='Password123!'
        )
        self.user.profile.email_notifications = True
        self.user.profile.save()

        self.project = Project.objects.create(title='Reminder Project', owner=self.user)
        ProjectMember.objects.create(project=self.project, user=self.user, role=ProjectMember.ROLE_MEMBER)

    def test_deadline_reminder_sent_for_upcoming_task(self):
        """Tasks due in < 24h trigger email reminder and set reminder_sent_at."""
        now = timezone.now()
        task = Task.objects.create(
            title='Upcoming Task',
            project=self.project,
            creator=self.user,
            assignee=self.user,
            status=Task.STATUS_IN_PROGRESS,
            priority=Task.PRIORITY_URGENT,
            due_date=now + timedelta(hours=10),
            reminder_sent_at=None
        )

        result = send_task_deadline_reminders()
        self.assertEqual(result['reminders_sent'], 1)

        # Check outbox
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn('Reminder: Task \'Upcoming Task\' is due within 24 hours', mail.outbox[0].subject)
        self.assertEqual(mail.outbox[0].to, ['remind@example.com'])

        task.refresh_from_db()
        self.assertIsNotNone(task.reminder_sent_at)

    def test_done_or_distant_tasks_are_not_reminded(self):
        """Tasks already done or due past 24 hours should not trigger email."""
        now = timezone.now()
        # Task 1: already done
        Task.objects.create(
            title='Done Task',
            project=self.project,
            creator=self.user,
            assignee=self.user,
            status=Task.STATUS_DONE,
            due_date=now + timedelta(hours=5),
        )
        # Task 2: due in 3 days
        Task.objects.create(
            title='Distant Task',
            project=self.project,
            creator=self.user,
            assignee=self.user,
            status=Task.STATUS_TODO,
            due_date=now + timedelta(days=3),
        )

        mail.outbox = []
        result = send_task_deadline_reminders()
        self.assertEqual(result['reminders_sent'], 0)
        self.assertEqual(len(mail.outbox), 0)
