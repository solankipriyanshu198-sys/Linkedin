#!/usr/bin/env python
import os
import sys
import django

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'internship.settings')
sys.path.insert(0, os.path.dirname(__file__))
django.setup()

from jobportal.models import Job, Company

# Create a test job matching "Python" keyword
company = Company.objects.first()
if company:
    job = Job.objects.create(
        company=company,
        title='Senior Python Developer',
        location='Ahmedabad',
        description='We are looking for an experienced Python developer to join our team. Must have 3+ years of experience with Django and REST APIs.',
        job_type='Full Time'
    )
    print(f'✓ Created job: {job.title}')
    print('Email alerts should be sent automatically!')
else:
    print('✗ No company found')
