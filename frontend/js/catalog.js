"use strict";

/* Каталог курсов (базовая версия): загружает все курсы сразу и выводит карточки. */
function buildCard(course) {
  const img = App.el("img", { src: "/img/cat-" + course.category_id + ".svg", alt: "" });
  const price = new Intl.NumberFormat("ru-RU").format(course.price) + " ₽";
  const body = App.el("div", { class: "body" },
    App.el("h3", { text: course.name }),
    App.el("span", { class: "meta", text: course.hours + " ак. часов" }),
    App.el("span", { class: "price", text: price }),
    App.el("a", { class: "btn", href: "/create_application?course_id=" + course.id, text: "Записаться" }));
  return App.el("article", { class: "course-card" }, img, body);
}

document.addEventListener("DOMContentLoaded", async () => {
  const cards = document.getElementById("cards");
  const statusLine = document.getElementById("status");
  statusLine.textContent = "Загрузка курсов";
  try {
    let page = 1, hasNext = true, total = 0;
    while (hasNext) {
      const data = await App.api("/api/catalog?page=" + page + "&per_page=100");
      data.items.forEach((course) => cards.append(buildCard(course)));
      hasNext = data.has_next;
      total = data.total;
      page += 1;
    }
    statusLine.textContent = "Всего курсов: " + total;
  } catch (err) {
    statusLine.textContent = "Не удалось загрузить курсы: " + err.message;
  }
});
