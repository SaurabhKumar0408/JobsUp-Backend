from django.db import models
from django.contrib.auth.models import User

# Create your models here.
class Company(models.Model):
    name = models.CharField(max_length=50, blank=False)
    logo = models.ImageField(upload_to='company/', blank=True)
    description = models.TextField()
    location = models.CharField(max_length=200, blank=True)
    website = models.URLField(blank=True)
    owner = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='owned_companies',
        blank=True,
        null=True
    )

    def __str__(self):
        return self.name
    

class Job(models.Model):
    JOB_TYPES = (
        ('full-time', 'Full Time'),
        ('part-time', 'Part Time'),
        ('internship', 'Internship'),
        ('remote', 'Remote'),
    )

    title = models.CharField(max_length=200)
    company = models.ForeignKey(Company, on_delete=models.CASCADE)
    description = models.TextField()
    skills_required = models.CharField(max_length=300)
    min_salary = models.IntegerField()
    max_salary = models.IntegerField()
    location = models.CharField(max_length=100)
    job_type = models.CharField(max_length=20, choices=JOB_TYPES)
    posted_on = models.DateTimeField(auto_now_add=True)
    application_deadline = models.DateField()

    def __str__(self):
        return self.title

