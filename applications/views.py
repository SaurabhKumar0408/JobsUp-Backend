from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.shortcuts import get_object_or_404
from jobs.models import Job
from django.utils import timezone
from .models import Application
from accounts.decorators import recruiter_required, jwt_required
from django.views.decorators.csrf import csrf_exempt
import json
# Create your views here.
@jwt_required
@csrf_exempt
def applyToJob(request, job_id):

    if request.method == 'POST':

        job = get_object_or_404(Job, id=job_id)
        user = request.user

        if job.application_deadline < timezone.now().date():
            return JsonResponse({"error" : "This job application is closed."}, status=400)
        
        if Application.objects.filter(applicant=user, job=job, status__in =['applied', 'shortlisted']).exists():
            return JsonResponse({"error" : "You have already applied to this job"}, status=400)
        
        application = Application.objects.create(
            applicant=user,
            job = job,
            cover_letter = request.POST.get('cover_letter'),
            resume = request.FILES.get('resume')
        )

        return JsonResponse({"message" : "Application submitted successfully."})

@jwt_required
def viewMyApplications(request):
    user = request.user

    application = Application.objects.filter(applicant=user).exclude(status='withdrawn').select_related('job', 'job__company')

    app_list = []
    for app in application.order_by('-applied_on'):
        app_list.append({
            'id' : app.id,
            'job_id' : app.job.id,
            'job_title' : app.job.title,
            'company' : app.job.company.name,
            'company_logo' : request.build_absolute_uri(app.job.company.logo.url) if app.job.company.logo else None,
            'applied_on' : app.applied_on.strftime("%Y-%m-%d"),
            'status': app.status,
        })
    return JsonResponse({"applications" : app_list})


@jwt_required
def applicationDetail(request, application_id):
    application = get_object_or_404(
        Application.objects.select_related('job', 'job__company'),
        id = application_id,
        applicant=request.user
    )

    data = {
        'application_id' : application_id,
        'status' : application.status,
        'applied_on': application.applied_on.strftime("%Y-%m-%d %H:%M"),
        'cover_letter' : application.cover_letter,
        'resume' : application.resume.url if application.resume else None,

        'job' : {
            'id' : application.job.id,
            'title' : application.job.title,
            'location' : application.job.location,
            'job_type' : application.job.job_type,
            'min_salary' : application.job.min_salary,
            'max_salary' : application.job.max_salary,
            'deadline' : application.job.application_deadline.strftime("%Y-%m-%d")
        },
        'company' : {
            'name' : application.job.company.name,
            'logo' : request.build_absolute_uri(application.job.company.logo.url) if application.job.company.logo else None,
            'website' : application.job.company.website,
        }
    }
    return JsonResponse(data)

@jwt_required
@csrf_exempt
def withdrawApplication(request, application_id):

    if request.method != 'POST':
        return JsonResponse(
            {'error': "Only POST method allowed"},
            status=405
        )
    
    application = get_object_or_404(
        Application,
        id=application_id,
        applicant=request.user
    )

    if application.status != 'applied':
        return JsonResponse(
            {'error' : f'Applications cannot be withdrawn in {application.status}'},
            status = 400
        )
    
    application.status = 'withdrawn'
    application.save(update_fields=['status'])

    return JsonResponse(
        {'message' : 'Application withdrawn successfully'}
    )


@jwt_required
@recruiter_required
def viewApplicationsForJob(request, job_id):
    job = get_object_or_404(Job, id = job_id, company__owner = request.user)

    applications = Application.objects.filter(job=job).select_related('applicant').order_by('-applied_on')

    app_list = []

    for app in applications:
        app_list.append({
            'application_id': app.id,
            'applicant': app.applicant.username,
            'status': app.status,
            'applied_on': app.applied_on.strftime("%Y-%m-%d"),
            'resume': app.resume.url if app.resume else None,
            'cover_letter': app.cover_letter,
        })

    return JsonResponse({
        'job': {
            'id': job_id,
            'title': job.title,
            'company': job.company.name,
        },
        'applications_count': applications.count(),
        'applications': app_list
    })


@jwt_required
@recruiter_required
@csrf_exempt
def changeStatus(request, application_id):
    application = get_object_or_404(Application, id=application_id, job__company__owner = request.user)

    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error' : "Invalid JSON"}, status=400)
    new_status = data.get('new_status')

    allowed_status = ['shortlisted', 'rejected']

    if new_status not in allowed_status:
        return JsonResponse({'error' : "Invalid status value"}, status=400)
    
    if application.status == 'withdrawn':
        return JsonResponse({'error' : 'withdrawn application cannot be updated'}, status=400)
    
    application.status=new_status
    application.save()

    return JsonResponse({
        'message': 'Application status updated successfully',
        'application_id': application.id,
        'new_status': new_status
    })