import uuid
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion

class Migration(migrations.Migration):
    initial = True
    dependencies = [migrations.swappable_dependency(settings.AUTH_USER_MODEL)]
    operations = [
        migrations.CreateModel(name="Organization", fields=[("id", models.UUIDField(primary_key=True, serialize=False, default=uuid.uuid4, editable=False)), ("created_at", models.DateTimeField(auto_now_add=True)), ("updated_at", models.DateTimeField(auto_now=True)), ("name", models.CharField(max_length=180)), ("slug", models.SlugField(max_length=180, unique=True)), ("settings", models.JSONField(blank=True, default=dict))]),
        migrations.CreateModel(name="Membership", fields=[("id", models.UUIDField(primary_key=True, serialize=False, default=uuid.uuid4, editable=False)), ("created_at", models.DateTimeField(auto_now_add=True)), ("updated_at", models.DateTimeField(auto_now=True)), ("role", models.CharField(choices=[("OWNER", "Owner"), ("ADMIN", "Admin"), ("EDITOR", "Editor"), ("REVIEWER", "Reviewer"), ("VIEWER", "Viewer")], default="EDITOR", max_length=12)), ("organization", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="memberships", to="core.organization")), ("user", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="memberships", to=settings.AUTH_USER_MODEL))]),
        migrations.AddConstraint(model_name="membership", constraint=models.UniqueConstraint(fields=("organization", "user"), name="unique_org_membership")),
        migrations.CreateModel(name="ReviewTask", fields=[("id", models.UUIDField(primary_key=True, serialize=False, default=uuid.uuid4, editable=False)), ("created_at", models.DateTimeField(auto_now_add=True)), ("updated_at", models.DateTimeField(auto_now=True)), ("title", models.CharField(max_length=240)), ("reason", models.CharField(default="MANUAL_REVIEW", max_length=32)), ("status", models.CharField(default="OPEN", max_length=20)), ("assigned_to", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)), ("organization", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to="core.organization"))]),
        migrations.CreateModel(name="AuditLog", fields=[("id", models.UUIDField(primary_key=True, serialize=False, default=uuid.uuid4, editable=False)), ("action", models.CharField(max_length=80)), ("resource_type", models.CharField(max_length=80)), ("resource_id", models.UUIDField(null=True)), ("metadata", models.JSONField(blank=True, default=dict)), ("created_at", models.DateTimeField(auto_now_add=True)), ("actor", models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)), ("organization", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to="core.organization"))]),
    ]
