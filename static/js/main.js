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

    const initMobileMenu = () => {
        const button = document.querySelector("[data-menu-toggle]");
        const nav = document.getElementById("main-nav");

        if (!button || !nav) return;

        const toggle = () => {
            const isOpen = nav.classList.toggle("open");
            button.classList.toggle("open", isOpen);
            button.setAttribute("aria-expanded", String(isOpen));
            document.body.classList.toggle("no-scroll", isOpen);
        };

        button.addEventListener("click", toggle);

        // بستن منو با کلید Esc یا کلیک روی لینک
        document.addEventListener("keydown", (e) => {
            if (e.key === "Escape" && nav.classList.contains("open")) toggle();
        });

        nav.querySelectorAll("a").forEach((link) => {
            link.addEventListener("click", () => {
                if (nav.classList.contains("open")) toggle();
            });
        });
    };

    const initHeaderScroll = () => {
        const header = document.querySelector("[data-header]");
        if (!header) return;

        const update = () => {
            header.classList.toggle("is-scrolled", window.scrollY > 10);
        };

        window.addEventListener("scroll", update, {passive: true});
        update();
    };

    document.addEventListener("DOMContentLoaded", () => {
        initAlerts();
        initMobileMenu();
        initHeaderScroll();
    });
})();