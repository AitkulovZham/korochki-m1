"use strict";

/* Формы входа и регистрации */
document.addEventListener("DOMContentLoaded", () => {
  const loginForm = document.getElementById("login-form");
  const registerForm = document.getElementById("register-form");
  const errorBox = document.getElementById("error");

  if (loginForm) {
    const params = new URLSearchParams(location.search);
    if (params.get("registered")) {
      App.showMessage(errorBox, "Регистрация выполнена. Теперь войдите.", "ok");
      errorBox.setAttribute("role", "status");
    }
    loginForm.addEventListener("submit", async (e) => {
      e.preventDefault();
      const login = loginForm.login.value.trim();
      const password = loginForm.password.value;
      if (login.length < 6 || password.length < 8) {
        return App.showMessage(errorBox, "Логин — не менее 6 символов, пароль — не менее 8.", "error");
      }
      const btn = loginForm.querySelector("button[type=submit]");
      btn.disabled = true;
      try {
        const data = await App.api("/api/login", { method: "POST", body: { login, password } });
        App.setSession({ token: data.token, role_id: data.role_id, login: data.login });
        location.href = App.safeNext(params.get("next"));
      } catch (err) {
        App.showMessage(errorBox, err.message, "error");
      } finally {
        btn.disabled = false;
      }
    });
  }

  if (registerForm) {
    registerForm.addEventListener("submit", async (e) => {
      e.preventDefault();
      const login = registerForm.login.value.trim();
      const password = registerForm.password.value;
      if (!/^[A-Za-z0-9_.-]{6,50}$/.test(login)) {
        return App.showMessage(errorBox, "Логин: 6–50 символов (латиница, цифры, _ . -).", "error");
      }
      if (password.length < 8) return App.showMessage(errorBox, "Пароль — не менее 8 символов.", "error");
      if (password !== registerForm.password2.value) return App.showMessage(errorBox, "Пароли не совпадают.", "error");
      const btn = registerForm.querySelector("button[type=submit]");
      btn.disabled = true;
      try {
        await App.api("/api/register", { method: "POST", body: { login, password } });
        location.href = "/login?registered=1";
      } catch (err) {
        App.showMessage(errorBox, err.message, "error");
      } finally {
        btn.disabled = false;
      }
    });
  }
});
