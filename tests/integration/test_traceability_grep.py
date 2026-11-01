"""Integration: lệnh grep trong docs/test-traceability.md tìm ra test mẫu (REQ số 009).

Các mã được ghép từ hai nửa chuỗi để file này không tự khớp với lệnh tìm.
Dùng assertIn: test thật gắn cùng mã (quy tắc 6) được phép xuất hiện thêm.
"""
import shutil
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
    # grep: 0 = có kết quả, 1 = không có, >1 = lỗi
    if out.returncode not in (0, 1):
        raise AssertionError(f"grep lỗi (returncode={out.returncode}): {out.stderr}")
    return sorted(out.stdout.split())


@unittest.skipUnless(shutil.which("grep"), "không có lệnh grep")
class TraceabilityGrepTest(unittest.TestCase):
    def test_grep_br_finds_sample(self):
        self.assertIn(SAMPLE, grep_files("BR-" + "TD-01"))

    def test_grep_fr_finds_sample(self):
        self.assertIn(SAMPLE, grep_files("FR-" + "TD-01"))

    def test_grep_req_finds_sample(self):
        self.assertIn(SAMPLE, grep_files("REQ-" + "009"))


if __name__ == "__main__":
    unittest.main()
