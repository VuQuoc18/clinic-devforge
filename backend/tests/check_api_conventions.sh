#!/bin/sh
# Kiểm tra tài liệu quy ước API có đủ 3 mục, ví dụ request/response và ghi chú DEC-0001.
set -e
f="$(dirname "$0")/../../docs/api-conventions.md"
fail() { echo "FAIL: $1"; exit 1; }

[ -f "$f" ] || fail "missing $f"
grep -q '^## 1\. Định dạng lỗi' "$f" || fail "missing error section"
grep -q '^## 2\. Phân trang' "$f" || fail "missing pagination section"
grep -q '^## 3\. Đặt tên route' "$f" || fail "missing route section"
grep -q 'DEC-0001' "$f" || fail "missing DEC-0001 note"
grep -q 'CHỜ XÁC NHẬN' "$f" || fail "missing pending-confirmation marker"

# Mỗi mục phải có ít nhất một ví dụ request và response HTTP.
for n in 1 2 3; do
  sec=$(awk -v n="$n" '/^## /{p=($0 ~ "^## " n "\\.")} p' "$f")
  echo "$sec" | grep -Eq '^(GET|POST) /v1/' || fail "section $n has no request example"
  echo "$sec" | grep -Eq '^HTTP/1\.1 [0-9]{3}' || fail "section $n has no response example"
done
echo "OK"
