"""
Management command to seed realistic demo data into Smart Task Manager.
"""
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
from apps.accounts.models import UserProfile
from apps.projects.models import Project, ProjectMember
from apps.tasks.models import Task, Tag, TaskActivity


class Command(BaseCommand):
    help = "Populate the database with realistic demo users, projects, tags, and tasks."

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE("Seeding Smart Task Manager demo data..."))

        # 1. Create Users
        users_data = [
            {
                'username': 'admin',
                'email': 'admin@example.com',
                'first_name': 'Sarah',
                'last_name': 'Connor',
                'is_staff': True,
                'is_superuser': True,
                'password': 'AdminPass123!',
                'job_title': 'Engineering Director',
                'department': 'Core Infrastructure',
                'bio': 'Oversees technical direction, DevOps strategy, and platform reliability.',
            },
            {
                'username': 'alice_pm',
                'email': 'alice@example.com',
                'first_name': 'Alice',
                'last_name': 'Vance',
                'is_staff': False,
                'is_superuser': False,
                'password': 'DemoPass123!',
                'job_title': 'Principal Product Manager',
                'department': 'Product Strategy',
                'bio': 'Focused on user satisfaction, agile delivery, and milestone prioritization.',
            },
            {
                'username': 'bob_dev',
                'email': 'bob@example.com',
                'first_name': 'Bob',
                'last_name': 'Stone',
                'is_staff': False,
                'is_superuser': False,
                'password': 'DemoPass123!',
                'job_title': 'Senior Full-Stack Developer',
                'department': 'Software Engineering',
                'bio': 'Passionate about Python, Django, high-throughput microservices, and React.',
            },
            {
                'username': 'charlie_designer',
                'email': 'charlie@example.com',
                'first_name': 'Charlie',
                'last_name': 'Reed',
                'is_staff': False,
                'is_superuser': False,
                'password': 'DemoPass123!',
                'job_title': 'Lead UX/UI Designer',
                'department': 'Product Design',
                'bio': 'Design systems advocate, passionate about clean typography and accessibility.',
            },
        ]

        created_users = {}
        for udata in users_data:
            user, created = User.objects.get_or_create(
                username=udata['username'],
                defaults={
                    'email': udata['email'],
                    'first_name': udata['first_name'],
                    'last_name': udata['last_name'],
                    'is_staff': udata['is_staff'],
                    'is_superuser': udata['is_superuser'],
                }
            )
            user.set_password(udata['password'])
            user.save()

            # Ensure profile exists and has metadata
            profile, _ = UserProfile.objects.get_or_create(user=user)
            profile.job_title = udata['job_title']
            profile.department = udata['department']
            profile.bio = udata['bio']
            profile.email_notifications = True
            profile.save()

            created_users[udata['username']] = user
            status_text = "Created" if created else "Updated"
            self.stdout.write(f"  [{status_text}] User: {user.username} (pass: {udata['password']})")

        # 2. Create Tags
        tags_data = [
            ('Frontend', '#3b82f6'),
            ('Backend', '#10b981'),
            ('DevOps', '#8b5cf6'),
            ('Security', '#ef4444'),
            ('UI/UX', '#ec4899'),
            ('Database', '#f59e0b'),
            ('Bug', '#dc2626'),
            ('High Impact', '#6366f1'),
        ]

        created_tags = {}
        for name, color in tags_data:
            tag, _ = Tag.objects.get_or_create(name=name, defaults={'color': color})
            created_tags[name] = tag

        # 3. Create Projects
        projects_data = [
            {
                'title': 'Cloud-Native Platform Migration',
                'description': 'Transition legacy monolithic infrastructure into containerized microservices managed via Docker and Kubernetes.',
                'owner': created_users['admin'],
                'color': '#4f46e5',
                'status': Project.STATUS_ACTIVE,
                'members': [
                    (created_users['alice_pm'], ProjectMember.ROLE_ADMIN),
                    (created_users['bob_dev'], ProjectMember.ROLE_MEMBER),
                    (created_users['charlie_designer'], ProjectMember.ROLE_VIEWER),
                ]
            },
            {
                'title': 'Mobile Responsive Experience',
                'description': 'Modernize web and mobile viewports with Bootstrap 5 components, interactive Kanban flows, and WCAG AA accessibility.',
                'owner': created_users['alice_pm'],
                'color': '#06b6d4',
                'status': Project.STATUS_ACTIVE,
                'members': [
                    (created_users['admin'], ProjectMember.ROLE_ADMIN),
                    (created_users['bob_dev'], ProjectMember.ROLE_MEMBER),
                    (created_users['charlie_designer'], ProjectMember.ROLE_MEMBER),
                ]
            },
            {
                'title': 'Q3 Security & Compliance Audit',
                'description': 'Comprehensive penetration testing, RBAC permission checks, and OWASP Top 10 vulnerability remediation.',
                'owner': created_users['admin'],
                'color': '#10b981',
                'status': Project.STATUS_ARCHIVED,
                'members': [
                    (created_users['bob_dev'], ProjectMember.ROLE_MEMBER),
                ]
            },
        ]

        created_projects = []
        for pdata in projects_data:
            proj, _ = Project.objects.get_or_create(
                title=pdata['title'],
                defaults={
                    'description': pdata['description'],
                    'owner': pdata['owner'],
                    'color': pdata['color'],
                    'status': pdata['status'],
                }
            )
            # Add owner as admin member
            ProjectMember.objects.get_or_create(project=proj, user=pdata['owner'], defaults={'role': ProjectMember.ROLE_ADMIN})
            # Add team members
            for user_obj, role in pdata['members']:
                ProjectMember.objects.get_or_create(project=proj, user=user_obj, defaults={'role': role})

            created_projects.append(proj)
            self.stdout.write(f"  [Created Project] {proj.title}")

        # 4. Create Tasks across Kanban states
        now = timezone.now()
        tasks_data = [
            # Cloud-Native Platform Migration
            {
                'project': created_projects[0],
                'title': 'Containerize Django core app with multi-stage Dockerfile',
                'description': 'Build an optimized Docker image using python:3.12-slim, non-root user, and cached dependencies.',
                'creator': created_users['admin'],
                'assignee': created_users['bob_dev'],
                'status': Task.STATUS_DONE,
                'priority': Task.PRIORITY_HIGH,
                'due_date': now - timedelta(days=2),
                'tags': ['DevOps', 'Backend'],
            },
            {
                'project': created_projects[0],
                'title': 'Configure Celery Beat with Redis for automated reminders',
                'description': 'Write periodic task to check upcoming deadlines within 24 hours and dispatch email notices to assignees.',
                'creator': created_users['alice_pm'],
                'assignee': created_users['bob_dev'],
                'status': Task.STATUS_REVIEW,
                'priority': Task.PRIORITY_URGENT,
                'due_date': now + timedelta(hours=14),  # Due in 14h (tests Celery reminder!)
                'tags': ['Backend', 'DevOps', 'High Impact'],
            },
            {
                'project': created_projects[0],
                'title': 'Refactor PostgreSQL connection pool and health checks',
                'description': 'Ensure docker-compose services correctly wait for PostgreSQL 16 ready status before launching Gunicorn.',
                'creator': created_users['bob_dev'],
                'assignee': created_users['bob_dev'],
                'status': Task.STATUS_IN_PROGRESS,
                'priority': Task.PRIORITY_MEDIUM,
                'due_date': now + timedelta(days=3),
                'tags': ['Database', 'DevOps'],
            },
            {
                'project': created_projects[0],
                'title': 'Establish automated CI/CD pipeline and integration test suite',
                'description': 'Implement GitHub Actions matrix running pytest, flake8 linting, and coverage reporting.',
                'creator': created_users['admin'],
                'assignee': created_users['bob_dev'],
                'status': Task.STATUS_TODO,
                'priority': Task.PRIORITY_HIGH,
                'due_date': now + timedelta(days=6),
                'tags': ['DevOps'],
            },
            # Mobile Responsive Experience
            {
                'project': created_projects[1],
                'title': 'Design HTML5 Drag-and-Drop Kanban columns',
                'description': 'Implement fluid column layout with touch support, count badges, and immediate status persistence via AJAX.',
                'creator': created_users['alice_pm'],
                'assignee': created_users['charlie_designer'],
                'status': Task.STATUS_IN_PROGRESS,
                'priority': Task.PRIORITY_URGENT,
                'due_date': now - timedelta(days=1),  # Overdue task!
                'tags': ['Frontend', 'UI/UX', 'High Impact'],
            },
            {
                'project': created_projects[1],
                'title': 'Build real-time metric cards and Chart.js task breakdown',
                'description': 'Render completion rate doughnut chart, upcoming deadline counters, and overdue warning alerts.',
                'creator': created_users['alice_pm'],
                'assignee': created_users['bob_dev'],
                'status': Task.STATUS_TODO,
                'priority': Task.PRIORITY_MEDIUM,
                'due_date': now + timedelta(days=2),
                'tags': ['Frontend', 'UI/UX'],
            },
            {
                'project': created_projects[1],
                'title': 'Conduct cross-browser responsive layout testing',
                'description': 'Verify iOS Safari, Android Chrome, and Desktop Chrome rendering for sidebar collapse and modals.',
                'creator': created_users['charlie_designer'],
                'assignee': created_users['charlie_designer'],
                'status': Task.STATUS_TODO,
                'priority': Task.PRIORITY_LOW,
                'due_date': now + timedelta(days=5),
                'tags': ['UI/UX'],
            },
            {
                'project': created_projects[1],
                'title': 'Publish Design System Tokens and Color Palette',
                'description': 'Deliver unified CSS custom properties for dark mode readiness, typography hierarchy, and buttons.',
                'creator': created_users['charlie_designer'],
                'assignee': created_users['charlie_designer'],
                'status': Task.STATUS_DONE,
                'priority': Task.PRIORITY_MEDIUM,
                'due_date': now - timedelta(days=4),
                'tags': ['UI/UX'],
            },
            # Q3 Security & Compliance Audit
            {
                'project': created_projects[2],
                'title': 'Perform CSRF and XSS security assessment across API endpoints',
                'description': 'Audit Django REST Framework token and session authentication handlers, verify CORS and trusted origins.',
                'creator': created_users['admin'],
                'assignee': created_users['bob_dev'],
                'status': Task.STATUS_DONE,
                'priority': Task.PRIORITY_URGENT,
                'due_date': now - timedelta(days=10),
                'tags': ['Security', 'Backend'],
            },
        ]

        for tdata in tasks_data:
            task, created = Task.objects.get_or_create(
                project=tdata['project'],
                title=tdata['title'],
                defaults={
                    'description': tdata['description'],
                    'creator': tdata['creator'],
                    'assignee': tdata['assignee'],
                    'status': tdata['status'],
                    'priority': tdata['priority'],
                    'due_date': tdata['due_date'],
                }
            )
            for tag_name in tdata['tags']:
                if tag_name in created_tags:
                    task.tags.add(created_tags[tag_name])

            # Add sample activity
            TaskActivity.objects.get_or_create(
                task=task,
                user=tdata['creator'],
                action='created',
                defaults={'note': f"Task initialized with priority {task.priority}"}
            )
            self.stdout.write(f"  [Created Task] #{task.id}: {task.title} ({task.status})")

        self.stdout.write(self.style.SUCCESS("Demo seed data created successfully!"))
