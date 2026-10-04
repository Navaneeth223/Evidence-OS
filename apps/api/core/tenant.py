from rest_framework.exceptions import PermissionDenied
from rest_framework.exceptions import PermissionDenied
from .models import Membership

def active_organization(request):
    org_id = request.headers.get("X-Organization-ID")
    memberships = Membership.objects.filter(user=request.user).select_related("organization")
    membership = memberships.filter(organization_id=org_id).first() if org_id else memberships.first()
    if not membership:
        raise PermissionDenied("Choose an organization you belong to.")
    return membership.organization

def require_role(request, allowed_roles):
    org_id = request.headers.get("X-Organization-ID")
    memberships = Membership.objects.filter(user=request.user)
    membership = memberships.filter(organization_id=org_id).first() if org_id else memberships.first()
    if not membership:
        raise PermissionDenied("Choose an organization you belong to.")
    if membership.role not in allowed_roles:
        raise PermissionDenied("Your organization role does not allow this action.")
    return membership.organization
