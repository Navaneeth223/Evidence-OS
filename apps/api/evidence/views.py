import hashlib
from django.utils import timezone
from rest_framework import generics, status
from rest_framework.exceptions import ValidationError
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from core.models import AuditLog
from core.tenant import active_organization
from .models import EvidenceAtom, SourceDocument, DocumentVersion
from .serializers import EvidenceSerializer, DocumentSerializer

MAX_UPLOAD = 25 * 1024 * 1024
ALLOWED = {"application/pdf", "application/vnd.openxmlformats-officedocument.wordprocessingml.document", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", "text/plain", "text/csv", "text/markdown"}

class EvidenceList(generics.ListAPIView):
    serializer_class = EvidenceSerializer
    permission_classes = [IsAuthenticated]
    def get_queryset(self): return EvidenceAtom.objects.filter(organization=active_organization(self.request)).select_related("document")

class EvidenceVerify(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request, pk):
        org = active_organization(request)
        atom = EvidenceAtom.objects.filter(organization=org, id=pk).first()
        if atom is None: return Response(status=404)
        atom.verification_status = EvidenceAtom.Verification.VERIFIED
        atom.verified_by = request.user; atom.verified_at = timezone.now(); atom.save(update_fields=["verification_status", "verified_by", "verified_at", "updated_at"])
        AuditLog.objects.create(organization=org, actor=request.user, action="EVIDENCE_VERIFIED", resource_type="EvidenceAtom", resource_id=atom.id)
        return Response(EvidenceSerializer(atom).data)

class DocumentListCreate(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]
    def get(self, request):
        org = active_organization(request)
        return Response(DocumentSerializer(SourceDocument.objects.filter(organization=org), many=True).data)
    def post(self, request):
        org = active_organization(request)
        uploaded = request.FILES.get("file")
        title = request.data.get("title") or (uploaded.name if uploaded else "")
        if not uploaded: raise ValidationError({"file": "A file is required."})
        if uploaded.size > MAX_UPLOAD: raise ValidationError({"file": "Files must be 25 MB or smaller."})
        if uploaded.content_type not in ALLOWED: raise ValidationError({"file": "Supported formats: PDF, DOCX, XLSX, CSV, TXT and Markdown."})
        digest = hashlib.sha256()
        for part in uploaded.chunks(): digest.update(part)
        sha = digest.hexdigest(); uploaded.seek(0)
        existing = DocumentVersion.objects.filter(document__organization=org, sha256_hash=sha).select_related("document").first()
        if existing: return Response(DocumentSerializer(existing.document).data, status=200)
        doc = SourceDocument.objects.create(organization=org, title=title, owner=request.user)
        version = DocumentVersion.objects.create(document=doc, version_number=1, file=uploaded, original_filename=uploaded.name, mime_type=uploaded.content_type, file_size=uploaded.size, sha256_hash=sha)
        from .tasks import process_document
        process_document.delay(str(version.id))
        AuditLog.objects.create(organization=org, actor=request.user, action="DOCUMENT_UPLOADED", resource_type="SourceDocument", resource_id=doc.id, metadata={"version_id": str(version.id), "filename": uploaded.name})
        return Response(DocumentSerializer(doc).data, status=status.HTTP_201_CREATED)
