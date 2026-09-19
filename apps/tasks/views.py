from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.views.decorators.http import require_POST
from django.db.models import Q
from django.utils import timezone
from .models import Task, Tag
from .forms import TaskForm
from apps.projects.models import Project


@login_required
def task_list(request: HttpRequest) -> HttpResponse:
    """Filterable, searchable list of tasks with pagination."""
    # Only show tasks from projects the user is a member/owner of
    user_projects = Project.objects.filter(
        Q(owner=request.user) | Q(memberships__user=request.user)
    ).distinct()

    tasks = Task.objects.filter(project__in=user_projects).select_related(
        'project', 'assignee', 'assignee__profile', 'creator'
    ).prefetch_related('tags')

    # Filters
    project_id = request.GET.get('project')
    status = request.GET.get('status')
    priority = request.GET.get('priority')
    tag_id = request.GET.get('tag')
    assignee_id = request.GET.get('assignee')
    overdue = request.GET.get('overdue')
    search_query = request.GET.get('q', '').strip()

    if project_id:
        tasks = tasks.filter(project_id=project_id)
    if status:
        tasks = tasks.filter(status=status)
    if priority:
        tasks = tasks.filter(priority=priority)
    if tag_id:
        tasks = tasks.filter(tags__id=tag_id)
    if assignee_id:
        if assignee_id == 'unassigned':
            tasks = tasks.filter(assignee__isnull=True)
        else:
            tasks = tasks.filter(assignee_id=assignee_id)
    if overdue == '1':
        tasks = tasks.filter(due_date__lt=timezone.now()).exclude(status=Task.STATUS_DONE)
    if search_query:
        tasks = tasks.filter(
            Q(title__icontains=search_query) | Q(description__icontains=search_query)
        )

    # Distinct after tag filtering
    tasks = tasks.distinct()

    paginator = Paginator(tasks, 15)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    all_tags = Tag.objects.all()

    context = {
        'tasks': page_obj,
        'projects': user_projects,
        'tags': all_tags,
        'selected_project': project_id,
        'selected_status': status,
        'selected_priority': priority,
        'selected_tag': tag_id,
        'selected_assignee': assignee_id,
        'selected_overdue': overdue,
        'search_query': search_query,
    }
    return render(request, 'tasks/task_list.html', context)


@login_required
def kanban_board(request: HttpRequest) -> HttpResponse:
    """Interactive Kanban board organized into Todo, In Progress, Review, and Done."""
    user_projects = Project.objects.filter(
        Q(owner=request.user) | Q(memberships__user=request.user)
    ).distinct()

    project_id = request.GET.get('project')
    selected_project = None

    tasks = Task.objects.filter(project__in=user_projects).select_related(
        'project', 'assignee', 'assignee__profile'
    ).prefetch_related('tags')

    if project_id:
        selected_project = get_object_or_404(Project, pk=project_id)
        if not selected_project.is_member(request.user):
            raise PermissionDenied("Access denied to project.")
        tasks = tasks.filter(project=selected_project)

    # Categorize into 4 Kanban columns
    columns = {
        'todo': tasks.filter(status=Task.STATUS_TODO),
        'in_progress': tasks.filter(status=Task.STATUS_IN_PROGRESS),
        'review': tasks.filter(status=Task.STATUS_REVIEW),
        'done': tasks.filter(status=Task.STATUS_DONE),
    }

    context = {
        'columns': columns,
        'projects': user_projects,
        'selected_project': selected_project,
        'selected_project_id': int(project_id) if project_id else None,
    }
    return render(request, 'tasks/kanban_board.html', context)


