# Google OAuth Implementation - Code Changes Summary

## File 1: jobportal/views.py

### CHANGE 1: Add Imports (Top of file)

```diff
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
  import re
+ import requests
+ from urllib.parse import urlencode
+ import os
```

### CHANGE 2: Add Configuration (After imports, before existing code)

```diff
  import re
  import requests
  from urllib.parse import urlencode
  import os
  
  
+ # ==========================================
+ # GOOGLE OAUTH AUTHENTICATION
+ # ==========================================
+
+ GOOGLE_CLIENT_ID = os.environ.get('GOOGLE_CLIENT_ID', 'YOUR_GOOGLE_CLIENT_ID')
+ GOOGLE_CLIENT_SECRET = os.environ.get('GOOGLE_CLIENT_SECRET', 'YOUR_GOOGLE_CLIENT_SECRET')
+ GOOGLE_REDIRECT_URI = 'http://localhost:8000/auth/google/callback/'
+
  
  # 1. IMPORT MODELS
  from .models import (
```

### CHANGE 3: Add Google OAuth Views (After login_view function)

```diff
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
  
  
+ def google_login(request):
+     """
+     Redirect user to Google OAuth consent screen
+     """
+     params = {
+         'client_id': GOOGLE_CLIENT_ID,
+         'redirect_uri': GOOGLE_REDIRECT_URI,
+         'response_type': 'code',
+         'scope': 'email profile',
+         'access_type': 'offline',
+     }
+     return redirect(f"https://accounts.google.com/o/oauth2/v2/auth?{urlencode(params)}")
+
+
+ def google_callback(request):
+     """
+     Handle Google OAuth callback
+     """
+     code = request.GET.get('code')
+     error = request.GET.get('error')
+     
+     if error:
+         messages.error(request, f"Google authentication failed: {error}")
+         return redirect('login')
+     
+     if not code:
+         messages.error(request, "No authorization code received from Google")
+         return redirect('login')
+     
+     try:
+         # Exchange code for access token
+         token_url = 'https://oauth2.googleapis.com/token'
+         data = {
+             'code': code,
+             'client_id': GOOGLE_CLIENT_ID,
+             'client_secret': GOOGLE_CLIENT_SECRET,
+             'redirect_uri': GOOGLE_REDIRECT_URI,
+             'grant_type': 'authorization_code',
+         }
+         
+         response = requests.post(token_url, data=data, timeout=10)
+         token_data = response.json()
+         
+         if 'error' in token_data:
+             messages.error(request, f"Token exchange failed: {token_data['error']}")
+             return redirect('login')
+         
+         access_token = token_data.get('access_token')
+         
+         # Get user info from Google
+         user_info_url = 'https://www.googleapis.com/oauth2/v2/userinfo'
+         headers = {'Authorization': f'Bearer {access_token}'}
+         user_response = requests.get(user_info_url, headers=headers, timeout=10)
+         user_info = user_response.json()
+         
+         if 'error' in user_info:
+             messages.error(request, "Failed to retrieve user information from Google")
+             return redirect('login')
+         
+         email = user_info.get('email')
+         first_name = user_info.get('given_name', '')
+         last_name = user_info.get('family_name', '')
+         
+         # Check if user exists
+         user = User.objects.filter(email=email).first()
+         
+         if not user:
+             # Create new user
+             username = email.split('@')[0]
+             base_username = username
+             counter = 1
+             while User.objects.filter(username=username).exists():
+                 username = f"{base_username}{counter}"
+                 counter += 1
+             
+             user = User.objects.create_user(
+                 username=username,
+                 email=email,
+                 first_name=first_name,
+                 last_name=last_name
+             )
+             messages.success(request, f"Welcome {first_name}! Your account has been created.")
+             login(request, user)
+             return redirect('create_profile')
+         
+         # Login existing user
+         login(request, user)
+         messages.success(request, f"Welcome back, {user.first_name}!")
+         
+         next_url = request.session.pop('google_next', None) or request.GET.get('state')
+         if next_url and next_url.startswith('/'):
+             return redirect(next_url)
+         
+         if hasattr(user, 'company'):
+             return redirect('company_dashboard')
+         return redirect('home')
+     
+     except requests.RequestException as e:
+         messages.error(request, f"Error communicating with Google: {str(e)}")
+         return redirect('login')
+     except Exception as e:
+         messages.error(request, f"An error occurred: {str(e)}")
+         return redirect('login')
+
  
  def employer_login_view(request):
```

