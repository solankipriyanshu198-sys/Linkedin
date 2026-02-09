from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.exceptions import ObjectDoesNotExist

# ---------------------------------------------------------
# 1. COMPANY MODEL (Employers)
# ---------------------------------------------------------
class Company(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="company")
    company_name = models.CharField(max_length=200)
    location = models.CharField(max_length=200)
    address = models.TextField(default="")  # <--- Add this line
    
    # Followers field (Good)
    followers = models.ManyToManyField(
        User, 
        related_name='following_companies', 
        blank=True
    )

    # Profile Fields
    website = models.URLField(blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    
    # Extra fields
    industry = models.CharField(max_length=100, blank=True)
    company_size = models.CharField(max_length=50, blank=True)
    founded = models.CharField(max_length=4, blank=True)
    specialties = models.TextField(blank=True)

    # Images
    logo = models.ImageField(upload_to='company_logos/', blank=True, null=True)
    cover_image = models.ImageField(upload_to='company_covers/', blank=True, null=True)

    def __str__(self):
        return self.company_name


# ---------------------------------------------------------
# 2. JOB MODEL
# ---------------------------------------------------------
# Inside jobportal/models.py

class JobApplication(models.Model):  # You might have named this differently
    # ... your existing fields (user, job, date, etc.) ...
    
    # NEW: Add this status field
    STATUS_CHOICES = (
        ('applied', 'Applied'),
        ('screening', 'Screening'),
        ('interview', 'Interview'),
        ('selected', 'Selected'),
        ('rejected', 'Rejected'),
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='applied')

    # ... existing code ...


class Job(models.Model):
    JOB_TYPES = [
        ('Full Time', 'Full Time'),
        ('Part Time', 'Part Time'),
        ('Freelance', 'Freelance'),
        ('Internship', 'Internship'),
    ]

    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name="jobs"
    )

    title = models.CharField(max_length=200)
    company_name = models.CharField(max_length=100, editable=False)
    location = models.CharField(max_length=100)

    description = models.TextField()
    requirements = models.TextField(blank=True, default="No specific requirements.")
    benefits = models.TextField(blank=True, default="Competitive salary.")

    salary_min = models.PositiveIntegerField(default=0)
    salary_max = models.PositiveIntegerField(default=0)

    job_type = models.CharField(max_length=20, choices=JOB_TYPES, default='Full Time')

    is_remote = models.BooleanField(default=False)
    is_urgent = models.BooleanField(default=False)

    created_at = models.DateTimeField(default=timezone.now)
    views = models.IntegerField(default=0)
    
    # Skills required for the job (comma-separated)
    skills = models.TextField(blank=True, null=True, help_text="Comma-separated skills required for this job")

    def save(self, *args, **kwargs):
        # Auto-sync company name
        if self.company:
            self.company_name = self.company.company_name
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.title} at {self.company_name}"
    
    def get_requirements_list(self):
        return self.requirements.split('\n')

    def get_benefits_list(self):
        return self.benefits.split('\n')


# ---------------------------------------------------------
# 3. CANDIDATE DETAILS
# ---------------------------------------------------------
class Experience(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="experiences")
    title = models.CharField(max_length=100)
    company = models.CharField(max_length=100)
    location = models.CharField(max_length=100, blank=True)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    is_current = models.BooleanField(default=False)
    description = models.TextField(blank=True)

    def __str__(self):
        return f"{self.title} - {self.company}"


class Education(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="educations")
    school = models.CharField(max_length=100)
    degree = models.CharField(max_length=100)
    field_of_study = models.CharField(max_length=100, blank=True)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)

    def __str__(self):
        return self.school


class Certification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="certifications")
    name = models.CharField(max_length=100)
    issuing_organization = models.CharField(max_length=100)
    issue_date = models.DateField(null=True, blank=True)
    credential_url = models.URLField(blank=True)

    def __str__(self):
        return self.name


