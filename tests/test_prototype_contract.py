"""Contract checks for the static Tamam prototype; no real data or services."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "app" / "index.html"


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

    def test_has_basic_client_side_validation(self):
        self.assertIn("required", self.html)
        self.assertIn("min=", self.html)


if __name__ == "__main__":
    unittest.main()
