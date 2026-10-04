import uuid
from django.conf import settings
from django.db import models
from core.models import Timestamped

class Questionnaire(Timestamped):
    organization = models.ForeignKey("core.Organization", on_delete=models.CASCADE, related_name="questionnaires")
    name = models.CharField(max_length=240)
    buyer_name = models.CharField(max_length=180, blank=True)
    status = models.CharField(max_length=20, default="READY")
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL)

class Question(Timestamped):
    questionnaire = models.ForeignKey(Questionnaire, on_delete=models.CASCADE, related_name="questions")
    question_number = models.CharField(max_length=40, blank=True)
    question_text = models.TextField()
    required = models.BooleanField(default=True)
    sort_order = models.PositiveIntegerField(default=0)
    status = models.CharField(max_length=20, default="UNANSWERED")
    class Meta:
        ordering = ["sort_order", "id"]

class AnswerDraft(Timestamped):
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name="answers")
    version = models.PositiveIntegerField(default=1)
    answer_text = models.TextField(blank=True)
    generation_mode = models.CharField(max_length=16, default="AI")
    status = models.CharField(max_length=20, default="NEEDS_REVIEW")
    confidence = models.DecimalField(max_digits=5, decimal_places=4, default=0)
    grounding_score = models.DecimalField(max_digits=5, decimal_places=4, default=0)
    commitment_risk_score = models.DecimalField(max_digits=5, decimal_places=4, default=0)

class AnswerCitation(models.Model):
    answer = models.ForeignKey(AnswerDraft, on_delete=models.CASCADE, related_name="citations")
    evidence = models.ForeignKey("evidence.EvidenceAtom", on_delete=models.PROTECT)
    quoted_excerpt = models.TextField(blank=True)
    source_locator = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)

class ApprovalEvent(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey("core.Organization", on_delete=models.CASCADE)
    answer = models.ForeignKey(AnswerDraft, on_delete=models.PROTECT, related_name="approval_events")
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    action = models.CharField(max_length=24)
    previous_status = models.CharField(max_length=20)
    new_status = models.CharField(max_length=20)
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
