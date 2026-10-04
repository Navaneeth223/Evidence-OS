from rest_framework import serializers
from .models import EvidenceAtom, SourceDocument

class EvidenceSerializer(serializers.ModelSerializer):
    document_title = serializers.CharField(source="document.title", read_only=True)
    class Meta:
        model = EvidenceAtom
        fields = ["id", "document", "document_title", "title", "content", "evidence_type", "source_locator", "verification_status", "confidence", "created_at"]
        read_only_fields = ["id", "document_title", "created_at"]

class DocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = SourceDocument
        fields = ["id", "title", "document_type", "trust_level", "status", "created_at"]
        read_only_fields = fields
