"""Integration: chạy đúng lệnh trong README từ trạng thái sạch rồi kết nối DB."""
import os
import re
import shlex
import shutil
import socket
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
PORT = "55442"  # cổng riêng để không đụng môi trường dev đang chạy
PROJECT = "clinic-local-it"

pytestmark = pytest.mark.skipif(
    shutil.which("docker") is None
    or subprocess.run(["docker", "info"], capture_output=True).returncode != 0,
    reason="Docker không khả dụng",
)


def readme_cmd(prefix):
    text = (ROOT / "README.md").read_text(encoding="utf-8")
    for block in re.findall(r"```bash\n(.*?)```", text, flags=re.S):
        if block.strip().startswith(prefix):
            return shlex.split(block.strip())
    raise AssertionError(prefix)


def compose(cmd):
    env = {**os.environ, "DB_PORT": PORT, "COMPOSE_PROJECT_NAME": PROJECT}
    return subprocess.run(cmd, cwd=ROOT, env=env, capture_output=True, text=True, timeout=240)


@pytest.fixture
def clean_env():
    compose(readme_cmd("docker compose down -v"))
    yield
    compose(readme_cmd("docker compose down -v"))


def test_readme_up_command_brings_db_up_and_reachable(clean_env):
    up = compose(readme_cmd("docker compose up"))
    assert up.returncode == 0, up.stderr

    with socket.create_connection(("127.0.0.1", int(PORT)), timeout=5):
        pass

    q = compose(["docker", "compose", "exec", "-T", "db", "psql", "-U", "app", "-d", "app",
                 "-tAc", "SELECT 1"])
    assert q.returncode == 0, q.stderr
    assert q.stdout.strip() == "1"

    down = compose(readme_cmd("docker compose down -v"))
    assert down.returncode == 0, down.stderr
    ps = compose(["docker", "compose", "ps", "-q"])
    assert ps.stdout.strip() == ""
