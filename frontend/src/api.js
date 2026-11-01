// Client cho API đăng nhập bệnh nhân (hợp đồng API: xem docs/patient-login-screen.md).
export class ApiError extends Error {
  constructor({ status, code, message, meta }) {
    super(message || code || "Request failed");
    this.status = status;
    this.code = code;
    const m = meta || {};
    this.attemptsRemaining = m.attempts_remaining ?? null;
    this.retryAt = m.retry_at ?? null;
    this.resendAvailableAt = m.resend_available_at ?? null;
  }
}

export function createApi({ fetchFn, baseUrl = "/v1" } = {}) {
  const doFetch = fetchFn || ((...a) => globalThis.fetch(...a));

  async function post(path, body) {
    let res;
    try {
      res = await doFetch(`${baseUrl}${path}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });
    } catch (e) {
      throw new ApiError({ status: 0, code: "NETWORK_ERROR", message: String(e) });
    }
    let json = null;
    try {
      json = await res.json();
    } catch {
      json = null;
    }
    if (!res.ok) {
      const err = (json && json.error) || {};
      throw new ApiError({
        status: res.status,
        code: err.code || "INTERNAL_ERROR",
        message: err.message,
        meta: err.meta,
      });
    }
    return (json && json.data) || {};
  }

  return {
    // -> { resend_after_seconds, resend_available_at, expires_at }
    requestOtp(phone) {
      return post("/patient-otp-requests", { phone });
    },
    // -> { access_token, is_new_patient }
    verifyOtp(phone, otp) {
      return post("/patient-sessions", { phone, otp });
    },
  };
}
