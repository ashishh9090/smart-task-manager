from rest_framework import serializers
from django.contrib.auth.models import User
from apps.accounts.models import UserProfile
from apps.projects.models import Project, ProjectMember
from apps.tasks.models import Task, Tag, TaskActivity


class UserMiniSerializer(serializers.ModelSerializer):
    display_name = serializers.CharField(source='profile.display_name', read_only=True)
    avatar_url = serializers.CharField(source='profile.avatar_url', read_only=True)
    job_title = serializers.CharField(source='profile.job_title', read_only=True)

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'display_name', 'avatar_url', 'job_title']


class UserProfileSerializer(serializers.ModelSerializer):
    user = UserMiniSerializer(read_only=True)

    class Meta:
        model = UserProfile
        fields = ['id', 'user', 'avatar', 'bio', 'job_title', 'department', 'email_notifications', 'created_at', 'updated_at']


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ['id', 'name', 'slug', 'color']


class ProjectMemberSerializer(serializers.ModelSerializer):
    user = UserMiniSerializer(read_only=True)
    role_display = serializers.CharField(source='get_role_display', read_only=True)

    class Meta:
        model = ProjectMember
        fields = ['id', 'user', 'role', 'role_display', 'joined_at']


class ProjectSerializer(serializers.ModelSerializer):
    owner = UserMiniSerializer(read_only=True)
    tasks_count = serializers.IntegerField(source='tasks.count', read_only=True)
    members_count = serializers.IntegerField(source='memberships.count', read_only=True)

    class Meta:
        model = Project
        fields = ['id', 'title', 'description', 'owner', 'status', 'color', 'tasks_count', 'members_count', 'created_at', 'updated_at']
        read_only_fields = ['owner', 'created_at', 'updated_at']


class ProjectDetailSerializer(ProjectSerializer):
    memberships = ProjectMemberSerializer(many=True, read_only=True)

    class Meta(ProjectSerializer.Meta):
        fields = ProjectSerializer.Meta.fields + ['memberships']


class TaskActivitySerializer(serializers.ModelSerializer):
    user = UserMiniSerializer(read_only=True)

    class Meta:
        model = TaskActivity
        fields = ['id', 'user', 'action', 'field_name', 'old_value', 'new_value', 'note', 'created_at']


class TaskSerializer(serializers.ModelSerializer):
    creator = UserMiniSerializer(read_only=True)
    assignee = UserMiniSerializer(read_only=True)
    assignee_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(), source='assignee', write_only=True, required=False, allow_null=True
    )
    tags = TagSerializer(many=True, read_only=True)
    tag_ids = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(), many=True, source='tags', write_only=True, required=False
    )
    project_title = serializers.CharField(source='project.title', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    priority_display = serializers.CharField(source='get_priority_display', read_only=True)
    is_overdue = serializers.BooleanField(read_only=True)
    is_due_soon = serializers.BooleanField(read_only=True)

    class Meta:
        model = Task
        fields = [
            'id', 'title', 'description', 'project', 'project_title',
            'creator', 'assignee', 'assignee_id', 'status', 'status_display',
            'priority', 'priority_display', 'due_date', 'tags', 'tag_ids',
            'is_overdue', 'is_due_soon', 'reminder_sent_at', 'created_at', 'updated_at'
        ]
        read_only_fields = ['creator', 'created_at', 'updated_at']
