"""Unit: README và docker-compose.yml khớp nhau (REQ-002)."""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
README = (ROOT / "README.md").read_text(encoding="utf-8")
COMPOSE = (ROOT / "docker-compose.yml").read_text(encoding="utf-8")


def bash_commands():
    return re.findall(r"```bash\n(.*?)```", README, flags=re.S)


def test_readme_documents_single_up_command():
    assert "docker compose up -d --wait" in [c.strip() for c in bash_commands()]


def test_readme_documents_stop_and_cleanup():
    cmds = [c.strip() for c in bash_commands()]
    assert "docker compose down" in cmds
    assert "docker compose down -v" in cmds


def test_compose_has_db_with_healthcheck_and_volume():
    assert "postgres:" in COMPOSE
    assert "healthcheck:" in COMPOSE  # cần cho `--wait`
    assert "db-data:" in COMPOSE


def test_readme_database_url_matches_compose_defaults():
    assert "postgresql://app:app@127.0.0.1:5442/app" in README
    assert "${DB_PORT:-5442}" in COMPOSE
    assert "${DB_USER:-app}" in COMPOSE
    assert "${DB_PASSWORD:-app}" in COMPOSE
    assert "${DB_NAME:-app}" in COMPOSE
