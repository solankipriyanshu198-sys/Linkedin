# Google OAuth Integration - Visual Architecture

## System Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                        YOUR APPLICATION                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                    FRONTEND (Templates)                  │  │
│  ├──────────────────────────────────────────────────────────┤  │
│  │                                                          │  │
│  │  ┌─────────────────────┐  ┌──────────────────────────┐ │  │
│  │  │   login.html        │  │   register.html          │ │  │
│  │  │ ┌────────────────┐  │  │ ┌────────────────────┐  │ │  │
│  │  │ │ Traditional    │  │  │ │ Traditional Form   │  │ │  │
│  │  │ │ Login Form     │  │  │ │ (Email/Password)   │  │ │  │
│  │  │ └────────────────┘  │  │ └────────────────────┘  │ │  │
│  │  │        ─── or ───   │  │       ─── or ───        │ │  │
│  │  │ ┌────────────────┐  │  │ ┌────────────────────┐  │ │  │
│  │  │ │ 🔵 Google Btn  │◄─┼──┼─│ 🔵 Google Signup   │  │ │  │
│  │  │ │ (NEW)          │  │  │ │ (NEW)              │  │ │  │
│  │  │ └──────┬─────────┘  │  │ └───────┬────────────┘  │ │  │
│  │  └────────┼──────────┘  │  └────────┼───────────┘   │  │
│  │           │             │           │               │  │
│  └───────────┼─────────────┼───────────┼───────────────┘  │
│              │             │           │                  │
│         ┌────▼─────────────▼───────────▼────┐             │
│         │   BACKEND (views.py)               │             │
│         ├──────────────────────────────────┤             │
│         │                                  │             │
│         │  google_login(request)           │             │
│         │  ↓                               │             │
│         │  Generate OAuth URL              │             │
│         │  Return Redirect                 │             │
│         │                                  │             │
│         │  google_callback(request)        │             │
│         │  ↓                               │             │
│         │  Exchange Code for Token         │             │
│         │  ↓                               │             │
│         │  Fetch User Info                 │             │
│         │  ↓                               │             │
│         │  Check/Create User               │             │
│         │  ↓                               │             │
│         │  Create Session                  │             │
│         │  ↓                               │             │
│         │  Redirect (home or profile)      │             │
│         │                                  │             │
│         └──────────────────────────────────┘             │
│              │        │       │                         │
│         ┌────▼────┐   │    ┌──▼─────────┐              │
│         │ Database│   │    │ Sessions   │              │
│         │(User)   │   │    │ (Django)   │              │
│         └─────────┘   │    └────────────┘              │
│                       │                                 │
└───────────────────────┼─────────────────────────────────┘
                        │
                        │ INTERNET
                        │
                        ▼
              ┌──────────────────────┐
              │   GOOGLE SERVERS     │
              ├──────────────────────┤
              │                      │
              │ accounts.google.com  │
              │ oauth2.googleapis... │
              │ googleapis.com       │
              │                      │
              │ User Authentication  │
              │ Token Management     │
              │ User Information API │
              │                      │
              └──────────────────────┘
```

## Request/Response Flow

```
USER VISITS LOGIN PAGE
         │
         │ Sees traditional form AND Google button
         │
    ┌────▼─────┐
    │           │
    ▼           ▼
┌─────────────────────┐  ┌──────────────────────┐
│ Traditional Login   │  │ Google Login (NEW)   │
├─────────────────────┤  ├──────────────────────┤
│ Email + Password    │  │ Clicks Google Button │
│ Submit Form         │  │      │               │
│ Backend validates   │  │      ▼               │
│ Create session      │  │ Redirect to Google   │
│ Redirect home       │  │      │               │
└─────────────────────┘  │      ▼               │
                         │ Google Consent      │
                         │ Screen Shown        │
                         │      │              │
                         │      ▼              │
                         │ User Authenticates │
                         │ Grants Permission  │
                         │      │              │
                         │      ▼              │
                         │ Redirect Back to   │
                         │ /auth/google/      │
                         │ callback/          │
                         │ (with code)        │
                         │      │              │
                         │      ▼              │
                         │ Our Server:        │
                         │ - Exchange code    │
                         │ - Get access token │
                         │ - Fetch user info  │
                         │ - Create/Login     │
                         │ - Create session   │
                         │ - Redirect home    │
                         └──────────────────────┘
