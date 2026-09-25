(() => {
    "use strict";


    /* =====================================================
       ALERTS
    ====================================================== */

    const initAlerts = () => {

        document
            .querySelectorAll("[data-alert-close]")
            .forEach((button) => {

                button.addEventListener("click", () => {

                    const alert = button.closest(".alert");

                    if (!alert) {
                        return;
                    }

                    alert.style.transition =
                        "opacity 250ms ease, transform 250ms ease";

                    alert.style.opacity = "0";

                    alert.style.transform =
                        "translateY(-8px)";

                    window.setTimeout(() => {
                        alert.remove();
                    }, 260);

                });

            });

    };


    /* =====================================================
       DRAWER
    ====================================================== */

    const initDrawer = () => {

        const body = document.body;

        const drawer =
            document.getElementById("side-drawer");

        const toggle =
            document.querySelector("[data-drawer-toggle]");

        const overlay =
            document.querySelector("[data-drawer-overlay]");

        const closeButton =
            document.querySelector("[data-drawer-close]");


        if (!drawer || !toggle) {
            return;
        }


        let previousFocusedElement = null;


        const setState = (open) => {

            body.classList.toggle(
                "drawer-open",
                open
            );

            toggle.classList.toggle(
                "open",
                open
            );

            toggle.setAttribute(
                "aria-expanded",
                String(open)
            );

            drawer.setAttribute(
                "aria-hidden",
                String(!open)
            );


            if (open) {

                previousFocusedElement =
                    document.activeElement;

                document.documentElement.classList.add(
                    "drawer-is-open"
                );

                const firstFocusable =
                    drawer.querySelector(
                        "button, a, input, select, textarea"
                    );

                firstFocusable?.focus();

            } else {

                document.documentElement.classList.remove(
                    "drawer-is-open"
                );

                if (
                    previousFocusedElement &&
                    typeof previousFocusedElement.focus === "function"
                ) {
                    previousFocusedElement.focus();
                }

            }

        };


        const closeDrawer = () => {
            setState(false);
        };


        toggle.addEventListener(
            "click",
            () => {

                const isOpen =
                    body.classList.contains("drawer-open");

                setState(!isOpen);

            }
        );


        overlay?.addEventListener(
            "click",
            closeDrawer
        );


        closeButton?.addEventListener(
            "click",
            closeDrawer
        );


        document.addEventListener(
            "keydown",
            (event) => {

                if (event.key === "Escape") {

                    if (
                        body.classList.contains("drawer-open")
                    ) {
                        closeDrawer();
                    }

                }

            }
        );


        drawer
            .querySelectorAll("a")
            .forEach((link) => {

                link.addEventListener(
                    "click",
                    () => {

                        window.setTimeout(
                            closeDrawer,
                            50
                        );

                    }
                );

            });


        window.addEventListener(
            "resize",
            () => {

                if (
                    window.innerWidth > 760 &&
                    body.classList.contains("drawer-open")
                ) {
                    closeDrawer();
                }

            }
        );

    };


    /* =====================================================
       ACCORDIONS
    ====================================================== */

    const initAccordions = () => {

        document
            .querySelectorAll("[data-accordion]")
            .forEach((button) => {

                button.addEventListener(
                    "click",
                    (event) => {

                        event.preventDefault();

                        event.stopPropagation();


                        const accordion = button.closest(".shine-drawer-accordion") || button.closest(".drawer-accordion");


                        if (!accordion) {
                            return;
                        }


                        const isOpen =
                            accordion.classList.contains("open");


                        accordion.classList.toggle(
                            "open",
                            !isOpen
                        );


                        button.setAttribute(
                            "aria-expanded",
                            String(!isOpen)
                        );

                    }
                );

            });

    };


    /* =====================================================
       HEADER SCROLL
    ====================================================== */

    const initHeaderScroll = () => {

        const header =
            document.querySelector("[data-header]");


        if (!header) {
            return;
        }


        const update = () => {

            header.classList.toggle(
                "is-scrolled",
                window.scrollY > 10
            );

        };


        window.addEventListener(
            "scroll",
            update,
            {
                passive: true
            }
        );


        update();

    };


    /* =====================================================
       CARD QUANTITY
    ====================================================== */

    const initCardQuantity = () => {

        document
            .querySelectorAll(".product-card-form")
            .forEach((form) => {

                const input =
                    form.querySelector(
                        'input[name="quantity"]'
                    );


                if (!input) {
                    return;
                }


                const clamp = () => {

                    let value =
                        parseInt(
                            input.value,
                            10
                        );


                    if (
                        Number.isNaN(value) ||
                        value < 1
                    ) {
                        value = 1;
                    }


                    if (value > 99) {
                        value = 99;
                    }


                    input.value = value;

                };


                form
                    .querySelectorAll(".quantity-btn")
                    .forEach((button) => {

                        button.addEventListener(
                            "click",
                            () => {

                                let value =
                                    parseInt(
                                        input.value,
                                        10
                                    ) || 1;


                                if (
                                    button.dataset.cardAction ===
                                    "increase"
                                ) {
                                    value += 1;
                                }


                                if (
                                    button.dataset.cardAction ===
                                    "decrease"
                                ) {
                                    value -= 1;
                                }


                                input.value =
                                    Math.min(
                                        Math.max(value, 1),
                                        99
                                    );

                            }
                        );

                    });


                input.addEventListener(
                    "blur",
                    clamp
                );

            });

    };


    /* =====================================================
       SEARCH INPUT
    ====================================================== */

    const initSearch = () => {

        document
            .querySelectorAll(".shine-search input")
            .forEach((input) => {

                input.addEventListener(
                    "keydown",
                    (event) => {

                        if (event.key === "Escape") {

                            input.value = "";

                            input.blur();

                        }

                    }
                );

            });

    };


    /* =====================================================
       INITIALIZE
    ====================================================== */

    document.addEventListener(
        "DOMContentLoaded",
        () => {

            initAlerts();

            initDrawer();

            initAccordions();

            initHeaderScroll();

            initCardQuantity();

            initSearch();

        }
    );

})();