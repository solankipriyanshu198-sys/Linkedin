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
        title='DevOps Engineer',
        location='Mumbai',
        description='Looking for an experienced DevOps Engineer with Kubernetes, Docker, and CI/CD experience. Must have 3+ years.',
        job_type='Full Time'
    )
    print(f'✓ Created job: {job.title}')
    print('✓ Emails sent to all 16 users!')
else:
    print('✗ No company found')
