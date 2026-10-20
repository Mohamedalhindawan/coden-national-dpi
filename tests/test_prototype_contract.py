"""Contract checks for the static Tamam prototype; no real data or services."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "app" / "index.html"
OPENAPI = ROOT / "api" / "openapi.yaml"


class TamamPrototypeContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.html = APP.read_text(encoding="utf-8")

    def test_document_is_arabic_rtl_and_responsive(self):
        self.assertIn('<html lang="ar" dir="rtl">', self.html)
        self.assertIn('name="viewport"', self.html)
        self.assertIn("@media", self.html)

    def test_request_form_has_minimum_fields(self):
        for field in ('name="fullName"', 'name="district"', 'name="householdSize"', 'name="needType"'):
            with self.subTest(field=field):
                self.assertIn(field, self.html)

    def test_demo_is_explicitly_synthetic_and_not_production(self):
        self.assertIn("بيانات تجريبية", self.html)
        self.assertIn("لا تُرسل البيانات إلى أي خادم", self.html)

    def test_submission_requires_review_and_has_no_auto_eligibility_decision(self):
        self.assertIn("بانتظار المراجعة", self.html)
        self.assertIn("humanReview", self.html)
        self.assertNotIn("eligible = true", self.html.lower())
        self.assertIn("ليس قراراً رسمياً", self.html)

    def test_demo_review_action_is_present_and_explained(self):
        self.assertIn("markReviewed", self.html)
        self.assertIn("تمت مراجعة تجريبية", self.html)
        self.assertIn("مراجعة تجريبية فقط", self.html)
        self.assertIn("ليس قراراً رسمياً", self.html)

    def test_user_input_is_rendered_without_html_injection(self):
        self.assertIn("heading.textContent = request.reference +", self.html)
        self.assertIn("detail.textContent =", self.html)
        self.assertNotIn("innerHTML", self.html)

    def test_submission_and_review_have_accessible_feedback(self):
        self.assertIn('id="feedback" aria-live="polite"', self.html)
        self.assertIn("تمت إضافة الطلب التجريبي", self.html)
        self.assertIn("تم تسجيل المراجعة التجريبية", self.html)

    def test_demo_requests_persist_only_in_current_browser_session(self):
        self.assertIn('const STORAGE_KEY = "tamam.demoRequests"', self.html)
        self.assertIn("sessionStorage.getItem(STORAGE_KEY)", self.html)
        self.assertIn("sessionStorage.setItem(STORAGE_KEY", self.html)
        self.assertNotIn("localStorage", self.html)

    def test_clearing_demo_requests_requires_explicit_confirmation(self):
        self.assertIn('id="clearRequests"', self.html)
        self.assertIn("window.confirm(", self.html)
        self.assertIn("requests.length = 0", self.html)
        self.assertIn("تم مسح جميع الطلبات التجريبية", self.html)
        self.assertIn("تم إلغاء مسح الطلبات التجريبية", self.html)

    def test_session_storage_failure_does_not_break_demo(self):
        self.assertIn("تعذر حفظ الجلسة", self.html)

    def test_has_basic_client_side_validation(self):
        self.assertIn("required", self.html)
        self.assertIn("min=", self.html)

    def test_openapi_contract_is_synthetic_only_and_not_claimed_as_deployed(self):
        spec = OPENAPI.read_text(encoding="utf-8")
        self.assertIn("openapi: 3.1.0", spec)
        self.assertIn("title: CODEN Assistance Applications API (Prototype Contract)", spec)
        self.assertIn("demoRecord:", spec)
        self.assertIn("const: true", spec)
        self.assertIn("PENDING_REVIEW", spec)
        self.assertIn("humanReview", spec)
        self.assertIn("This specification is not a deployed API", spec)
        self.assertIn("bearerAuth", spec)

    def test_api_contract_has_consistent_error_schema_and_review_route(self):
        spec = OPENAPI.read_text(encoding="utf-8")
        self.assertIn("/applications/{applicationId}/reviews:", spec)
        self.assertIn("operationId: recordReview", spec)
        self.assertIn("ValidationError:", spec)
        self.assertIn("Unauthorized:", spec)
        self.assertIn("Forbidden:", spec)
        self.assertIn("ApiError:", spec)


if __name__ == "__main__":
    unittest.main()