---

## File 2: jobportal/urls.py

```diff
  urlpatterns = [
      # Authentication
      path('register/', views.register_view, name='register'),
      path('login/', views.login_view, name='login'),
      path('employer-login/', views.employer_login_view, name='employer_login'),
      path('logout/', views.logout_view, name='logout'),
      
+     # Google OAuth
+     path('auth/google/login/', views.google_login, name='google_login'),
+     path('auth/google/callback/', views.google_callback, name='google_callback'),
+     
      # Main Pages
      path('', views.home, name='home'),
```

---

## File 3: jobportal/templates/jobportal/login.html

### CHANGE: Add CSS after error-alert style

```diff
      .error-alert {
          background: #fde8e8;
          color: #9b1c1c;
          padding: 10px;
          border-radius: 6px;
          margin-bottom: 20px;
          font-size: 0.9rem;
          text-align: left;
          border: 1px solid #f8b4b4;
      }
+
+     /* Divider */
+     .divider-section {
+         display: flex;
+         align-items: center;
+         margin: 25px 0 20px 0;
+         gap: 10px;
+     }
+     .divider-section::before,
+     .divider-section::after {
+         content: "";
+         flex: 1;
+         height: 1px;
+         background: #e1e5ee;
+     }
+     .divider-section span {
+         color: #999;
+         font-size: 0.9rem;
+     }
+
+     /* Google Button */
+     .btn-google {
+         width: 100%;
+         padding: 12px;
+         background: white;
+         border: 2px solid #e1e5ee;
+         border-radius: 8px;
+         font-size: 1rem;
+         font-weight: 600;
+         cursor: pointer;
+         display: flex;
+         align-items: center;
+         justify-content: center;
+         gap: 10px;
+         transition: all 0.3s;
+         color: #333;
+         margin-bottom: 12px;
+     }
+     .btn-google:hover {
+         background: #f8f9fa;
+         border-color: #4285f4;
+         box-shadow: 0 2px 8px rgba(66, 133, 244, 0.2);
+     }
+     .google-icon {
+         width: 20px;
+         height: 20px;
+     }
  </style>
```

### CHANGE: Add HTML after login form, before auth-footer

```diff
          </form>

+         <div class="divider-section">
+             <span>or</span>
+         </div>
+
+         <a href="{% url 'google_login' %}" class="btn-google">
+             <svg class="google-icon" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
+                 <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
+                 <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
+                 <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/>
+                 <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
+             </svg>
+             Continue with Google
+         </a>
+
          <div class="auth-footer">
```

---

## File 4: jobportal/templates/jobportal/register.html

### CHANGE: Add CSS after error-list style

```diff
      .error-list {
          color: #dc2626;
          font-size: 0.85rem;
          margin-top: 5px;
          list-style: none;
          padding: 0;
      }
+
+     /* Divider */
+     .divider-section {
+         display: flex;
+         align-items: center;
+         margin: 25px 0 20px 0;
+         gap: 10px;
+     }
+     .divider-section::before,
+     .divider-section::after {
+         content: "";
+         flex: 1;
+         height: 1px;
+         background: #e5e7eb;
+     }
+     .divider-section span {
+         color: #9ca3af;
+         font-size: 0.9rem;
+     }
+
+     /* Google Button */
+     .btn-google {
+         width: 100%;
+         padding: 14px;
+         background: white;
+         border: 2px solid #e5e7eb;
+         border-radius: 10px;
+         font-size: 1rem;
+         font-weight: 600;
+         cursor: pointer;
+         display: flex;
+         align-items: center;
+         justify-content: center;
+         gap: 10px;
+         transition: all 0.2s;
+         color: #111827;
+         margin-bottom: 12px;
+         text-decoration: none;
+     }
+     .btn-google:hover {
+         background: #f3f4f6;
+         border-color: #4f46e5;
+         box-shadow: 0 4px 12px rgba(79, 70, 229, 0.15);
+     }
+     .google-icon {
+         width: 20px;
+         height: 20px;
+     }
  </style>
```