```

## File Structure Changes

```
internship/
│
├── jobportal/
│   │
│   ├── views.py                                  ✏️ MODIFIED
│   │   ├── ... (existing views)
│   │   ├── google_login()                        ✨ NEW
│   │   └── google_callback()                     ✨ NEW
│   │
│   ├── urls.py                                   ✏️ MODIFIED
│   │   ├── path('register/', ...)
│   │   ├── path('login/', ...)
│   │   ├── path('auth/google/login/', ...)       ✨ NEW
│   │   └── path('auth/google/callback/', ...)    ✨ NEW
│   │
│   ├── google_auth.py                            ✨ NEW
│   │   ├── get_google_auth_url()
│   │   ├── exchange_google_code()
│   │   ├── get_google_user_info()
│   │   └── google_login_or_register()
│   │
│   └── templates/jobportal/
│       │
│       ├── login.html                            ✏️ MODIFIED
│       │   ├── (Traditional form - unchanged)
│       │   ├── <div class="divider-section">    ✨ NEW
│       │   └── <a href="google_login" ...>       ✨ NEW
│       │
│       └── register.html                         ✏️ MODIFIED
│           ├── (Traditional form - unchanged)
│           ├── <div class="divider-section">    ✨ NEW
│           └── <a href="google_login" ...>       ✨ NEW
│
└── internship/
    └── settings.py
        └── (No changes needed - uses env vars)

DOCUMENTATION ADDED:
├── GOOGLE_OAUTH_IMPLEMENTATION_SUMMARY.md
├── GOOGLE_OAUTH_SETUP.md
├── GOOGLE_OAUTH_QUICK_START.md
├── GOOGLE_OAUTH_VISUAL_REFERENCE.md
└── GOOGLE_OAUTH_CODE_REFERENCE.md
```

## Component Interaction Diagram

```
┌──────────────────────┐
│   Google Button      │
│  (login.html/       │
│   register.html)    │
└──────────┬───────────┘
           │ User Click
           │ href="{% url 'google_login' %}"
           ▼
┌──────────────────────────────┐
│   google_login()  VIEW        │
│  (views.py)                  │
│                              │
│  ├─ Build OAuth URL          │
│  │  - client_id              │
│  │  - redirect_uri           │
│  │  - scope: email profile   │
│  │  - response_type: code    │
│  │                           │
│  └─ Return Redirect()        │
│     ↓                        │
└──────────────────────────────┘
           │
           │ Redirect to:
           │ https://accounts.google.com/
           │ o/oauth2/v2/auth?...
           │
           ▼
┌──────────────────────┐
│  GOOGLE SERVERS      │
│                      │
│  ┌────────────────┐  │
│  │ Consent Screen │  │
│  ├────────────────┤  │
│  │ User sees:     │  │
│  │ - Your app name│  │
│  │ - Requested    │  │
│  │   permissions  │  │
│  │ - Sign in      │  │
│  │ - Authorize    │  │
│  └────────────────┘  │
└──────────────────────┘
           │
           │ User grants permission
           │ Redirects with code:
           │ http://yourapp.com/auth/
           │ google/callback/?code=ABC
           │
           ▼
┌──────────────────────────────────┐
│  google_callback()  VIEW         │
│  (views.py)                      │
│                                  │
│  ├─ Extract code parameter       │
│  │                              │
│  ├─ POST to Google token         │
│  │  - code                       │
│  │  - client_id                  │
│  │  - client_secret              │
│  │  - redirect_uri               │
│  │  ↓ Response: access_token    │
│  │                              │
│  ├─ GET from Google user info    │
│  │  - Authorization: Bearer token│
│  │  ↓ Response: {email, name}   │
│  │                              │
│  ├─ Check User.objects.filter()  │
│  │                              │
│  ├─ IF New User:                 │
│  │  ├─ Create User object        │
│  │  ├─ Set email, names          │
│  │  ├─ Save to database          │
│  │  ├─ login() → create session  │
│  │  └─ redirect('create_profile')│
│  │                              │
│  └─ ELSE Existing User:          │
│     ├─ login() → create session  │
│     └─ redirect('home')          │
└──────────────────────────────────┘
           │
           ▼
┌──────────────────────┐
│ USER LOGGED IN ✓     │
│                      │
│ Session created      │
│ Can access all pages │
│ Profile data loaded  │
└──────────────────────┘
```

## Database Impact

```
BEFORE OAuth Login:
┌──────────────────┐
│ auth_user        │
├──────────────────┤
│ id               │
│ username         │
│ email            │
│ password_hash    │
│ first_name       │
│ last_name        │
│ is_active        │
│ is_staff         │
│ date_joined      │
└──────────────────┘

