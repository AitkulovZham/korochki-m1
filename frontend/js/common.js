"use strict";

/* Общий модуль клиента: сессия (sessionStorage), обёртка над Fetch API, навигация. */
const App = (() => {
  const KEY = "korochki_session";
  const STATUS_NAMES = { 1: "Новая", 2: "В обработке", 3: "Подтверждена", 4: "Отклонена" };

  function session() {
    try { return JSON.parse(sessionStorage.getItem(KEY)) || null; } catch (_) { return null; }
  }
  function setSession(data) { sessionStorage.setItem(KEY, JSON.stringify(data)); }
  function clearSession() { sessionStorage.removeItem(KEY); }

  async function api(path, { method = "GET", body, signal } = {}) {
    const headers = { Accept: "application/json" };
    const s = session();
    if (s && s.token) headers.Authorization = "Bearer " + s.token;
    if (body !== undefined) headers["Content-Type"] = "application/json";
    const res = await fetch(path, {
      method, headers, signal,
      body: body === undefined ? undefined : JSON.stringify(body),
    });
    let data = null;
    try { data = await res.json(); } catch (_) { /* пустое тело */ }
    if (!res.ok) {
      const err = new Error((data && data.error) || "Ошибка запроса (" + res.status + ")");
      err.status = res.status;
      throw err;
    }
    return data;
  }

  function el(tag, attrs, ...children) {
    const node = document.createElement(tag);
    Object.entries(attrs || {}).forEach(([k, v]) => {
      if (k === "class") node.className = v;
      else if (k === "text") node.textContent = v;
      else node.setAttribute(k, v);
    });
    children.forEach((c) => node.append(c));
    return node;
  }

  function showMessage(node, text, kind) {
    node.textContent = text || "";
    node.className = "alert " + (kind || "error");
    node.hidden = !text;
  }

  /* Безопасный адрес возврата: только путь внутри сайта */
  function safeNext(value) {
    return value && value.startsWith("/") && !value.startsWith("//") ? value : "/applications";
  }

  function requireLogin() {
    if (session()) return true;
    location.href = "/login?next=" + encodeURIComponent(location.pathname + location.search);
    return false;
  }

  function renderNav() {
    const nav = document.getElementById("nav");
    if (!nav) return;
    const s = session();
    const links = [["/", "Каталог"]];
    if (s) {
      links.push(["/applications", "Мои заявки"], ["/create_application", "Записаться"]);
      if (s.role_id === 1 || s.role_id === 2) links.push(["/admin", "Панель оператора"]);
    } else {
      links.push(["/login", "Вход"], ["/register", "Регистрация"]);
    }
    links.forEach(([href, text]) => {
      const a = el("a", { href, text });
      if (location.pathname === href) a.setAttribute("aria-current", "page");
      nav.append(el("li", {}, a));
    });
    if (s) {
      const btn = el("button", { type: "button", class: "btn-secondary", text: "Выйти (" + s.login + ")" });
      btn.addEventListener("click", () => { clearSession(); location.href = "/"; });
      nav.append(el("li", {}, btn));
    }
  }

  document.addEventListener("DOMContentLoaded", renderNav);
  return { session, setSession, clearSession, api, el, showMessage, safeNext, requireLogin, STATUS_NAMES };
})();
