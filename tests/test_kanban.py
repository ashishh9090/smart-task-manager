from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
import json
from apps.projects.models import Project, ProjectMember
from apps.tasks.models import Task


class KanbanTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='kanban_user', password='Password123!')
        self.project = Project.objects.create(title='Kanban Project', owner=self.user)
        ProjectMember.objects.create(project=self.project, user=self.user, role=ProjectMember.ROLE_MEMBER)

        self.task = Task.objects.create(
            title='Kanban Card 1',
            project=self.project,
            creator=self.user,
            status=Task.STATUS_TODO
        )
        self.client.login(username='kanban_user', password='Password123!')

    def test_kanban_board_renders_all_columns(self):
        """Ensure kanban board view renders correctly with columns."""
        url = reverse('tasks:kanban')
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'Kanban Card 1')
        self.assertIn('columns', resp.context)

    def test_task_status_ajax_update(self):
        """Test dragging/moving task via status update AJAX endpoint."""
        url = reverse('tasks:update_status', kwargs={'pk': self.task.pk})
        data = json.dumps({'status': Task.STATUS_IN_PROGRESS})
        resp = self.client.post(url, data, content_type='application/json')
        self.assertEqual(resp.status_code, 200)

        resp_json = resp.json()
        self.assertTrue(resp_json['success'])
        self.assertEqual(resp_json['new_status'], Task.STATUS_IN_PROGRESS)

        self.task.refresh_from_db()
        self.assertEqual(self.task.status, Task.STATUS_IN_PROGRESS)

    def test_invalid_status_rejected(self):
        """Invalid status updates return 400."""
        url = reverse('tasks:update_status', kwargs={'pk': self.task.pk})
        data = json.dumps({'status': 'non_existent_status'})
        resp = self.client.post(url, data, content_type='application/json')
        self.assertEqual(resp.status_code, 400)
