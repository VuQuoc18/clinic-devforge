"""Test mẫu theo quy ước truy vết mã BR/FR/REQ (REQ-009).

Quy ước: docs/test-traceability.md.
"""
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DOC = (ROOT / "docs" / "test-traceability.md").read_text(encoding="utf-8")

CODE_RE = re.compile(r"^(BR|FR)-[A-Z]+-[0-9]{2}$|^REQ-[0-9]{3}$")


class TraceabilityConventionTest(unittest.TestCase):
    def test_br_td_01_doc_has_br_example_in_original_form(self):
        """[BR-TD-01] tài liệu quy ước có ví dụ BR giữ nguyên dạng mã"""
        self.assertIn("[BR-TD-01]", DOC)
        self.assertRegex("BR-TD-01", CODE_RE)

    def test_fr_td_01_doc_has_fr_example_in_original_form(self):
        """[FR-TD-01] tài liệu quy ước có ví dụ FR giữ nguyên dạng mã"""
        self.assertIn("[FR-TD-01]", DOC)
        self.assertRegex("FR-TD-01", CODE_RE)

    def test_req_009_doc_has_req_example_and_grep_command(self):
        """[REQ-009] tài liệu có ví dụ REQ và lệnh tìm chuỗi theo mã"""
        self.assertIn("[REQ-009]", DOC)
        self.assertRegex("REQ-009", CODE_RE)
        self.assertIn('grep -rn --include="*.py" "BR-TD-01" tests', DOC)

    def test_codes_with_underscores_are_not_valid_codes(self):
        """[REQ-009] mã sai dạng (gạch dưới, chữ thường) bị từ chối"""
        for bad in ("br_td_01", "BR_TD_01", "br-td-01", "REQ_009"):
            self.assertNotRegex(bad, CODE_RE)


if __name__ == "__main__":
    unittest.main()
