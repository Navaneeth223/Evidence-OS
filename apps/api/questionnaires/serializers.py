from rest_framework import serializers
from .models import Questionnaire, Question, AnswerDraft

class QuestionnaireSerializer(serializers.ModelSerializer):
    question_count = serializers.IntegerField(read_only=True)
    class Meta:
        model = Questionnaire
        fields = ["id", "name", "buyer_name", "status", "question_count", "created_at"]
        read_only_fields = fields

class QuestionSerializer(serializers.ModelSerializer):
    latest_answer = serializers.SerializerMethodField()
    class Meta:
        model = Question
        fields = ["id", "questionnaire", "question_number", "question_text", "required", "sort_order", "status", "latest_answer"]
        read_only_fields = fields
    def get_latest_answer(self, obj):
        answer = obj.answers.order_by("-version").first()
        return AnswerSerializer(answer).data if answer else None

class AnswerSerializer(serializers.ModelSerializer):
    citations = serializers.SerializerMethodField()
    class Meta:
        model = AnswerDraft
        fields = ["id", "answer_text", "status", "confidence", "grounding_score", "commitment_risk_score", "citations", "created_at"]
    def get_citations(self, obj):
        return [{"evidence_id": str(c.evidence_id), "excerpt": c.quoted_excerpt, "source_locator": c.source_locator} for c in obj.citations.select_related("evidence")]
