(() => {
    "use strict";

    const initGallery = () => {
        const mainImage = document.getElementById("mainProductImage");
        const thumbnails = document.querySelectorAll(".product-thumbnail");

        if (!mainImage || !thumbnails.length) return;

        thumbnails.forEach((thumb) => {
            thumb.addEventListener("click", () => {
                const url = thumb.dataset.image;
                if (!url) return;

                mainImage.src = url;
                mainImage.style.opacity = "0";

                requestAnimationFrame(() => {
                    mainImage.style.transition = "opacity 250ms ease";
                    mainImage.style.opacity = "1";
                });

                thumbnails.forEach((t) => t.classList.remove("is-active"));
                thumb.classList.add("is-active");
            });
        });
    };

    const initQuantity = () => {
        const input = document.getElementById("quantityInput");
        if (!input) return;

        const clamp = () => {
            const max = parseInt(input.max, 10) || 99;
            const min = parseInt(input.min, 10) || 1;
            let value = parseInt(input.value, 10) || min;
            value = Math.min(Math.max(value, min), max);
            input.value = value;
        };

        document.querySelectorAll(".quantity-btn").forEach((btn) => {
            btn.addEventListener("click", () => {
                const action = btn.dataset.action;
                let value = parseInt(input.value, 10) || 1;

                if (action === "increase") value += 1;
                if (action === "decrease") value = Math.max(1, value - 1);

                input.value = value;
                clamp();
            });
        });

        input.addEventListener("change", clamp);
    };

    const initVariants = () => {
        const hidden = document.getElementById("selectedVariant");
        const radios = document.querySelectorAll('input[name="variant"]');

        if (!hidden || !radios.length) return;

        const sync = () => {
            const checked = document.querySelector('input[name="variant"]:checked');
            hidden.value = checked ? checked.value : "";
        };

        radios.forEach((radio) => {
            radio.addEventListener("change", sync);
        });

        sync();
    };

    document.addEventListener("DOMContentLoaded", () => {
        initGallery();
        initQuantity();
        initVariants();
    });
})();