from functools import wraps
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404
from .models import Project


def user_can_access_project(user, project: Project) -> bool:
    """Check if the user has permission to view the project."""
    return project.is_member(user)


def user_can_modify_project(user, project: Project) -> bool:
    """Check if the user is owner or admin who can modify project settings."""
    return project.can_edit(user)


def project_member_required(view_func):
    """Decorator to ensure request user is a member of the project."""
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        project_pk = kwargs.get('pk') or kwargs.get('project_id')
        project = get_object_or_404(Project, pk=project_pk)
        if not user_can_access_project(request.user, project):
            raise PermissionDenied("You are not a member of this project.")
        request.project = project
        return view_func(request, *args, **kwargs)
    return _wrapped_view
