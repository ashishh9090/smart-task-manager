from django.test import TestCase
from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework.test import APIClient
from apps.projects.models import Project, ProjectMember
from apps.tasks.models import Task, Tag


class ApiEndpointsTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username='api_user', password='Password123!')
        self.client.force_authenticate(user=self.user)

        self.project = Project.objects.create(title='API Project', owner=self.user)
        ProjectMember.objects.create(project=self.project, user=self.user, role=ProjectMember.ROLE_ADMIN)

        self.tag = Tag.objects.create(name='API Tag', color='#6366f1')
        self.task = Task.objects.create(
            title='API Task',
            project=self.project,
            creator=self.user,
            assignee=self.user,
            status=Task.STATUS_TODO,
            priority=Task.PRIORITY_MEDIUM
        )

    def test_dashboard_stats_endpoint(self):
        """Test GET /api/v1/dashboard/stats/."""
        url = reverse('api:dashboard-stats')
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data['total_projects'], 1)
        self.assertEqual(data['total_tasks'], 1)
        self.assertIn('completion_rate', data)

    def test_project_list_and_create_api(self):
        """Test project endpoints via DRF."""
        url = reverse('api:project-list')
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()['count'], 1)

        create_resp = self.client.post(url, {
            'title': 'New API Project',
            'description': 'Created via API',
            'color': '#ef4444',
            'status': 'active'
        })
        self.assertEqual(create_resp.status_code, 201)

    def test_task_kanban_status_update_api(self):
        """Test POST /api/v1/tasks/<id>/update-status/."""
        url = reverse('api:task-update-status', kwargs={'pk': self.task.pk})
        resp = self.client.post(url, {'status': 'done'})
        self.assertEqual(resp.status_code, 200)
        self.task.refresh_from_db()
        self.assertEqual(self.task.status, 'done')
