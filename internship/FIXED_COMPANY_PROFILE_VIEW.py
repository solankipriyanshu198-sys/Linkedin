"""
COMPLETE FIXED CODE - jobportal/views.py
Company Profile View (Lines 1101-1145)
"""

def company_profile(request, pk):  # Renamed from company_detail to company_profile
    # Get the company
    company = get_object_or_404(Company, id=pk)
    
    # Query the Job model directly - THIS GETS THE JOBS!
    jobs = Job.objects.filter(company=company).order_by('-created_at')
    
    # Get other details
    active_tab = request.GET.get('tab', 'home')
    active_filter = request.GET.get('filter', 'culture')
    
    # Check employees
    try:
        employees = UserProfile.objects.filter(company=company)
        employee_count = employees.count()
    except:
        employees = []
        employee_count = 0

    # Determine which template to use based on user type
    is_owner = request.user.is_authenticated and hasattr(request.user, 'company') and request.user.company.id == pk
    template_name = 'companies/company_profile.html' if is_owner else 'jobportal/company_profile.html'
    
    # Check if user is following the company
    is_following = False
    if request.user.is_authenticated:
        is_following = company.followers.filter(id=request.user.id).exists()

    context = {
        'company': company,
        'active_tab': active_tab,
        'active_filter': active_filter,
        'jobs': jobs,  # <-- JOBS ARE PASSED HERE!
        'employees': employees,
        'employee_count': employee_count,
        'is_company_profile': True,
        'is_following': is_following,
    }
    
    return render(request, template_name, context)


def company_profile_debug(request, pk):
    """Debug view to check what data is being passed"""
    company = get_object_or_404(Company, id=pk)
    jobs = Job.objects.filter(company=company).order_by('-created_at')
    
    try:
        employees = UserProfile.objects.filter(company=company)
        employee_count = employees.count()
    except:
        employees = []
        employee_count = 0
    
    is_owner = request.user.is_authenticated and hasattr(request.user, 'company') and request.user.company.id == pk
    
    context = {
        'company': company,
        'active_tab': request.GET.get('tab', 'home'),
        'jobs': jobs,
        'employees': employees,
        'employee_count': employee_count,
        'is_owner': is_owner,
    }
    
    return render(request, 'jobportal/debug_company.html', context)
