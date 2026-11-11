"""Acceptance contracts for synthetic RTL request filtering."""
from pathlib import Path
import unittest

HTML = (Path(__file__).resolve().parents[1] / "app" / "index.html").read_text(encoding="utf-8")

class TamamReviewFilterAcceptance(unittest.TestCase):
    def test_arabic_rtl_and_synthetic_boundary(self):
        self.assertIn('<html lang="ar" dir="rtl">', HTML)
        self.assertIn("لا تُرسل البيانات إلى أي خادم", HTML)
        self.assertIn("ليس قراراً رسمياً", HTML)

    def test_filter_supports_all_pending_and_reviewed(self):
        self.assertIn('id="statusFilter"', HTML)
        for value in ("all", "pending", "reviewed"):
            self.assertIn('value="' + value + '"', HTML)
        self.assertIn('statusFilter.addEventListener("change", renderRequests)', HTML)
        self.assertIn('Boolean(request.reviewed)', HTML)
        self.assertIn('!request.reviewed', HTML)

    def test_empty_filtered_result_and_no_html_injection(self):
        self.assertIn("لا توجد طلبات تجريبية تطابق هذه الحالة.", HTML)
        self.assertIn("empty.textContent =", HTML)
        self.assertNotIn("innerHTML", HTML)

    def test_review_remains_human_and_demo_only(self):
        self.assertIn("humanReview: true", HTML)
        self.assertIn("markReviewed(reference)", HTML)
        self.assertIn("تمت مراجعة تجريبية", HTML)

if __name__ == "__main__":
    unittest.main()
