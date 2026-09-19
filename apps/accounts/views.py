from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.views import LoginView, LogoutView
from django.contrib.auth.decorators import login_required
from django.http import HttpRequest, HttpResponse
from django.urls import reverse_lazy
from .forms import UserRegisterForm, UserUpdateForm, ProfileUpdateForm


class CustomLoginView(LoginView):
    template_name = 'accounts/login.html'
    redirect_authenticated_user = True

    def form_valid(self, form) -> HttpResponse:
        messages.success(self.request, f"Welcome back, {form.get_user().username}!")
        return super().form_valid(form)


class CustomLogoutView(LogoutView):
    next_page = reverse_lazy('accounts:login')

    def dispatch(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        if request.user.is_authenticated:
            messages.info(request, "You have been logged out successfully.")
        return super().dispatch(request, *args, **kwargs)


def register(request: HttpRequest) -> HttpResponse:
    if request.user.is_authenticated:
        return redirect('dashboard:index')

    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, f"Account created successfully! Welcome to Smart Task Manager, {user.username}.")
            return redirect('dashboard:index')
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = UserRegisterForm()

    return render(request, 'accounts/register.html', {'form': form})


@login_required
def profile_view(request: HttpRequest) -> HttpResponse:
    profile = request.user.profile
    if request.method == 'POST':
        user_form = UserUpdateForm(request.POST, instance=request.user)
        profile_form = ProfileUpdateForm(request.POST, request.FILES, instance=profile)

        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            messages.success(request, "Your profile has been updated successfully.")
            return redirect('accounts:profile')
        else:
            messages.error(request, "Please fix the errors indicated below.")
    else:
        user_form = UserUpdateForm(instance=request.user)
        profile_form = ProfileUpdateForm(instance=profile)

    context = {
        'user_form': user_form,
        'profile_form': profile_form,
        'profile': profile,
    }
    return render(request, 'accounts/profile.html', context)


# Custom error handlers
def error_403(request: HttpRequest, exception=None) -> HttpResponse:
    return render(request, 'errors/403.html', status=403)


def error_404(request: HttpRequest, exception=None) -> HttpResponse:
    return render(request, 'errors/404.html', status=404)


def error_500(request: HttpRequest) -> HttpResponse:
    return render(request, 'errors/500.html', status=500)
