(() => {
    "use strict";

    document.addEventListener("DOMContentLoaded", () => {
        const wrapper = document.querySelector("[data-slider]");
        if (!wrapper) return;

        const slides = wrapper.querySelectorAll(".slide");
        const dots = wrapper.querySelectorAll("[data-slide-to]");

        if (slides.length < 2) return;

        let current = 0;
        let timer = null;

        const show = (index) => {
            slides[current].classList.remove("is-active");
            dots[current]?.classList.remove("is-active");

            current = (index + slides.length) % slides.length;

            slides[current].classList.add("is-active");
            dots[current]?.classList.add("is-active");
        };

        const start = () => {
            timer = setInterval(() => show(current + 1), 5000);
        };

        const stop = () => {
            clearInterval(timer);
        };

        dots.forEach((dot) => {
            dot.addEventListener("click", () => {
                stop();
                show(parseInt(dot.dataset.slideTo, 10));
                start();
            });
        });

        wrapper.addEventListener("mouseenter", stop);
        wrapper.addEventListener("mouseleave", start);

        start();
    });
})();