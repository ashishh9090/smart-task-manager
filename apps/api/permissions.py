from rest_framework import permissions
from apps.projects.models import Project


class IsProjectMember(permissions.BasePermission):
    """
    Object-level permission allowing only project members/owners to view or edit project.
    """
    def has_object_permission(self, request, view, obj: Project) -> bool:
        if request.user.is_superuser:
            return True
        if request.method in permissions.SAFE_METHODS:
            return obj.is_member(request.user)
        return obj.can_edit(request.user)


class IsTaskProjectMember(permissions.BasePermission):
    """
    Allows task access only to members of the task's parent project.
    """
    def has_object_permission(self, request, view, obj) -> bool:
        if request.user.is_superuser:
            return True
        if request.method in permissions.SAFE_METHODS:
            return obj.project.is_member(request.user)
        return obj.project.can_manage_tasks(request.user)
