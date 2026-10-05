import uuid
from django.conf import settings
from django.db import models

class Timestamped(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    class Meta:
        abstract = True

class Organization(Timestamped):
    name = models.CharField(max_length=180)
    slug = models.SlugField(max_length=180, unique=True)
    settings = models.JSONField(default=dict, blank=True)
    def __str__(self): return self.name

class Membership(Timestamped):
    class Role(models.TextChoices):
        OWNER = "OWNER", "Owner"; ADMIN = "ADMIN", "Admin"; EDITOR = "EDITOR", "Editor"; REVIEWER = "REVIEWER", "Reviewer"; VIEWER = "VIEWER", "Viewer"
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name="memberships")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="memberships")
    role = models.CharField(max_length=12, choices=Role.choices, default=Role.EDITOR)
    class Meta:
        constraints = [models.UniqueConstraint(fields=["organization", "user"], name="unique_org_membership")]

class AuditLog(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey(Organization, on_delete=models.PROTECT)
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL)
    action = models.CharField(max_length=80)
    resource_type = models.CharField(max_length=80)
    resource_id = models.UUIDField(null=True)
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

class ReviewTask(Timestamped):
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE)
    title = models.CharField(max_length=240)
    reason = models.CharField(max_length=32, default="MANUAL_REVIEW")
    status = models.CharField(max_length=20, default="OPEN")
    assigned_to = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)

class AIRun(models.Model):
    class Status(models.TextChoices):
        RUNNING = "RUNNING", "Running"; COMPLETED = "COMPLETED", "Completed"; FAILED = "FAILED", "Failed"
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name="ai_runs")
    run_type = models.CharField(max_length=40)
    provider = models.CharField(max_length=40)
    model = models.CharField(max_length=120, blank=True)
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.RUNNING)
    input_tokens = models.PositiveIntegerField(null=True, blank=True)
    output_tokens = models.PositiveIntegerField(null=True, blank=True)
    latency_ms = models.PositiveIntegerField(null=True, blank=True)
    request_metadata = models.JSONField(default=dict, blank=True)
    result_metadata = models.JSONField(default=dict, blank=True)
    error_type = models.CharField(max_length=80, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
