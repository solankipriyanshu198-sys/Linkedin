from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import Group

# Consolidate all your imports here to avoid confusion
from .models import (
    Job, Company, UserProfile, Post, Experience, Education,
    Certification, Application, ConnectionRequest,
    Message, MessageThread, SavedJob,
    CandidateUser, EmployerUser
)

# 1. Unregister Groups (Optional: Hides "Groups" from Authentication section)
admin.site.unregister(Group)

# 2. Candidate User Admin (Only shows users WITHOUT a company)
@admin.register(CandidateUser)
class CandidateUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_active')
    search_fields = ('username', 'email')
    
    def get_queryset(self, request):
        # Filter: Show users who do NOT have a company linked
        return super().get_queryset(request).filter(company__isnull=True)

# 3. Employer User Admin (Only shows users WITH a company)
@admin.register(EmployerUser)
class EmployerUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'company_name', 'is_active')
    search_fields = ('username', 'email', 'company__company_name')

    # Custom column to show Company Name in the User list
    def company_name(self, obj):
        return obj.company.company_name if hasattr(obj, 'company') and obj.company else '-'
    company_name.short_description = 'Company'

    def get_queryset(self, request):
        # Filter: Show users who HAVE a company linked
        return super().get_queryset(request).filter(company__isnull=False)

# 4. Job Admin (Customized)
@admin.register(Job)
class JobAdmin(admin.ModelAdmin):
    # Note: Ensure 'company_name' exists in your Job model or use 'company'
    list_display = ('title', 'company', 'job_type', 'location', 'created_at') 
    list_filter = ('job_type', 'is_remote', 'is_urgent')
    # Use double underscore for foreign key search (company__company_name)
    search_fields = ('title', 'company__company_name', 'description')

# 5. Company Admin (Customized)
@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ('company_name', 'website', 'location')
    search_fields = ('company_name', 'website', 'location')

# 6. Simple Registers (For models without custom admin classes)
admin.site.register(UserProfile)
admin.site.register(Post)
admin.site.register(Experience)
admin.site.register(Education)
admin.site.register(Application)
admin.site.register(Certification)
admin.site.register(ConnectionRequest)
admin.site.register(SavedJob)