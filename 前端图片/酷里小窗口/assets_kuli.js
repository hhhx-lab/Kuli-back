(function () {
  const root = document.documentElement;
  const savedTheme = localStorage.getItem("kuli-theme");
  const preferredTheme = window.matchMedia("(prefers-color-scheme: light)").matches ? "light" : "dark";
  root.dataset.theme = savedTheme || preferredTheme;

  function updateToggles() {
    document.querySelectorAll("[data-theme-toggle]").forEach((button) => {
      const isLight = root.dataset.theme === "light";
      button.setAttribute("aria-label", isLight ? "切换到深色模式" : "切换到浅色模式");
      const text = button.querySelector("[data-theme-label]");
      if (text) text.textContent = isLight ? "浅色" : "深色";
      const icon = button.querySelector("[data-theme-icon]");
      if (icon) icon.textContent = isLight ? "亮" : "暗";
    });
  }

  document.addEventListener("click", (event) => {
    const toggle = event.target.closest("[data-theme-toggle]");
    if (!toggle) return;
    root.dataset.theme = root.dataset.theme === "light" ? "dark" : "light";
    localStorage.setItem("kuli-theme", root.dataset.theme);
    updateToggles();
  });

  document.addEventListener("input", (event) => {
    const target = event.target;
    if (!(target instanceof HTMLTextAreaElement)) return;
    const counter = document.querySelector(`[data-count-for="${target.id}"]`);
    if (counter) counter.textContent = `${target.value.length} / ${target.maxLength || 800}`;
  });

  document.addEventListener("submit", (event) => {
    const form = event.target.closest("[data-note-form]");
    if (!form) return;
    event.preventDefault();

    const status = document.querySelector("[data-submit-status]");
    const detail = form.querySelector("#need-detail");
    const contact = form.querySelector("#contact");
    if (!detail.value.trim() || !contact.value.trim()) {
      status.textContent = "还差一点：请写下需求和联系方式，酷里才知道怎么回你。";
      status.classList.add("is-visible");
      return;
    }

    status.textContent = "小纸条已经模拟投递。真实上线时这里会接入表单、飞书或微信提醒。";
    status.classList.add("is-visible");
    form.querySelector("[data-submit-button]").textContent = "已丢给酷里";
  });

  document.addEventListener("click", (event) => {
    const filterButton = event.target.closest("[data-filter]");
    if (!filterButton) return;

    const filterGroup = filterButton.closest("[data-faq-filters]");
    const topic = filterButton.dataset.filter;
    filterGroup.querySelectorAll("[data-filter]").forEach((button) => {
      button.classList.toggle("is-active", button === filterButton);
    });

    document.querySelectorAll("[data-faq-list] details").forEach((item) => {
      const shouldShow = topic === "all" || item.dataset.topic === topic;
      item.hidden = !shouldShow;
      if (shouldShow && topic !== "all") item.open = true;
    });
  });

  updateToggles();
})();
