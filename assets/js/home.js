document.addEventListener("DOMContentLoaded", () => {
  const featured = document.querySelector(".sg-featured");
  const featuredButton = document.querySelector(".sg-featured-toggle");
  const featuredContent = document.querySelector(".sg-featured-content");

  if (featured && featuredButton && featuredContent) {
    featuredButton.addEventListener("click", () => {
      const willOpen = featuredContent.hidden;

      featuredContent.hidden = !willOpen;
      featured.classList.toggle("is-open", willOpen);
      featuredButton.textContent = willOpen ? "Ocultar" : "Mostrar";
      featuredButton.setAttribute("aria-expanded", String(willOpen));
    });
  }

  const archive = document.querySelector("[data-archive]");
  const viewButtons = [...document.querySelectorAll(".sg-view-button")];

  const applyView = (view) => {
    if (!archive) return;

    const grid = view === "grid";
    archive.classList.toggle("is-grid", grid);

    viewButtons.forEach((button) => {
      const active = button.dataset.view === view;
      button.classList.toggle("is-active", active);
      button.setAttribute("aria-pressed", String(active));
    });

    localStorage.setItem("southghost-view", view);
  };

  if (archive && viewButtons.length) {
    const saved = localStorage.getItem("southghost-view");
    applyView(saved === "grid" ? "grid" : "list");

    viewButtons.forEach((button) => {
      button.addEventListener("click", () => applyView(button.dataset.view));
    });
  }

  const sidebarLinks = [...document.querySelectorAll(".sg-sidebar a")];
  const months = [...document.querySelectorAll(".sg-month")];

  if ("IntersectionObserver" in window && sidebarLinks.length && months.length) {
    const linksById = new Map(
      sidebarLinks.map((link) => [decodeURIComponent(link.hash.slice(1)), link])
    );

    const observer = new IntersectionObserver(
      (entries) => {
        const visible = entries
          .filter((entry) => entry.isIntersecting)
          .sort((a, b) => a.boundingClientRect.top - b.boundingClientRect.top)[0];

        if (!visible) return;

        sidebarLinks.forEach((link) => link.classList.remove("is-active"));
        linksById.get(visible.target.id)?.classList.add("is-active");
      },
      {
        rootMargin: "-20% 0px -70% 0px",
        threshold: 0
      }
    );

    months.forEach((month) => observer.observe(month));
  }
});