@login_required
@require_POST
def task_update_status_api(request: HttpRequest, pk: int) -> JsonResponse:
    """
    AJAX endpoint for moving tasks across Kanban columns or updating status.
    Returns JSON status.
    """
    import json
    task = get_object_or_404(Task, pk=pk)

    if not task.project.is_member(request.user):
        return JsonResponse({'error': 'Permission denied.'}, status=403)

    if not task.project.can_manage_tasks(request.user):
        return JsonResponse({'error': 'Viewers cannot change task status.'}, status=403)

    try:
        data = json.loads(request.body.decode('utf-8'))
        new_status = data.get('status')
    except Exception:
        new_status = request.POST.get('status')

    valid_statuses = [choice[0] for choice in Task.STATUS_CHOICES]
    if new_status not in valid_statuses:
        return JsonResponse({'error': f"Invalid status '{new_status}'."}, status=400)

    old_status = task.status
    if old_status != new_status:
        task._actor = request.user
        task.status = new_status
        task.save()

    return JsonResponse({
        'success': True,
        'task_id': task.id,
        'old_status': old_status,
        'new_status': task.status,
        'new_status_display': task.get_status_display(),
        'badge_class': task.status_badge_class,
    })


@login_required
def task_detail(request: HttpRequest, pk: int) -> HttpResponse:
    """View task details and full activity timeline."""
    task = get_object_or_404(Task.objects.select_related('project', 'assignee', 'assignee__profile', 'creator'), pk=pk)
    if not task.project.is_member(request.user):
        raise PermissionDenied("You do not have access to this task's project.")

    activities = task.activities.select_related('user', 'user__profile').all()

    context = {
        'task': task,
        'activities': activities,
        'can_manage': task.project.can_manage_tasks(request.user),
    }
    return render(request, 'tasks/task_detail.html', context)


@login_required
def task_create(request: HttpRequest) -> HttpResponse:
    """Create a new task."""
    project_id = request.GET.get('project')
    initial_project = None
    if project_id:
        initial_project = get_object_or_404(Project, pk=project_id)
        if not initial_project.is_member(request.user):
            raise PermissionDenied("Cannot create task for a project you don't belong to.")

    if request.method == 'POST':
        form = TaskForm(request.POST, user=request.user, project=initial_project)
        if form.is_valid():
            task = form.save(commit=False)
            task.creator = request.user
            if initial_project:
                task.project = initial_project
            task._actor = request.user
            task.save()
            form.save_m2m()
            messages.success(request, f"Task '{task.title}' created successfully!")
            return redirect('tasks:detail', pk=task.pk)
        else:
            messages.error(request, "Please correct the form errors.")
    else:
        form = TaskForm(user=request.user, project=initial_project)

    return render(request, 'tasks/task_form.html', {'form': form, 'action': 'Create', 'project': initial_project})


@login_required
def task_edit(request: HttpRequest, pk: int) -> HttpResponse:
    """Edit an existing task."""
    task = get_object_or_404(Task, pk=pk)
    if not task.project.can_manage_tasks(request.user):
        raise PermissionDenied("You do not have permission to edit this task.")

    if request.method == 'POST':
        form = TaskForm(request.POST, instance=task, user=request.user)
        if form.is_valid():
            task = form.save(commit=False)
            task._actor = request.user
            task.save()
            form.save_m2m()
            messages.success(request, f"Task '{task.title}' updated successfully!")
            return redirect('tasks:detail', pk=task.pk)
        else:
            messages.error(request, "Please fix the indicated errors.")
    else:
        form = TaskForm(instance=task, user=request.user)

    return render(request, 'tasks/task_form.html', {'form': form, 'task': task, 'action': 'Edit'})


@login_required
def task_delete(request: HttpRequest, pk: int) -> HttpResponse:
    """Delete a task."""
    task = get_object_or_404(Task, pk=pk)
    if not task.project.can_manage_tasks(request.user):
        raise PermissionDenied("You do not have permission to delete this task.")

    project_pk = task.project.pk
    if request.method == 'POST':
        title = task.title
        task.delete()
        messages.success(request, f"Task '{title}' has been deleted.")
        return redirect('projects:detail', pk=project_pk)

    return render(request, 'tasks/task_confirm_delete.html', {'task': task})
