import hashlib
import logging
from django.http import HttpResponse
from django.db.models import Count
from openpyxl import Workbook
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.exceptions import ValidationError
from core.models import AuditLog
from core.tenant import active_organization, require_role
from .models import Questionnaire, Question, AnswerDraft
from .serializers import QuestionnaireSerializer, QuestionSerializer, AnswerSerializer
from .services import draft_answer, approve_answer
from ai.providers import ProviderError

class QuestionnaireList(generics.ListAPIView):
    serializer_class = QuestionnaireSerializer
    permission_classes = [IsAuthenticated]
    def get_queryset(self): return Questionnaire.objects.filter(organization=active_organization(self.request)).annotate(question_count=Count("questions"))

class QuestionList(generics.ListAPIView):
    serializer_class = QuestionSerializer
    permission_classes = [IsAuthenticated]
    def get_queryset(self):
        org = active_organization(self.request)
        queryset = Question.objects.filter(questionnaire__organization=org).select_related("questionnaire").prefetch_related("answers__citations__evidence__document")
        questionnaire_id = self.request.query_params.get("questionnaire")
        return queryset.filter(questionnaire_id=questionnaire_id) if questionnaire_id else queryset

class DraftAnswer(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request, question_id):
        org = require_role(request, {"OWNER", "ADMIN", "EDITOR", "REVIEWER"})
        question = Question.objects.filter(id=question_id, questionnaire__organization=org).first()
        if question is None: return Response(status=404)
        try: answer = draft_answer(question)
        except ProviderError as exc: return Response({"detail": str(exc)}, status=503)
        AuditLog.objects.create(organization=org, actor=request.user, action="ANSWER_DRAFTED", resource_type="Question", resource_id=question.id, metadata={"provider": answer.generation_mode, "answer_id": str(answer.id)})
        return Response(AnswerSerializer(answer).data, status=201)

class ApproveAnswer(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request, answer_id):
        org = require_role(request, {"OWNER", "ADMIN", "REVIEWER"})
        answer = AnswerDraft.objects.filter(id=answer_id, question__questionnaire__organization=org).first()
        if answer is None: return Response(status=404)
        try: answer = approve_answer(answer, request.user, request.data.get("comment", ""))
        except ValueError as exc: raise ValidationError({"detail": str(exc)})
        return Response(AnswerSerializer(answer).data)

class QuestionnaireImport(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]
    def post(self, request):
        org = require_role(request, {"OWNER", "ADMIN", "EDITOR"})
        uploaded = request.FILES.get("file")
        if not uploaded: raise ValidationError({"file": "A questionnaire file is required."})
        if uploaded.size > 25 * 1024 * 1024: raise ValidationError({"file": "Files must be 25 MB or smaller."})
        suffix = uploaded.name.lower().rsplit(".", 1)[-1]
        if suffix not in {"pdf", "docx", "xlsx", "csv", "txt", "md"}:
            raise ValidationError({"file": "Supported formats: PDF, DOCX, XLSX, CSV, TXT and Markdown."})
        digest = hashlib.sha256()
        for chunk in uploaded.chunks(): digest.update(chunk)
        file_hash = digest.hexdigest(); uploaded.seek(0)
        existing = Questionnaire.objects.filter(organization=org, file_hash=file_hash).annotate(question_count=Count("questions")).first()
        if existing: return Response(QuestionnaireSerializer(existing).data)
        questionnaire = Questionnaire.objects.create(organization=org, name=request.data.get("name") or uploaded.name, buyer_name=request.data.get("buyer_name", ""), owner=request.user, source_file=uploaded, original_filename=uploaded.name, file_hash=file_hash, status="PROCESSING", processing_status="QUEUED")
        from .tasks import process_questionnaire
        try: process_questionnaire.delay(str(questionnaire.id))
        except Exception as exc:
            questionnaire.status="FAILED"; questionnaire.processing_status="FAILED"; questionnaire.processing_error="Background processing is unavailable. Retry when the worker is online."; questionnaire.save(update_fields=["status", "processing_status", "processing_error", "updated_at"])
            logging.getLogger(__name__).warning("Questionnaire task enqueue failed: questionnaire_id=%s error_type=%s", questionnaire.id, type(exc).__name__)
        return Response(QuestionnaireSerializer(questionnaire).data, status=201)

class QuestionnaireExport(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request, questionnaire_id):
        org = active_organization(request)
        questionnaire = Questionnaire.objects.filter(organization=org, id=questionnaire_id).first()
        if questionnaire is None: return Response(status=404)
        workbook = Workbook(); sheet = workbook.active; sheet.title = "Responses"
        sheet.append(["Question #", "Question", "Answer", "Status", "Confidence", "Evidence sources"])
        questions = questionnaire.questions.prefetch_related("answers__citations__evidence").all()
        def safe_cell(value):
            text = str(value or "")
            return "'" + text if text[:1] in {"=", "+", "-", "@"} else text
        for question in questions:
            answer = question.answers.order_by("-version").first()
            citations = list(answer.citations.all()) if answer else []
            sources = "; ".join(f"{citation.evidence.document.title} ({citation.source_locator})" for citation in citations)
            sheet.append([safe_cell(question.question_number), safe_cell(question.question_text), safe_cell(answer.answer_text if answer else ""), safe_cell(answer.status if answer else question.status), float(answer.confidence) if answer else 0, safe_cell(sources)])
        for column, width in {"A":14,"B":70,"C":80,"D":18,"E":14,"F":80}.items(): sheet.column_dimensions[column].width = width
        response = HttpResponse(content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        response["Content-Disposition"] = f'attachment; filename="questionnaire-{questionnaire.id}.xlsx"'
        workbook.save(response)
        from core.models import AuditLog
        AuditLog.objects.create(organization=org, actor=request.user, action="QUESTIONNAIRE_EXPORTED", resource_type="Questionnaire", resource_id=questionnaire.id)
        return response
