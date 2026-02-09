#!/usr/bin/env python
import os
import sys
import django

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'internship.settings')
sys.path.insert(0, os.path.dirname(__file__))

django.setup()

from jobportal.models import Company, Job

# Check all companies
print("=== Companies and Jobs ===\n")
companies = Company.objects.all()
print(f'Total companies: {companies.count()}\n')

for company in companies:
    jobs_count = Job.objects.filter(company=company).count()
    print(f'Company {company.id}: {company.company_name} - {jobs_count} jobs')
    
    # Show details of jobs for each company
    jobs = Job.objects.filter(company=company)
    for job in jobs:
        print(f'  - {job.title} (ID: {job.id}, company_id: {job.company_id})')

# Check company 4 specifically
print("\n=== Company 4 Details ===")
try:
    company4 = Company.objects.get(id=4)
    print(f"Company: {company4.company_name}")
    print(f"User: {company4.user.username if company4.user else 'None'}")
    
    jobs = Job.objects.filter(company=company4)
    print(f"Total jobs: {jobs.count()}")
    for job in jobs:
        print(f"  - {job.title}")
except Company.DoesNotExist:
    print("Company 4 not found!")
