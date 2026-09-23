(() => {
    "use strict";

    const initAlerts = () => {
        document.querySelectorAll("[data-alert-close]").forEach((button) => {
            button.addEventListener("click", () => {
                const alert = button.closest(".alert");
                if (!alert) return;

                alert.style.transition = "opacity 250ms ease, transform 250ms ease";
                alert.style.opacity = "0";
                alert.style.transform = "translateY(-8px)";

                setTimeout(() => alert.remove(), 260);
            });
        });
    };

    const initDrawer = () => {
        const body = document.body;
        const drawer = document.getElementById("side-drawer");
        const toggle = document.querySelector("[data-drawer-toggle]");
        const overlay = document.querySelector("[data-drawer-overlay]");
        const closeButton = document.querySelector("[data-drawer-close]");

        if (!drawer || !toggle) return;

        const setState = (open) => {
            body.classList.toggle("drawer-open", open);
            toggle.classList.toggle("open", open);
            toggle.setAttribute("aria-expanded", String(open));
            drawer.setAttribute("aria-hidden", String(!open));
        };

        toggle.addEventListener("click", () => {
            setState(!body.classList.contains("drawer-open"));
        });

        overlay?.addEventListener("click", () => setState(false));
        closeButton?.addEventListener("click", () => setState(false));

        document.addEventListener("keydown", (event) => {
            if (event.key === "Escape") setState(false);
        });

        drawer.querySelectorAll("a").forEach((link) => {
            link.addEventListener("click", () => setState(false));
        });
    };

    const initAccordions = () => {
        document.querySelectorAll("[data-accordion]").forEach((button) => {
            button.addEventListener("click", (event) => {
                event.stopPropagation();
                button.closest(".drawer-accordion")?.classList.toggle("open");
            });
        });
    };

    const initHeaderScroll = () => {
        const header = document.querySelector("[data-header]");
        if (!header) return;

        const update = () => {
            header.classList.toggle("is-scrolled", window.scrollY > 12);
        };

        window.addEventListener("scroll", update, {passive: true});
        update();
    };
    const initCardQuantity = () => {
        document.querySelectorAll(".product-card-form").forEach((form) => {
            const input = form.querySelector('input[name="quantity"]');
            if (!input) return;

            form.querySelectorAll(".quantity-btn").forEach((btn) => {
                btn.addEventListener("click", () => {
                    let value = parseInt(input.value, 10) || 1;

                    if (btn.dataset.cardAction === "increase") value += 1;
                    if (btn.dataset.cardAction === "decrease") value = Math.max(1, value - 1);

                    input.value = Math.min(value, 99);
                });
            });
        });
    };

    document.addEventListener("DOMContentLoaded", () => {
        initAlerts();
        initDrawer();
        initAccordions();
        initHeaderScroll();
    });
})();