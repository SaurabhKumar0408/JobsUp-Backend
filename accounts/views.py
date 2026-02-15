from django.views.decorators.http import require_POST
import json
from django.http import JsonResponse
from django.contrib.auth.models import User
from django.db import transaction

from django.views.decorators.csrf import csrf_exempt

from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate


# Create your views here.
@require_POST
@csrf_exempt
def register(request):
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error':'Invalid Json'}, status=400)
    
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')
    role = data.get('role')

    if not all([username, email, password, role]):
        return JsonResponse(
            {'error':"All fields are required"},
            status=400
        )
    
    if role not in ['Applicant', 'Recruiter']:
        return JsonResponse({'error':"Invalid role"}, status=400)
    
    if User.objects.filter(email=email).exists():
        return JsonResponse({'error':"Email already exists"}, status=400)
    
    try:
        with transaction.atomic():
            user=User.objects.create_user(
                username=username,
                email=email,
                password=password
            )

        
            user.profile.role=role
            user.profile.save()
            print(user.profile.role)
    except Exception:

        return JsonResponse({'error':"Something went wrong"}, status=500)
    
    return JsonResponse(
        {'message':'Registration successful, Please login'},
        status=201
    )



@csrf_exempt
def login(request):
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error':'Invalid Json'},  status=400)
    username = data.get('username')
    password = data.get('password')

    user = authenticate(username=username, password=password)

    if not user:
        return JsonResponse({'error': 'Invalid credentials'}, status=401)

    refresh = RefreshToken.for_user(user)

    return JsonResponse({
        'access': str(refresh.access_token),
        'refresh': str(refresh),
        'user': {
            'id': user.id,
            'username': user.username,
            'role': user.profile.role   
        }
    })
