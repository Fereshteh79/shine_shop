(() => {
    "use strict";

    const initGallery = () => {
        const mainImage = document.getElementById("mainProductImage");
        const thumbnails = document.querySelectorAll(".product-thumbnail");

        if (!mainImage || !thumbnails.length) {
            return;
        }

        thumbnails.forEach((thumb) => {
            thumb.addEventListener("click", () => {
                const url = thumb.dataset.image;

                if (!url || mainImage.src === url) {
                    return;
                }

                mainImage.style.opacity = "0";

                const updateImage = () => {
                    mainImage.src = url;

                    requestAnimationFrame(() => {
                        mainImage.style.transition = "opacity 250ms ease";
                        mainImage.style.opacity = "1";
                    });
                };

                if (mainImage.complete) {
                    updateImage();
                } else {
                    mainImage.addEventListener("load", updateImage, {once: true});
                }

                thumbnails.forEach((item) => {
                    item.classList.remove("is-active");
                });

                thumb.classList.add("is-active");
            });
        });
    };

    const initQuantity = () => {
        const input = document.getElementById("quantityInput");
        const buttons = document.querySelectorAll(".quantity-btn");

        if (!input) {
            return;
        }

        const getLimits = () => ({
            min: parseInt(input.min, 10) || 1,
            max: parseInt(input.max, 10) || 99,
        });

        const clamp = () => {
            const {min, max} = getLimits();
            let value = parseInt(input.value, 10);

            if (Number.isNaN(value)) {
                value = min;
            }

            value = Math.min(Math.max(value, min), max);
            input.value = value;
        };

        buttons.forEach((button) => {
            button.addEventListener("click", () => {
                const {min, max} = getLimits();
                const action = button.dataset.action;
                let value = parseInt(input.value, 10);

                if (Number.isNaN(value)) {
                    value = min;
                }

                if (action === "increase") {
                    value += 1;
                }

                if (action === "decrease") {
                    value -= 1;
                }

                input.value = Math.min(Math.max(value, min), max);
            });
        });

        input.addEventListener("change", clamp);
        input.addEventListener("input", clamp);

        clamp();
    };

    const initVariants = () => {
        const hiddenInput = document.getElementById("selectedVariant");
        const radios = document.querySelectorAll('input[name="variant"]');

        if (!hiddenInput || !radios.length) {
            return;
        }

        const syncVariant = () => {
            const checkedRadio = document.querySelector(
                'input[name="variant"]:checked'
            );

            hiddenInput.value = checkedRadio ? checkedRadio.value : "";
        };

        radios.forEach((radio) => {
            radio.addEventListener("change", syncVariant);
        });

        syncVariant();
    };

    const initProductPage = () => {
        initGallery();
        initQuantity();
        initVariants();
    };

    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", initProductPage, {
            once: true,
        });
    } else {
        initProductPage();
    }
})();