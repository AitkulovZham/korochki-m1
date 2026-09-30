"use strict";

/* Панель оператора: список всех заявок, фильтр по статусу, смена статуса */
document.addEventListener("DOMContentLoaded", () => {
  if (!App.requireLogin()) return;
  const s = App.session();
  const message = document.getElementById("message");
  if (s.role_id !== 1 && s.role_id !== 2) {
    return App.showMessage(message, "Раздел доступен только оператору и администратору.", "error");
  }
  const PER_PAGE = 20;
  const rows = document.getElementById("rows");
  const statusLine = document.getElementById("status");
  const filter = document.getElementById("status-filter");
  const prev = document.getElementById("prev");
  const next = document.getElementById("next");
  const label = document.getElementById("page-label");
  let page = 1;

  async function load() {
    statusLine.textContent = "Загрузка заявок";
    const params = new URLSearchParams({ page, per_page: PER_PAGE });
    if (filter.value) params.set("status_id", filter.value);
    try {
      const data = await App.api("/api/admin/applications?" + params);
      rows.replaceChildren();
      data.items.forEach((a) => {
        const sel = App.el("select", { "aria-label": "Новый статус заявки №" + a.id });
        Object.entries(App.STATUS_NAMES).forEach(([id, name]) => {
          const opt = App.el("option", { value: id, text: name });
          if (Number(id) === a.status_id) opt.selected = true;
          sel.append(opt);
        });
        const save = App.el("button", { type: "button", text: "Сохранить" });
        save.addEventListener("click", async () => {
          save.disabled = true;
          try {
            await App.api("/api/admin/applications/" + a.id + "/status", { method: "PATCH", body: { status_id: Number(sel.value) } });
            App.showMessage(message, "", "error");
            load();
          } catch (err) { App.showMessage(message, err.message, "error"); save.disabled = false; }
        });
        rows.append(App.el("tr", {},
          App.el("td", { text: String(a.id) }),
          App.el("td", { text: a.login }),
          App.el("td", { text: a.course_name }),
          App.el("td", { text: new Date(a.start_date).toLocaleDateString("ru-RU") }),
          App.el("td", {}, App.el("span", { class: "badge s" + a.status_id, text: App.STATUS_NAMES[a.status_id] })),
          App.el("td", {}, sel, document.createTextNode(" "), save)));
      });
      statusLine.textContent = data.items.length ? "" : "Заявок не найдено.";
      label.textContent = "Страница " + page;
      prev.disabled = page === 1;
      next.disabled = data.items.length < PER_PAGE;
    } catch (err) {
      if (err.status === 401) { App.clearSession(); return App.requireLogin(); }
      App.showMessage(message, err.message, "error");
      statusLine.textContent = "";
    }
  }

  filter.addEventListener("change", () => { page = 1; load(); });
  prev.addEventListener("click", () => { page -= 1; load(); });
  next.addEventListener("click", () => { page += 1; load(); });
  load();
});
