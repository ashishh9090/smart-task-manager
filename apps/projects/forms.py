from django import forms
from django.contrib.auth.models import User
from django.db.models import Q
from .models import Project, ProjectMember


class ProjectForm(forms.ModelForm):
    class Meta:
        model = Project
        fields = ['title', 'description', 'status', 'color']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Project Title'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Project details and goals...'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'color': forms.TextInput(attrs={'type': 'color', 'class': 'form-control form-control-color', 'title': 'Choose accent color'}),
        }


class ProjectMemberAddForm(forms.Form):
    username_or_email = forms.CharField(
        max_length=150,
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter username or email address'})
    )
    role = forms.ChoiceField(
        choices=ProjectMember.ROLE_CHOICES,
        initial=ProjectMember.ROLE_MEMBER,
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    def __init__(self, *args, project=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.project = project

    def clean_username_or_email(self) -> User:
        query = self.cleaned_data.get('username_or_email', '').strip()
        user = User.objects.filter(Q(username__iexact=query) | Q(email__iexact=query)).first()
        if not user:
            raise forms.ValidationError(f"No user found with username or email '{query}'.")
        if self.project and self.project.is_member(user):
            raise forms.ValidationError(f"{user.username} is already a member of this project.")
        return user
