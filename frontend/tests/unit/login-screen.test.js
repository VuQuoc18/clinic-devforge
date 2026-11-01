import test, { beforeEach, afterEach, mock } from "node:test";
import assert from "node:assert/strict";
import { ApiError } from "../../src/api.js";
import { mountLoginScreen, ROUTE_NEW_PATIENT, ROUTE_RETURNING_PATIENT } from "../../src/login-screen.js";
import { createDom, flush, typeInto, typeOtp } from "../helpers.js";

let env, api, nav, screen;

function mount(overrides = {}) {
  env = createDom();
  nav = [];
  api = {
    requestOtp: async () => ({ resend_after_seconds: 60 }),
    verifyOtp: async () => ({ access_token: "t", is_new_patient: false }),
    ...overrides,
  };
  screen = mountLoginScreen(env.root, { api, navigate: (p) => nav.push(p) });
  return env;
}
const q = (sel) => env.root.querySelector(sel);

beforeEach(() => mock.timers.enable({ apis: ["setInterval"] }));
afterEach(() => {
  screen?.destroy();
  mock.timers.reset();
});

for (const [label, value] of [
  ["9 chữ số", "091234567"],
  ["không bắt đầu bằng 0", "1912345678"],
  ["có ký tự chữ", "09123abc78"],
]) {
  test(`số ${label}: khóa nút Gửi mã và báo lỗi dưới ô nhập`, () => {
    mount();
    typeInto(env.window, q("#phone"), value);
    assert.equal(q("#send-code").disabled, true);
    assert.equal(q("#phone-error").hidden, false);
    assert.ok(q("#phone-error").textContent.length > 0);
    assert.equal(q("#phone").nextElementSibling, q("#phone-error"), "lỗi nằm ngay dưới ô nhập");
    assert.equal(q("#phone").getAttribute("aria-invalid"), "true");
  });
}

test("số 10 chữ số bắt đầu bằng 0: mở nút, không có lỗi", () => {
  mount();
  typeInto(env.window, q("#phone"), "0912345678");
  assert.equal(q("#send-code").disabled, false);
  assert.equal(q("#phone-error").hidden, true);
});

test("ban đầu nút khóa, OTP chưa hiện", () => {
  mount();
  assert.equal(q("#send-code").disabled, true);
  assert.equal(q("#otp-section").hidden, true);
});

test("không có ô mật khẩu, nút Google/Zalo", () => {
  mount();
  assert.equal(env.root.querySelectorAll('input[type="password"]').length, 0);
  assert.doesNotMatch(env.root.textContent, /google|zalo|mật khẩu/i);
  assert.equal(env.root.querySelectorAll("a[href*=google i], a[href*=zalo i]").length, 0);
});

test("sau khi gửi: hiện 6 ô OTP, đồng hồ; Gửi lại mã chỉ mở khi về 0", async () => {
  let calls = 0;
  mount({ requestOtp: async () => (calls++, { resend_after_seconds: 3 }) });
  typeInto(env.window, q("#phone"), "0912345678");
  q("#send-code").click();
  await flush();
  assert.equal(calls, 1);
  assert.equal(q("#otp-section").hidden, false);
  assert.equal(env.root.querySelectorAll(".otp-box").length, 6);
  assert.match(q("#countdown").textContent, /00:03/);
  assert.equal(q("#resend").disabled, true);
  assert.equal(q("#send-code").disabled, true);

  mock.timers.tick(2000);
  assert.match(q("#countdown").textContent, /00:01/);
  assert.equal(q("#resend").disabled, true);
  mock.timers.tick(1000);
  assert.equal(q("#resend").disabled, false);

  q("#resend").click();
  await flush();
  assert.equal(calls, 2);
  assert.equal(q("#resend").disabled, true);
  assert.match(q("#countdown").textContent, /00:03/);
});

test("nhập đủ 6 số thì gửi xác thực; số mới -> form hồ sơ", async () => {
  let args;
  mount({ verifyOtp: async (p, o) => ((args = [p, o]), { is_new_patient: true }) });
  typeInto(env.window, q("#phone"), "0912345678");
  q("#send-code").click();
  await flush();
  typeOtp(env.window, env.root, "123456");
  await flush();
  assert.deepEqual(args, ["0912345678", "123456"]);
  assert.deepEqual(nav, [ROUTE_NEW_PATIENT]);
});

test("số cũ -> Lịch hẹn của tôi", async () => {
  mount();
  typeInto(env.window, q("#phone"), "0912345678");
  q("#send-code").click();
  await flush();
  typeOtp(env.window, env.root, "123456");
  await flush();
  assert.deepEqual(nav, [ROUTE_RETURNING_PATIENT]);
});

test("OTP sai: hiện 'Mã không đúng', số lần còn lại, giờ thử lại và gửi lại theo giờ VN", async () => {
  mount({
    verifyOtp: async () => {
      throw new ApiError({
        status: 401,
        code: "OTP_INVALID",
        meta: {
          attempts_remaining: 2,
          retry_at: "2025-01-01T17:30:05Z",
          resend_available_at: "2025-06-15T02:00:00Z",
        },
      });
    },
  });
  typeInto(env.window, q("#phone"), "0912345678");
  q("#send-code").click();
  await flush();
  typeOtp(env.window, env.root, "000000");
  await flush();
  assert.equal(q("#otp-error").textContent, "Mã không đúng");
  const d = q("#otp-details").textContent;
  assert.match(d, /Còn 2 lần/);
  assert.match(d, /00:30:05 02\/01\/2025/);
  assert.match(d, /09:00:00 15\/06\/2025/);
  assert.deepEqual(nav, []);
  assert.equal([...env.root.querySelectorAll(".otp-box")].every((b) => b.value === ""), true);
});

test("hết lượt thử: khóa các ô OTP", async () => {
  mount({
    verifyOtp: async () => {
      throw new ApiError({ status: 401, code: "OTP_INVALID", meta: { attempts_remaining: 0 } });
    },
  });
  typeInto(env.window, q("#phone"), "0912345678");
  q("#send-code").click();
  await flush();
  typeOtp(env.window, env.root, "000000");
  await flush();
  assert.match(q("#otp-details").textContent, /Còn 0 lần/);
  assert.equal([...env.root.querySelectorAll(".otp-box")].every((b) => b.disabled), true);
});

test("gửi mã lỗi: báo lỗi, không hiện OTP", async () => {
  mount({
    requestOtp: async () => {
      throw new ApiError({ status: 429, code: "RATE_LIMITED" });
    },
  });
  typeInto(env.window, q("#phone"), "0912345678");
  q("#send-code").click();
  await flush();
  assert.equal(q("#send-error").hidden, false);
  assert.equal(q("#otp-section").hidden, true);
  assert.equal(q("#send-code").disabled, false);
});
