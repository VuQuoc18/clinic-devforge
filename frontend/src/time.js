const VN_TZ = "Asia/Ho_Chi_Minh";

const formatter = new Intl.DateTimeFormat("en-GB", {
  timeZone: VN_TZ,
  year: "numeric",
  month: "2-digit",
  day: "2-digit",
  hour: "2-digit",
  minute: "2-digit",
  second: "2-digit",
  hourCycle: "h23",
});

// Định dạng thời điểm (ISO 8601 / Date) theo giờ Việt Nam (UTC+7): "HH:mm:ss dd/MM/yyyy".
export function formatVietnamTime(value) {
  const d = value instanceof Date ? value : new Date(value);
  if (Number.isNaN(d.getTime())) return "";
  const p = Object.fromEntries(
    formatter.formatToParts(d).map((x) => [x.type, x.value]),
  );
  return `${p.hour}:${p.minute}:${p.second} ${p.day}/${p.month}/${p.year}`;
}

// Số giây -> "mm:ss".
export function formatCountdown(totalSeconds) {
  const s = Math.max(0, Math.floor(totalSeconds));
  const mm = String(Math.floor(s / 60)).padStart(2, "0");
  const ss = String(s % 60).padStart(2, "0");
  return `${mm}:${ss}`;
}
