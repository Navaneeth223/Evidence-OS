import uuid
from django.conf import settings
from django.db import models
from django.contrib.postgres.indexes import GinIndex
from django.contrib.postgres.search import SearchVector
from pgvector.django import HnswIndex, VectorField
from core.models import Timestamped

class SourceDocument(Timestamped):
    organization = models.ForeignKey("core.Organization", on_delete=models.CASCADE, related_name="documents")
    title = models.CharField(max_length=240)
    document_type = models.CharField(max_length=40, default="OTHER")
    trust_level = models.CharField(max_length=20, default="UNVERIFIED")
    status = models.CharField(max_length=20, default="UPLOADED")
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL)

class DocumentVersion(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    document = models.ForeignKey(SourceDocument, on_delete=models.CASCADE, related_name="versions")
    version_number = models.PositiveIntegerField()
    file = models.FileField(upload_to="source-documents/%Y/%m/")
    original_filename = models.CharField(max_length=255)
    mime_type = models.CharField(max_length=120)
    file_size = models.PositiveBigIntegerField()
    sha256_hash = models.CharField(max_length=64)
    processing_status = models.CharField(max_length=20, default="QUEUED")
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        constraints = [models.UniqueConstraint(fields=["document", "version_number"], name="unique_document_version")]

class DocumentSection(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    version = models.ForeignKey(DocumentVersion, on_delete=models.CASCADE, related_name="sections")
    section_type = models.CharField(max_length=24)
    section_path = models.TextField(blank=True)
    page_number = models.PositiveIntegerField(null=True, blank=True)
    sheet_name = models.CharField(max_length=120, blank=True)
    content = models.TextField()
    start_offset = models.PositiveIntegerField(null=True, blank=True)
    end_offset = models.PositiveIntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

class EvidenceAtom(Timestamped):
    class Verification(models.TextChoices):
        UNVERIFIED = "UNVERIFIED", "Unverified"; VERIFIED = "VERIFIED", "Verified"; STALE = "STALE", "Stale"; REVOKED = "REVOKED", "Revoked"; CONFLICTED = "CONFLICTED", "Conflicted"
    organization = models.ForeignKey("core.Organization", on_delete=models.CASCADE, related_name="evidence")
    document = models.ForeignKey(SourceDocument, on_delete=models.PROTECT, related_name="evidence")
    version = models.ForeignKey(DocumentVersion, on_delete=models.PROTECT, related_name="evidence")
    title = models.CharField(max_length=240, blank=True)
    content = models.TextField()
    evidence_type = models.CharField(max_length=40, default="OTHER")
    source_locator = models.JSONField(default=dict)
    verification_status = models.CharField(max_length=16, choices=Verification.choices, default=Verification.UNVERIFIED)
    confidence = models.DecimalField(max_digits=5, decimal_places=4, default=0)
    content_hash = models.CharField(max_length=64, blank=True)
    embedding = VectorField(dimensions=1536, null=True, blank=True)
    embedding_model = models.CharField(max_length=120, blank=True)
    embedding_hash = models.CharField(max_length=64, blank=True)
    verified_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)
    verified_at = models.DateTimeField(null=True, blank=True)
    class Meta:
        indexes = [
            HnswIndex(name="evidence_embedding_hnsw", fields=["embedding"], m=16, ef_construction=64, opclasses=["vector_cosine_ops"]),
            GinIndex(SearchVector("title", "content", config="simple"), name="evidence_content_gin"),
        ]

class EvidenceClaim(Timestamped):
    organization = models.ForeignKey("core.Organization", on_delete=models.CASCADE)
    subject = models.CharField(max_length=240)
    predicate = models.CharField(max_length=120)
    object_text = models.TextField(blank=True)
    status = models.CharField(max_length=16, default="ACTIVE")
    confidence = models.DecimalField(max_digits=5, decimal_places=4, default=0)

class ClaimEvidence(models.Model):
    claim = models.ForeignKey(EvidenceClaim, on_delete=models.CASCADE)
    evidence = models.ForeignKey(EvidenceAtom, on_delete=models.CASCADE)
    relationship_type = models.CharField(max_length=16, default="DIRECT")
    class Meta:
        constraints = [models.UniqueConstraint(fields=["claim", "evidence"], name="unique_claim_evidence")]
