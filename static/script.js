const animatedItems = document.querySelectorAll("[data-animate]");
const confirmForms = document.querySelectorAll("form[data-confirm]");
const clockElement = document.querySelector("[data-clock]");
const scrollLinks = document.querySelectorAll('a[href^="#"]');

if ("IntersectionObserver" in window) {
  const observer = new IntersectionObserver(
    (entries, obs) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          entry.target.classList.add("is-visible");
          obs.unobserve(entry.target);
        }
      });
    },
    { threshold: 0.2 }
  );

  animatedItems.forEach((item) => observer.observe(item));
} else {
  animatedItems.forEach((item) => item.classList.add("is-visible"));
}

confirmForms.forEach((form) => {
  form.addEventListener("submit", (event) => {
    const message = form.getAttribute("data-confirm-message") ||
      "Bu içeriği silmek istediğinizden emin misiniz?";
    if (!window.confirm(message)) {
      event.preventDefault();
    }
  });
});

function updateClock() {
  if (!clockElement) return;
  const now = new Date();
  clockElement.textContent = now.toLocaleTimeString("tr-TR", {
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
  });
}

if (clockElement) {
  updateClock();
  setInterval(updateClock, 1000);
}

scrollLinks.forEach((link) => {
  link.addEventListener("click", (event) => {
    const targetId = link.getAttribute("href")?.slice(1);
    const target = targetId ? document.getElementById(targetId) : null;
    if (!target) return;
    event.preventDefault();
    target.scrollIntoView({ behavior: "smooth", block: "start" });
    target.classList.add("is-visible");
  });
});
