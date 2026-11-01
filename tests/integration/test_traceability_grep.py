"""Integration: lệnh grep trong docs/test-traceability.md tìm đúng test mẫu (REQ số 009).

Các mã được ghép từ hai nửa chuỗi để file này không tự khớp với lệnh tìm,
nhờ đó kết quả grep chỉ gồm test mẫu.
"""
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SAMPLE = "tests/unit/test_traceability_convention.py"


def grep_files(code):
    out = subprocess.run(
        ["grep", "-rl", "--include=*.py", code, "tests"],
        cwd=ROOT, capture_output=True, text=True,
    )
    return sorted(out.stdout.split())


class TraceabilityGrepTest(unittest.TestCase):
    def test_grep_br_returns_only_sample(self):
        self.assertEqual(grep_files("BR-" + "TD-01"), [SAMPLE])

    def test_grep_fr_returns_only_sample(self):
        self.assertEqual(grep_files("FR-" + "TD-01"), [SAMPLE])

    def test_grep_req_returns_only_sample(self):
        self.assertEqual(grep_files("REQ-" + "009"), [SAMPLE])


if __name__ == "__main__":
    unittest.main()
