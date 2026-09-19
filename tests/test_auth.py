from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from apps.accounts.models import UserProfile


class AuthenticationTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='testuser@example.com',
            password='TestPassword123!'
        )

    def test_user_profile_signal_creation(self):
        """Verify UserProfile is automatically created via post_save signal."""
        self.assertTrue(hasattr(self.user, 'profile'))
        self.assertIsInstance(self.user.profile, UserProfile)
        self.assertEqual(self.user.profile.display_name, 'testuser')

    def test_user_registration_flow(self):
        """Test user registration endpoint with valid data."""
        url = reverse('accounts:register')
        data = {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'first_name': 'New',
            'last_name': 'Person',
            'password1': 'StrongPass123!',
            'password2': 'StrongPass123!',
        }
        response = self.client.post(url, data)
        self.assertRedirects(response, reverse('dashboard:index'))
        self.assertTrue(User.objects.filter(username='newuser').exists())

    def test_user_login_and_logout(self):
        """Test sign in and sign out lifecycle."""
        login_url = reverse('accounts:login')
        response = self.client.post(login_url, {
            'username': 'testuser',
            'password': 'TestPassword123!'
        })
        self.assertRedirects(response, reverse('dashboard:index'))

        # Logout
        logout_url = reverse('accounts:logout')
        logout_resp = self.client.post(logout_url)
        self.assertRedirects(logout_resp, reverse('accounts:login'))

    def test_user_profile_update(self):
        """Test updating profile information."""
        self.client.login(username='testuser', password='TestPassword123!')
        url = reverse('accounts:profile')
        data = {
            'first_name': 'Updated',
            'last_name': 'Name',
            'email': 'updated@example.com',
            'job_title': 'Staff Architect',
            'department': 'Platform Infrastructure',
            'bio': 'Test bio string',
            'email_notifications': 'on',
        }
        response = self.client.post(url, data)
        self.assertRedirects(response, reverse('accounts:profile'))
        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, 'Updated')
        self.assertEqual(self.user.profile.job_title, 'Staff Architect')
