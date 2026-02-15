from .models import Job, Company
from django.db.models import Q
from django.http import JsonResponse
from django.views.decorators.http import require_GET
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt

from accounts.decorators import recruiter_required, jwt_required
from django.views.decorators.http import require_POST
import json
from django.core.paginator import Paginator

# Create your views here.
def viewAllJobs(request):

    if request.method == 'GET':
        today = timezone.now().date()
        jobs = Job.objects.filter(application_deadline__gte = today).select_related('company')

        job_type = request.GET.get("job_type")
        location = request.GET.get("location")
        min_salary = request.GET.get('min_salary')
        max_salary = request.GET.get('max_salary')
        search = request.GET.get('search')

        if job_type:
            jobs = jobs.filter(job_type = job_type)

        if location:
            jobs = jobs.filter(location__icontains = location)

        if min_salary:
            jobs = jobs.filter(min_salary__gte = min_salary)
        
        if max_salary:
            jobs = jobs.filter(max_salary__lte = max_salary)
        
        if search:
            search_words = search.split()

            query = Q()
            for word in search_words:
                query |= Q(title__icontains=word)
                query |= Q(skills_required__icontains=word)
                query |= Q(description__icontains=word)

            jobs = jobs.filter(query)
    
        job_list = []
        jobs = jobs.order_by('-posted_on')
        page = request.GET.get('page')
        page_size = int(request.GET.get('page_size', 10))
        paginator = Paginator(jobs, page_size)
        page_jobs = paginator.get_page(page)

        for job in page_jobs:
            job_list.append({
                'id' : job.id,
                'title': job.title,
                
                'location': job.location,
                'min_salary' : job.min_salary,
                'max_salary' : job.max_salary,
                'posted_on' : job.posted_on.strftime("%Y-%m-%d"),
                'job_type' : job.job_type, 
                'company': {
                    'id': job.company.id,
                    'name': job.company.name,
                    'location': job.company.location,
                    'logo' : request.build_absolute_uri(job.company.logo.url) if job.company.logo else None,
                },
            })

        return JsonResponse({
            "count" : jobs.count(),
            "total_pages": paginator.num_pages,
            'current':page,
            'jobs' : job_list
            }, safe=False)

@require_GET
def jobDetail(request, job_id):
    job = get_object_or_404(
        Job.objects.select_related('company'),
        id = job_id
    )

    job_data = {
        'id' : job.id,
        'title' : job.title,
        'description' : job.description,
        'skills_required' : job.skills_required,
        'job_type' : job.job_type,
        'location' : job.location,
        'min_salary' : job.min_salary,
        'max_salary' : job.max_salary,
        'deadline' : job.application_deadline.strftime("%Y-%m-%d"),
        'posted_on' : job.posted_on.strftime("%Y-%m-%d"),
        'company' : {
            'id' : job.company.id,
            'name' : job.company.name,
            'description' : job.company.description,
            'location' : job.company.location,
            'website' : job.company.website,
            'logo' : request.build_absolute_uri(job.company.logo.url) if job.company.logo else None,
        }
    }

    return JsonResponse(job_data)

@jwt_required
@recruiter_required
@require_POST
@csrf_exempt
def create_company(request):
    name = request.POST.get('name')
    description = request.POST.get('description')
    location = request.POST.get('location')
    website = request.POST.get('website')
    logo = request.FILES.get('logo')

    if not name or not description:
        return JsonResponse(
            {'error' : "Name and Description are required"},
            status=400
        )
    
    company = Company.objects.create(
        owner = request.user,
        name=name,
        description=description,
        location = location,
        website = website,
        logo = logo
    )

    return JsonResponse({
        'message' : 'Company created successfully',
        'company' : {
            'id' : company.id,
            'name' : company.name,
            'logo' : request.build_absolute_uri(company.logo.url) if company.logo else None,
            'location': company.location,
            'website' : company.website
        }
    })

@jwt_required
@recruiter_required
@require_POST
@csrf_exempt
def createJob(request):
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error':'Invalid Json'},  status=400)
    
    title = data.get('title')
    company_id = data.get('company_id')
    description = data.get('description')
    skills_required = data.get('skills_required')
    min_salary = data.get('min_salary')
    max_salary = data.get('max_salary')
    location = data.get('location')
    job_type = data.get('job_type')
    deadline = data.get('application_deadline')

    if not all([title, company_id, description, skills_required, min_salary, max_salary, location, job_type, deadline]):
        return JsonResponse(
            {'error' : "All fields are required"},
            status = 400
        )
    
    try:
        company = Company.objects.get(id = company_id, owner=request.user)
    except Company.DoesNotExist:
        return JsonResponse({'error' : "Company not found"}, status = 404)
    
    try:
        deadline_date = timezone.datetime.strptime(deadline, '%Y-%m-%d').date()
        if deadline_date < timezone.now().date():
            return JsonResponse({'error' : 'Deadline cannot be in the past'}, status=400)
    except ValueError:
        return JsonResponse({'error' : 'Invalid date format. Use YYYY-MM-DD'}, status = 400)
    
    job = Job.objects.create(
        title = title,
        company=company,
        description=description,
        skills_required=skills_required,
        min_salary=min_salary,
        max_salary=max_salary,
        location=location,
        job_type=job_type,
        application_deadline = deadline_date
    )

    return JsonResponse({
        'message': 'Job created successfully',
        'job': {
            'id': job.id,
            'title': job.title,
            'company': job.company.name,
            'location': job.location,
            'job_type': job.job_type,
            'min_salary': job.min_salary,
            'max_salary': job.max_salary,
            'deadline': job.application_deadline.strftime("%Y-%m-%d"),
        }
    })