# ---------------------------------------------------------
# 4. SOCIAL POSTS & COMMENTS
# ---------------------------------------------------------
class Post(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="posts")
    content = models.TextField()
    image = models.ImageField(upload_to='post_images/', blank=True, null=True)
    video = models.FileField(upload_to='post_videos/', blank=True, null=True) 
    created_at = models.DateTimeField(auto_now_add=True)
    likes = models.ManyToManyField(User, related_name='liked_posts', blank=True)
    impressions_count = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f"Post by {self.user.username}"

    @property
    def total_likes(self):
        return self.likes.count()

class PostComment(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='comments')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Comment by {self.user.username} on {self.post.id}"


# ---------------------------------------------------------
# 5. APPLICATIONS & SAVED JOBS
# ---------------------------------------------------------
class Application(models.Model):
    STATUS_CHOICES = [
        ('applied', 'Applied'),
        ('interview', 'Interview'),
        ('selected', 'Selected'),
        ('rejected', 'Rejected'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name='applications')
    resume = models.FileField(upload_to='resumes/')
    
    phone = models.CharField(max_length=20, blank=True, null=True)
    
    # --- ADD THESE TWO FIELDS ---
    experience = models.CharField(max_length=50, blank=True, null=True)
    commute = models.CharField(max_length=10, blank=True, null=True)
    # -----------------------------

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='applied')
    applied_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'job')

    def __str__(self):
        return f"{self.user.username} applied to {self.job.title}"
class SavedJob(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    job = models.ForeignKey(Job, on_delete=models.CASCADE)
    saved_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'job')


# ---------------------------------------------------------
# 6. NETWORKING
# ---------------------------------------------------------
class ConnectionRequest(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('ignored', 'Ignored'),
    )
    sender = models.ForeignKey(User, related_name='sent_requests', on_delete=models.CASCADE)
    receiver = models.ForeignKey(User, related_name='received_requests', on_delete=models.CASCADE)
    note = models.TextField(blank=True, null=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    timestamp = models.DateTimeField(auto_now_add=True) 

    class Meta:
        unique_together = ('sender', 'receiver')


# ---------------------------------------------------------
# 7. MESSAGING
# ---------------------------------------------------------
class MessageThread(models.Model):
    participants = models.ManyToManyField(User, related_name="threads")
    updated_at = models.DateTimeField(auto_now=True)


class Message(models.Model):
    thread = models.ForeignKey(MessageThread, on_delete=models.CASCADE, related_name="messages")
    sender = models.ForeignKey(User, on_delete=models.CASCADE)
    body = models.TextField(blank=True, null=True)
    image = models.ImageField(upload_to='message_images/', blank=True, null=True)
    post = models.ForeignKey(Post, on_delete=models.CASCADE, blank=True, null=True, related_name="shared_messages")
    created_at = models.DateTimeField(auto_now_add=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    class Meta: 
        ordering = ['timestamp']


# ---------------------------------------------------------
# 8. PROXY MODELS (Admin Separation)
# ---------------------------------------------------------
class CandidateUser(User):
    class Meta:
        proxy = True
        verbose_name = 'Candidate User'
        verbose_name_plural = 'Candidate Users'

class EmployerUser(User):
    class Meta:
        proxy = True
        verbose_name = 'Employer User'
        verbose_name_plural = 'Employer Users'


# ---------------------------------------------------------
# 9. USER PROFILE
# ---------------------------------------------------------
class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='userprofile')
    
    # --- BASIC PROFILE FIELDS ---
    headline = models.CharField(max_length=255, blank=True, null=True)
    bio = models.TextField(blank=True, null=True)
    location = models.CharField(max_length=100, blank=True, null=True)
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    
    # --- MEDIA ---
    profile_picture = models.ImageField(upload_to='profile_pics/', blank=True, null=True)
    cover_image = models.ImageField(upload_to='cover_images/', blank=True, null=True)
    resume = models.FileField(upload_to='resumes/', blank=True, null=True)
    
    # --- LINKS & SKILLS ---
    portfolio_url = models.URLField(blank=True, null=True)
    skills = models.TextField(blank=True, null=True, help_text="Comma-separated skills")

    # --- >>> THIS IS THE MISSING FIELD THAT CAUSED THE ERROR <<< ---
    connections = models.ManyToManyField("self", blank=True)

    # --- SETTINGS TOGGLES ---
    profile_visibility = models.BooleanField(default=True)
    email_visibility = models.BooleanField(default=False)
    activity_status = models.BooleanField(default=True)
    data_sharing = models.BooleanField(default=False)
    personalized_ads = models.BooleanField(default=True)
    notify_jobs = models.BooleanField(default=True)
    notify_network = models.BooleanField(default=True)

    # --- ANALYTICS ---
    search_appearances_count = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f"{self.user.username}'s Profile"


# ---------------------------------------------------------
# 9.1. PROFILE VIEW TRACKING
# ---------------------------------------------------------
class ProfileView(models.Model):
    profile = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name='views')
    viewer = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('profile', 'viewer')


