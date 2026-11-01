// MH-TK-01 Đăng nhập bệnh nhân (REQ-001, REQ-005, REQ-007, REQ-022).
// Chỉ đăng nhập bằng số điện thoại + OTP; không có ô mật khẩu, không có nút Google/Zalo.
import { isValidPhone, phoneError } from "./phone.js";
import { formatCountdown, formatVietnamTime } from "./time.js";

export const OTP_LENGTH = 6;
export const DEFAULT_RESEND_SECONDS = 60;
export const ROUTE_NEW_PATIENT = "/ho-so/tao-moi"; // form hồ sơ
export const ROUTE_RETURNING_PATIENT = "/lich-hen-cua-toi"; // Lịch hẹn của tôi

const TEMPLATE = `
<form class="login" novalidate autocomplete="off">
  <h1>Đăng nhập</h1>
  <div class="field">
    <label for="phone">Số điện thoại</label>
    <input id="phone" name="phone" type="tel" inputmode="tel" autocomplete="tel"
           aria-describedby="phone-error" aria-invalid="false">
    <p id="phone-error" class="error" role="alert" hidden></p>
  </div>
  <button id="send-code" type="submit" disabled>Gửi mã</button>
  <p id="send-error" class="error" role="alert" hidden></p>

  <section id="otp-section" hidden>
    <div class="otp-label" id="otp-label">Nhập mã OTP gồm 6 chữ số</div>
    <div class="otp-boxes" role="group" aria-labelledby="otp-label"></div>
    <p id="otp-error" class="error" role="alert" hidden></p>
    <div id="otp-details" class="otp-details" hidden></div>
    <p class="resend">
      <span id="countdown" aria-live="off"></span>
      <button id="resend" type="button" class="link" disabled>Gửi lại mã</button>
    </p>
  </section>
</form>`;

function setMessage(el, text) {
  el.textContent = text || "";
  el.hidden = !text;
}

/**
 * @param {HTMLElement} root
 * @param {{api: {requestOtp, verifyOtp}, navigate: (path:string)=>void,
 *          onLoggedIn?: (data:object)=>void}} deps
 */
