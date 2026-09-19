from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from .models import UserProfile


class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'Profile Info'
    fields = ('avatar', 'job_title', 'department', 'bio', 'email_notifications')


class UserAdmin(BaseUserAdmin):
    inlines = (UserProfileInline,)
    list_display = ('username', 'email', 'first_name', 'last_name', 'get_job_title', 'is_staff')

    @admin.display(description='Job Title')
    def get_job_title(self, obj: User) -> str:
        return obj.profile.job_title if hasattr(obj, 'profile') else '-'


admin.site.unregister(User)
admin.site.register(User, UserAdmin)
admin.site.register(UserProfile)
