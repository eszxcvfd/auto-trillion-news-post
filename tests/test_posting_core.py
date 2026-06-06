import unittest
from src.models import BusinessWorkbookRow
from src.posting_core import (
    canonicalize_platform,
    parse_link_post_document,
    serialize_link_post_document,
    evaluate_row_eligibility,
    build_posting_plan
)

class TestPostingCore(unittest.TestCase):

    def test_canonicalize_platform(self):
        self.assertEqual(canonicalize_platform("LinkedIn"), "linkedin")
        self.assertEqual(canonicalize_platform(" x (twitter)  "), "x")
        self.assertEqual(canonicalize_platform("Twitter"), "x")
        self.assertEqual(canonicalize_platform("facebook"), "facebook")
        
        with self.assertRaises(ValueError):
            canonicalize_platform("unsupported_platform")

    def test_parse_link_post_document_success_and_tags(self):
        raw_text = (
            "LinkedIn: https://linkedin.com/post/123\n"
            "Facebook: [posted-no-link]\n"
            "X: [pending]\n"
            "Instagram: [error] Image layout failed\n"
            "Pinterest: [skip] Not relevant\n"
            "Threads: [login-required]\n"
        )
        
        doc = parse_link_post_document(raw_text)
        self.assertEqual(len(doc.states), 6)
        
        # Test states
        self.assertEqual(doc.states["linkedin"].status_type, "success")
        self.assertEqual(doc.states["linkedin"].raw_value, "https://linkedin.com/post/123")
        
        self.assertEqual(doc.states["facebook"].status_type, "success")
        self.assertEqual(doc.states["facebook"].raw_value, "[posted-no-link]")
        
        self.assertEqual(doc.states["x"].status_type, "retryable")
        self.assertEqual(doc.states["x"].raw_value, "[pending]")
        
        self.assertEqual(doc.states["instagram"].status_type, "retryable")
        self.assertEqual(doc.states["instagram"].raw_value, "[error] Image layout failed")
        
        self.assertEqual(doc.states["pinterest"].status_type, "skip")
        self.assertEqual(doc.states["pinterest"].raw_value, "[skip] Not relevant")
        
        self.assertEqual(doc.states["threads"].status_type, "retryable")
        self.assertEqual(doc.states["threads"].raw_value, "[login-required]")

    def test_parse_link_post_document_malformed(self):
        # Missing colon
        with self.assertRaises(ValueError) as context:
            parse_link_post_document("LinkedIn no-colon")
        self.assertIn("missing ':' separator", str(context.exception))
        
        # Unrecognized platform
        with self.assertRaises(ValueError) as context2:
            parse_link_post_document("GoogleMyBusiness: https://google.com")
        self.assertIn("unrecognized platform", str(context2.exception))
        
        # Invalid status value
        with self.assertRaises(ValueError) as context3:
            parse_link_post_document("LinkedIn: custom plain text status")
        self.assertIn("invalid status value", str(context3.exception))

    def test_serialize_link_post_document(self):
        raw_text = (
            "LinkedIn: https://linkedin.com/post/123\n"
            "X: [posted-no-link]"
        )
        doc = parse_link_post_document(raw_text)
        serialized = serialize_link_post_document(doc)
        
        # Serializer sorts alphabetically by display name (LinkedIn, then X)
        expected = "LinkedIn: https://linkedin.com/post/123\nX: [posted-no-link]"
        self.assertEqual(serialized, expected)

    def test_evaluate_row_eligibility(self):
        # Row with LinkedIn and Facebook drafts, but no X draft
        row = BusinessWorkbookRow(
            sheet_name="Test",
            row_idx=2,
            id=1,
            title="Test Title",
            linkedin_draft="LinkedIn content",
            facebook_draft="Facebook content",
            link_post_raw="LinkedIn: https://linkedin.com/post/123\nFacebook: [error] Failed"
        )
        
        # 1. LinkedIn is success -> skipped_already_posted
        status_li, reason_li = evaluate_row_eligibility(row, "linkedin")
        self.assertEqual(status_li, "skipped_already_posted")
        
        # 2. Facebook is error -> eligible (retryable)
        status_fb, reason_fb = evaluate_row_eligibility(row, "facebook")
        self.assertEqual(status_fb, "eligible")
        self.assertEqual(reason_fb, None)
        
        # 3. X has no draft -> skipped_no_content
        status_x, reason_x = evaluate_row_eligibility(row, "x")
        self.assertEqual(status_x, "skipped_no_content")
        
        # 4. Instagram has no link_post entry but no draft either -> skipped_no_content
        status_ig, reason_ig = evaluate_row_eligibility(row, "instagram")
        self.assertEqual(status_ig, "skipped_no_content")

    def test_build_posting_plan_limits(self):
        # Create 4 rows, all eligible for LinkedIn
        rows = [
            BusinessWorkbookRow(sheet_name="A", row_idx=2, id=1, title="Title 1", linkedin_draft="Draft 1"),
            BusinessWorkbookRow(sheet_name="A", row_idx=3, id=2, title="Title 2", linkedin_draft="Draft 2"),
            BusinessWorkbookRow(sheet_name="B", row_idx=2, id=1, title="Title 3", linkedin_draft="Draft 3"),
            BusinessWorkbookRow(sheet_name="B", row_idx=3, id=2, title="Title 4", linkedin_draft="Draft 4")
        ]
        
        plan = build_posting_plan(rows, platforms=["linkedin"], limit_per_platform=2)
        
        # We expect only the first 2 candidates for LinkedIn
        candidates = plan.candidates["linkedin"]
        self.assertEqual(len(candidates), 2)
        self.assertEqual(candidates[0].title, "Title 1")
        self.assertEqual(candidates[0].sheet_name, "A")
        self.assertEqual(candidates[1].title, "Title 2")
        self.assertEqual(candidates[1].sheet_name, "A")
        
        # The other 2 should be logged in skipped_summary as limit reached
        self.assertEqual(len(plan.skipped_summary), 2)
        self.assertTrue(any("skipped for platform 'LinkedIn' because maximum limit of 2 was reached" in s for s in plan.skipped_summary))

    def test_build_posting_plan_mixed_eligibility(self):
        rows = [
            BusinessWorkbookRow(
                sheet_name="Payment", row_idx=2, id=1, title="Title 1", 
                linkedin_draft="Draft 1", 
                link_post_raw="LinkedIn: https://linkedin.com/1"
            ), # LI: skipped (already posted)
            BusinessWorkbookRow(
                sheet_name="Payment", row_idx=3, id=2, title="Title 2", 
                linkedin_draft="Draft 2", 
                link_post_raw="LinkedIn: [skip] Operator skip"
            ), # LI: skipped (explicit skip)
            BusinessWorkbookRow(
                sheet_name="Payment", row_idx=4, id=3, title="Title 3", 
                linkedin_draft="Draft 3"
            )  # LI: eligible
        ]
        
        plan = build_posting_plan(rows, platforms=["linkedin"], limit_per_platform=2)
        
        candidates = plan.candidates["linkedin"]
        self.assertEqual(len(candidates), 1)
        self.assertEqual(candidates[0].title, "Title 3")
        
        self.assertTrue(any("skipped for platform 'LinkedIn': Already posted" in s for s in plan.skipped_summary))
        self.assertTrue(any("skipped for platform 'LinkedIn': Explicitly skipped" in s for s in plan.skipped_summary))

if __name__ == "__main__":
    unittest.main()
