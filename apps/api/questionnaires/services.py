from core.models import AuditLog, ReviewTask
from evidence.models import EvidenceAtom
from django.db.models import Max
from .models import AnswerDraft, AnswerCitation, Question, ApprovalEvent

def draft_answer(question):
    """Deterministic development fallback: abstains without evidence; never invents claims."""
    org = question.questionnaire.organization
    terms = {word.lower().strip(".,?!()") for word in question.question_text.split() if len(word) > 3}
    candidates = EvidenceAtom.objects.filter(organization=org, verification_status=EvidenceAtom.Verification.VERIFIED).only("id", "content", "source_locator")[:500]
    ranked = sorted(((len(terms & set(atom.content.lower().split())), atom) for atom in candidates), key=lambda item: item[0], reverse=True)
    score, atom = ranked[0] if ranked else (0, None)
    if atom and score >= 2:
        text = f"Based on verified company evidence: {atom.content}"
        version = (question.answers.aggregate(last=Max("version"))["last"] or 0) + 1
        answer = AnswerDraft.objects.create(question=question, version=version, generation_mode="MOCK", answer_text=text, confidence=min(score / max(len(terms), 1), 0.75), grounding_score=0.7)
        AnswerCitation.objects.create(answer=answer, evidence=atom, quoted_excerpt=atom.content[:500], source_locator=atom.source_locator)
        reason = "MANUAL_REVIEW"
    else:
        version = (question.answers.aggregate(last=Max("version"))["last"] or 0) + 1
        answer = AnswerDraft.objects.create(question=question, version=version, generation_mode="MOCK", answer_text="I don't have enough verified evidence to answer this question.", confidence=0, grounding_score=0, status="BLOCKED")
        reason = "NO_EVIDENCE"
    question.status = "REVIEW" if answer.status != "BLOCKED" else "BLOCKED"; question.save(update_fields=["status", "updated_at"])
    ReviewTask.objects.create(organization=org, title=f"Review answer: {question.question_text[:140]}", reason=reason)
    return answer

def approve_answer(answer, actor, comment=""):
    if answer.status == "BLOCKED" or not answer.citations.exists():
        raise ValueError("An answer needs supporting evidence citations before approval.")
    previous = answer.status; answer.status = "APPROVED"; answer.save(update_fields=["status", "updated_at"])
    ApprovalEvent.objects.create(organization=answer.question.questionnaire.organization, answer=answer, actor=actor, action="APPROVED", previous_status=previous, new_status=answer.status, comment=comment)
    org = answer.question.questionnaire.organization
    AuditLog.objects.create(organization=org, actor=actor, action="ANSWER_APPROVED", resource_type="AnswerDraft", resource_id=answer.id)
    return answer
