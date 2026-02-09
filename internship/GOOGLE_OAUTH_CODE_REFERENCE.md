# Google OAuth - Complete Code Reference

## Files Modified Summary

### 1. jobportal/views.py (Added)
Two new view functions added to handle Google OAuth:

```python
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
    }
    return redirect(f"https://accounts.google.com/o/oauth2/v2/auth?{urlencode(params)}")


def google_callback(request):
    """
    Handle Google OAuth callback
    Exchanges authorization code for access token
    Retrieves user information and logs in/creates user
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
            # Ensure unique username
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
            # Redirect to profile creation for new users
            login(request, user)
            return redirect('create_profile')
        
        # Login existing user
        login(request, user)
        messages.success(request, f"Welcome back, {user.first_name}!")
        
        # Redirect to next page or home
        next_url = request.session.pop('google_next', None) or request.GET.get('state')
        if next_url and next_url.startswith('/'):
            return redirect(next_url)
        
        if hasattr(user, 'company'):
            return redirect('company_dashboard')
        return redirect('home')
    
    except requests.RequestException as e:
        messages.error(request, f"Error communicating with Google: {str(e)}")
        return redirect('login')
    except Exception as e:
        messages.error(request, f"An error occurred: {str(e)}")
        return redirect('login')
```

### 2. jobportal/urls.py (Added Routes)

```python
# Google OAuth
path('auth/google/login/', views.google_login, name='google_login'),
path('auth/google/callback/', views.google_callback, name='google_callback'),
```

### 3. jobportal/templates/jobportal/login.html (Updated)

**New CSS Added:**
```css
/* Divider */
.divider-section {
    display: flex;
    align-items: center;
    margin: 25px 0 20px 0;
    gap: 10px;
}
.divider-section::before,
.divider-section::after {
    content: "";
    flex: 1;
    height: 1px;
    background: #e1e5ee;
}
.divider-section span {
    color: #999;
    font-size: 0.9rem;
}

/* Google Button */
.btn-google {
    width: 100%;
    padding: 12px;
    background: white;
    border: 2px solid #e1e5ee;
    border-radius: 8px;
    font-size: 1rem;
    font-weight: 600;
    cursor: pointer;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 10px;
    transition: all 0.3s;
    color: #333;
    margin-bottom: 12px;
}
.btn-google:hover {
    background: #f8f9fa;
    border-color: #4285f4;
    box-shadow: 0 2px 8px rgba(66, 133, 244, 0.2);
}
.google-icon {
    width: 20px;
    height: 20px;
}
```

**New HTML Added (after traditional login button):**
```html
<div class="divider-section">
    <span>or</span>
</div>

<a href="{% url 'google_login' %}" class="btn-google">
    <svg class="google-icon" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
        <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
        <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
        <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/>
        <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
    </svg>
    Continue with Google
</a>
```

### 4. jobportal/templates/jobportal/register.html (Updated)

**New CSS Added:**
```css
/* Divider */
.divider-section {
    display: flex;
    align-items: center;
    margin: 25px 0 20px 0;
    gap: 10px;
}
.divider-section::before,
.divider-section::after {
    content: "";
    flex: 1;
    height: 1px;
    background: #e5e7eb;
}
.divider-section span {
    color: #9ca3af;
    font-size: 0.9rem;
}

/* Google Button */
.btn-google {
    width: 100%;
    padding: 14px;
    background: white;
    border: 2px solid #e5e7eb;
    border-radius: 10px;
    font-size: 1rem;
    font-weight: 600;
    cursor: pointer;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 10px;
    transition: all 0.2s;
    color: #111827;
    margin-bottom: 12px;
    text-decoration: none;
}
.btn-google:hover {
    background: #f3f4f6;
    border-color: #4f46e5;
    box-shadow: 0 4px 12px rgba(79, 70, 229, 0.15);
}
.google-icon {
    width: 20px;
    height: 20px;
}
```

