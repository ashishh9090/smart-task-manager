from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import HttpRequest, HttpResponse
from django.db.models import Q
from django.utils import timezone
from datetime import timedelta
import json
from apps.projects.models import Project
from apps.tasks.models import Task, TaskActivity


@login_required
def dashboard_index(request: HttpRequest) -> HttpResponse:
    """
    Main executive dashboard showing aggregated metrics, upcoming deadlines,
    completion rate, Chart.js breakdown, and recent activities.
    """
    user = request.user
    now = timezone.now()
    next_7_days = now + timedelta(days=7)

    # Scoped projects
    user_projects = Project.objects.filter(
        Q(owner=user) | Q(memberships__user=user)
    ).distinct()

    # Base tasks queryset
    tasks = Task.objects.filter(project__in=user_projects).distinct()

    total_tasks = tasks.count()
    completed_tasks = tasks.filter(status=Task.STATUS_DONE).count()
    in_progress_tasks = tasks.filter(status=Task.STATUS_IN_PROGRESS).count()
    review_tasks = tasks.filter(status=Task.STATUS_REVIEW).count()
    todo_tasks = tasks.filter(status=Task.STATUS_TODO).count()

    overdue_tasks = tasks.filter(due_date__lt=now).exclude(status=Task.STATUS_DONE).count()

    completion_rate = round((completed_tasks / total_tasks * 100), 1) if total_tasks > 0 else 0.0

    # Tasks assigned specifically to current user
    my_tasks_count = tasks.filter(assignee=user).count()
    my_pending_tasks = tasks.filter(assignee=user).exclude(status=Task.STATUS_DONE).count()

    # Upcoming deadlines within next 7 days
    upcoming_deadlines = tasks.filter(
        due_date__gte=now,
        due_date__lte=next_7_days,
    ).exclude(status=Task.STATUS_DONE).select_related('project', 'assignee', 'assignee__profile').order_by('due_date')[:6]

    # Priority breakdown
    priority_counts = {
        'urgent': tasks.filter(priority=Task.PRIORITY_URGENT).count(),
        'high': tasks.filter(priority=Task.PRIORITY_HIGH).count(),
        'medium': tasks.filter(priority=Task.PRIORITY_MEDIUM).count(),
        'low': tasks.filter(priority=Task.PRIORITY_LOW).count(),
    }

    # Project progress summaries
    project_stats = []
    for proj in user_projects.filter(status=Project.STATUS_ACTIVE)[:5]:
        p_total = proj.tasks.count()
        p_done = proj.tasks.filter(status=Task.STATUS_DONE).count()
        p_rate = round((p_done / p_total * 100)) if p_total > 0 else 0
        project_stats.append({
            'project': proj,
            'total': p_total,
            'done': p_done,
            'rate': p_rate,
        })

    # Recent activities across user's projects
    recent_activities = TaskActivity.objects.filter(
        task__project__in=user_projects
    ).select_related('task', 'user', 'user__profile', 'task__project').order_by('-created_at')[:8]

    # Chart.js JSON data
    status_chart_data = {
        'labels': ['To Do', 'In Progress', 'In Review', 'Done'],
        'data': [todo_tasks, in_progress_tasks, review_tasks, completed_tasks],
    }

    priority_chart_data = {
        'labels': ['Urgent', 'High', 'Medium', 'Low'],
        'data': [
            priority_counts['urgent'],
            priority_counts['high'],
            priority_counts['medium'],
            priority_counts['low']
        ],
    }

    context = {
        'total_projects': user_projects.count(),
        'active_projects': user_projects.filter(status=Project.STATUS_ACTIVE).count(),
        'total_tasks': total_tasks,
        'completed_tasks': completed_tasks,
        'in_progress_tasks': in_progress_tasks,
        'overdue_tasks': overdue_tasks,
        'completion_rate': completion_rate,
        'my_tasks_count': my_tasks_count,
        'my_pending_tasks': my_pending_tasks,
        'upcoming_deadlines': upcoming_deadlines,
        'project_stats': project_stats,
        'recent_activities': recent_activities,
        'status_chart_json': json.dumps(status_chart_data),
        'priority_chart_json': json.dumps(priority_chart_data),
    }
    return render(request, 'dashboard/index.html', context)
