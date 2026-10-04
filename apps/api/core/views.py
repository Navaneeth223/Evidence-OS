import re
from django.contrib.auth import get_user_model
from django.db import transaction
from django.db.utils import OperationalError
from django.http import JsonResponse
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from .models import Organization, Membership

@api_view(["GET"])
@permission_classes([AllowAny])
def health(request):
    try:
        from django.db import connection
        connection.ensure_connection()
        return JsonResponse({"status": "ok"})
    except OperationalError:
        return JsonResponse({"status": "unavailable"}, status=503)

@api_view(["POST"])
@permission_classes([AllowAny])
def register(request):
    email = request.data.get("email", "").strip().lower()
    password = request.data.get("password", "")
    org_name = request.data.get("organization_name", "").strip()
    if not email or not org_name or len(password) < 12:
        return Response({"detail": "Email, organization name, and a password of at least 12 characters are required."}, status=400)
    User = get_user_model()
    if User.objects.filter(username=email).exists():
        return Response({"email": ["An account with this email already exists."]}, status=400)
    base = re.sub(r"[^a-z0-9]+", "-", org_name.lower()).strip("-")[:150] or "company"
    slug, suffix = base, 1
    while Organization.objects.filter(slug=slug).exists(): suffix += 1; slug = f"{base}-{suffix}"
    with transaction.atomic():
        user = User.objects.create_user(username=email, email=email, password=password, first_name=request.data.get("first_name", ""))
        org = Organization.objects.create(name=org_name, slug=slug)
        Membership.objects.create(user=user, organization=org, role=Membership.Role.OWNER)
    token = RefreshToken.for_user(user)
    return Response({"access": str(token.access_token), "refresh": str(token), "organization": {"id": str(org.id), "name": org.name, "slug": org.slug}}, status=status.HTTP_201_CREATED)

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def me(request):
    return Response({"id": request.user.id, "email": request.user.email, "first_name": request.user.first_name})

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def organizations(request):
    return Response([{"id": str(m.organization_id), "name": m.organization.name, "role": m.role} for m in Membership.objects.filter(user=request.user).select_related("organization")])
