import json
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.db.models import Count, Q, Sum
from django.core.exceptions import ObjectDoesNotExist, PermissionDenied
from django.views.decorators.http import require_POST
from django.utils import timezone
from django.db.models import Max
import re # Import regex to handle punctuation
import requests
from urllib.parse import urlencode
import os


# 1. IMPORT MODELS
from .models import (
    Job, Application, SavedJob, Company, 
    UserProfile, Experience, Education, Certification, Post,
    ConnectionRequest, MessageThread, Message, PostComment, ProfileView, Connection
)

# 2. IMPORT FORMS
from .forms import (
    UserRegistrationForm, UserLoginForm, CompanyRegistrationForm,
    JobPostForm, UserProfileForm, PostForm,
    ExperienceForm, EducationForm, CertificationForm, CompanyUpdateForm,
    ProfileImageForm 
)

############################
# PROFILE MATCH HELPER FUNCTIONS
############################

def split_skills(skill_text):
    """
    Splits a skill string by Commas (,) OR Newlines (Enter key).
    This handles cases where you pasted a list or pressed Enter between skills.
    """
    if not skill_text:
        return []
    
    # Regex Explanation:
    # [,\n\r]+  -> Means "Split whenever you find a comma OR a new line"
    skills = re.split(r'[,\n\r]+', skill_text)
    
    # Clean up each skill (remove extra spaces)
    return [s.strip() for s in skills if s.strip()]

def normalize_skill(skill):
    """
    Standardizes a skill for comparison:
    - "Sketch." -> "sketch" (Removes dots)
    - "Python"  -> "python" (Case insensitive)
    - " C++ "   -> "c++"    (Removes spaces)
    """
    if not skill:
        return ""
    # Lowercase and remove trailing punctuation (. or ,)
    return skill.strip().lower().rstrip('.,')

def calculate_match_score(job_skills_text, candidate_skills_text):
    """
    Calculates the match percentage between two raw text fields.
    """
    # 1. Use the SMART SPLIT on both texts
    job_list = split_skills(job_skills_text)
    candidate_list = split_skills(candidate_skills_text)
    
    if not job_list:
        return 0
    
    # 2. Normalize both lists (handling "Sketch." vs "Sketch")
    job_set = {normalize_skill(s) for s in job_list}
    candidate_set = {normalize_skill(s) for s in candidate_list}
    
    # Remove empty strings if any crept in
    job_set.discard("")
    candidate_set.discard("")

    if not job_set:
        return 0

    # 3. Count Matches
    matches = 0
    for j_skill in job_set:
        if j_skill in candidate_set:
            matches += 1
            
    # Calculate Percentage
    return int((matches / len(job_set)) * 100)

############################
# 0. ROLE-BASED HELPERS    #
############################

def candidate_only(view_func):
    """Decorator to prevent Employers from accessing Candidate pages."""
    def _wrapped_view(request, *args, **kwargs):
        if request.user.is_authenticated and hasattr(request.user, 'company'):
            return redirect('company_dashboard')
        return view_func(request, *args, **kwargs)
    return _wrapped_view

def employer_only(view_func):
    """Decorator to prevent Candidates from accessing Employer pages."""
    def _wrapped_view(request, *args, **kwargs):
        if request.user.is_authenticated and not hasattr(request.user, 'company'):
            return redirect('home')
        return view_func(request, *args, **kwargs)
    return _wrapped_view

############################
# 1. AUTHENTICATION        #
############################

# Removed: company_detail view - use company_profile instead

def register_view(request):
    if request.user.is_authenticated:
        if hasattr(request.user, 'company'):
            return redirect('company_dashboard')
        return redirect('home')

    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.username = form.cleaned_data['email']
            user.set_password(form.cleaned_data['password'])
            user.save()
            login(request, user)
            return redirect('create_profile')
    else:
        form = UserRegistrationForm()
    return render(request, 'jobportal/register.html', {'form': form})


