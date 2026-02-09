from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import AuthenticationForm
from .models import (
    Company, UserProfile, Job,
    Experience, Education, Certification, Post
)

# ==========================================
# 1. AUTHENTICATION & REGISTRATION FORMS
# ==========================================

class UserRegistrationForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput(attrs={
        'placeholder': 'Min. 8 characters', 
        'class': 'form-input'
    }))
    confirm_password = forms.CharField(widget=forms.PasswordInput(attrs={
        'placeholder': 'Re-enter password', 
        'class': 'form-input'
    }), label="Confirm Password")

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'password']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'First Name'}),
            'last_name': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Last Name'}),
            'email': forms.EmailInput(attrs={'class': 'form-input', 'placeholder': 'name@example.com'}),
        }

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("This email is already registered.")
        return email

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        confirm_password = cleaned_data.get("confirm_password")

        if password != confirm_password:
            self.add_error('confirm_password', "Passwords do not match")
        return cleaned_data


class CompanyRegistrationForm(forms.ModelForm):
    class Meta:
        model = Company
        fields = ['company_name', 'location', 'website', 'description', 'logo']
        widgets = {
            'company_name': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Company Name'}),
            'location': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Headquarters Location'}),
            
            # ✅ FIXED: Used forms.URLInput instead of forms.URLField
            'website': forms.URLInput(attrs={'class': 'form-input', 'placeholder': 'https://example.com'}),
            
            'description': forms.Textarea(attrs={'class': 'form-input', 'placeholder': 'Tell us about your company...', 'rows': 4}),
            'logo': forms.FileInput(attrs={'class': 'form-input'}), 
        }


class UserLoginForm(AuthenticationForm):
    username = forms.CharField(
        widget=forms.TextInput(attrs={'placeholder': 'Username', 'class': 'form-control'})
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'placeholder': 'Password', 'class': 'form-control'})
    )


# ==========================================
# 2. COMPANY MANAGEMENT FORMS
# ==========================================

class CompanyUpdateForm(forms.ModelForm):
    class Meta:
        model = Company
        fields = [
            'company_name', 'location', 'logo', 'cover_image',
            'website', 'description', 
            'industry', 'company_size', 'founded', 'specialties' 
        ]
        widgets = {
            'company_name': forms.TextInput(attrs={'class': 'form-control'}),
            'location': forms.TextInput(attrs={'class': 'form-control'}),
            'website': forms.URLInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 5}),
            'logo': forms.FileInput(attrs={'class': 'form-control'}),
            'cover_image': forms.FileInput(attrs={'class': 'form-control'}),
            'industry': forms.TextInput(attrs={'class': 'form-control'}),
            'company_size': forms.TextInput(attrs={'class': 'form-control'}),
            'founded': forms.TextInput(attrs={'class': 'form-control'}),
            'specialties': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }


# ==========================================
# 3. JOB POST FORM
# ==========================================

class JobPostForm(forms.ModelForm):
    class Meta:
        model = Job
        fields = [
            'title', 'location', 'job_type',
            'salary_min', 'salary_max',
            'description', 'skills',
            'requirements', 'benefits',
            'is_remote', 'is_urgent'
        ]
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Senior Software Engineer'}),
            'location': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. New York, NY'}),
            'job_type': forms.Select(attrs={'class': 'form-select'}),
            'salary_min': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Min Salary'}),
            'salary_max': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Max Salary'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 6}),
            'skills': forms.TextInput(attrs={
                'class': 'form-control', 
                'placeholder': 'Python, Django, React, JavaScript'
            }),
            'requirements': forms.Textarea(attrs={
                'class': 'form-control', 
                'rows': 4, 
                'placeholder': '- 3+ years of experience\n- Knowledge of Python'
            }),
            'benefits': forms.Textarea(attrs={
                'class': 'form-control', 
                'rows': 4, 
                'placeholder': '- Health Insurance\n- Remote Options'
            }),
            'is_remote': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_urgent': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


# ==========================================
# 4. USER PROFILE & DETAILS FORMS
# ==========================================

class UserProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ['headline', 'location', 'phone_number', 'skills', 'bio', 'profile_picture', 'resume']
        widgets = {
            'headline': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Software Engineer | Python Developer'}),
            'location': forms.TextInput(attrs={'class': 'form-control'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-control'}),
            'skills': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Python, Django, React'}),
            'bio': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'profile_picture': forms.FileInput(attrs={'class': 'form-control'}),
            'resume': forms.FileInput(attrs={'class': 'form-control'}),
        }

class ProfileImageForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ['profile_picture', 'cover_image']

class ExperienceForm(forms.ModelForm):
    class Meta:
        model = Experience
        fields = ['title', 'company', 'location', 'start_date', 'end_date', 'is_current', 'description']
        widgets = {
            'start_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'end_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'company': forms.TextInput(attrs={'class': 'form-control'}),
            'location': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'is_current': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class EducationForm(forms.ModelForm):
    class Meta:
        model = Education
        fields = ['school', 'degree', 'field_of_study', 'start_date', 'end_date']
        widgets = {
            'start_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'end_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'school': forms.TextInput(attrs={'class': 'form-control'}),
            'degree': forms.TextInput(attrs={'class': 'form-control'}),
            'field_of_study': forms.TextInput(attrs={'class': 'form-control'}),
        }


class CertificationForm(forms.ModelForm):
    class Meta:
        model = Certification
        fields = ['name', 'issuing_organization', 'issue_date', 'credential_url']
        widgets = {
            'issue_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'issuing_organization': forms.TextInput(attrs={'class': 'form-control'}),
            'credential_url': forms.URLInput(attrs={'class': 'form-control'}),
        }


# ==========================================
# 5. SOCIAL POST FORM
# ==========================================

class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ['content', 'image', 'video'] 
        widgets = {
            'content': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Start a post...'
            }),
            'image': forms.FileInput(attrs={'class': 'form-control'}),
            'video': forms.FileInput(attrs={'class': 'form-control'}),
        }

from django import forms
from .models import JobAlert

class JobAlertForm(forms.ModelForm):
    class Meta:
        model = JobAlert
        fields = ['keyword', 'location']
        widgets = {
            'keyword': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Job Title or Skill'}),
            'location': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'City'}),
        }

# forms.py
from django import forms
from django_recaptcha.fields import ReCaptchaField
from django_recaptcha.widgets import ReCaptchaV2Checkbox

# jobportal/forms.py
class CompanyRegistrationForm(forms.ModelForm):
    # User fields (Keep these)
    email = forms.EmailField()
    password = forms.CharField(widget=forms.PasswordInput)

    class Meta:
        model = Company
        # ⚠️ ADD 'location' AND 'description' HERE:
        fields = ['company_name', 'website', 'location', 'description', 'logo']