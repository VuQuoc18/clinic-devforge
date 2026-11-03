"""Integration: hai script kiểm tra tài liệu vẫn chạy qua sau khi dời vào backend/tests (TASK-0042)."""
import shutil
import subprocess
import tempfile
from pathlib import Path

import pytest

TESTS_DIR = Path(__file__).resolve().parents[1]
pytestmark = pytest.mark.skipif(shutil.which("sh") is None, reason="không có sh")

SCRIPTS = ["check_conventions.sh", "check_api_conventions.sh"]


@pytest.mark.parametrize("name", SCRIPTS)
def test_script_passes_from_any_cwd(name):
    # Script tự định vị docs/ theo vị trí của chính nó, không phụ thuộc cwd.
    with tempfile.TemporaryDirectory() as d:
        r = subprocess.run(["sh", str(TESTS_DIR / name)], cwd=d, capture_output=True, text=True)
    assert r.returncode == 0, r.stdout + r.stderr
    assert r.stdout.strip().endswith("OK")
