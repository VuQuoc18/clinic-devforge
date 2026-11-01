import test from "node:test";
import assert from "node:assert/strict";
import { formatCountdown, formatVietnamTime } from "../../src/time.js";

test("hiển thị theo giờ Việt Nam (UTC+7)", () => {
  assert.equal(formatVietnamTime("2025-01-01T17:30:05Z"), "00:30:05 02/01/2025");
  assert.equal(formatVietnamTime("2025-06-15T02:00:00Z"), "09:00:00 15/06/2025");
});

test("giá trị sai trả chuỗi rỗng", () => {
  assert.equal(formatVietnamTime("không phải ngày"), "");
});

test("formatCountdown", () => {
  assert.equal(formatCountdown(59), "00:59");
  assert.equal(formatCountdown(125), "02:05");
  assert.equal(formatCountdown(-3), "00:00");
});
