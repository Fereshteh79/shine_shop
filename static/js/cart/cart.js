(() => {
    "use strict";

    const initQuantityControls = () => {
        document.querySelectorAll("[data-cart-update]").forEach((form) => {
            const input = form.querySelector('input[name="quantity"]');
            if (!input) return;

            const clamp = () => {
                const max = parseInt(input.max, 10) || 99;
                const min = parseInt(input.min, 10) || 1;
                let value = parseInt(input.value, 10) || min;
                input.value = Math.min(Math.max(value, min), max);
            };

            form.querySelectorAll(".quantity-btn").forEach((btn) => {
                btn.addEventListener("click", () => {
                    let value = parseInt(input.value, 10) || 1;

                    if (btn.dataset.action === "increase") value += 1;
                    if (btn.dataset.action === "decrease") value = Math.max(1, value - 1);

                    input.value = value;
                    clamp();
                    form.submit();
                });
            });

            input.addEventListener("change", () => {
                clamp();
                form.submit();
            });
        });
    };

    const initConfirmations = () => {
        document.querySelectorAll("form[data-confirm]").forEach((form) => {
            form.addEventListener("submit", (event) => {
                if (!window.confirm(form.dataset.confirm)) {
                    event.preventDefault();
                }
            });
        });
    };

    document.addEventListener("DOMContentLoaded", () => {
        initQuantityControls();
        initConfirmations();
    });
})();