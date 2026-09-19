from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.http import HttpRequest, HttpResponse
from django.db.models import Q, Count
from .models import Project, ProjectMember
from .forms import ProjectForm, ProjectMemberAddForm


@login_required
def project_list(request: HttpRequest) -> HttpResponse:
    """List all projects that the current user has access to."""
    filter_status = request.GET.get('status', 'active')
    search_query = request.GET.get('q', '').strip()

    # User can see projects where they are owner or member
    projects = Project.objects.filter(
        Q(owner=request.user) | Q(memberships__user=request.user)
    ).distinct().annotate(
        task_count=Count('tasks'),
        completed_task_count=Count('tasks', filter=Q(tasks__status='done'))
    )

    if filter_status and filter_status != 'all':
        projects = projects.filter(status=filter_status)

    if search_query:
        projects = projects.filter(
            Q(title__icontains=search_query) | Q(description__icontains=search_query)
        )

    context = {
        'projects': projects,
        'current_status': filter_status,
        'search_query': search_query,
    }
    return render(request, 'projects/project_list.html', context)


@login_required
def project_detail(request: HttpRequest, pk: int) -> HttpResponse:
    """Project overview, member list, and quick task metrics."""
    project = get_object_or_404(Project, pk=pk)
    if not project.is_member(request.user):
        raise PermissionDenied("You do not have permission to view this project.")

    memberships = project.memberships.select_related('user', 'user__profile').all()
    tasks = project.tasks.select_related('assignee', 'assignee__profile').prefetch_related('tags').order_by('-created_at')[:10]

    member_form = ProjectMemberAddForm(project=project) if project.can_edit(request.user) else None

    # Calculate completion percentage
    total_tasks = project.tasks.count()
    done_tasks = project.tasks.filter(status='done').count()
    completion_rate = int((done_tasks / total_tasks * 100)) if total_tasks > 0 else 0

    context = {
        'project': project,
        'memberships': memberships,
        'recent_tasks': tasks,
        'member_form': member_form,
        'user_role': project.get_user_role(request.user),
        'can_edit': project.can_edit(request.user),
        'total_tasks': total_tasks,
        'done_tasks': done_tasks,
        'completion_rate': completion_rate,
    }
    return render(request, 'projects/project_detail.html', context)


@login_required
def project_create(request: HttpRequest) -> HttpResponse:
    """Create a new project and assign owner as Project Admin."""
    if request.method == 'POST':
        form = ProjectForm(request.POST)
        if form.is_valid():
            project = form.save(commit=False)
            project.owner = request.user
            project.save()
            # Add owner as admin member
            ProjectMember.objects.create(project=project, user=request.user, role=ProjectMember.ROLE_ADMIN)
            messages.success(request, f"Project '{project.title}' created successfully!")
            return redirect('projects:detail', pk=project.pk)
        else:
            messages.error(request, "Please correct the errors in the form.")
    else:
        form = ProjectForm()

    return render(request, 'projects/project_form.html', {'form': form, 'action': 'Create'})


@login_required
def project_edit(request: HttpRequest, pk: int) -> HttpResponse:
    """Edit an existing project."""
    project = get_object_or_404(Project, pk=pk)
    if not project.can_edit(request.user):
        raise PermissionDenied("Only project owners and admins can edit this project.")

    if request.method == 'POST':
        form = ProjectForm(request.POST, instance=project)
        if form.is_valid():
            form.save()
            messages.success(request, f"Project '{project.title}' updated successfully!")
            return redirect('projects:detail', pk=project.pk)
        else:
            messages.error(request, "Please fix the errors indicated below.")
    else:
        form = ProjectForm(instance=project)

    return render(request, 'projects/project_form.html', {'form': form, 'project': project, 'action': 'Edit'})


@login_required
def project_delete(request: HttpRequest, pk: int) -> HttpResponse:
    """Delete an existing project (owner only)."""
    project = get_object_or_404(Project, pk=pk)
    if project.owner != request.user and not request.user.is_superuser:
        raise PermissionDenied("Only the project owner can delete this project.")

    if request.method == 'POST':
        title = project.title
        project.delete()
        messages.success(request, f"Project '{title}' has been deleted.")
        return redirect('projects:list')

    return render(request, 'projects/project_confirm_delete.html', {'project': project})


@login_required
def project_archive_toggle(request: HttpRequest, pk: int) -> HttpResponse:
    """Toggle between active and archived statuses."""
    project = get_object_or_404(Project, pk=pk)
    if not project.can_edit(request.user):
        raise PermissionDenied("You do not have permission to archive this project.")

    if project.status == Project.STATUS_ARCHIVED:
        project.status = Project.STATUS_ACTIVE
        msg = f"Project '{project.title}' has been unarchived."
    else:
        project.status = Project.STATUS_ARCHIVED
        msg = f"Project '{project.title}' has been archived."

    project.save(update_fields=['status', 'updated_at'])
    messages.info(request, msg)
    return redirect('projects:detail', pk=project.pk)


@login_required
def project_member_add(request: HttpRequest, pk: int) -> HttpResponse:
    """Add a new member to the project."""
    project = get_object_or_404(Project, pk=pk)
    if not project.can_edit(request.user):
        raise PermissionDenied("Only project admins can add members.")

    if request.method == 'POST':
        form = ProjectMemberAddForm(request.POST, project=project)
        if form.is_valid():
            user = form.cleaned_data['username_or_email']
            role = form.cleaned_data['role']
            ProjectMember.objects.create(project=project, user=user, role=role)
            messages.success(request, f"{user.username} has been added as a {role} to '{project.title}'.")
        else:
            for field, errs in form.errors.items():
                for err in errs:
                    messages.error(request, err)

    return redirect('projects:detail', pk=project.pk)


@login_required
def project_member_remove(request: HttpRequest, pk: int, member_id: int) -> HttpResponse:
    """Remove a member from the project."""
    project = get_object_or_404(Project, pk=pk)
    if not project.can_edit(request.user):
        raise PermissionDenied("Only project admins can remove members.")

    membership = get_object_or_404(ProjectMember, pk=member_id, project=project)
    if membership.user == project.owner:
        messages.error(request, "The project owner cannot be removed.")
        return redirect('projects:detail', pk=project.pk)

    username = membership.user.username
    membership.delete()
    messages.info(request, f"{username} has been removed from the project.")
    return redirect('projects:detail', pk=project.pk)
