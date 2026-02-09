#!/usr/bin/env python
import os
import sys
import django

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'internship.settings')
sys.path.insert(0, os.path.dirname(__file__))
django.setup()

from jobportal.models import Job, Company

# Create a test job
company = Company.objects.first()
if company:
    job = Job.objects.create(
        company=company,
        title='Cloud Architect - AWS/Azure',
        location='Hyderabad',
        description='Looking for a Cloud Architect with 7+ years experience in AWS and Azure cloud platforms. Must have expertise in infrastructure as code and DevOps.',
        job_type='Full Time',
        salary_min=120000,
        salary_max=180000
    )
    print(f'✅ Job created: {job.title}')
    print(f'📧 Emails sent! Check Mailtrap for inbox.')
else:
    print('❌ No company found')
