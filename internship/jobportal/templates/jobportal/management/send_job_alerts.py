from django.core.management.base import BaseCommand
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings
from datetime import timedelta
from your_app_name.models import JobAlert, Job  # Update 'your_app_name'

class Command(BaseCommand):
    help = 'Sends email alerts for new jobs posted in the last 24 hours'

    def handle(self, *args, **kwargs):
        # 1. Define the time range (last 24 hours)
        time_threshold = timezone.now() - timedelta(days=1)

        # 2. Loop through every user alert
        alerts = JobAlert.objects.all()
        
        for alert in alerts:
            # 3. Find matching jobs created recently
            matching_jobs = Job.objects.filter(
                title__icontains=alert.keyword,
                created_at__gte=time_threshold
            )

            # If location is specified, filter by that too
            if alert.location:
                matching_jobs = matching_jobs.filter(location__icontains=alert.location)

            # 4. If matches found, send email
            if matching_jobs.exists():
                job_list_text = "\n".join([f"- {job.title} at {job.company_name}" for job in matching_jobs])
                
                subject = f"New Jobs Found: {alert.keyword}"
                message = (
                    f"Hello {alert.user.username},\n\n"
                    f"We found new jobs matching your alert for '{alert.keyword}':\n\n"
                    f"{job_list_text}\n\n"
                    f"Log in to apply now!"
                )
                
                try:
                    send_mail(
                        subject,
                        message,
                        settings.EMAIL_HOST_USER,
                        [alert.user.email],
                        fail_silently=False,
                    )
                    self.stdout.write(self.style.SUCCESS(f"Email sent to {alert.user.email}"))
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f"Failed to send to {alert.user.email}: {e}"))