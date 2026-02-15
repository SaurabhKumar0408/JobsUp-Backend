from functools import wraps
from django.http import JsonResponse, HttpResponse
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.exceptions import AuthenticationFailed

def recruiter_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if request.method == "OPTIONS":
            return HttpResponse(status=200)
        user = request.user

        if not user or not user.is_authenticated:
            return JsonResponse(
                {'error': 'Authentication credentials were not provided'},
                status=403
            )

        if not hasattr(user, 'profile'):
            return JsonResponse(
                {'error': 'User profile not found'},
                status=403
            )

        if (user.profile.role != 'recruiter' and user.profile.role != 'Recruiter'):
            return JsonResponse(
                {'error':'Recruiter access only'},
                status=403
            )

        return view_func(request, *args, **kwargs)

    return _wrapped_view

def jwt_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        auth = JWTAuthentication()
        if request.method == "OPTIONS":
            return HttpResponse(status=200)
        try:
            validated_token= auth.get_validated_token(
                auth.get_raw_token(auth.get_header(request))
            )
            request.user = auth.get_user(validated_token)
        except AuthenticationFailed:
            return JsonResponse(
                {'error' : 'Authentication credentials we not provided or invalid'},
                status=401
            )
        return view_func(request, *args, **kwargs)
    return _wrapped_view
