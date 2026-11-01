"""Test mẫu theo quy ước truy vết mã BR/FR/REQ (REQ-009).

Quy ước: docs/test-traceability.md.
"""
import ast
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DOC = (ROOT / "docs" / "test-traceability.md").read_text(encoding="utf-8")

CODE_RE = re.compile(r"^(BR|FR)-[A-Z]+-[0-9]{2}$|^REQ-[0-9]{3}$")
TAG_RE = re.compile(r"\[([^\]]+)\]")
LEADING_TAGS_RE = re.compile(r"^(\[[^\]]+\])+")


def traced_tests():
    """Trả về (file, tên hàm, [mã]) cho mọi test có docstring bắt đầu bằng [mã]."""
    found = []
    for path in sorted((ROOT / "tests").rglob("test_*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name.startswith("test"):
                doc = (ast.get_docstring(node) or "").splitlines()
                m = LEADING_TAGS_RE.match(doc[0]) if doc else None
                if m:
                    found.append((path.name, node.name, TAG_RE.findall(m.group(0))))
    return found


class TraceabilityConventionTest(unittest.TestCase):
    def test_br_td_01_doc_has_br_example_in_original_form(self):
        """[BR-TD-01] tài liệu quy ước có ví dụ BR giữ nguyên dạng mã (mã minh họa, xem quy tắc 5)"""
        self.assertIn("[BR-TD-01]", DOC)
        self.assertIn("test_br_td_01_", DOC)

    def test_fr_td_01_doc_has_fr_example_in_original_form(self):
        """[FR-TD-01] tài liệu quy ước có ví dụ FR giữ nguyên dạng mã (mã minh họa, xem quy tắc 5)"""
        self.assertIn("[FR-TD-01]", DOC)
        self.assertIn("test_fr_td_01_", DOC)

    def test_req_009_doc_has_req_example_and_grep_command(self):
        """[REQ-009] tài liệu có ví dụ REQ và lệnh tìm chuỗi theo mã"""
        self.assertIn("[REQ-009]", DOC)
        self.assertIn("test_req_009_", DOC)
        self.assertIn('grep -rn --include="*.py" "BR-TD-01" tests', DOC)

    def test_req_009_all_tagged_tests_use_valid_codes_and_names(self):
        """[REQ-009] mọi test có gắn mã dùng đúng định dạng và tên hàm chứa mã dạng gạch dưới"""
        tagged = traced_tests()
        self.assertTrue(tagged, "không tìm thấy test nào gắn mã")
        for filename, name, codes in tagged:
            for code in codes:
                self.assertRegex(code, CODE_RE, f"{filename}::{name}")
                self.assertIn(code.lower().replace("-", "_"), name, f"{filename}::{name}")

    def test_req_009_sample_carries_br_fr_and_req_codes(self):
        """[REQ-009] test mẫu có đủ mã BR, FR và REQ"""
        codes = {c for f, _, cs in traced_tests() if f == Path(__file__).name for c in cs}
        self.assertTrue({"BR-TD-01", "FR-TD-01", "REQ-009"} <= codes)

    def test_req_009_codes_with_underscores_are_not_valid_codes(self):
        """[REQ-009] mã sai dạng (gạch dưới, chữ thường) bị từ chối"""
        for bad in ("br_td_01", "BR_TD_01", "br-td-01", "REQ_009", "BR-TD-1", "REQ-09"):
            self.assertNotRegex(bad, CODE_RE)


if __name__ == "__main__":
    unittest.main()
