from django.urls import path
from . import views

urlpatterns = [
    # Authentication
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('employer-login/', views.employer_login_view, name='employer_login'),
    path('logout/', views.logout_view, name='logout'),
    
    # Google OAuth
    path('auth/google/login/', views.google_login, name='google_login'),
    path('auth/google/callback/', views.google_callback, name='google_callback'),
    
    # Main Pages
    path('', views.home, name='home'),
    path('search/', views.search_results, name='search_results'),
    path('find-jobs/', views.find_jobs, name='find_jobs'),
    path('job/<int:job_id>/kanban/', views.kanban_board, name='kanban_board'),
    path('job/<int:pk>/', views.job_detail_view, name='job_detail'),
    path('job/<int:pk>/save/', views.save_job, name='save_job'),
    path('add-skill/', views.add_skill, name='add_skill'),
    path('delete-skill/', views.delete_skill, name='delete_skill'),
    # Dashboard & Profile
    
    
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('applications/', views.my_applications_view, name='my_applications'),
    path('saved-jobs/', views.saved_jobs_view, name='saved_jobs'),
    path('profile/', views.profile_view, name='profile_redirect'),
    path('profile/<str:username>/', views.profile_view, name='profile'),
    path('profile/<str:username>/skills/', views.view_all_skills, name='view_all_skills'),
    path('create-profile/', views.create_profile_view, name='create_profile'),
    path('add-experience/', views.add_experience, name='add_experience'),
    path('add-education/', views.add_education, name='add_education'),
    path('add-certification/', views.add_certification, name='add_certification'),
    path('settings/', views.settings_view, name='settings'),
    
    # ... other urls ...
    path('activity/', views.activity, name='activity'),  # <--- Add this line
    path('connect/<int:user_id>/', views.send_connection_request, name='send_connection_request'),
    
    # Company Views
    path('employer-register/', views.employer_register, name='employer_register'),
    path('company/<int:pk>/', views.company_profile, name='company_profile'),
    path('company/<int:pk>/follow/', views.follow_company, name='follow_company'),
    path('company/<int:pk>/debug/', views.company_profile_debug, name='company_profile_debug'),
    path('company-dashboard/', views.company_dashboard, name='company_dashboard'),
    path('post-job/', views.post_job, name='post_job'),
    path('company-settings/', views.company_settings, name='company_settings'),
    path('company/applicants/', views.employer_applicants_view, name='employer_applicants'),
    path('application/<int:application_id>/status/', views.update_application_status, name='update_application_status'),
    
    # jobportal/urls.py (Example)
    
    # Networking
    path('network/', views.network_page, name='network'),
    # Following list
    path('network/following/', views.following_list, name='following_list'),

    path('connections/', views.connections_list_view, name='connections_list'),
    path('send-request/<int:user_id>/', views.send_request, name='send_request'),
    path('accept-request/<int:request_id>/', views.accept_request, name='accept_request'),
    path('ignore-request/<int:request_id>/', views.ignore_request, name='ignore_request'),
    path('withdraw-request/<int:request_id>/', views.withdraw_request, name='withdraw_request'),
    path('user-search/', views.user_search_api, name='user_search_api'),
    
    # Messaging
    path('messages/', views.messaging, name='messaging'),
    path('messages/<int:thread_id>/', views.messaging, name='message_thread'),
    path('send-message/<int:thread_id>/', views.send_message, name='send_message'),
    path('delete-message/<int:message_id>/', views.delete_message, name='delete_message'),
    
    # Posts (AJAX)
    path('like-post/<int:post_id>/', views.like_post, name='like_post'),
    path('add-comment/<int:post_id>/', views.add_comment, name='add_comment'),
    path('share-post/<int:post_id>/', views.share_post, name='share_post'),
    path('get-share-users/', views.get_share_users, name='get_share_users'),
    path('create-post/', views.create_post, name='create_post'),
    path('posts/<int:pk>/delete/', views.delete_post, name='delete_post'),


    path('user/<int:pk>/', views.user_profile, name='user_profile'),

    # Existing profile URLs (likely already there)
    path('profile/', views.profile_view, name='profile'),
    path('profile/<str:username>/', views.profile_view, name='profile'),
]
