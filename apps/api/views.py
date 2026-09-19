from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.views import APIView

from django.db.models import Q
from django.utils import timezone
from apps.projects.models import Project
from apps.tasks.models import Task, Tag
from .serializers import (
    ProjectSerializer, ProjectDetailSerializer,
    TaskSerializer, TagSerializer, UserProfileSerializer
)
from .permissions import IsProjectMember, IsTaskProjectMember


class UserProfileView(APIView):
    """
    Retrieve or update the authenticated user's profile.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        serializer = UserProfileSerializer(request.user.profile)
        return Response(serializer.data)

    def put(self, request):
        serializer = UserProfileSerializer(request.user.profile, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class TagViewSet(viewsets.ModelViewSet):
    """
    CRUD endpoints for task tags.
    """
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = [permissions.IsAuthenticated]
    search_fields = ['name', 'slug']


class ProjectViewSet(viewsets.ModelViewSet):
    """
    CRUD endpoints for Projects. Only accessible by project members and owners.
    """
    permission_classes = [permissions.IsAuthenticated, IsProjectMember]
    filterset_fields = ['status']
    search_fields = ['title', 'description']
    ordering_fields = ['title', 'created_at', 'updated_at']

    def get_queryset(self):
        user = self.request.user
        return Project.objects.filter(
            Q(owner=user) | Q(memberships__user=user)
        ).distinct()

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return ProjectDetailSerializer
        return ProjectSerializer

    def perform_create(self, serializer):
        from apps.projects.models import ProjectMember
        project = serializer.save(owner=self.request.user)
        ProjectMember.objects.create(project=project, user=self.request.user, role=ProjectMember.ROLE_ADMIN)

    @action(detail=True, methods=['post'])
    def toggle_archive(self, request, pk=None):
        project = self.get_object()
        if project.status == Project.STATUS_ARCHIVED:
            project.status = Project.STATUS_ACTIVE
        else:
            project.status = Project.STATUS_ARCHIVED
        project.save(update_fields=['status', 'updated_at'])
        return Response({'status': project.status, 'message': f"Project is now {project.status}"})


class TaskViewSet(viewsets.ModelViewSet):
    """
    CRUD endpoints for Tasks with filtering, searching, and status updates for Kanban.
    """
    serializer_class = TaskSerializer
    permission_classes = [permissions.IsAuthenticated, IsTaskProjectMember]
    filterset_fields = ['project', 'status', 'priority', 'assignee']
    search_fields = ['title', 'description']
    ordering_fields = ['priority', 'due_date', 'created_at']

    def get_queryset(self):
        user = self.request.user
        user_projects = Project.objects.filter(
            Q(owner=user) | Q(memberships__user=user)
        ).distinct()
        qs = Task.objects.filter(project__in=user_projects).select_related(
            'project', 'creator', 'assignee', 'assignee__profile'
        ).prefetch_related('tags')

        # Additional query param filtering
        tag_id = self.request.query_params.get('tag')
        if tag_id:
            qs = qs.filter(tags__id=tag_id)

        overdue = self.request.query_params.get('overdue')
        if overdue in ('1', 'true', 'True'):
            qs = qs.filter(due_date__lt=timezone.now()).exclude(status=Task.STATUS_DONE)

        return qs.distinct()

    def perform_create(self, serializer):
        task = serializer.save(creator=self.request.user)
        task._actor = self.request.user

    def perform_update(self, serializer):
        task = serializer.save()
        task._actor = self.request.user

    @action(detail=True, methods=['post'], url_path='update-status')
    def update_status(self, request, pk=None):
        """
        Specialized endpoint for Kanban board drag & drop movements.
        """
        task = self.get_object()
        new_status = request.data.get('status')
        valid_statuses = [c[0] for c in Task.STATUS_CHOICES]
        if new_status not in valid_statuses:
            return Response({'error': f"Invalid status '{new_status}'."}, status=status.HTTP_400_BAD_REQUEST)

        task._actor = request.user
        task.status = new_status
        task.save()
        return Response({
            'success': True,
            'task_id': task.id,
            'status': task.status,
            'status_display': task.get_status_display()
        })


class DashboardStatsView(APIView):
    """
    Aggregated dashboard analytics for the current user.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user
        now = timezone.now()

        user_projects = Project.objects.filter(
            Q(owner=user) | Q(memberships__user=user)
        ).distinct()

        tasks = Task.objects.filter(project__in=user_projects)

        total_tasks = tasks.count()
        completed_tasks = tasks.filter(status=Task.STATUS_DONE).count()
        overdue_tasks = tasks.filter(due_date__lt=now).exclude(status=Task.STATUS_DONE).count()
        completion_rate = round((completed_tasks / total_tasks * 100), 1) if total_tasks > 0 else 0.0

        return Response({
            'total_projects': user_projects.count(),
            'active_projects': user_projects.filter(status=Project.STATUS_ACTIVE).count(),
            'total_tasks': total_tasks,
            'completed_tasks': completed_tasks,
            'in_progress_tasks': tasks.filter(status=Task.STATUS_IN_PROGRESS).count(),
            'review_tasks': tasks.filter(status=Task.STATUS_REVIEW).count(),
            'todo_tasks': tasks.filter(status=Task.STATUS_TODO).count(),
            'overdue_tasks': overdue_tasks,
            'completion_rate': completion_rate,
            'priority_distribution': {
                'urgent': tasks.filter(priority=Task.PRIORITY_URGENT).count(),
                'high': tasks.filter(priority=Task.PRIORITY_HIGH).count(),
                'medium': tasks.filter(priority=Task.PRIORITY_MEDIUM).count(),
                'low': tasks.filter(priority=Task.PRIORITY_LOW).count(),
            }
        })
