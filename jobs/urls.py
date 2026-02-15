
from django.urls import path
from . import views

urlpatterns = [
    path('job/', views.viewAllJobs, name="view_all_jobs"),
    path('job/<int:job_id>/', views.jobDetail, name='job_detail'),
    path('createCompany/', views.create_company, name='create_company'),
    path('createJob/', views.createJob, name='create_job'),
    path('updateJob/<int:job_id>/', views.updateJob, name='update_job'),
    path('deleteJob/<int:job_id>/', views.deleteJob, name='delete_job'),
    path('myJobs/', views.myJobs, name="my_jobs"),
    path('myCompanies/', views.myCompanies, name='my_companies'),
    path('company/<int:company_id>/', views.companyDetails, name='company_details'),
    path('myCompanyJobs/<int:company_id>/', views.myCompanyJobs, name="my_company_jobs"),
    
]