from django.shortcuts import render

from main.models import Organization


def login(request, **kwargs):
    org_code = kwargs.get('org_code')
    error = None
    organization = None
    try:
        organization = Organization.objects.get(code=org_code)
    except Organization.DoesNotExist:
        error = "Organization not found!"
    context = {
        'error': error,
        'organization': organization,
    }
    return render(request, 'main/login.html', context=context)


def dashboard(request):
    return render(request, 'main/dashboard.html')