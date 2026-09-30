"use strict";

/* Форма записи на курс: направление → курс, дата начала, способ оплаты */
document.addEventListener("DOMContentLoaded", async () => {
  if (!App.requireLogin()) return;
  const form = document.getElementById("app-form");
  const category = document.getElementById("category");
  const course = document.getElementById("course");
  const payment = document.getElementById("payment");
  const startDate = document.getElementById("start_date");
  const errorBox = document.getElementById("error");
  const okBox = document.getElementById("ok");
  const submit = document.getElementById("submit");

  const today = new Date();
  startDate.min = today.getFullYear() + "-" + String(today.getMonth() + 1).padStart(2, "0") + "-" + String(today.getDate()).padStart(2, "0");

  async function loadCourses(categoryId, selectedId) {
    course.replaceChildren(App.el("option", { value: "", text: "Загрузка…" }));
    course.disabled = true;
    if (!categoryId) {
      course.replaceChildren(App.el("option", { value: "", text: "Сначала выберите направление" }));
      return;
    }
    const data = await App.api("/api/catalog?category_id=" + categoryId + "&per_page=100");
    course.replaceChildren(App.el("option", { value: "", text: "Выберите курс" }));
    data.items.forEach((c) => course.append(App.el("option", { value: c.id, text: c.name + " — " + c.hours + " ч." })));
    course.disabled = false;
    if (selectedId) course.value = String(selectedId);
  }

  try {
    const [cats, pays] = await Promise.all([App.api("/api/categories"), App.api("/api/payment_methods")]);
    cats.forEach((c) => category.append(App.el("option", { value: c.id, text: c.name })));
    pays.forEach((p) => payment.append(App.el("option", { value: p.id, text: p.name })));
    const presetId = new URLSearchParams(location.search).get("course_id");
    if (presetId && /^\d+$/.test(presetId)) {
      const item = await App.api("/api/catalog/" + presetId).catch(() => null);
      if (item) { category.value = String(item.category_id); await loadCourses(item.category_id, item.id); }
    }
  } catch (err) { App.showMessage(errorBox, err.message, "error"); }

  category.addEventListener("change", () => {
    loadCourses(category.value).catch((err) => App.showMessage(errorBox, err.message, "error"));
  });

  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    App.showMessage(okBox, "", "ok");
    if (!course.value || !startDate.value || !payment.value) {
      return App.showMessage(errorBox, "Заполните все поля формы.", "error");
    }
    submit.disabled = true;
    submit.textContent = "Отправка…";
    try {
      const res = await App.api("/api/applications", {
        method: "POST",
        body: { course_id: Number(course.value), start_date: startDate.value, payment_method_id: Number(payment.value) },
      });
      App.showMessage(errorBox, "", "error");
      App.showMessage(okBox, "Заявка №" + res.id + " принята. Статус: «Новая».", "ok");
      form.reset();
      course.disabled = true;
    } catch (err) {
      if (err.status === 401) { App.clearSession(); return App.requireLogin(); }
      App.showMessage(errorBox, err.message, "error");
    } finally {
      submit.disabled = false;
      submit.textContent = "Отправить заявку";
    }
  });
});
