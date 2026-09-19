from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from apps.projects.models import Project, ProjectMember


class ProjectPermissionsTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.owner = User.objects.create_user(username='owner', password='Password123!')
        self.member = User.objects.create_user(username='member', password='Password123!')
        self.outsider = User.objects.create_user(username='outsider', password='Password123!')

        self.project = Project.objects.create(
            title='Alpha Project',
            description='Test description',
            owner=self.owner,
            status=Project.STATUS_ACTIVE
        )
        ProjectMember.objects.create(project=self.project, user=self.owner, role=ProjectMember.ROLE_ADMIN)
        ProjectMember.objects.create(project=self.project, user=self.member, role=ProjectMember.ROLE_MEMBER)

    def test_owner_and_member_can_access_project(self):
        """Project members and owner can access the project detail page."""
        self.client.login(username='owner', password='Password123!')
        resp = self.client.get(reverse('projects:detail', kwargs={'pk': self.project.pk}))
        self.assertEqual(resp.status_code, 200)

        self.client.login(username='member', password='Password123!')
        resp = self.client.get(reverse('projects:detail', kwargs={'pk': self.project.pk}))
        self.assertEqual(resp.status_code, 200)

    def test_outsider_cannot_access_project(self):
        """Non-members are denied access (403 Forbidden)."""
        self.client.login(username='outsider', password='Password123!')
        resp = self.client.get(reverse('projects:detail', kwargs={'pk': self.project.pk}))
        self.assertEqual(resp.status_code, 403)

    def test_only_admin_can_edit_project(self):
        """Members cannot edit project settings, but Admins/Owners can."""
        edit_url = reverse('projects:edit', kwargs={'pk': self.project.pk})

        # Member tries to edit
        self.client.login(username='member', password='Password123!')
        resp = self.client.get(edit_url)
        self.assertEqual(resp.status_code, 403)

        # Owner edits
        self.client.login(username='owner', password='Password123!')
        resp = self.client.get(edit_url)
        self.assertEqual(resp.status_code, 200)

    def test_project_archive_toggle(self):
        """Owner can toggle archive status."""
        self.client.login(username='owner', password='Password123!')
        url = reverse('projects:archive_toggle', kwargs={'pk': self.project.pk})
        self.client.get(url)
        self.project.refresh_from_db()
        self.assertEqual(self.project.status, Project.STATUS_ARCHIVED)