def login_view(request):
    if request.user.is_authenticated:
        if hasattr(request.user, 'company'):
            return redirect('company_dashboard')
        return redirect('home')

    if request.method == 'POST':
        form = UserLoginForm(data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            next_url = request.POST.get('next') or request.GET.get('next')
            if next_url:
                return redirect(next_url)
            if hasattr(user, 'company'):
                return redirect('company_dashboard')
            return redirect('home')
    else:
        form = UserLoginForm()
    return render(request, 'jobportal/login.html', {'form': form})


# ==========================================
# GOOGLE OAUTH AUTHENTICATION
#import os
import requests
from django.shortcuts import redirect, render
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.models import User
from django.contrib import messages
from urllib.parse import urlencode

# ==========================================
# GOOGLE OAUTH CONFIGURATION
# ==========================================
import os
import requests
from django.shortcuts import redirect, render
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.models import User
from django.contrib import messages
from urllib.parse import urlencode

# Make sure your forms and models are imported correctly
# You might need to adjust this line if UserLoginForm is in a different file
from .forms import UserLoginForm 

# ==========================================
# GOOGLE OAUTH CONFIGURATION
# ==========================================

# 1. Your Client ID (Fixed)
GOOGLE_CLIENT_ID = '751752402385-979qquoil594tsd98r9hpgv35calm7m5.apps.googleusercontent.com'

# 2. PASTE YOUR NEW SECRET HERE (The one from your screenshot '****gkNX' is hidden)
GOOGLE_CLIENT_SECRET = 'YOUR_SECRET_KEY'

# 3. Correct Redirect URI (Matches Google Console)
GOOGLE_REDIRECT_URI = 'http://127.0.0.1:8000/auth/google/callback/'

# ==========================================
# GOOGLE LOGIN VIEWS
# ==========================================

def google_login(request):
    """
    Redirect user to Google OAuth consent screen
    """
    params = {
        'client_id': GOOGLE_CLIENT_ID,
        'redirect_uri': GOOGLE_REDIRECT_URI,
        'response_type': 'code',
        'scope': 'email profile',
        'access_type': 'offline',
        'prompt': 'select_account',
    }
    return redirect(f"https://accounts.google.com/o/oauth2/v2/auth?{urlencode(params)}")

def google_callback(request):
    """
    Handle Google OAuth callback
    """
    code = request.GET.get('code')
    error = request.GET.get('error')
    
    if error:
        messages.error(request, f"Google authentication failed: {error}")
        return redirect('login')
    
    if not code:
        messages.error(request, "No authorization code received from Google")
        return redirect('login')
    
    try:
        # Exchange code for access token
        token_url = 'https://oauth2.googleapis.com/token'
        data = {
            'code': code,
            'client_id': GOOGLE_CLIENT_ID,
            'client_secret': GOOGLE_CLIENT_SECRET,
            'redirect_uri': GOOGLE_REDIRECT_URI,
            'grant_type': 'authorization_code',
        }
        
        response = requests.post(token_url, data=data, timeout=10)
        token_data = response.json()
        
        if 'error' in token_data:
            messages.error(request, f"Token exchange failed: {token_data['error']}")
            return redirect('login')
        
        access_token = token_data.get('access_token')
        
        # Get user info from Google
        user_info_url = 'https://www.googleapis.com/oauth2/v2/userinfo'
        headers = {'Authorization': f'Bearer {access_token}'}
        user_response = requests.get(user_info_url, headers=headers, timeout=10)
        user_info = user_response.json()
        
        if 'error' in user_info:
            messages.error(request, "Failed to retrieve user information from Google")
            return redirect('login')
        
        email = user_info.get('email')
        first_name = user_info.get('given_name', '')
        last_name = user_info.get('family_name', '')
        
        # Check if user exists
        user = User.objects.filter(email=email).first()
        
        if not user:
            # Create new user
            username = email.split('@')[0]
            base_username = username
            counter = 1
            while User.objects.filter(username=username).exists():
                username = f"{base_username}{counter}"
                counter += 1
            
            user = User.objects.create_user(
                username=username,
                email=email,
                first_name=first_name,
                last_name=last_name
            )
            messages.success(request, f"Welcome {first_name}! Your account has been created.")
            login(request, user)
            # You mentioned 'create_profile' in previous logs. Ensure this view exists or change to 'home'
            return redirect('home') 
        
        # Login existing user
        login(request, user)
        messages.success(request, f"Welcome back, {user.first_name}!")
        
        if hasattr(user, 'company'):
            return redirect('company_dashboard')
        return redirect('home')
    
    except requests.RequestException as e:
        messages.error(request, f"Error communicating with Google: {str(e)}")
        return redirect('login')
    except Exception as e:
        messages.error(request, f"An error occurred: {str(e)}")
        return redirect('login')

# ==========================================
# EMPLOYER & LOGOUT VIEWS (RESTORED)
# ==========================================

def employer_login_view(request):
    if request.user.is_authenticated:
        if hasattr(request.user, 'company'):
            return redirect('company_dashboard')
        return redirect('home')

    if request.method == 'POST':
        form = UserLoginForm(data=request.POST)
        if form.is_valid():
            user = form.get_user()
            if hasattr(user, 'company'):
                login(request, user)
                next_url = request.POST.get('next') or request.GET.get('next')
                if next_url:
                    return redirect(next_url)
                return redirect('company_dashboard')
            else:
                messages.warning(request, "No company profile found. Please register as an employer.")
                return redirect('employer_register') 
        else:
            messages.error(request, "Invalid username or password.")
    else:
        form = UserLoginForm()
    return render(request, 'companies/company_login.html', {'form': form})

def logout_view(request):
    logout(request)
    return redirect('login')

############################
# 2. MAIN PAGES & JOBS     #
############################

@login_required(login_url='login')
@candidate_only
def home(request):
    jobs = Job.objects.all().order_by('-created_at')
    
    # Fetch all posts from users and employers
    posts = Post.objects.select_related('user').prefetch_related('likes', 'comments').order_by('-created_at')

    # Search Logic
    query = request.GET.get('q')
    if query:
        jobs = jobs.filter(
            Q(title__icontains=query) | 
            Q(company__company_name__icontains=query) |
            Q(description__icontains=query) |
            Q(location__icontains=query)
        )

    # Filter Logic
    if request.GET.get('remote') == 'on':
        jobs = jobs.filter(is_remote=True)
    if request.GET.get('fulltime') == 'on':
        jobs = jobs.filter(job_type__iexact='Full Time')

    top_companies = Company.objects.annotate(
        total_positions=Count('jobs') 
    ).order_by('-total_positions')[:5]

    # Sidebar counts
    applied_count = 0
    saved_count = 0
    if request.user.is_authenticated:
        applied_count = Application.objects.filter(user=request.user).count()
        saved_count = SavedJob.objects.filter(user=request.user).count()

    context = {
        'jobs': jobs,
        'posts': posts,
        'top_companies': top_companies,
        'applied_count': applied_count,
        'saved_count': saved_count,
    }
    return render(request, 'jobportal/home.html', context)


def search_results(request):
    """Unified search across users, companies, and jobs"""
    query = request.GET.get('q', '').strip()
    search_type = request.GET.get('type', 'all')  # all, people, companies, jobs
    
    users_list = []
    companies_list = []
    jobs_list = []
    
    if query:
        # Split query into words for better matching
        query_words = query.split()
        
        # Search Users/People
        if search_type in ['all', 'people']:
            user_query = Q()
            # Add individual word searches for flexible matching
            for word in query_words:
                user_query |= Q(username__icontains=word)
                user_query |= Q(first_name__icontains=word)
                user_query |= Q(last_name__icontains=word)
                user_query |= Q(userprofile__headline__icontains=word)
            # Also search for the full query as a phrase
            user_query |= Q(username__icontains=query)
            user_query |= Q(first_name__icontains=query)
            user_query |= Q(last_name__icontains=query)
            user_query |= Q(userprofile__headline__icontains=query)
            
            users_list = User.objects.filter(user_query).distinct()
        
        # Search Companies
        if search_type in ['all', 'companies']:
            company_query = Q()
            for word in query_words:
                company_query |= Q(company_name__icontains=word)
                company_query |= Q(industry__icontains=word)
                company_query |= Q(location__icontains=word)
            company_query |= Q(company_name__icontains=query)
            company_query |= Q(industry__icontains=query)
            company_query |= Q(location__icontains=query)
            
            companies_list = Company.objects.filter(company_query).distinct()
        
        # Search Jobs
        if search_type in ['all', 'jobs']:
            job_query = Q()
            for word in query_words:
                job_query |= Q(title__icontains=word)
                job_query |= Q(description__icontains=word)
                job_query |= Q(company__company_name__icontains=word)
                job_query |= Q(location__icontains=word)
                job_query |= Q(skills__icontains=word)
            job_query |= Q(title__icontains=query)
            job_query |= Q(description__icontains=query)
            job_query |= Q(company__company_name__icontains=query)
            job_query |= Q(location__icontains=query)
            job_query |= Q(skills__icontains=query)
            
            jobs_list = Job.objects.filter(job_query).select_related('company').distinct().order_by('-created_at')
    
    context = {
        'query': query,
        'search_type': search_type,
        'users_list': users_list,
        'companies_list': companies_list,
        'jobs_list': jobs_list,
        'total_results': len(users_list) + len(companies_list) + len(jobs_list),
    }
    return render(request, 'jobportal/search_results.html', context)


@login_required(login_url='login') 
@candidate_only
def find_jobs(request):
    jobs = Job.objects.all().order_by('-created_at')
    query = request.GET.get('q')
    
    if query:
        jobs = jobs.filter(
            Q(title__icontains=query) |
            Q(company__company_name__icontains=query) |
            Q(location__icontains=query) |
            Q(description__icontains=query)
        )

    if request.GET.get('remote') == 'on':
        jobs = jobs.filter(is_remote=True)
    if request.GET.get('fulltime') == 'on':
        jobs = jobs.filter(job_type='Full Time')
    if request.GET.get('internship') == 'on':
        jobs = jobs.filter(job_type='Internship')

    context = {'jobs': jobs}
    return render(request, 'jobportal/find_jobs.html', context)

# Put this function at the very top of views.py, outside of any class or function
def calculate_match_score(job_skills, candidate_skills):
    if not job_skills: 
        return 0
    
    # Simple logic: check how many job skills the candidate has
    matches = 0
    # Assuming skills are strings. If they are objects, use skill.name
    for skill in job_skills:
        if skill in candidate_skills:
            matches += 1
            
    score = (matches / len(job_skills)) * 100
    return round(score)

# Add this new view function inside views.py

def kanban_board(request, job_id):
    job = get_object_or_404(Job, id=job_id)
    applicants = Application.objects.filter(job=job)

    # 1. Calculate Match Score for each applicant
    for app in applicants:
        c_text = ""
        # Safely get candidate skills text
        if hasattr(app.user, 'userprofile') and app.user.userprofile.skills:
             c_text = app.user.userprofile.skills
             
        # Use the same smart calculator for the kanban board
        app.match_score = calculate_match_score(job.skills or "", c_text)

    context = {
        'job': job,
        'applicants': applicants
    }
    return render(request, 'companies/kanban_board.html', context)



from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
# Import your models here if not already imported
# from .models import Job, Application, SavedJob

# --- 1. Helper Function (Paste this ABOVE your view function) ---
def calculate_match_score(job_skills, candidate_skills):
    """
    Calculates percentage match between job requirements and candidate skills.
    Expects lists of strings.
    """
    if not job_skills:
        return 0
    
    # Convert to sets for easy comparison
    # Lowercase everything to ensure 'Python' matches 'python'
    j_skills_set = {s.lower() for s in job_skills}
    c_skills_set = {s.lower() for s in candidate_skills}
    
    # Count matches
    match_count = 0
    for skill in j_skills_set:
        if skill in c_skills_set:
            match_count += 1
            
    if len(j_skills_set) == 0:
        return 0
        
    score = (match_count / len(j_skills_set)) * 100
    return int(score)


# --- 2. Updated View Function ---


# --- 1. ROBUST MATCHING HELPER FUNCTION (UPDATED) ---
def split_skills(skill_text):
    """
    The 'Better Solution':
    Splits a skill string by Commas (,) OR Newlines (Enter key).
    This handles cases where you pasted a list or pressed Enter between skills.
    """
    if not skill_text:
        return []
    
    # Regex Explanation:
    # [,\n\r]+  -> Means "Split whenever you find a comma OR a new line"
    skills = re.split(r'[,\n\r]+', skill_text)
    
    # Clean up each skill (remove extra spaces)
    return [s.strip() for s in skills if s.strip()]

def normalize_skill(skill):
    """
    Standardizes a skill for comparison:
    - "Sketch." -> "sketch" (Removes dots)
    - "Python"  -> "python" (Case insensitive)
    - " C++ "   -> "c++"    (Removes spaces)
    """
    if not skill:
        return ""
    # Lowercase and remove trailing punctuation (. or ,)
    return skill.strip().lower().rstrip('.,')

def calculate_match_score(job_skills_text, candidate_skills_text):
    """
    Calculates the match percentage between two raw text fields.
    """
    # 1. Use the SMART SPLIT on both texts
    job_list = split_skills(job_skills_text)
    candidate_list = split_skills(candidate_skills_text)
    
    if not job_list:
        return 0
    
    # 2. Normalize both lists (handling "Sketch." vs "Sketch")
    job_set = {normalize_skill(s) for s in job_list}
    candidate_set = {normalize_skill(s) for s in candidate_list}
    
    # Remove empty strings if any crept in
    job_set.discard("")
    candidate_set.discard("")

    if not job_set:
        return 0

    # 3. Count Matches
    matches = 0
    for j_skill in job_set:
        if j_skill in candidate_set:
            matches += 1
            
    # Calculate Percentage
    return int((matches / len(job_set)) * 100)

# ==========================================
# 2. VIEWS
# ==========================================

@login_required(login_url='login')
def job_detail_view(request, pk):
    job = get_object_or_404(Job, pk=pk)
    
    # --- CALCULATE MATCH SCORE ---
    match_score = 0
    if request.user.is_authenticated and hasattr(request.user, 'userprofile'):
        # Pass the raw text fields directly to our smart calculator
        match_score = calculate_match_score(
            job.skills, 
            request.user.userprofile.skills
        )
    # -----------------------------

    # Track Views count
    if not hasattr(job, 'views'):
        job.views = 0
    job.views += 1
    job.save()

    has_applied = Application.objects.filter(user=request.user, job=job).exists()
    is_saved = SavedJob.objects.filter(user=request.user, job=job).exists()
    similar_jobs = Job.objects.exclude(pk=pk).order_by('?')[:3]

    if request.method == 'POST':
        if hasattr(request.user, 'company'):
            messages.error(request, "Employers cannot apply for jobs.")
            return redirect('job_detail', pk=pk)

        if 'email' in request.POST or 'apply' in request.POST:
            if not has_applied:
                # 1. Get Resume
                resume_file = request.FILES.get('resume')
                if not resume_file and hasattr(request.user, 'userprofile') and request.user.userprofile.resume:
                    resume_file = request.user.userprofile.resume

                # 2. Capture Form Data
                phone_val = request.POST.get('phone')
                experience_val = request.POST.get('q2')
                commute_val = request.POST.get('q1')

                # 3. Create Application
                Application.objects.create(
                    user=request.user, 
                    job=job, 
                    status='applied', 
                    resume=resume_file,
                    phone=phone_val,
                    experience=experience_val,
                    commute=commute_val
                )
                
                messages.success(request, f'Successfully applied to {job.title}!')
                return redirect('my_applications')
            else:
                messages.warning(request, 'You have already applied for this job.')
        
        elif 'save' in request.POST:
            if is_saved:
                SavedJob.objects.filter(user=request.user, job=job).delete()
                messages.info(request, 'Job removed from saved items.')
            else:
                SavedJob.objects.create(user=request.user, job=job)
                messages.success(request, 'Job saved successfully!')
            return redirect('job_detail', pk=pk)

    context = {
        'job': job,
        'has_applied': has_applied,
        'is_saved': is_saved,
        'similar_jobs': similar_jobs,
        'match_score': match_score, 
    }
    return render(request, 'jobportal/job_detail.html', context)

@login_required(login_url='login')
def kanban_board(request, job_id):
    job = get_object_or_404(Job, id=job_id)
    applicants = Application.objects.filter(job=job)
    
    for app in applicants:
        c_text = ""
        # Safely get candidate skills text
        if hasattr(app.user, 'userprofile') and app.user.userprofile.skills:
             c_text = app.user.userprofile.skills
             
        # Use the same smart calculator for the company view
        app.match_score = calculate_match_score(job.skills or "", c_text)

    context = {
        'job': job,
        'applicants': applicants
    }
    return render(request, 'companies/kanban_board.html', context)


@login_required(login_url='login')
def job_detail_view(request, pk):
    job = get_object_or_404(Job, pk=pk)
    
    # Track Views
    if not hasattr(job, 'views'):
        job.views = 0
    job.views += 1
    job.save()

    has_applied = Application.objects.filter(user=request.user, job=job).exists()
    is_saved = SavedJob.objects.filter(user=request.user, job=job).exists()
    similar_jobs = Job.objects.exclude(pk=pk).order_by('?')[:3]

    # --- START INNOVATION: AI Match Score Logic ---
    match_score = 0
    if request.user.is_authenticated and hasattr(request.user, 'userprofile'):
        try:
            # Use the text-based match score calculation
            match_score = calculate_match_score(
                job.skills or "",  # Job skills as text
                request.user.userprofile.skills or ""  # User skills as text
            )
        except AttributeError:
            # Handles cases where skills might not exist or be named differently
            match_score = 0
    # --- END INNOVATION ---

    if request.method == 'POST':
        if hasattr(request.user, 'company'):
            messages.error(request, "Employers cannot apply for jobs.")
            return redirect('job_detail', pk=pk)

        if 'email' in request.POST or 'apply' in request.POST:
            if not has_applied:
                # 1. Get Resume
                resume_file = request.FILES.get('resume')
                if not resume_file and hasattr(request.user, 'userprofile') and request.user.userprofile.resume:
                    resume_file = request.user.userprofile.resume

                # 2. Capture Form Data
                phone_val = request.POST.get('phone')
                experience_val = request.POST.get('q2')
                commute_val = request.POST.get('q1')

                # 3. Create Application
                Application.objects.create(
                    user=request.user, 
                    job=job, 
                    status='applied',  # Changed from 'Pending' to 'applied'
                    resume=resume_file,
                    phone=phone_val,
                    experience=experience_val,
                    commute=commute_val
                )
                
                messages.success(request, f'Successfully applied to {job.title}!')
                return redirect('my_applications')
            else:
                messages.warning(request, 'You have already applied for this job.')
        
        elif 'save' in request.POST:
            if is_saved:
                SavedJob.objects.filter(user=request.user, job=job).delete()
                messages.info(request, 'Job removed from saved items.')
            else:
                SavedJob.objects.create(user=request.user, job=job)
                messages.success(request, 'Job saved successfully!')
            return redirect('job_detail', pk=pk)

    context = {
        'job': job,
        'has_applied': has_applied,
        'is_saved': is_saved,
        'similar_jobs': similar_jobs,
        'match_score': match_score, # Passed to template
    }
    return render(request, 'jobportal/job_detail.html', context)

@login_required
@candidate_only
def save_job(request, pk):
    job = get_object_or_404(Job, pk=pk)
    SavedJob.objects.get_or_create(user=request.user, job=job)
    messages.success(request, "Job saved successfully")
    return redirect('job_detail', pk=pk)


############################
# 3. DASHBOARD & PROFILE   #
############################

@login_required(login_url='login')
@candidate_only
def dashboard_view(request):
    recommended_jobs = Job.objects.order_by('-created_at')[:4]
    recent_applications = Application.objects.filter(user=request.user)\
        .select_related('job', 'job__company')\
        .order_by('-applied_at')[:5]

    context = {
        'user': request.user,
        'recommended_jobs': recommended_jobs,
        'recent_applications': recent_applications,
        'stats': {
            'applied': Application.objects.filter(user=request.user).count(),
            'saved': SavedJob.objects.filter(user=request.user).count(),
            'interviews': Application.objects.filter(user=request.user, status='Interview').count(),
        }
    }
    return render(request, 'jobportal/dashboard.html', context)

@login_required
@candidate_only
def my_applications_view(request):
    applications = Application.objects.filter(user=request.user).order_by('-applied_at')
    return render(request, 'jobportal/my_applications.html', {'applications': applications})

@login_required
@candidate_only
def saved_jobs_view(request):
    saved_jobs = SavedJob.objects.filter(user=request.user).order_by('-saved_at')
    return render(request, 'jobportal/saved_jobs.html', {'saved_jobs': saved_jobs})


@login_required
def profile_view(request, username=None):
    if username is None:
        username = request.user.username

    profile_user = get_object_or_404(User, username=username)
    profile, created = UserProfile.objects.get_or_create(user=profile_user)
    is_own_profile = request.user == profile_user

    if request.method == 'POST':
        if 'update_images' in request.POST:
            if request.user == profile_user:
                form = ProfileImageForm(request.POST, request.FILES, instance=profile)
                if form.is_valid():
                    form.save()
                    return redirect('profile', username=username)

    # --- 1. TRACKING PROFILE VIEWS (Logic) ---
    if not is_own_profile and request.user.is_authenticated:
        # Record that request.user viewed profile_user
        ProfileView.objects.get_or_create(
            profile=profile,
            viewer=request.user
        )

    # --- 2. GATHERING ANALYTICS DATA (For own profile) ---
    analytics = {}
    if is_own_profile:
        # Count profile views
        analytics['profile_views'] = ProfileView.objects.filter(profile=profile).count()
        
        # Sum impressions from all user's posts
        total_impressions = Post.objects.filter(user=profile_user).aggregate(Sum('impressions_count'))
        analytics['post_impressions'] = total_impressions['impressions_count__sum'] or 0
        
        # Get search appearances
        analytics['search_appearances'] = profile.search_appearances_count

    # --- 3. PEOPLE YOU MAY KNOW LOGIC ---
    # Find users who are NOT the current user AND NOT already connected
    suggested_people = []
    if request.user.is_authenticated:
        # Get IDs of people user is already connected with (or sent request to)
        connected_ids = ConnectionRequest.objects.filter(
            Q(sender=request.user) | Q(receiver=request.user)
        ).values_list('sender_id', 'receiver_id')
        
        # Flatten the list of IDs
        exclude_ids = set()
        for sender_id, receiver_id in connected_ids:
            exclude_ids.add(sender_id)
            exclude_ids.add(receiver_id)
        exclude_ids.add(request.user.id)  # Exclude self

        # Get 3 random profiles not in that list
        suggested_people = UserProfile.objects.exclude(user__id__in=exclude_ids).order_by('?')[:3]

    # Parse skills into a list for template
    skills_list = []
    if profile.skills:
        skills_list = [s.strip() for s in profile.skills.split(',') if s.strip()]
    
    context = {
        'profile': profile,
        'profile_user': profile_user,
        'is_own_profile': is_own_profile,
        'experiences': Experience.objects.filter(user=profile_user),
        'education': Education.objects.filter(user=profile_user),
        'certifications': Certification.objects.filter(user=profile_user),
        'posts': Post.objects.filter(user=profile_user).order_by('-created_at'),
        'analytics': analytics,  # Pass analytics data
        'suggested_people': suggested_people,  # Pass suggestions
        'skills': skills_list,  # Pass parsed skills list
    }
    return render(request, 'jobportal/profile.html', context)

# --- NEW VIEW: Fixes NoReverseMatch error ---
@login_required
def user_profile(request, pk):
    """View a user profile by ID"""
    profile_user = get_object_or_404(User, pk=pk)
    # Reuse the standard profile template or a specific one
    # Assuming we want to show the public profile:
    return profile_view(request, username=profile_user.username)

# views.py
# views.py



@login_required
def delete_skill(request):
    if request.method == 'POST':
        skill_to_delete = request.POST.get('skill_name', '').strip()
        
        try:
            profile = request.user.userprofile
            
            if profile.skills and skill_to_delete:
                # Split by comma and strip whitespace from each skill
                skill_list = [s.strip() for s in profile.skills.split(',')]
                
                # Remove the skill if it exists (case-sensitive match)
                if skill_to_delete in skill_list:
                    skill_list.remove(skill_to_delete)
                    # Join back and save
                    profile.skills = ",".join(skill_list)
                    profile.save()
                    messages.success(request, f"Skill '{skill_to_delete}' removed successfully!")
                else:
                    messages.warning(request, f"Skill '{skill_to_delete}' not found.")
            else:
                messages.warning(request, "No skills to delete.")
        except Exception as e:
            messages.error(request, f"Error deleting skill: {str(e)}")
            
    return redirect('profile', username=request.user.username)


@login_required
def add_skill(request):
    if request.method == 'POST':
        skill_name = request.POST.get('skill_name', '').strip()
        
        if skill_name:
            try:
                profile = request.user.userprofile
                
                # Check if skill already exists
                existing_skills = [s.strip() for s in profile.skills.split(',') if s.strip()] if profile.skills else []
                
                if skill_name not in existing_skills:
                    if profile.skills:
                        profile.skills += f",{skill_name}"
                    else:
                        profile.skills = skill_name
                    profile.save()
                    messages.success(request, f"Skill '{skill_name}' added successfully!")
                else:
                    messages.warning(request, f"Skill '{skill_name}' already exists in your profile.")
            except Exception as e:
                messages.error(request, f"Error adding skill: {str(e)}")
        else:
            messages.warning(request, "Please enter a skill name.")
            
    return redirect('profile', username=request.user.username)
@login_required
def view_all_skills(request, username=None):
    """View all skills for a user profile"""
    if username is None:
        username = request.user.username

    profile_user = get_object_or_404(User, username=username)
    profile, created = UserProfile.objects.get_or_create(user=profile_user)
    is_own_profile = request.user == profile_user

    # Parse skills from comma-separated string
    skills = [skill.strip() for skill in profile.skills.split(',') if skill.strip()] if profile.skills else []

    context = {
        'profile': profile,
        'profile_user': profile_user,
        'is_own_profile': is_own_profile,
        'skills': skills,
    }
    return render(request, 'jobportal/view_all_skills.html', context)

@login_required
@candidate_only
def create_profile_view(request):
    profile, created = UserProfile.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        form = UserProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()

            # 1. Experience
            exp_title = request.POST.get('exp_title')
            exp_company = request.POST.get('exp_company')
            if exp_title and exp_company:
                Experience.objects.create(
                    user=request.user,
                    title=exp_title,
                    company=exp_company,
                    start_date=request.POST.get('exp_start_date') or timezone.now(), 
                    end_date=request.POST.get('exp_end_date') or None 
                )

            # 2. Education
            edu_school = request.POST.get('edu_school')
            edu_degree = request.POST.get('edu_degree')
            if edu_school and edu_degree:
                Education.objects.create(
                    user=request.user,
                    school=edu_school,
                    degree=edu_degree,
                    field_of_study=request.POST.get('edu_field', ''),
                    end_date=request.POST.get('edu_date') or None,
                    start_date=timezone.now()
                )

            # 3. Certification
            cert_name = request.POST.get('cert_name')
            if cert_name:
                Certification.objects.create(
                    user=request.user,
                    name=cert_name,
                    issuing_organization=request.POST.get('cert_org', ''),
                    issue_date=timezone.now()
                )

            messages.success(request, "Profile created successfully!")
            return redirect('profile', username=request.user.username)

    else:
        form = UserProfileForm(instance=profile)
    
    return render(request, 'jobportal/create_profile.html', {'form': form})

@login_required
@candidate_only
def add_experience(request):
    if request.method == 'POST':
        form = ExperienceForm(request.POST)
        if form.is_valid():
            exp = form.save(commit=False)
            exp.user = request.user
            exp.save()
            return redirect('profile')
    else:
        form = ExperienceForm()
    return render(request, 'jobportal/form_generic.html', {'form': form, 'title': 'Add Experience'})

@login_required
@candidate_only
def add_education(request):
    if request.method == 'POST':
        form = EducationForm(request.POST)
        if form.is_valid():
            edu = form.save(commit=False)
            edu.user = request.user
            edu.save()
            return redirect('profile')
    else:
        form = EducationForm()
    return render(request, 'jobportal/form_generic.html', {'form': form, 'title': 'Add Education'})

@login_required
@candidate_only
def add_certification(request):
    if request.method == 'POST':
        form = CertificationForm(request.POST)
        if form.is_valid():
            cert = form.save(commit=False)
            cert.user = request.user
            cert.save()
            return redirect('profile')
    else:
        form = CertificationForm()
    return render(request, 'jobportal/form_generic.html', {'form': form, 'title': 'Add Certification'})

@login_required
@candidate_only
def settings_view(request):
    user = request.user
    profile, created = UserProfile.objects.get_or_create(user=user)

    if request.method == 'POST':
        # 1. Update User Account
        user.first_name = request.POST.get('first_name', user.first_name)
        user.last_name = request.POST.get('last_name', user.last_name)
        user.email = request.POST.get('email', user.email)
        user.save()

        # 2. Update Profile Fields
        profile.headline = request.POST.get('headline', profile.headline)
        profile.location = request.POST.get('location', profile.location)
        profile.phone_number = request.POST.get('phone_number', profile.phone_number)
        
        # 3. Update Settings Toggles
        profile.profile_visibility = 'profile_visibility' in request.POST
        profile.email_visibility = 'email_visibility' in request.POST
        profile.activity_status = 'activity_status' in request.POST
        profile.data_sharing = 'data_sharing' in request.POST
        profile.personalized_ads = 'personalized_ads' in request.POST
        profile.notify_jobs = 'notify_jobs' in request.POST
        profile.notify_network = 'notify_network' in request.POST
        
        # 4. Handle Profile Picture Upload
        if 'profile_picture' in request.FILES:
            profile.profile_picture = request.FILES['profile_picture']
            
        profile.save()
        messages.success(request, "Settings updated successfully!")
        return redirect('settings')

    return render(request, 'jobportal/settings.html', {'user': user})


############################
# 4. COMPANY VIEWS         #
############################

def employer_register(request):
    if request.user.is_authenticated:
        if hasattr(request.user, 'company'):
            return redirect('company_dashboard')
        return redirect('home')

    if request.method == 'POST':
        user_form = UserRegistrationForm(request.POST)
        company_form = CompanyRegistrationForm(request.POST, request.FILES) 
        if user_form.is_valid() and company_form.is_valid():
            user = user_form.save(commit=False)
            user.username = user_form.cleaned_data['email']
            user.set_password(user_form.cleaned_data['password']) 
            user.save()

            company = company_form.save(commit=False)
            company.user = user 
            company.save()

            login(request, user)
            messages.success(request, "Account created successfully!")
            return redirect('company_dashboard')
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        user_form = UserRegistrationForm()
        company_form = CompanyRegistrationForm()

    return render(request, 'companies/company_register.html', {
        'user_form': user_form, 
        'company_form': company_form
    })


@login_required(login_url='employer_login')
@employer_only
def company_dashboard(request):
    try:
        company = request.user.company
    except ObjectDoesNotExist:
        return redirect('company_register') 
    
    jobs = Job.objects.filter(company=company).order_by('-created_at')
    total_jobs = jobs.count()
    total_applicants = Application.objects.filter(job__company=company).count()
    profile_views = jobs.aggregate(total_views=Sum('views'))['total_views'] or 0
    recent_posts = Post.objects.filter(user=request.user).prefetch_related('comments', 'likes').order_by('-created_at')[:5]

    context = {
        'company': company,
        'jobs': jobs[:5], 
        'total_jobs': total_jobs,
        'total_applicants': total_applicants,
        'profile_views': profile_views,
        'recent_posts': recent_posts,
    }
    return render(request, 'companies/company_dashboard.html', context)

@login_required(login_url='employer_login')
@employer_only
def post_job(request):
    try:
        company = request.user.company
    except AttributeError:
        messages.error(request, "You must have a company profile to post a job.")
        return redirect('company_register') 
    
    if request.method == 'POST':
        form = JobPostForm(request.POST)
        if form.is_valid():
            job = form.save(commit=False)
            job.company = company
            job.save()
            messages.success(request, "Job posted successfully!")
            return redirect('company_dashboard')
    else:
        form = JobPostForm()
    return render(request, 'companies/post_job.html', {'form': form, 'company': company})

@login_required(login_url='employer_login')
@employer_only
def company_settings(request):
    try:
        company = request.user.company
    except AttributeError:
        return redirect('company_register')

    if request.method == 'POST':
        form = CompanyUpdateForm(request.POST, request.FILES, instance=company)
        user = request.user
        user.first_name = request.POST.get('first_name', user.first_name)
        user.last_name = request.POST.get('last_name', user.last_name)
        user.save()

        if form.is_valid():
            form.save()
            messages.success(request, "Company settings updated successfully!")
            return redirect('company_settings')
    else:
        form = CompanyUpdateForm(instance=company)
    return render(request, 'companies/company_settings.html', {'form': form, 'company': company})
# In jobportal/views.py

def company_profile(request, pk):  # Renamed from company_detail to company_profile
    # Get the company
    company = get_object_or_404(Company, id=pk)
    
    # Query the Job model directly
    jobs = Job.objects.filter(company=company).order_by('-created_at')
    
    # Get other details
    active_tab = request.GET.get('tab', 'home')
    active_filter = request.GET.get('filter', 'culture')
    
    # Check employees
    try:
        employees = UserProfile.objects.filter(company=company)
        employee_count = employees.count()
    except:
        employees = []
        employee_count = 0

    # Determine which template to use based on user type
    is_owner = request.user.is_authenticated and hasattr(request.user, 'company') and request.user.company.id == pk
    template_name = 'companies/company_profile.html' if is_owner else 'jobportal/company_profile.html'
    
    # Check if user is following the company
    is_following = False
    if request.user.is_authenticated:
        is_following = company.followers.filter(id=request.user.id).exists()

    context = {
        'company': company,
        'active_tab': active_tab,
        'active_filter': active_filter,
        'jobs': jobs,
        'employees': employees,
        'employee_count': employee_count,
        'is_company_profile': True,
        'is_following': is_following,
    }
    
    return render(request, template_name, context)


def company_profile_debug(request, pk):
    """Debug view to check what data is being passed"""
    company = get_object_or_404(Company, id=pk)
    jobs = Job.objects.filter(company=company).order_by('-created_at')
    
    try:
        employees = UserProfile.objects.filter(company=company)
        employee_count = employees.count()
    except:
        employees = []
        employee_count = 0
    
    is_owner = request.user.is_authenticated and hasattr(request.user, 'company') and request.user.company.id == pk
    
    context = {
        'company': company,
        'active_tab': request.GET.get('tab', 'home'),
        'jobs': jobs,
        'employees': employees,
        'employee_count': employee_count,
        'is_owner': is_owner,
    }
    
    return render(request, 'jobportal/debug_company.html', context)


@login_required(login_url='login')
@require_POST
def follow_company(request, pk):
    """Toggle follow/unfollow company"""
    company = get_object_or_404(Company, id=pk)
    
    # Check if user is already following
    is_following = company.followers.filter(id=request.user.id).exists()
    
    if is_following:
        # Unfollow
        company.followers.remove(request.user)
        is_now_following = False
    else:
        # Follow
        company.followers.add(request.user)
        is_now_following = True
    
    # Return JSON response for AJAX
    return JsonResponse({
        'success': True,
        'is_following': is_now_following,
        'followers_count': company.followers.count()
    })


@login_required(login_url='employer_login') 
@employer_only
def employer_applicants_view(request):
    # 1. Check if user is an employer
    if not hasattr(request.user, 'company'):
        return redirect('employer_register')
    
    company = request.user.company

    # 2. Fetch Applications
    # FIXED: Changed 'user__profile' to 'user__userprofile'
    applications = Application.objects.filter(
        job__company=company
    ).select_related('user', 'job', 'user__userprofile').order_by('-applied_at')

    context = {
        'company': company,
        'applications': applications
    }
    
    return render(request, 'companies/employer_applicants.html', context)


@login_required(login_url='employer_login')
@employer_only
def update_application_status(request, application_id):
    if request.method == 'POST':
        application = get_object_or_404(Application, id=application_id)
        if application.job.company.user != request.user:
            messages.error(request, "Permission denied.")
            return redirect('employer_applicants')

        new_status = request.POST.get('status')
        if new_status in ['Accepted', 'Rejected', 'Interview']:
            application.status = new_status
            application.save()
            messages.success(request, f"Applicant status updated to {new_status}")
    return redirect('employer_applicants')


############################
# 5. NETWORKING & MESSAGES #
############################
@login_required
def network_page(request):
    user = request.user
    
    # 1. FIX: COUNT CONNECTIONS FROM ConnectionRequest
    connections_count = ConnectionRequest.objects.filter(
        (Q(sender=user) | Q(receiver=user)) & Q(status='accepted')
    ).count()

    # 2. CALCULATE INVITATIONS (Received & Pending)
    received_requests = ConnectionRequest.objects.filter(
        receiver=user, 
        status='pending'
    )
    invitations_count = received_requests.count()

    # 3. CALCULATE FOLLOWING (Companies)
    following_count = user.following_companies.count()

    # 4. SENT REQUESTS (To show in the "Sent" section)
    sent_requests = ConnectionRequest.objects.filter(
        sender=user, 
        status='pending'
    )

    # 5. SUGGESTIONS (People you may know)
    suggestions = User.objects.exclude(id=user.id).order_by('?')[:4]

    context = {
        'connections_count': connections_count,
        'invitations_count': invitations_count,
        'following_count': following_count,
        'received_requests': received_requests,
        'sent_requests': sent_requests,
        'suggestions': suggestions,
    }
    
    return render(request, 'jobportal/network.html', context)

@login_required
def following_list(request):
    # Fetch all companies the user is following
    followed_companies = request.user.following_companies.all()
    
    context = {
        'followed_companies': followed_companies
    }
    return render(request, 'jobportal/following_list.html', context)


@login_required
def connections_list_view(request):
    """Display all user's connections with search and sort options"""
    query = request.GET.get('name', '').strip()
    sort_by = request.GET.get('sort', '-timestamp')
    
    # Get all accepted connections
    connections_qs = ConnectionRequest.objects.filter(
        Q(sender=request.user) | Q(receiver=request.user),
        status='accepted'
    ).select_related('sender', 'receiver', 'sender__userprofile', 'receiver__userprofile').order_by('-timestamp')
    
    # Build user list with their connection info
    user_list = []
    for conn in connections_qs:
        other_user = conn.receiver if conn.sender == request.user else conn.sender
        
        # Apply search filter
        if query and query.lower() not in other_user.get_full_name().lower():
            continue
            
        user_list.append({
            'user': other_user,
            'connected_at': conn.timestamp,
            'connection_id': conn.id
        })
    
    # Apply sorting
    if 'first_name' in sort_by:
        user_list.sort(key=lambda x: x['user'].first_name)
    elif 'last_name' in sort_by:
        user_list.sort(key=lambda x: x['user'].last_name)
    else:
        user_list.sort(key=lambda x: x['connected_at'], reverse=True)

    return render(request, 'jobportal/connections_list.html', {
        'connections': user_list,
        'count': len(user_list),
        'query': query,
        'sort_by': sort_by
    })

@login_required
def send_request(request, user_id):
    receiver = get_object_or_404(User, id=user_id)
    if receiver != request.user:
        ConnectionRequest.objects.get_or_create(sender=request.user, receiver=receiver, defaults={'status': 'pending'})
    return redirect('network')

@login_required
def accept_request(request, request_id):
    req = get_object_or_404(ConnectionRequest, id=request_id, receiver=request.user)
    req.status = 'accepted'
    req.save()
    return redirect('network')

@login_required
def ignore_request(request, request_id):
    req = get_object_or_404(ConnectionRequest, id=request_id, receiver=request.user)
    req.status = 'ignored'
    req.save()
    return redirect('network')

@login_required
def withdraw_request(request, request_id):
    req = get_object_or_404(ConnectionRequest, id=request_id, sender=request.user)
    req.delete()
    return redirect('network')

@login_required
def user_search_api(request):
    query = request.GET.get('q', '')
    users = User.objects.filter(Q(first_name__icontains=query) | Q(last_name__icontains=query)).exclude(id=request.user.id)[:5]
    results = []
    for user in users:
        img_url = user.userprofile.profile_picture.url if hasattr(user, 'userprofile') and user.userprofile.profile_picture else None
        headline = user.userprofile.headline if hasattr(user, 'userprofile') else "Job Seeker"
        results.append({'id': user.id, 'name': f"{user.first_name} {user.last_name}", 'headline': headline, 'image': img_url})
    return JsonResponse(results, safe=False)


@login_required
def messaging(request, thread_id=None):
    user = request.user
    
    threads = MessageThread.objects.filter(participants=user).annotate(
        last_msg_time=Max('messages__timestamp')
    ).order_by('-last_msg_time')
    
    active_thread = None
    chat_messages = [] 

    if thread_id:
        active_thread = get_object_or_404(MessageThread, id=thread_id, participants=user)
        chat_messages = Message.objects.filter(thread=active_thread).order_by('timestamp')
    elif threads.exists():
        active_thread = threads.first()
        chat_messages = Message.objects.filter(thread=active_thread).order_by('timestamp')

    context = {
        'threads': threads,
        'active_thread': active_thread,
        'chat_messages': chat_messages, 
    }
    return render(request, 'jobportal/messaging.html', context)

@login_required
def send_message(request, thread_id):
    if request.method == 'POST':
        thread = get_object_or_404(MessageThread, id=thread_id, participants=request.user)
        body = request.POST.get('body')
        image = request.FILES.get('image')

        if body or image:
            Message.objects.create(
                thread=thread,
                sender=request.user,
                body=body if body else "",
                image=image
            )
            thread.save()
            return redirect('message_thread', thread_id=thread_id)
            
    return redirect('messaging')

@login_required
def delete_message(request, message_id):
    message = get_object_or_404(Message, id=message_id, sender=request.user)
    thread_id = message.thread.id
    message.delete()
    return redirect('message_thread', thread_id=thread_id)


############################
# 6. POST ACTIONS (AJAX)   #
############################

@login_required
def like_post(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    if post.likes.filter(id=request.user.id).exists():
        post.likes.remove(request.user)
        is_liked = False
    else:
        post.likes.add(request.user)
        is_liked = True
    return JsonResponse({'likes_count': post.total_likes, 'is_liked': is_liked})

@login_required
@require_POST
def add_comment(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    try:
        data = json.loads(request.body)
        text = data.get('text', '').strip()
        if text:
            comment = PostComment.objects.create(post=post, user=request.user, text=text)
            return JsonResponse({'status': 'success', 'user': f"{request.user.first_name} {request.user.last_name}", 'text': comment.text, 'date': 'Just now'})
        return JsonResponse({'status': 'error', 'message': 'Empty comment'}, status=400)
    except json.JSONDecodeError:
        return JsonResponse({'status': 'error', 'message': 'Invalid JSON'}, status=400)

@login_required
def create_post(request):
    if request.method == 'POST':
        form = PostForm(request.POST, request.FILES)
        if form.is_valid():
            post = form.save(commit=False)
            post.user = request.user
            post.save()
            messages.success(request, "Post created successfully!")
        else:
            messages.error(request, "Error creating post.")
    return redirect(request.META.get('HTTP_REFERER', 'home'))


@login_required
def delete_post(request, pk):
    """Delete a post - only the post owner can delete"""
    post = get_object_or_404(Post, pk=pk)
    
    # Check if the current user is the post owner
    if post.user != request.user:
        messages.error(request, "You can only delete your own posts.")
        return redirect(request.META.get('HTTP_REFERER', 'home'))
    
    if request.method == 'POST':
        post.delete()
        messages.success(request, "Post deleted successfully!")
    
    return redirect(request.META.get('HTTP_REFERER', 'home'))

# ---------------------------------------------------------
# View: Share Post & Activity
# ---------------------------------------------------------

@login_required
@require_POST
def share_post(request, post_id):
    """Share a post with selected users by creating messages in their chat threads"""
    post = get_object_or_404(Post, id=post_id)
    try:
        data = json.loads(request.body)
        user_ids = data.get('user_ids', [])
        
        if not user_ids:
            return JsonResponse({'status': 'error', 'message': 'Please select at least one user to share with'}, status=400)
        
        # Get the recipient users
        recipients = User.objects.filter(id__in=user_ids)
        shared_with_count = 0
        
        for recipient in recipients:
            # Find or create a thread between these two users
            # First, look for an existing thread with both users
            existing_threads = MessageThread.objects.filter(
                participants=request.user
            ).filter(
                participants=recipient
            )
            
            if existing_threads.exists():
                thread = existing_threads.first()
            else:
                # Create a new thread
                thread = MessageThread.objects.create()
                thread.participants.add(request.user, recipient)
            
            # Create a message with the shared post
            Message.objects.create(
                thread=thread,
                sender=request.user,
                post=post,
                body="Shared a post with you"
            )
            
            shared_with_count += 1
        
        return JsonResponse({
            'status': 'success', 
            'message': f'Post shared with {shared_with_count} user(s)'
        })
    except json.JSONDecodeError:
        return JsonResponse({'status': 'error', 'message': 'Invalid JSON'}, status=400)
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)

@login_required
def get_share_users(request):
    """Get list of users to share post with (connections/network)"""
    search = request.GET.get('q', '').strip()
    
    # Get all users except the current user
    users = User.objects.exclude(id=request.user.id).select_related('userprofile')
    
    if search:
        users = users.filter(
            Q(first_name__icontains=search) |
            Q(last_name__icontains=search) |
            Q(email__icontains=search)
        )
    
    users = users[:10]  # Limit to 10 results
    
    user_list = []
    for user in users:
        user_list.append({
            'id': user.id,
            'name': user.get_full_name() or user.username,
            'username': user.username,
            'headline': getattr(user.userprofile, 'headline', 'User') if hasattr(user, 'userprofile') else 'User',
            'profile_picture': user.userprofile.profile_picture.url if hasattr(user, 'userprofile') and user.userprofile.profile_picture else None,
        })
    
    return JsonResponse({'users': user_list})

@login_required
def activity(request):
    # 1. Fetch posts created by the current user
    user_posts = Post.objects.filter(user=request.user).order_by('-created_at')

    # 2. Calculate "Connections" (People who sent you a request that is ACCEPTED)
    try:
        followers_count = ConnectionRequest.objects.filter(
            receiver=request.user, 
            status='accepted'
        ).count()
    except Exception:
        followers_count = 0

    # 3. Impressions (Placeholder until you add a views field)
    total_impressions = 0 

    # 4. Get Suggested Users
    try:
        # Get list of IDs where YOU are the sender
        sent_request_ids = ConnectionRequest.objects.filter(sender=request.user).values_list('receiver_id', flat=True)
        
        suggested_users = User.objects.exclude(id=request.user.id).exclude(id__in=sent_request_ids)[:3]
    except Exception:
        suggested_users = []

    context = {
        'posts': user_posts,
        'followers_count': followers_count,
        'total_impressions': total_impressions,
        'suggested_users': suggested_users,
    }
    
    return render(request, 'jobportal/activity.html', context)


# ---------------------------------------------------------
# View 2: Send Connection Request (Handle the Modal Form)
# ---------------------------------------------------------
@login_required
def send_connection_request(request, user_id):
    if request.method == 'POST':
        # Get the person you are trying to connect with
        to_user = get_object_or_404(User, id=user_id)
        
        # Get the note from the HTML Modal
        note = request.POST.get('note', '')

        # Check if a request already exists (sender=you, receiver=them)
        existing_request = ConnectionRequest.objects.filter(
            sender=request.user, 
            receiver=to_user
        ).first()
        
        if not existing_request:
            # Create the request using YOUR model structure
            ConnectionRequest.objects.create(
                sender=request.user,
                receiver=to_user,
                note=note,
                status='pending'
            )
            messages.success(request, f"Invitation sent to {to_user.first_name}.")
        else:
            messages.info(request, "Request already pending or sent.")

    # Redirect back to the same page
    return redirect(request.META.get('HTTP_REFERER', 'activity'))

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import JobAlertForm
from .models import JobAlert

@login_required
def create_job_alert(request):
    if request.method == 'POST':
        form = JobAlertForm(request.POST)
        if form.is_valid():
            alert = form.save(commit=False)
            alert.user = request.user
            alert.save()
            messages.success(request, "Job alert created successfully!")
            return redirect('job_list') # Redirect to your main job page
    else:
        form = JobAlertForm()
    
    return render(request, 'create_alert.html', {'form': form})