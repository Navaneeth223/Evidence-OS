from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient
from .models import Organization, Membership
from evidence.models import SourceDocument, DocumentVersion, EvidenceAtom
from questionnaires.models import Questionnaire, Question, AnswerDraft
from questionnaires.services import approve_answer
from questionnaires.tasks import parse_questionnaire
from django.core.files.uploadedfile import SimpleUploadedFile
from ai.providers import MockProvider

class TenantIsolationTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user(username="a@example.com", password="a-long-password-value")
        self.org_a = Organization.objects.create(name="A", slug="org-a")
        self.org_b = Organization.objects.create(name="B", slug="org-b")
        Membership.objects.create(user=self.user, organization=self.org_a, role="OWNER")
        other = User.objects.create_user(username="b@example.com", password="another-long-password")
        Membership.objects.create(user=other, organization=self.org_b, role="OWNER")
        doc = SourceDocument.objects.create(organization=self.org_b, title="Private source")
        version = DocumentVersion.objects.create(document=doc, version_number=1, file="private.txt", original_filename="private.txt", mime_type="text/plain", file_size=1, sha256_hash="b" * 64)
        self.atom = EvidenceAtom.objects.create(organization=self.org_b, document=doc, version=version, content="Private fact")
        q = Questionnaire.objects.create(organization=self.org_b, name="Private questionnaire")
        self.question = Question.objects.create(questionnaire=q, question_text="Private question")
        self.answer = AnswerDraft.objects.create(question=self.question, answer_text="Private answer")
        self.client = APIClient()
        self.client.force_authenticate(self.user)

    def test_other_organization_resources_are_not_returned(self):
        for endpoint in ("/api/evidence/documents/", "/api/evidence/", "/api/questionnaires/", "/api/questionnaires/questions/"):
            response = self.client.get(endpoint, HTTP_X_ORGANIZATION_ID=str(self.org_a.id))
            self.assertEqual(response.status_code, 200)
            self.assertNotContains(response, "Private", status_code=200)

    def test_cannot_verify_other_organization_evidence(self):
        response = self.client.post(f"/api/evidence/{self.atom.id}/verify/", {}, format="json", HTTP_X_ORGANIZATION_ID=str(self.org_a.id))
        self.assertEqual(response.status_code, 404)
        self.atom.refresh_from_db()
        self.assertEqual(self.atom.verification_status, "UNVERIFIED")

    def test_cannot_draft_for_other_organization_question(self):
        response = self.client.post(f"/api/questionnaires/questions/{self.question.id}/draft/", {}, format="json", HTTP_X_ORGANIZATION_ID=str(self.org_a.id))
        self.assertEqual(response.status_code, 404)

    def test_cannot_export_other_organization_questionnaire(self):
        response = self.client.get(f"/api/questionnaires/{self.question.questionnaire_id}/export/xlsx/", HTTP_X_ORGANIZATION_ID=str(self.org_a.id))
        self.assertEqual(response.status_code, 404)

class ApprovalTests(TestCase):
    def test_blocked_or_uncited_answer_cannot_be_approved(self):
        user = get_user_model().objects.create_user(username="reviewer@example.com", password="very-long-password-value")
        org = Organization.objects.create(name="Tenant", slug="tenant")
        q = Questionnaire.objects.create(organization=org, name="RFP")
        question = Question.objects.create(questionnaire=q, question_text="Are you certified?")
        answer = AnswerDraft.objects.create(question=question, answer_text="No evidence", status="BLOCKED")
        with self.assertRaises(ValueError): approve_answer(answer, user)

class QuestionnaireParserTests(TestCase):
    def test_csv_question_import_detects_question_column(self):
        org = Organization.objects.create(name="Parser", slug="parser")
        question_file = SimpleUploadedFile("buyer.csv", b"ID,Question,Answer\nQ1,Do you support SSO?,\nQ2,Describe your backup process,\n")
        questionnaire = Questionnaire.objects.create(organization=org, name="Buyer", original_filename="buyer.csv", source_file=question_file)
        result = parse_questionnaire(questionnaire)
        self.assertEqual([item[0] for item in result], ["Q1", "Q2"])
        self.assertEqual(len(result), 2)

class MockProviderTests(TestCase):
    def test_provider_abstains_when_no_evidence_is_available(self):
        result = MockProvider().draft("Do you support SSO?", [])
        self.assertTrue(result.abstain)
        self.assertEqual(result.evidence_ids, [])

    def test_provider_only_cites_the_selected_source(self):
        evidence = [{"id": "source-1", "content": "The product supports SAML single sign on."}]
        result = MockProvider().draft("Do you support SAML single sign on?", evidence)
        self.assertFalse(result.abstain)
        self.assertEqual(result.evidence_ids, ["source-1"])
