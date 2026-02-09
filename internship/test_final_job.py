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
        title='Senior Backend Developer (Django/FastAPI)',
        location='Pune',
        description='Looking for a senior backend developer with 5+ years of experience in Python, Django, and FastAPI. Must have experience with REST APIs, database design, and cloud deployment.',
        job_type='Full Time',
        salary_min=80000,
        salary_max=120000
    )
    print(f'\n✅ Job created: {job.title}')
    print(f'Check your terminal for email notifications!\n')
else:
    print('❌ No company found')
