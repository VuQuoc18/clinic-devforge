import { JSDOM } from "jsdom";

export function createDom() {
  const dom = new JSDOM('<!doctype html><main id="app"></main>', { pretendToBeVisual: true });
  return { dom, window: dom.window, document: dom.window.document, root: dom.window.document.getElementById("app") };
}

export function typeInto(window, input, value) {
  input.value = value;
  input.dispatchEvent(new window.Event("input", { bubbles: true }));
}

export const flush = () => new Promise((r) => setImmediate(r));

export function typeOtp(window, root, code) {
  const boxes = root.querySelectorAll(".otp-box");
  [...code].forEach((d, i) => typeInto(window, boxes[i], d));
}
