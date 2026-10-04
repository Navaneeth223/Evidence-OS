from django.db.models import Count
from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.exceptions import ValidationError
from core.models import AuditLog
from core.tenant import active_organization
from .models import Questionnaire, Question, AnswerDraft
from .serializers import QuestionnaireSerializer, QuestionSerializer, AnswerSerializer
from .services import draft_answer, approve_answer

class QuestionnaireList(generics.ListAPIView):
    serializer_class = QuestionnaireSerializer
    permission_classes = [IsAuthenticated]
    def get_queryset(self): return Questionnaire.objects.filter(organization=active_organization(self.request)).annotate(question_count=Count("questions"))

class QuestionList(generics.ListAPIView):
    serializer_class = QuestionSerializer
    permission_classes = [IsAuthenticated]
    def get_queryset(self):
        org = active_organization(self.request)
        return Question.objects.filter(questionnaire__organization=org).select_related("questionnaire").prefetch_related("answers__citations")

class DraftAnswer(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request, question_id):
        org = active_organization(request)
        question = Question.objects.filter(id=question_id, questionnaire__organization=org).first()
        if question is None: return Response(status=404)
        answer = draft_answer(question)
        AuditLog.objects.create(organization=org, actor=request.user, action="ANSWER_DRAFTED", resource_type="Question", resource_id=question.id, metadata={"provider": "mock"})
        return Response(AnswerSerializer(answer).data, status=201)

class ApproveAnswer(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request, answer_id):
        org = active_organization(request)
        answer = AnswerDraft.objects.filter(id=answer_id, question__questionnaire__organization=org).first()
        if answer is None: return Response(status=404)
        try: answer = approve_answer(answer, request.user, request.data.get("comment", ""))
        except ValueError as exc: raise ValidationError({"detail": str(exc)})
        return Response(AnswerSerializer(answer).data)