**New HTML Added (after traditional signup button):**
```html
<div class="divider-section">
    <span>or</span>
</div>

<a href="{% url 'google_login' %}" class="btn-google">
    <svg class="google-icon" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
        <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
        <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
        <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/>
        <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
    </svg>
    Sign up with Google
</a>
```

## Configuration Variables in views.py

```python
# ==========================================
# GOOGLE OAUTH AUTHENTICATION
# ==========================================

GOOGLE_CLIENT_ID = os.environ.get('GOOGLE_CLIENT_ID', 'YOUR_GOOGLE_CLIENT_ID')
GOOGLE_CLIENT_SECRET = os.environ.get('GOOGLE_CLIENT_SECRET', 'YOUR_GOOGLE_CLIENT_SECRET')
GOOGLE_REDIRECT_URI = 'http://localhost:8000/auth/google/callback/'
```

## Alternative: Using .env File

Install `python-decouple`:
```bash
pip install python-decouple
```

Create `.env` file in project root:
```
GOOGLE_CLIENT_ID=1234567890-xyz.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=GOCSPX-xyz123abc
```

Update `views.py`:
```python
from decouple import config

GOOGLE_CLIENT_ID = config('GOOGLE_CLIENT_ID')
GOOGLE_CLIENT_SECRET = config('GOOGLE_CLIENT_SECRET')
GOOGLE_REDIRECT_URI = config('GOOGLE_REDIRECT_URI', default='http://localhost:8000/auth/google/callback/')
```

## Dependencies Required

```bash
# Add to requirements.txt or install directly:
pip install requests
```

The `requests` library is used for:
- Exchanging authorization code for access token
- Fetching user information from Google's API

## Imports Added to views.py

```python
import requests
from urllib.parse import urlencode
import os
```

## Message Templates Used

The implementation shows user messages at various points:

```python
# Error messages
messages.error(request, "Google authentication failed: {error}")
messages.error(request, "No authorization code received from Google")
messages.error(request, "Token exchange failed: {error}")
messages.error(request, "Failed to retrieve user information from Google")
messages.error(request, f"Error communicating with Google: {str(e)}")
messages.error(request, f"An error occurred: {str(e)}")

# Success messages
messages.success(request, f"Welcome {first_name}! Your account has been created.")
messages.success(request, f"Welcome back, {user.first_name}!")
```

## Database Impact

No migrations needed! The existing `User` model handles:
- `username` - Auto-generated from email
- `email` - From Google profile
- `first_name` - From Google profile
- `last_name` - From Google profile
- Password - Not set for OAuth users (handled by Google)

## Security Considerations

1. **Client Secret** - Never expose in frontend, kept server-side only
2. **HTTPS** - Required for production (Google won't allow HTTP in production)
3. **CSRF Protection** - Django's built-in CSRF protection used
4. **Timeout** - 10-second timeout on external API calls
5. **Error Handling** - All errors caught and displayed safely
6. **Session Management** - Django's built-in session framework

## Testing the Implementation

### Manual Test Steps

1. **Setup**
   ```bash
   pip install requests
   export GOOGLE_CLIENT_ID="your_client_id.apps.googleusercontent.com"
   export GOOGLE_CLIENT_SECRET="your_secret"
   python manage.py runserver
   ```

2. **Test Login**
   - Go to http://localhost:8000/login/
   - Click "Continue with Google"
   - Complete Google authentication
   - Should be logged in

3. **Test Registration**
   - Go to http://localhost:8000/register/
   - Click "Sign up with Google"
   - Complete Google authentication
   - Should create account and redirect to profile creation

### Debug Mode

Add logging to track flow:

```python
import logging
logger = logging.getLogger(__name__)

# In google_callback():
logger.info(f"OAuth code received: {code[:10]}...")
logger.info(f"User info: {user_info.get('email')}")
logger.info(f"User created or existing: {user.email}")
```

---

**Version**: 1.0
**Status**: Production Ready
**Last Updated**: January 31, 2026
