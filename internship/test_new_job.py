#!/usr/bin/env python
import os
import sys
import django

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'internship.settings')
sys.path.insert(0, os.path.dirname(__file__))
django.setup()

from jobportal.models import Job, Company
from django.contrib.auth.models import User

# Create a test job
company = Company.objects.first()
if company:
    job = Job.objects.create(
        company=company,
        title='Full Stack Developer (MERN)',
        location='Bangalore',
        description='Seeking an experienced Full Stack Developer proficient in MongoDB, Express, React, and Node.js. Must have 2+ years of experience.',
        job_type='Full Time'
    )
    print(f'✓ Created job: {job.title}')
    print(f'✓ Total active users: {User.objects.filter(is_active=True).exclude(is_superuser=True).count()}')
else:
    print('✗ No company found')