### CHANGE: Add HTML after submit button

```diff
              <button type="submit" class="btn-primary">Create Account</button>

+             <div class="divider-section">
+                 <span>or</span>
+             </div>
+
+             <a href="{% url 'google_login' %}" class="btn-google">
+                 <svg class="google-icon" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
+                     <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
+                     <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
+                     <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/>
+                     <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
+                 </svg>
+                 Sign up with Google
+             </a>
+
              <div class="login-footer">
```

---

## File 5: jobportal/google_auth.py (NEW - Optional)

```python
"""
Google OAuth Authentication Handler
This module handles Google OAuth 2.0 authentication for user login and registration
"""

from django.shortcuts import redirect
from django.contrib.auth import authenticate, login
from django.contrib.auth.models import User
from django.contrib import messages
import requests
import os
from urllib.parse import urlencode

# Google OAuth Configuration
GOOGLE_CLIENT_ID = os.environ.get('GOOGLE_CLIENT_ID', 'YOUR_GOOGLE_CLIENT_ID')
GOOGLE_CLIENT_SECRET = os.environ.get('GOOGLE_CLIENT_SECRET', 'YOUR_GOOGLE_CLIENT_SECRET')
GOOGLE_REDIRECT_URI = 'http://localhost:8000/auth/google/callback/'


def get_google_auth_url(redirect_to='login'):
    """
    Generate Google OAuth authorization URL
    """
    params = {
        'client_id': GOOGLE_CLIENT_ID,
        'redirect_uri': GOOGLE_REDIRECT_URI,
        'response_type': 'code',
        'scope': 'email profile',
        'state': redirect_to,
    }
    return f"https://accounts.google.com/o/oauth2/v2/auth?{urlencode(params)}"


def exchange_google_code(code):
    """
    Exchange authorization code for access token
    """
    token_url = 'https://oauth2.googleapis.com/token'
    
    data = {
        'code': code,
        'client_id': GOOGLE_CLIENT_ID,
        'client_secret': GOOGLE_CLIENT_SECRET,
        'redirect_uri': GOOGLE_REDIRECT_URI,
        'grant_type': 'authorization_code',
    }
    
    response = requests.post(token_url, data=data)
    return response.json()


def get_google_user_info(access_token):
    """
    Get user information from Google
    """
    user_info_url = 'https://www.googleapis.com/oauth2/v2/userinfo'
    headers = {'Authorization': f'Bearer {access_token}'}
    
    response = requests.get(user_info_url, headers=headers)
    return response.json()


def google_login_or_register(user_info):
    """
    Create or login user based on Google user info
    """
    email = user_info.get('email')
    first_name = user_info.get('given_name', '')
    last_name = user_info.get('family_name', '')
    
    user = User.objects.filter(email=email).first()
    
    if not user:
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
    
    return user
```

---

## Summary of Changes

| File | Lines Added | Changes |
|------|------------|---------|
| views.py | ~120 | 2 functions + imports + config |
| urls.py | 3 | 2 new URL routes |
| login.html | ~40 | CSS + Google button HTML |
| register.html | ~40 | CSS + Google button HTML |
| google_auth.py | ~80 | New utility module (optional) |
| **TOTAL** | **~283** | **Complete OAuth integration** |

---

**Implementation Status**: ✅ COMPLETE
**All Files**: Ready to use
**Time to Setup**: ~5 minutes (after getting credentials)
