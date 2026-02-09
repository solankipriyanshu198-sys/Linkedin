# Quick Start - Google OAuth Setup

## 5-Minute Setup

### 1. Get Google Credentials (5 mins)
```
→ Go to: https://console.cloud.google.com/
→ Create Project
→ Enable Google+ API
→ Create OAuth 2.0 credentials (Web application)
→ Add redirect URI: http://localhost:8000/auth/google/callback/
→ Copy: Client ID & Client Secret
```

### 2. Set Environment Variables

**Windows PowerShell:**
```powershell
$env:GOOGLE_CLIENT_ID = "YOUR_CLIENT_ID.apps.googleusercontent.com"
$env:GOOGLE_CLIENT_SECRET = "YOUR_CLIENT_SECRET"
```

**macOS/Linux:**
```bash
export GOOGLE_CLIENT_ID="YOUR_CLIENT_ID.apps.googleusercontent.com"
export GOOGLE_CLIENT_SECRET="YOUR_CLIENT_SECRET"
```

### 3. Install Dependency
```bash
pip install requests
```

### 4. Run Server
```bash
python manage.py runserver
```

### 5. Test It
- Go to: http://localhost:8000/login/
- Click "Continue with Google"
- Sign in and you're done!

---

## Files Added/Modified

✅ **Created:**
- `jobportal/google_auth.py` - OAuth utilities

✅ **Modified:**
- `jobportal/views.py` - Added google_login() & google_callback() views
- `jobportal/urls.py` - Added Google OAuth routes
- `jobportal/templates/jobportal/login.html` - Added Google button
- `jobportal/templates/jobportal/register.html` - Added Google button

---

## Key Code Sections

### Login Template Button (Already Added)
```html
<a href="{% url 'google_login' %}" class="btn-google">
    <svg class="google-icon">...</svg>
    Continue with Google
</a>
```

### Register Template Button (Already Added)
```html
<a href="{% url 'google_login' %}" class="btn-google">
    <svg class="google-icon">...</svg>
    Sign up with Google
</a>
```

### Backend Views (Already Added)
```python
def google_login(request):
    # Redirects to Google OAuth consent screen
    
def google_callback(request):
    # Handles OAuth callback and user login/creation
```

### URLs (Already Added)
```python
path('auth/google/login/', views.google_login, name='google_login'),
path('auth/google/callback/', views.google_callback, name='google_callback'),
```

---

## What Happens When User Clicks "Google Button"

1. **New User** 
   - ✓ Google OAuth login
   - ✓ Account auto-created with email
   - ✓ Redirected to profile creation

2. **Existing User**
   - ✓ Google OAuth login
   - ✓ Session created
   - ✓ Redirected to home/dashboard

---

## Environment Variables Reference

```
GOOGLE_CLIENT_ID          → YOUR_ID.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET      → YOUR_SECRET_KEY
```

**Where to get them:**
- Go to Google Cloud Console
- APIs & Services > Credentials
- Create OAuth 2.0 Client ID (Web application)

---

## Redirect URI (Important!)

Must match EXACTLY in:
1. **Google Cloud Console** (Authorized redirect URIs)
2. **Code** (GOOGLE_REDIRECT_URI variable in views.py)

**Development:**
```
http://localhost:8000/auth/google/callback/
```

**Production:**
```
https://yourdomain.com/auth/google/callback/
```

---

## Testing URLs

- Login: http://localhost:8000/login/
- Register: http://localhost:8000/register/
- Google button on both pages

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| "Invalid client" | Check CLIENT_ID and CLIENT_SECRET |
| "Redirect URI mismatch" | Ensure exact match in Google Console |
| Button not working | Check GOOGLE_CLIENT_ID is set |
| "requests not found" | Run: `pip install requests` |

---

**Status**: ✅ Implementation Complete
**Ready to Use**: Yes
**Requires**: Google Account + Google Cloud Project
