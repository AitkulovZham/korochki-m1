"use strict";

/* Каталог курсов: фильтр по направлению, постраничная подгрузка и lazy-load карточек
   через IntersectionObserver, отмена устаревших запросов (AbortController). */
document.addEventListener("DOMContentLoaded", () => {
  const PER_PAGE = 12;
  const cards = document.getElementById("cards");
  const statusLine = document.getElementById("status");
  const select = document.getElementById("category");
  const sentinel = document.getElementById("sentinel");
  const state = { page: 0, hasNext: true, loading: false, total: 0, shown: 0, controller: null };

  /* Плавное появление карточек только когда они попали в область видимости */
  const revealObserver = new IntersectionObserver((entries) => {
    entries.forEach((entry) => {
      if (entry.isIntersecting) {
        entry.target.classList.add("is-visible");
        revealObserver.unobserve(entry.target);
      }
    });
  }, { rootMargin: "0px 0px -40px 0px" });

  function buildCard(course) {
    const img = App.el("img", {
      src: "/img/cat-" + course.category_id + ".svg", alt: "", width: "320", height: "180",
      loading: "lazy", decoding: "async",
    });
    const price = new Intl.NumberFormat("ru-RU").format(course.price) + " ₽";
    const body = App.el("div", { class: "body" },
      App.el("h3", { text: course.name }),
      App.el("span", { class: "meta", text: course.hours + " ак. часов" }),
      App.el("span", { class: "price", text: price }),
      App.el("a", { class: "btn", href: "/create_application?course_id=" + course.id, text: "Записаться" }));
    const card = App.el("article", { class: "course-card" }, img, body);
    revealObserver.observe(card);
    return card;
  }

  async function loadNextPage() {
    if (state.loading || !state.hasNext) return;
    state.loading = true;
    cards.setAttribute("aria-busy", "true");
    statusLine.textContent = "Загрузка курсов";
    statusLine.classList.add("loading");
    const controller = new AbortController();
    state.controller = controller;
    try {
      const params = new URLSearchParams({ page: state.page + 1, per_page: PER_PAGE });
      if (select.value) params.set("category_id", select.value);
      const data = await App.api("/api/catalog?" + params, { signal: controller.signal });
      data.items.forEach((course) => cards.append(buildCard(course)));
      state.page = data.page;
      state.hasNext = data.has_next;
      state.total = data.total;
      state.shown += data.items.length;
      statusLine.textContent = state.total === 0
        ? "В этом направлении пока нет курсов."
        : "Показано " + state.shown + " из " + state.total;
    } catch (err) {
      if (err.name === "AbortError") return;
      statusLine.textContent = "Не удалось загрузить курсы: " + err.message;
    } finally {
      if (state.controller === controller) {
        state.loading = false;
        cards.setAttribute("aria-busy", "false");
        statusLine.classList.remove("loading");
        /* если «маркер конца» всё ещё в зоне видимости (высокий экран), подгружаем дальше */
        if (state.hasNext) { sentinelObserver.unobserve(sentinel); sentinelObserver.observe(sentinel); }
      }
    }
  }

  function resetAndLoad() {
    if (state.controller) state.controller.abort();
    Object.assign(state, { page: 0, hasNext: true, loading: false, total: 0, shown: 0 });
    cards.replaceChildren();
    loadNextPage();
  }

  /* Подгрузка следующей страницы, когда до конца списка остаётся ~300px */
  const sentinelObserver = new IntersectionObserver((entries) => {
    if (entries[0].isIntersecting) loadNextPage();
  }, { rootMargin: "300px" });
  sentinelObserver.observe(sentinel);

  select.addEventListener("change", resetAndLoad);

  App.api("/api/categories").then((list) => {
    list.forEach((c) => select.append(App.el("option", { value: c.id, text: c.name })));
  }).catch(() => { /* фильтр останется «Все направления» */ });
});
