from django.core.management.base import BaseCommand
from django.core.mail import send_mail
from django.utils import timezone
from datetime import timedelta
from jobportal.models import JobAlert, Job

class Command(BaseCommand):
    help = 'Send job alerts to users based on their saved job alerts'

    def handle(self, *args, **options):
        # Get all job alerts
        alerts = JobAlert.objects.all()
        
        for alert in alerts:
            # Find matching jobs
            jobs_query = Job.objects.filter(
                title__icontains=alert.keyword
            ) | Job.objects.filter(
                description__icontains=alert.keyword
            ) | Job.objects.filter(
                skills__icontains=alert.keyword
            )
            
            if alert.location:
                jobs_query = jobs_query.filter(location__icontains=alert.location)
            
            # Only jobs from last 24 hours to avoid spam
            yesterday = timezone.now() - timedelta(days=1)
            jobs_query = jobs_query.filter(created_at__gte=yesterday)
            
            matching_jobs = jobs_query.distinct()
            
            if matching_jobs.exists():
                # Prepare email content
                job_list = "\n".join([f"- {job.title} at {job.company_name} in {job.location}" for job in matching_jobs])
                
                subject = f"New job matches for '{alert.keyword}'"
                message = f"""
Hello {alert.user.username},

We found new job opportunities matching your alert for '{alert.keyword}':

{job_list}

Check them out on our platform!

Best regards,
Job Portal Team
"""
                
                # Send email
                send_mail(
                    subject,
                    message,
                    'noreply@jobportal.com',  # From email
                    [alert.user.email],
                    fail_silently=False,
                )
                
                self.stdout.write(
                    self.style.SUCCESS(f'Sent job alert to {alert.user.email} for {matching_jobs.count()} jobs')
                )
            else:
                self.stdout.write(f'No new jobs found for alert: {alert.keyword} by {alert.user.username}')
        
        self.stdout.write(self.style.SUCCESS('Job alerts sent successfully'))