// REQ-007: số điện thoại gồm đúng 10 chữ số và bắt đầu bằng 0.
export const PHONE_PATTERN = /^0[0-9]{9}$/;

export const PHONE_ERROR_MESSAGE =
  "Số điện thoại phải gồm 10 chữ số và bắt đầu bằng 0.";

export function isValidPhone(value) {
  return PHONE_PATTERN.test(String(value ?? ""));
}

// Trả về chuỗi lỗi, hoặc "" nếu hợp lệ hoặc chưa nhập gì.
export function phoneError(value) {
  const v = String(value ?? "");
  if (v === "") return "";
  return isValidPhone(v) ? "" : PHONE_ERROR_MESSAGE;
}
