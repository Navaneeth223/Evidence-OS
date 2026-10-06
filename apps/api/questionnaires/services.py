import time
from django.conf import settings
from django.db.models import Max
from django.utils import timezone
from core.models import AIRun, AuditLog, ReviewTask
from evidence.models import EvidenceAtom
from evidence.services.search import SearchService
from .models import AnswerDraft, AnswerCitation, Question, ApprovalEvent
from ai.providers import DraftResult, ProviderError, get_provider

def draft_answer(question):
    """Retrieve same-tenant verified evidence, generate a cited draft, and persist a safe run record."""
    org = question.questionnaire.organization
    matched = SearchService.hybrid_search(org, question.question_text, limit=8)
    allowed = {str(atom.id): atom for _, atom in matched}
    matched_score = matched[0][0] if matched else 0
    prompt_version = "grounded-json-v1"
    run = AIRun.objects.create(organization=org, run_type="ANSWER_GENERATION", provider=settings.AI_PROVIDER.lower(), model=settings.AI_MODEL, request_metadata={"question_id": str(question.id), "evidence_ids": list(allowed), "prompt_version": prompt_version})
    started = time.monotonic()
    try:
        if not matched:
            result = DraftResult("I don't have enough verified evidence to answer this question.", [], True, "abstention", "no-evidence")
        else:
            evidence = [{"id": evidence_id, "title": atom.title, "content": atom.content[:6000]} for evidence_id, atom in allowed.items()]
            result = get_provider().draft(question.question_text, evidence)
        referenced = set(result.evidence_ids)
        if not referenced.issubset(allowed):
            raise ProviderError("The AI provider returned an unknown evidence citation. Retry the draft.")
        citations = [allowed[evidence_id] for evidence_id in result.evidence_ids]
        abstain = result.abstain or not result.answer.strip() or not citations
        answer_text = "I don't have enough verified evidence to answer this question." if abstain else result.answer.strip()
        commitment_pattern = re.compile(r"\b(?:we\s+will|will\s+provide|guarantee[sd]?|promise[sd]?|commit(?:s|ted)?\s+to|ensure[sd]?)\b", re.I)
        commitment_risk = 0.8 if not abstain and commitment_pattern.search(answer_text) else 0
        version = (question.answers.aggregate(last=Max("version"))["last"] or 0) + 1
        status = "BLOCKED" if abstain or commitment_risk else "NEEDS_REVIEW"
        answer = AnswerDraft.objects.create(question=question, version=version, generation_mode="MOCK" if result.provider == "mock" else "AI", answer_text=answer_text, confidence=min(matched_score, 0.75) if not abstain else 0, grounding_score=min(matched_score, 1) if citations else 0, commitment_risk_score=commitment_risk, generated_by_model=result.model, prompt_version=prompt_version, status=status)
        for atom in citations:
            AnswerCitation.objects.create(answer=answer, evidence=atom, quoted_excerpt=atom.content[:500], source_locator=atom.source_locator)
        run.provider = result.provider; run.model = result.model; run.status = AIRun.Status.COMPLETED; run.input_tokens = result.input_tokens; run.output_tokens = result.output_tokens; run.latency_ms = int((time.monotonic() - started) * 1000); run.completed_at = timezone.now(); run.result_metadata = {"answer_id": str(answer.id), "citation_ids": [str(atom.id) for atom in citations], "abstained": abstain, "commitment_risk": bool(commitment_risk)}; run.save()
    except Exception as exc:
        run.status = AIRun.Status.FAILED; run.latency_ms = int((time.monotonic() - started) * 1000); run.completed_at = timezone.now(); run.error_type = type(exc).__name__; run.save()
        raise
    question.status = "BLOCKED" if answer.status == "BLOCKED" else "REVIEW"; question.save(update_fields=["status", "updated_at"])
    reason = "NO_EVIDENCE" if abstain else "COMMITMENT_RISK" if commitment_risk else "MANUAL_REVIEW"
    ReviewTask.objects.create(organization=org, title=f"Review answer: {question.question_text[:140]}", reason=reason)
    return answer

def approve_answer(answer, actor, comment=""):
    if answer.status == "BLOCKED" or answer.commitment_risk_score >= 0.5 or not answer.citations.exists():
        raise ValueError("An answer needs supporting evidence citations before approval.")
    previous = answer.status; answer.status = "APPROVED"; answer.save(update_fields=["status", "updated_at"])
    ApprovalEvent.objects.create(organization=answer.question.questionnaire.organization, answer=answer, actor=actor, action="APPROVED", previous_status=previous, new_status=answer.status, comment=comment)
    org = answer.question.questionnaire.organization
    AuditLog.objects.create(organization=org, actor=actor, action="ANSWER_APPROVED", resource_type="AnswerDraft", resource_id=answer.id)
    return answer
