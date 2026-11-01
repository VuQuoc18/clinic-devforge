import { createApi } from "./api.js";
import { mountLoginScreen } from "./login-screen.js";

mountLoginScreen(document.getElementById("app"), {
  api: createApi(),
  navigate: (path) => window.location.assign(path),
  onLoggedIn: (data) => {
    if (data.access_token) sessionStorage.setItem("patient_access_token", data.access_token);
  },
});
