import uuid
from django.db import migrations, models
import django.db.models.deletion

class Migration(migrations.Migration):
    dependencies = [("core", "0001_initial")]
    operations = [migrations.CreateModel(name="AIRun", fields=[
        ("id", models.UUIDField(primary_key=True, serialize=False, default=uuid.uuid4, editable=False)),
        ("run_type", models.CharField(max_length=40)), ("provider", models.CharField(max_length=40)),
        ("model", models.CharField(blank=True, max_length=120)),
        ("status", models.CharField(choices=[("RUNNING", "Running"), ("COMPLETED", "Completed"), ("FAILED", "Failed")], default="RUNNING", max_length=12)),
        ("input_tokens", models.PositiveIntegerField(blank=True, null=True)), ("output_tokens", models.PositiveIntegerField(blank=True, null=True)),
        ("latency_ms", models.PositiveIntegerField(blank=True, null=True)), ("request_metadata", models.JSONField(blank=True, default=dict)),
        ("result_metadata", models.JSONField(blank=True, default=dict)), ("error_type", models.CharField(blank=True, max_length=80)),
        ("created_at", models.DateTimeField(auto_now_add=True)), ("completed_at", models.DateTimeField(blank=True, null=True)),
        ("organization", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="ai_runs", to="core.organization")),
    ])]