AFTER Google OAuth Login:
┌──────────────────────┐         ┌──────────────────┐
│ auth_user            │         │ EXISTING User:   │
├──────────────────────┤         ├──────────────────┤
│ id: 5                │         │ Email: matches   │
│ username: john      │         │ Login: proceeds  │
│ email: john@g...    │         │ Session: created │
│ password_hash: ****  │         │ Redirect: home   │
│ first_name: John     │         └──────────────────┘
│ last_name: Doe       │
│ is_active: true      │
│ date_joined: 2026... │         ┌──────────────────┐
└──────────────────────┘         │ NEW User:        │
                                  ├──────────────────┤
                   NEW Record:     │ Email: NEW       │
                   ┌────────────┐  │ Created: yes     │
                   │ john       │  │ Login: yes       │
                   │ john@g.com │  │ Session: yes     │
                   │ John Doe   │  │ Redirect: prof   │
                   └────────────┘  └──────────────────┘
```

## Error Handling Flow

```
google_callback() starts
         │
         ├─ Check for 'error' in params
         │  └─ YES → Error message → Redirect login ✗
         │
         ├─ Check for 'code' in params
         │  └─ NO → Error message → Redirect login ✗
         │
         ├─ Exchange code for token
         │  ├─ Network error → Timeout error → Redirect ✗
         │  ├─ Invalid code → Token error → Redirect ✗
         │  └─ SUCCESS → Continue
         │
         ├─ Fetch user info
         │  ├─ Network error → Timeout error → Redirect ✗
         │  ├─ Invalid token → API error → Redirect ✗
         │  └─ SUCCESS → Continue
         │
         ├─ Check/Create user
         │  ├─ Database error → General error → Redirect ✗
         │  └─ SUCCESS → Continue
         │
         ├─ Create session & redirect
         │  └─ SUCCESS → User logged in ✓
         │
         └─ All errors caught in try/except
            └─ Display user-friendly message
```

## Session & Authentication State

```
STATE 1: Before Login
├─ request.user.is_authenticated = False
├─ request.user = AnonymousUser()
├─ request.session = {} (empty)
└─ Can only access public pages

    ↓ User completes Google OAuth ↓

STATE 2: After OAuth Callback
├─ user = User.objects.get(email=email)
├─ login(request, user)  ← Creates session
├─ request.session['_auth_user_id'] = user.id
└─ request.session['_auth_user_backend'] = 'django.contrib.auth.backends.ModelBackend'

    ↓ Session middleware processes ↓

STATE 3: User Logged In (All Pages)
├─ request.user.is_authenticated = True
├─ request.user = User object
├─ request.user.email = "user@example.com"
├─ request.user.first_name = "John"
├─ request.user.last_name = "Doe"
├─ Can access protected pages
└─ @login_required decorator works
```

## Timeline: User Journey

```
T=0     User on login page
        └─ Sees "Continue with Google" button

T=1s    User clicks Google button
        └─ Browser redirect initiated

T=2s    Google login page loads
        └─ User sees consent screen

T=5s    User enters Google credentials
        └─ Google verifies password

T=6s    Google shows permissions dialog
        └─ "JobPortal wants access to: Email, Profile"

T=7s    User clicks "Allow"
        └─ Google prepares redirect

T=8s    Browser redirects back to your app
        └─ URL: /auth/google/callback/?code=ABC123

T=9s    Your server receives callback
        ├─ Extracts authorization code
        └─ Begins token exchange

T=10s   Your server exchanges code
        ├─ Calls Google token endpoint
        ├─ Receives access_token
        └─ Stores temporarily

T=11s   Your server fetches user info
        ├─ Calls Google user API
        ├─ Receives email, name
        └─ Validates response

T=12s   Your server checks database
        ├─ Looks for existing user
        ├─ Creates new user if needed
        └─ Prepares login

T=13s   Session created
        ├─ Creates session record
        ├─ Sets session cookie
        └─ Authenticates user

T=14s   User redirected
        ├─ New user: to /create-profile/
        ├─ Existing user: to /home/
        └─ User sees logged-in state

T=15s   User fully logged in ✓
        └─ Dashboard visible, all features available

Total time: ~15 seconds (typical)
```

---

**Diagram Version**: 1.0
**Last Updated**: January 31, 2026
