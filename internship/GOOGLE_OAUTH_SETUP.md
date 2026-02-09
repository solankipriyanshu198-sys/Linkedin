# Google OAuth Integration Setup Guide

This guide explains how to set up Google OAuth authentication for your JobPortal application.

## Overview

Google OAuth has been integrated into your application with the following features:
- **Login with Google** button on the login page
- **Sign up with Google** button on the registration page
- Automatic user creation for first-time Google users
- Automatic login for returning Google users
- Professional UI matching your design system

## Files Modified/Created

1. **[jobportal/google_auth.py](jobportal/google_auth.py)** - Google OAuth utility functions
2. **[jobportal/views.py](jobportal/views.py)** - Added `google_login()` and `google_callback()` views
3. **[jobportal/urls.py](jobportal/urls.py)** - Added Google OAuth URL routes
4. **[jobportal/templates/jobportal/login.html](jobportal/templates/jobportal/login.html)** - Updated with Google login button
5. **[jobportal/templates/jobportal/register.html](jobportal/templates/jobportal/register.html)** - Updated with Google signup button

## Setup Instructions

### Step 1: Get Google OAuth Credentials

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project (or select existing one)
3. Enable the Google+ API:
   - Navigate to "APIs & Services" > "Library"
   - Search for "Google+ API"
   - Click "Enable"
4. Create OAuth 2.0 credentials:
   - Go to "APIs & Services" > "Credentials"
   - Click "Create Credentials" > "OAuth 2.0 Client ID"
   - Select "Web application"
   - Add authorized redirect URIs:
     - `http://localhost:8000/auth/google/callback/` (for development)
     - `https://yourdomain.com/auth/google/callback/` (for production)
   - Click "Create"
   - Copy the Client ID and Client Secret

### Step 2: Install Required Package

```bash
pip install requests
```

### Step 3: Set Environment Variables

Create a `.env` file in your project root or set environment variables:

```bash
# .env file
GOOGLE_CLIENT_ID=your_client_id_here.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your_client_secret_here
```

Or set them in your terminal:

```bash
# Windows PowerShell
$env:GOOGLE_CLIENT_ID = "your_client_id_here"
$env:GOOGLE_CLIENT_SECRET = "your_client_secret_here"

# macOS/Linux
export GOOGLE_CLIENT_ID="your_client_id_here"
export GOOGLE_CLIENT_SECRET="your_client_secret_here"
```

### Step 4: Update Settings (Optional)

If you want to use a `.env` file, install python-decouple:

```bash
pip install python-decouple
```

Then update your `internship/settings.py`:

```python
from decouple import config

GOOGLE_CLIENT_ID = config('GOOGLE_CLIENT_ID', default='YOUR_GOOGLE_CLIENT_ID')
GOOGLE_CLIENT_SECRET = config('GOOGLE_CLIENT_SECRET', default='YOUR_GOOGLE_CLIENT_SECRET')
```

## How It Works

### User Flow

1. **New User Clicks "Continue with Google"**
   - Redirected to Google OAuth consent screen
   - User grants permission
   - Redirected to callback URL with authorization code

2. **Callback Handler**
   - Exchange code for access token
   - Fetch user information (email, name)
   - Check if user exists in database:
     - **If new user**: Create account and redirect to profile creation
     - **If existing user**: Login and redirect to dashboard/home

3. **User Authentication**
   - Session created for logged-in user
   - User can access protected pages

### API Endpoints

- `GET /auth/google/login/` - Initiates Google OAuth flow
- `GET /auth/google/callback/` - Handles OAuth callback

## Features Implemented

### 1. Google Login Button
- Professional Google-branded button
- Styled to match your design system
- Added to login page with divider

### 2. Google Signup Button
- Same professional styling
- Added to registration page
- "Sign up with Google" text

### 3. Automatic User Creation
- Extracts email, first name, last name from Google profile
- Creates unique username from email
- Handles duplicate usernames

### 4. Error Handling
- Network error handling with timeout (10 seconds)
- Token exchange error handling
- User info retrieval error handling
- Displays user-friendly error messages

## Testing

### In Development

1. Ensure you have set the environment variables correctly
2. Navigate to `http://localhost:8000/login/` or `/register/`
3. Click the "Continue with Google" button
4. You'll be redirected to Google's login page
5. After authorizing, you'll be redirected back and logged in

### Common Issues

**Issue**: "Invalid client" error
- **Solution**: Check that your GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET are correct

**Issue**: Redirect URI mismatch
- **Solution**: Ensure the redirect URI in Google Cloud Console matches exactly:
  `http://localhost:8000/auth/google/callback/`

**Issue**: "requests" module not found
- **Solution**: Install it with `pip install requests`

## Customization

### Change Redirect after Login/Signup

Edit in `jobportal/views.py` > `google_callback()`:

```python
# For new users (currently: create_profile)
return redirect('create_profile')

# For existing users (currently: home or company_dashboard)
return redirect('home')
```

### Add More Scopes

In `jobportal/views.py` > `google_login()`, modify the scope parameter:

```python
params = {
    ...
    'scope': 'email profile openid',  # Add more scopes as needed
    ...
}
```

Available scopes:
- `email` - User's email address
- `profile` - Basic profile info (name, picture, etc.)
- `openid` - OpenID Connect

### Customize Button Styling

The Google button styling is in your templates' `<style>` sections:

```html
<style>
    .btn-google {
        /* Customize button appearance */
    }
</style>
```

## Production Deployment

### Important Changes Needed

1. **Update Redirect URIs** in Google Cloud Console:
   - Replace `localhost:8000` with your production domain

2. **Change GOOGLE_REDIRECT_URI** in `jobportal/views.py`:
   ```python
   GOOGLE_REDIRECT_URI = 'https://yourdomain.com/auth/google/callback/'
   ```

3. **Use Environment Variables** (never hardcode credentials):
   ```bash
   GOOGLE_CLIENT_ID=your_production_client_id
   GOOGLE_CLIENT_SECRET=your_production_secret
   ```

4. **Enable HTTPS** - Google requires HTTPS in production

5. **Security Settings**:
   - Ensure `DEBUG = False` in production
   - Set appropriate `ALLOWED_HOSTS` in settings
   - Use secure session cookies

## Troubleshooting

### Debug Information

Add logging to track OAuth flow:

```python
import logging
logger = logging.getLogger(__name__)

# In google_callback view:
logger.info(f"Google OAuth callback: {user_info}")
logger.error(f"OAuth error: {str(e)}")
```

### Manual Testing

Test the OAuth flow manually using curl:

```bash
# Step 1: Get authorization code
curl "https://accounts.google.com/o/oauth2/v2/auth?client_id=YOUR_CLIENT_ID&redirect_uri=http://localhost:8000/auth/google/callback/&response_type=code&scope=email%20profile"

# Step 2: Exchange for token (from callback code)
curl -X POST https://oauth2.googleapis.com/token \
  -d "code=AUTH_CODE&client_id=YOUR_CLIENT_ID&client_secret=YOUR_SECRET&redirect_uri=http://localhost:8000/auth/google/callback/&grant_type=authorization_code"
```

## References

- [Google OAuth 2.0 Documentation](https://developers.google.com/identity/protocols/oauth2)
- [Google Cloud Console](https://console.cloud.google.com/)
- [OAuth 2.0 Scopes](https://developers.google.com/identity/protocols/oauth2/scopes)

## Support

For issues or questions:
1. Check the Google Cloud Console logs
2. Verify environment variables are set
3. Ensure redirect URIs match exactly
4. Check browser console for JavaScript errors

---

**Last Updated**: January 31, 2026
**Framework**: Django 5.2.2