@jwt_required
@recruiter_required
@require_POST
@csrf_exempt
def updateJob(request, job_id):

    job = get_object_or_404(Job, id=job_id, company__owner = request.user)

    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    title = data.get('title')
    description = data.get('description')
    skills_required = data.get('skills_required')
    min_salary = data.get('min_salary')
    max_salary = data.get('max_salary')
    location = data.get('location')
    job_type = data.get('job_type')
    deadline = data.get('deadline')

    if title:
        job.title = title
    if description:
        job.description = description
    if skills_required:
        job.skills_required = skills_required
    if location:
        job.location = location
    if job_type:
        job.job_type = job_type

    if min_salary or max_salary:
        try:
            min_sal = int(min_salary) if min_salary else job.min_salary
            max_sal = int(max_salary) if max_salary else job.max_salary

            if min_sal > max_sal:
                return JsonResponse(
                    {'error': 'Min salary cannot be greater than max salary'},
                    status=400
                )

            job.min_salary = min_sal
            job.max_salary = max_sal

        except ValueError:
            return JsonResponse(
                {'error': 'Salary must be numeric'},
                status=400
            )

    if deadline:
        try:
            deadline_date = timezone.datetime.strptime(deadline, '%Y-%m-%d').date()
            if deadline_date < timezone.now().date():
                return JsonResponse(
                    {'error' : 'Deadline cannot be in the past'},
                    status=400
                )
            job.application_deadline = deadline_date
        except ValueError:
            return JsonResponse(
                {'error' : "Invalid date format. Use YYYY-MM-DD"},
                status=400
            )
    
    job.save()
    return JsonResponse({
        'message' : 'Job updated successfully',
        'job_id' : job.id
    })


@jwt_required
@recruiter_required
@require_POST
def deleteJob(request, job_id):
    job = get_object_or_404(Job, id = job_id, company__owner = request.user)

    job.delete()

    return JsonResponse({
        'message' : 'Job delete successfully',
        'job_id' : job_id
    })


@jwt_required
@recruiter_required
@require_GET
def myCompanyJobs(request, company_id):
    jobs = Job.objects.filter(company__owner = request.user).select_related('company').order_by('-posted_on')
    company = get_object_or_404(Company, id=company_id)

    if company_id:
        jobs = jobs.filter(company = company)
    job_list = []
    for job in jobs:
        job_list.append({
            'id' : job.id,
            'title':job.title,
            'location': job.location,
            'job_type': job.job_type,
            'min_salary': job.min_salary,
            'max_salary': job.max_salary,
            'deadline' : job.application_deadline.strftime("%Y-%m-%d"),
            'company': {
                'id' : job.company.id,
                'name' : job.company.name,
                'logo' : request.build_absolute_uri(job.company.logo.url) if job.company.logo else None,

            }
        })
    return JsonResponse({'count' : jobs.count(), 'jobs':job_list})

@jwt_required
@recruiter_required
@require_GET
def myJobs(request):
    jobs = Job.objects.filter(company__owner = request.user).select_related('company').order_by('-posted_on')
    
    job_list = []
    for job in jobs:
        job_list.append({
            'id' : job.id,
            'title':job.title,
            'location': job.location,
            'job_type': job.job_type,
            'min_salary': job.min_salary,
            'max_salary': job.max_salary,
            'deadline' : job.application_deadline.strftime("%Y-%m-%d"),
            'company': {
                'id' : job.company.id,
                'name' : job.company.name,
                'logo' : request.build_absolute_uri(job.company.logo.url) if job.company.logo else None,

            }
        })
    return JsonResponse({'count' : jobs.count(), 'jobs':job_list})

@jwt_required
@recruiter_required
@require_GET
def myCompanies(request):
    companies = Company.objects.filter(owner=request.user)

    company_list = []
    for company in companies:
        company_list.append({
            'id': company.id,
            'name': company.name,
            'location': company.location,
            'website': company.website,
            'logo': request.build_absolute_uri(company.logo.url) if company.logo else None,
        })

    return JsonResponse({
        'count': len(company_list),
        'companies': company_list
    })

@jwt_required
@recruiter_required
@require_GET
def companyDetails(request, company_id):
    company = get_object_or_404(Company, owner=request.user, id=company_id)
    companyJobs = Job.objects.filter(company = company)
    jobs = []
    for job in companyJobs:
        jobs.append({
            'id' : job.id,
            'title' : job.title,
            'location' : job.location,
            'job_type' : job.job_type,
            'min_salary' : job.min_salary,
            'max_salary' : job.max_salary,
        })

    companyData = {
        'company_id' : company.id,
        'name' : company.name,
        'location' : company.location,
        'website' : company.website,
        'logo' : request.build_absolute_uri(company.logo.url) if company.logo else None,
        'jobs' : jobs,
        'description': company.description,
    }

    return JsonResponse({
        'company' : companyData,
    })
