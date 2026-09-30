"use strict";

/* Личный кабинет: список своих заявок с пагинацией и отменой заявки со статусом «Новая» */
document.addEventListener("DOMContentLoaded", () => {
  if (!App.requireLogin()) return;
  const PER_PAGE = 10;
  const rows = document.getElementById("rows");
  const message = document.getElementById("message");
  const statusLine = document.getElementById("status");
  const prev = document.getElementById("prev");
  const next = document.getElementById("next");
  const label = document.getElementById("page-label");
  let page = 1;

  function formatDate(iso) { return new Date(iso).toLocaleDateString("ru-RU"); }

  async function load() {
    statusLine.textContent = "Загрузка заявок";
    try {
      const data = await App.api("/api/applications/my?page=" + page + "&per_page=" + PER_PAGE);
      rows.replaceChildren();
      data.items.forEach((a) => {
        const cancel = a.status_id === 1
          ? App.el("button", { type: "button", class: "btn-secondary", text: "Отменить" })
          : App.el("span", { text: "—" });
        if (a.status_id === 1) cancel.addEventListener("click", () => cancelApplication(a.id));
        rows.append(App.el("tr", {},
          App.el("td", { text: String(a.id) }),
          App.el("td", { text: a.course_name }),
          App.el("td", { text: formatDate(a.start_date) }),
          App.el("td", {}, App.el("span", { class: "badge s" + a.status_id, text: App.STATUS_NAMES[a.status_id] })),
          App.el("td", {}, cancel)));
      });
      statusLine.textContent = data.items.length ? "" : "Заявок пока нет.";
      label.textContent = "Страница " + page;
      prev.disabled = page === 1;
      next.disabled = data.items.length < PER_PAGE;
    } catch (err) {
      if (err.status === 401) { App.clearSession(); return App.requireLogin(); }
      App.showMessage(message, err.message, "error");
      statusLine.textContent = "";
    }
  }

  async function cancelApplication(id) {
    if (!confirm("Отменить заявку №" + id + "?")) return;
    try {
      await App.api("/api/applications/" + id, { method: "DELETE" });
      App.showMessage(message, "", "error");
      load();
    } catch (err) { App.showMessage(message, err.message, "error"); }
  }

  prev.addEventListener("click", () => { page -= 1; load(); });
  next.addEventListener("click", () => { page += 1; load(); });
  load();
});
