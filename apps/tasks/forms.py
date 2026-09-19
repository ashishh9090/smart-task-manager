from django import forms
from django.contrib.auth.models import User
from django.db.models import Q
from .models import Task, Tag
from apps.projects.models import Project


class TaskForm(forms.ModelForm):
    tags = forms.ModelMultipleChoiceField(
        queryset=Tag.objects.all(),
        required=False,
        widget=forms.SelectMultiple(attrs={'class': 'form-select', 'size': '4'})
    )

    class Meta:
        model = Task
        fields = ['title', 'description', 'project', 'assignee', 'status', 'priority', 'due_date', 'tags']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Task Title'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Detailed task requirements and acceptance criteria...'}),
            'project': forms.Select(attrs={'class': 'form-select'}),
            'assignee': forms.Select(attrs={'class': 'form-select'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'priority': forms.Select(attrs={'class': 'form-select'}),
            'due_date': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
        }

    def __init__(self, *args, user=None, project=None, **kwargs):
        super().__init__(*args, **kwargs)
        if user:
            # Only list projects the user belongs to
            allowed_projects = Project.objects.filter(
                Q(owner=user) | Q(memberships__user=user)
            ).distinct()
            self.fields['project'].queryset = allowed_projects

        if project:
            self.fields['project'].initial = project
            self.fields['project'].disabled = True
            # Restrict assignees to project members
            project_user_ids = project.memberships.values_list('user_id', flat=True)
            self.fields['assignee'].queryset = User.objects.filter(id__in=project_user_ids)
        elif self.instance and self.instance.pk:
            project_user_ids = self.instance.project.memberships.values_list('user_id', flat=True)
            self.fields['assignee'].queryset = User.objects.filter(id__in=project_user_ids)


class TagForm(forms.ModelForm):
    class Meta:
        model = Tag
        fields = ['name', 'color']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Tag Name'}),
            'color': forms.TextInput(attrs={'type': 'color', 'class': 'form-control form-control-color'}),
        }
