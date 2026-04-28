"""
Auth views for admin login.
Returns a DRF Token for the megaglow admin user so the frontend can call admin-only endpoints.
"""

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from django.contrib.auth import authenticate
from django.views.decorators.csrf import csrf_exempt
from rest_framework.authtoken.models import Token


@csrf_exempt  # Disable CSRF for this endpoint - token auth handles security
@api_view(['POST'])
@permission_classes([AllowAny])
def admin_login(request):
    """
    POST with { "username": "megaglow", "password": "mega123glow" }.
    Returns { "token": "<key>" } if credentials are valid and user is staff.
    """
    username = (request.data.get('username') or '').strip()
    password = request.data.get('password') or ''

    if not username or not password:
        return Response(
            {'error': 'Username and password are required'},
            status=status.HTTP_400_BAD_REQUEST
        )

    user = authenticate(request, username=username, password=password)
    if not user:
        return Response(
            {'error': 'Invalid username or password'},
            status=status.HTTP_401_UNAUTHORIZED
        )
    if not user.is_staff:
        return Response(
            {'error': 'Not authorized for admin access'},
            status=status.HTTP_403_FORBIDDEN
        )

    token, _ = Token.objects.get_or_create(user=user)
    return Response({'token': token.key})
