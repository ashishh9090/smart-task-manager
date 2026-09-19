from django.test import TestCase, Client
from django.contrib.auth.models import User

from django.utils import timezone
from datetime import timedelta
from apps.projects.models import Project, ProjectMember
from apps.tasks.models import Task, Tag, TaskActivity


class TaskCRUDTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='dev_user', password='Password123!')
        self.project = Project.objects.create(title='Beta Project', owner=self.user)
        ProjectMember.objects.create(project=self.project, user=self.user, role=ProjectMember.ROLE_ADMIN)
        self.tag = Tag.objects.create(name='Backend', color='#10b981')
        self.client.login(username='dev_user', password='Password123!')

    def test_create_task_and_activity_logging(self):
        """Creating a task records initial activity."""
        task = Task.objects.create(
            title='Implement Cache',
            project=self.project,
            creator=self.user,
            assignee=self.user,
            status=Task.STATUS_TODO,
            priority=Task.PRIORITY_HIGH
        )
        task.tags.add(self.tag)

        self.assertEqual(task.tags.count(), 1)
        self.assertTrue(TaskActivity.objects.filter(task=task, action='created').exists())

    def test_status_change_creates_audit_activity(self):
        """Changing task status creates status_changed activity."""
        task = Task.objects.create(
            title='Refactor DB',
            project=self.project,
            creator=self.user,
            status=Task.STATUS_TODO
        )
        task.status = Task.STATUS_IN_PROGRESS
        task.save()

        activity = TaskActivity.objects.filter(task=task, action='status_changed').first()
        self.assertIsNotNone(activity)
        self.assertEqual(activity.old_value, Task.STATUS_TODO)
        self.assertEqual(activity.new_value, Task.STATUS_IN_PROGRESS)

    def test_task_is_overdue_property(self):
        """Verify is_overdue property behaves correctly."""
        overdue_task = Task.objects.create(
            title='Past Task',
            project=self.project,
            creator=self.user,
            due_date=timezone.now() - timedelta(days=2),
            status=Task.STATUS_IN_PROGRESS
        )
        self.assertTrue(overdue_task.is_overdue)

        # Done task should not be overdue
        overdue_task.status = Task.STATUS_DONE
        overdue_task.save()
        self.assertFalse(overdue_task.is_overdue)
