#!/bin/sh
# Kiểm tra tài liệu quy ước và mẫu PR (REQ-006).
cd "$(dirname "$0")/../.." || exit 1
fail=0
err() { echo "FAIL: $1"; fail=1; }

DOC=docs/conventions.md
TPL=.github/pull_request_template.md

[ -f "$DOC" ] || err "thiếu $DOC"
[ -f "$TPL" ] || err "thiếu $TPL"
[ "$fail" -eq 0 ] || exit 1

for s in "## Mô tả" "## REQ / Task liên quan" "## Cách test"; do
  grep -qF "$s" "$TPL" || err "mẫu PR thiếu mục '$s'"
done

BRANCH_RE='^(feat|fix|docs|refactor|test|chore)/TASK-[0-9]{4}-[a-z0-9]+(-[a-z0-9]+)*$'
COMMIT_RE='^(feat|fix|docs|refactor|test|chore)\(TASK-[0-9]{4}\): .{1,72}$'

for b in docs/TASK-0035-quy-uoc-nhanh-commit-pr feat/TASK-0012-dang-nhap fix/TASK-0101-sua-loi-timeout; do
  grep -qF "$b" "$DOC" || err "tài liệu thiếu ví dụ nhánh $b"
  echo "$b" | grep -Eq "$BRANCH_RE" || err "nhánh hợp lệ bị từ chối: $b"
done
for b in my-branch feat/TASK-12-dang-nhap feat/TASK-0012-Dang_Nhap; do
  echo "$b" | grep -Eq "$BRANCH_RE" && err "nhánh sai được chấp nhận: $b"
done

for c in "docs(TASK-0035): thêm quy ước nhánh, commit và mẫu PR" "feat(TASK-0012): thêm màn hình đăng nhập" "fix(TASK-0101): tăng timeout khi gọi dịch vụ"; do
  grep -qF "$c" "$DOC" || err "tài liệu thiếu ví dụ commit '$c'"
  echo "$c" | grep -Eq "$COMMIT_RE" || err "commit hợp lệ bị từ chối: $c"
done
for c in "update stuff" "Fix: sửa lỗi."; do
  echo "$c" | grep -Eq "$COMMIT_RE" && err "commit sai được chấp nhận: $c"
done

[ "$fail" -eq 0 ] && echo "OK"
exit "$fail"
