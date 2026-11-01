import test, { before, after } from "node:test";
import assert from "node:assert/strict";
import http from "node:http";
import { createApi } from "../../src/api.js";
import { mountLoginScreen, ROUTE_NEW_PATIENT, ROUTE_RETURNING_PATIENT } from "../../src/login-screen.js";
import { createDom, typeInto, typeOtp } from "../helpers.js";

// Máy chủ giả lập hợp đồng API trong docs/patient-login-screen.md.
const KNOWN_PHONES = new Set(["0900000001"]);
const VALID_OTP = "123456";
let server, baseUrl;

before(async () => {
  server = http.createServer((req, res) => {
    let body = "";
    req.on("data", (c) => (body += c));
    req.on("end", () => {
      const json = JSON.parse(body || "{}");
      const send = (status, obj) => {
        res.writeHead(status, { "Content-Type": "application/json" });
        res.end(JSON.stringify(obj));
      };
      if (req.method === "POST" && req.url === "/v1/patient-otp-requests") {
        return send(200, { data: { resend_after_seconds: 60 } });
      }
      if (req.method === "POST" && req.url === "/v1/patient-sessions") {
        if (json.otp !== VALID_OTP) {
          return send(401, {
            error: {
              code: "OTP_INVALID",
              message: "Invalid OTP.",
              meta: { attempts_remaining: 4, retry_at: "2025-01-01T17:30:05Z" },
            },
          });
        }
        return send(200, { data: { access_token: "tok", is_new_patient: !KNOWN_PHONES.has(json.phone) } });
      }
      send(404, { error: { code: "RESOURCE_NOT_FOUND", message: "x" } });
    });
  });
  await new Promise((r) => server.listen(0, "127.0.0.1", r));
  baseUrl = `http://127.0.0.1:${server.address().port}/v1`;
});
after(() => server.close());

const waitFor = async (cond) => {
  for (let i = 0; i < 200; i++) {
    if (cond()) return;
    await new Promise((r) => setTimeout(r, 10));
  }
  assert.fail("timeout");
};

async function login(phone, otp) {
  const env = createDom();
  const nav = [];
  const logged = [];
  const screen = mountLoginScreen(env.root, {
    api: createApi({ baseUrl }),
    navigate: (p) => nav.push(p),
    onLoggedIn: (d) => logged.push(d),
  });
  typeInto(env.window, env.root.querySelector("#phone"), phone);
  env.root.querySelector("#send-code").click();
  await waitFor(() => !env.root.querySelector("#otp-section").hidden);
  typeOtp(env.window, env.root, otp);
  return { env, nav, logged, screen };
}

test("số mới đăng nhập bằng OTP đúng -> form hồ sơ", async () => {
  const { nav, logged, screen } = await login("0911111111", VALID_OTP);
  await waitFor(() => nav.length > 0);
  assert.deepEqual(nav, [ROUTE_NEW_PATIENT]);
  assert.equal(logged[0].access_token, "tok");
  screen.destroy();
});

test("số cũ đăng nhập bằng OTP đúng -> Lịch hẹn của tôi", async () => {
  const { nav, screen } = await login("0900000001", VALID_OTP);
  await waitFor(() => nav.length > 0);
  assert.deepEqual(nav, [ROUTE_RETURNING_PATIENT]);
  screen.destroy();
});

test("OTP sai qua HTTP thật -> 'Mã không đúng' kèm số lần còn lại, không điều hướng", async () => {
  const { env, nav, screen } = await login("0900000001", "000000");
  await waitFor(() => env.root.querySelector("#otp-error").textContent !== "");
  assert.equal(env.root.querySelector("#otp-error").textContent, "Mã không đúng");
  assert.match(env.root.querySelector("#otp-details").textContent, /Còn 4 lần/);
  assert.match(env.root.querySelector("#otp-details").textContent, /00:30:05 02\/01\/2025/);
  assert.deepEqual(nav, []);
  screen.destroy();
});
