import test from "node:test";
import assert from "node:assert/strict";
import { isValidPhone, phoneError } from "../../src/phone.js";

test("số hợp lệ: 10 chữ số bắt đầu bằng 0", () => {
  assert.equal(isValidPhone("0912345678"), true);
  assert.equal(phoneError("0912345678"), "");
});

test("số không hợp lệ", () => {
  for (const v of ["091234567", "09123456789", "1912345678", "09123abc78", " 0912345678", "+84912345678", ""]) {
    assert.equal(isValidPhone(v), false, v);
  }
  assert.notEqual(phoneError("091234567"), "");
  assert.equal(phoneError(""), "", "chưa nhập thì chưa báo lỗi");
});
