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
        title='React Developer',
        location='Ahmedabad',
        description='Looking for React expert with 2+ years experience',
        job_type='Full Time'
    )
    print(f'✓ Created job: {job.title}')
else:
    print('✗ No company found')
