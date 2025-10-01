document.addEventListener("scroll", () => {
    const nav = document.querySelector(".nav");
    if (!nav) return;

    if (window.scrollY > 40) {
        nav.classList.add("nav--scrolled");
    } else {
        nav.classList.remove("nav--scrolled");
    }
});

// Add a small fade-in effect for cards
const observer = new IntersectionObserver(
    (entries) => {
        entries.forEach((entry) => {
            if (entry.isIntersecting) {
                entry.target.classList.add("is-visible");
                observer.unobserve(entry.target);
            }
        });
    },
    { threshold: 0.2 }
);

document.querySelectorAll(".event-card").forEach((card) => {
    card.classList.add("will-animate");
    observer.observe(card);
});