# ---------------------------------------------------------
# 9.2. CONNECTION MODEL (For "People you may know")
# ---------------------------------------------------------
class Connection(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
    )
    sender = models.ForeignKey(User, related_name='sent_connections', on_delete=models.CASCADE)
    receiver = models.ForeignKey(User, related_name='received_connections', on_delete=models.CASCADE)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('sender', 'receiver')


# ---------------------------------------------------------
# 10. SIGNALS
# ---------------------------------------------------------
@receiver(post_save, sender=User)
def create_profile_signal(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.get_or_create(user=instance)

@receiver(post_save, sender=User)
def save_profile_signal(sender, instance, **kwargs):
    try:
        instance.userprofile.save()
    except ObjectDoesNotExist:
        UserProfile.objects.create(user=instance)
    except AttributeError:
        pass



class JobAlert(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    keyword = models.CharField(max_length=100, help_text="e.g., Python Developer")
    location = models.CharField(max_length=100, blank=True, null=True, help_text="e.g., Ahmedabad")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.keyword}"


# ---------------------------------------------------------
# 11. SIGNAL FOR AUTOMATIC JOB ALERTS
# ---------------------------------------------------------
@receiver(post_save, sender=Job)
def send_job_alert_on_new_job(sender, instance, created, **kwargs):
    """Send job alerts to ALL users when a new job is posted"""
    if not created:
        return  # Only send on new jobs, not updates
    
    try:
        from django.core.mail import send_mail
        from django.contrib.auth.models import User as DjangoUser
        
        # Get all candidate users (exclude superusers and admins)
        candidate_users = DjangoUser.objects.filter(
            is_active=True,
            is_staff=False
        )
        
        print(f"\n{'='*80}")
        print(f"📧 SENDING JOB ALERTS FOR NEW JOB: {instance.title}")
        print(f"{'='*80}\n")
        
        sent_count = 0
        failed_count = 0
        
        for user in candidate_users:
            if not user.email:
                print(f"⚠️  Skipping {user.username} - No email address")
                continue
            
            try:
                subject = f"🎯 New Job Posted: {instance.title}"
                message = f"""
Hello {user.first_name or user.username},

🎉 A new exciting job opportunity has been posted on JobPortal!

{'─'*80}
📌 JOB DETAILS:
{'─'*80}
Job Title:   {instance.title}
Company:     {instance.company_name}
Location:    {instance.location}
Job Type:    {instance.job_type}
Salary:      ${instance.salary_min} - ${instance.salary_max} (if available)
{'─'*80}

📝 DESCRIPTION:
{instance.description[:500]}...

✨ Don't miss this opportunity! Login to JobPortal to view full details and apply now.

Best regards,
JobPortal Team
"""
                
                # Send email
                send_mail(
                    subject,
                    message,
                    'noreply@jobportal.com',
                    [user.email],
                    fail_silently=False,
                )
                
                sent_count += 1
                print(f"✅ Email sent to {user.email} ({user.username})")
                
            except Exception as email_error:
                failed_count += 1
                print(f"❌ Failed to send email to {user.email}: {str(email_error)}")
        
        print(f"\n{'='*80}")
        print(f"📊 SUMMARY: {sent_count} emails sent, {failed_count} failed")
        print(f"{'='*80}\n")
        
    except Exception as e:
        print(f"❌ ERROR IN JOB ALERT SIGNAL: {str(e)}")
        import traceback
        traceback.print_exc()