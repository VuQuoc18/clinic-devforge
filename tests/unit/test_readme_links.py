"""Unit: README và docs/README.md có liên kết hợp lệ tới tài liệu (REQ-001)."""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
README = ROOT / "README.md"
DOCS_INDEX = ROOT / "docs" / "README.md"


def relative_links(path):
    text = path.read_text(encoding="utf-8")
    links = re.findall(r"\]\(([^)#\s]+)(?:#[^)]*)?\)", text)
    return [l for l in links if not re.match(r"^[a-z]+://", l)]


def test_docs_dir_and_index_exist():
    assert DOCS_INDEX.is_file()


def test_readme_links_to_docs_index_and_conventions():
    links = relative_links(README)
    assert "docs/README.md" in links
    assert "docs/conventions.md" in links
    assert "docs/api-conventions.md" in links
    assert "docs/db-migrations.md" in links


def test_all_relative_links_resolve():
    for doc in (README, DOCS_INDEX):
        for link in relative_links(doc):
            assert (doc.parent / link).exists(), "%s: liên kết hỏng %s" % (doc.name, link)


def test_every_doc_is_listed_in_docs_index():
    index = DOCS_INDEX.read_text(encoding="utf-8")
    for f in (ROOT / "docs").glob("*.md"):
        if f.name != "README.md":
            assert f.name in index, "docs/README.md thiếu %s" % f.name


def test_readme_has_backend_frontend_section():
    text = README.read_text(encoding="utf-8")
    assert re.search(r"^## Backend và frontend", text, re.M)


def test_readme_has_run_commands_when_backend_or_frontend_exist():
    text = README.read_text(encoding="utf-8").lower()
    for name in ("backend", "frontend"):
        if (ROOT / name).is_dir():
            assert "cd %s" % name in text, "README thiếu lệnh chạy cho %s/" % name


def github_slug(heading):
    slug = heading.strip().lower()
    slug = re.sub(r"[^\w\- ]", "", slug)
    return slug.replace(" ", "-")


def anchors(path):
    text = path.read_text(encoding="utf-8")
    text = re.sub(r"```.*?```", "", text, flags=re.S)
    return {github_slug(h) for h in re.findall(r"^#{1,6}\s+(.+)$", text, re.M)}


def test_anchor_links_resolve():
    for doc in (README, DOCS_INDEX):
        text = doc.read_text(encoding="utf-8")
        for target, frag in re.findall(r"\]\(([^)#\s]*)#([^)\s]+)\)", text):
            if re.match(r"^[a-z]+://", target):
                continue
            path = doc if not target else (doc.parent / target)
            assert frag in anchors(path), "%s: anchor hỏng %s#%s" % (doc.name, target, frag)
