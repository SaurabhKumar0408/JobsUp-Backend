from django.urls import path
from . import views

urlpatterns = [
   path('apply/<int:job_id>', views.applyToJob, name='apply_to_job'),

   path('viewMyApplication/', views.viewMyApplications, name='view_my_applications'),
   
   path('viewMyApplication/<int:application_id>/', views.applicationDetail, name='application_details'),

   path('withdrawApplication/<int:application_id>/', views.withdrawApplication, name='withdraw_application'),

   path('viewApplicationForJobs/<int:job_id>/', views.viewApplicationsForJob, name='view_application_for_jobs'),

   path('changeStatus/<int:application_id>/', views.changeStatus, name='change_status'),

    
] 
