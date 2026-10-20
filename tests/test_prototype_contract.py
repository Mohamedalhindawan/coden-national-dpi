"""Contract checks for the static Tamam prototype; no real data or services."""
from html.parser import HTMLParser
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "app" / "index.html"
OPENAPI = ROOT / "api" / "openapi.yaml"


class ElementAttributesFinder(HTMLParser):
    """Collects the attributes of the first element with a given id."""

    def __init__(self, element_id):
        super().__init__()
        self.element_id = element_id
        self.attributes = None

    def handle_starttag(self, tag, attrs):
        if self.attributes is not None:
            return
        attributes = dict(attrs)
        if attributes.get("id") == self.element_id:
            self.attributes = attributes


def element_attributes(markup, element_id):
    """Return the attributes of an element by id, independent of attribute order."""
    finder = ElementAttributesFinder(element_id)
    finder.feed(markup)
    return finder.attributes or {}


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
        feedback = element_attributes(self.html, "feedback")
        self.assertEqual(feedback.get("aria-live"), "polite")
        self.assertEqual(feedback.get("role"), "status")
        self.assertIn("تمت إضافة الطلب التجريبي", self.html)
        self.assertIn("تم تسجيل المراجعة التجريبية", self.html)

    def test_inline_validation_errors_are_accessible(self):
        name_input = element_attributes(self.html, "fullName")
        self.assertEqual(name_input.get("maxlength"), "80")
        self.assertEqual(name_input.get("aria-describedby"), "fullNameHint fullNameError")
        self.assertIn("id=\"fullNameHint\"", self.html)

        described_by = {
            "district": "districtError",
            "householdSize": "householdSizeError",
            "needType": "needTypeError",
        }
        for field_id, error_id in described_by.items():
            with self.subTest(field_id=field_id):
                field = element_attributes(self.html, field_id)
                self.assertEqual(field.get("aria-describedby"), error_id)
                error = element_attributes(self.html, error_id)
                self.assertEqual(error.get("role"), "alert")
                self.assertIn("hidden", error)

    def test_inline_validation_feedback_is_arabic_and_demo_only(self):
        for message in (
            "لا يمكن أن يكون الحقل فارغاً",
            "اختر المديرية التجريبية من القائمة",
            "أدخل عدداً صحيحاً لأفراد الأسرة بين 1 و30",
            "اختر نوع الاحتياج من القائمة",
        ):
            with self.subTest(message=message):
                self.assertIn(message, self.html)
        self.assertIn("showFieldError", self.html)
        self.assertIn("clearFieldError", self.html)
        self.assertIn('setAttribute("aria-invalid", "true")', self.html)
        self.assertIn('removeAttribute("aria-invalid")', self.html)
        self.assertIn("firstInvalid.input.focus()", self.html)
        self.assertNotIn("innerHTML", self.html)

    def test_native_validation_is_replaced_by_arabic_messages(self):
        form = element_attributes(self.html, "requestForm")
        self.assertIn("novalidate", form)
        self.assertIn("isValid", self.html)

    def test_demo_records_are_still_not_persisted_or_transmitted(self):
        self.assertNotIn("localStorage", self.html)
        self.assertNotIn("sessionStorage", self.html)
        self.assertNotIn("fetch(", self.html)
        self.assertNotIn("XMLHttpRequest", self.html)

    def test_demo_requests_can_be_cleared_from_the_current_session(self):
        self.assertIn('id="clearRequests"', self.html)
        self.assertIn("requests.length = 0", self.html)
        self.assertIn("تم مسح جميع الطلبات التجريبية", self.html)

    def test_has_basic_client_side_validation(self):
        self.assertIn("required", self.html)
        self.assertIn("min=", self.html)
        self.assertIn("max=", self.html)
        self.assertIn("novalidate", self.html)

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