export function mountLoginScreen(root, { api, navigate, onLoggedIn }) {
  const doc = root.ownerDocument;
  const win = doc.defaultView;
  root.innerHTML = TEMPLATE;

  const $ = (sel) => root.querySelector(sel);
  const phoneInput = $("#phone");
  const phoneErr = $("#phone-error");
  const sendBtn = $("#send-code");
  const sendErr = $("#send-error");
  const otpSection = $("#otp-section");
  const otpErr = $("#otp-error");
  const otpDetails = $("#otp-details");
  const countdownEl = $("#countdown");
  const resendBtn = $("#resend");
  const boxesWrap = $(".otp-boxes");

  const boxes = [];
  for (let i = 0; i < OTP_LENGTH; i++) {
    const b = doc.createElement("input");
    b.type = "text";
    b.inputMode = "numeric";
    b.maxLength = 1;
    b.className = "otp-box";
    b.setAttribute("data-index", String(i));
    b.setAttribute("aria-label", `Chữ số OTP thứ ${i + 1}`);
    b.autocomplete = i === 0 ? "one-time-code" : "off";
    boxesWrap.appendChild(b);
    boxes.push(b);
  }

  let timer = null;
  let remaining = 0;
  let busy = false;
  let otpSent = false;

  // ----- Số điện thoại -----
  function refreshPhone() {
    const v = phoneInput.value;
    const err = phoneError(v);
    setMessage(phoneErr, err);
    phoneInput.setAttribute("aria-invalid", err ? "true" : "false");
    sendBtn.disabled = busy || otpSent || !isValidPhone(v);
  }
  phoneInput.addEventListener("input", refreshPhone);

  // ----- Đồng hồ đếm ngược -----
  function renderCountdown() {
    if (remaining > 0) {
      countdownEl.textContent = `Gửi lại mã sau ${formatCountdown(remaining)}`;
      resendBtn.disabled = true;
    } else {
      countdownEl.textContent = "Bạn chưa nhận được mã?";
      resendBtn.disabled = busy;
    }
  }
  function stopTimer() {
    if (timer !== null) {
      globalThis.clearInterval(timer);
      timer = null;
    }
  }
  function startCountdown(seconds) {
    stopTimer();
    remaining = Math.max(0, Math.floor(seconds));
    renderCountdown();
    if (remaining === 0) return;
    timer = globalThis.setInterval(() => {
      remaining -= 1;
      if (remaining <= 0) {
        remaining = 0;
        stopTimer();
      }
      renderCountdown();
    }, 1000);
  }

  // ----- OTP -----
  const otpValue = () => boxes.map((b) => b.value).join("");
  function clearOtp() {
    boxes.forEach((b) => {
      b.value = "";
    });
  }
  function setOtpDisabled(disabled) {
    boxes.forEach((b) => {
      b.disabled = disabled;
    });
  }
  function showSent(data) {
    otpSent = true;
    otpSection.hidden = false;
    phoneInput.readOnly = true;
    refreshPhone();
    clearOtp();
    setOtpDisabled(false);
    setMessage(otpErr, "");
    otpDetails.hidden = true;
    otpDetails.textContent = "";
    startCountdown(data.resend_after_seconds ?? DEFAULT_RESEND_SECONDS);
    boxes[0].focus();
  }

  async function sendCode() {
    if (busy || !isValidPhone(phoneInput.value)) return;
    busy = true;
    setMessage(sendErr, "");
    refreshPhone();
    resendBtn.disabled = true;
    try {
      const data = await api.requestOtp(phoneInput.value);
      busy = false;
      showSent(data);
    } catch (e) {
      busy = false;
      let msg = "Không gửi được mã. Vui lòng thử lại.";
      if (e.resendAvailableAt) {
        msg += ` Bạn có thể gửi lại mã lúc ${formatVietnamTime(e.resendAvailableAt)} (giờ Việt Nam).`;
      }
      setMessage(otpSent ? otpErr : sendErr, msg);
      refreshPhone();
      renderCountdown();
    }
  }

  async function submitOtp() {
    const code = otpValue();
    if (busy || code.length !== OTP_LENGTH || !/^[0-9]{6}$/.test(code)) return;
    busy = true;
    setMessage(otpErr, "");
    resendBtn.disabled = true;
    try {
      const data = await api.verifyOtp(phoneInput.value, code);
      busy = false;
      stopTimer();
      if (onLoggedIn) onLoggedIn(data);
      // Điều hướng theo cờ từ API: số mới -> form hồ sơ, số cũ -> Lịch hẹn của tôi.
      navigate(data.is_new_patient ? ROUTE_NEW_PATIENT : ROUTE_RETURNING_PATIENT);
    } catch (e) {
      busy = false;
      renderCountdown();
      showVerifyError(e);
    }
  }

  function showVerifyError(e) {
    if (e.code !== "OTP_INVALID") {
      setMessage(otpErr, "Không xác thực được mã. Vui lòng thử lại.");
      if (e.retryAt) {
        otpDetails.textContent = `Bạn có thể thử lại lúc ${formatVietnamTime(e.retryAt)} (giờ Việt Nam).`;
        otpDetails.hidden = false;
      }
      return;
    }
    setMessage(otpErr, "Mã không đúng");
    const lines = [];
    if (e.attemptsRemaining !== null && e.attemptsRemaining !== undefined) {
      lines.push(`Còn ${e.attemptsRemaining} lần thử.`);
    }
    if (e.retryAt) {
      lines.push(`Bạn có thể thử lại lúc ${formatVietnamTime(e.retryAt)} (giờ Việt Nam).`);
    }
    if (e.resendAvailableAt) {
      lines.push(`Bạn có thể gửi lại mã lúc ${formatVietnamTime(e.resendAvailableAt)} (giờ Việt Nam).`);
    }
    otpDetails.textContent = lines.join(" ");
    otpDetails.hidden = lines.length === 0;
    clearOtp();
    if (e.attemptsRemaining === 0) {
      setOtpDisabled(true);
    } else {
      boxes[0].focus();
    }
  }

  boxes.forEach((box, i) => {
    box.addEventListener("input", () => {
      const digits = box.value.replace(/[^0-9]/g, "");
      if (digits.length > 1) {
        // dán / tự điền nhiều chữ số
        digits
          .slice(0, OTP_LENGTH - i)
          .split("")
          .forEach((d, k) => {
            boxes[i + k].value = d;
          });
        boxes[Math.min(i + digits.length, OTP_LENGTH - 1)].focus();
      } else {
        box.value = digits;
        if (digits && i < OTP_LENGTH - 1) boxes[i + 1].focus();
      }
      submitOtp();
    });
    box.addEventListener("keydown", (ev) => {
      if (ev.key === "Backspace" && !box.value && i > 0) boxes[i - 1].focus();
    });
  });

  root.querySelector("form").addEventListener("submit", (ev) => {
    ev.preventDefault();
    if (!otpSent) sendCode();
  });
  resendBtn.addEventListener("click", () => {
    if (remaining === 0) sendCode();
  });

  refreshPhone();
  renderCountdown();

  return {
    destroy() {
      stopTimer();
      root.innerHTML = "";
    },
  };
}
