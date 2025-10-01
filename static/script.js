const nav = document.querySelector(".nav");
let statusElement = document.getElementById("status");
const eventsContainer = document.getElementById("events");
const todayElement = document.querySelector("[data-date]");

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

function updateNavOnScroll() {
    if (!nav) return;
    if (window.scrollY > 40) {
        nav.classList.add("nav--scrolled");
    } else {
        nav.classList.remove("nav--scrolled");
    }
}

document.addEventListener("scroll", updateNavOnScroll);

function formatDate(now = new Date()) {
    return now.toLocaleDateString("tr-TR", {
        day: "2-digit",
        month: "long",
        year: "numeric",
    });
}

function showStatus(title, message, role = "status") {
    if (!statusElement) {
        statusElement = document.createElement("div");
        statusElement.className = "empty-state";
        statusElement.id = "status";
        statusElement.setAttribute("role", role);
        eventsContainer?.appendChild(statusElement);
    }

    statusElement.innerHTML = `<h2>${title}</h2><p>${message}</p>`;
    statusElement.setAttribute("role", role);
}

function clearStatus() {
    if (statusElement) {
        statusElement.remove();
        statusElement = null;
    }
}

function createEventCard(event) {
    const article = document.createElement("article");
    article.className = "event-card will-animate";

    const year = document.createElement("div");
    year.className = "event-year";
    year.textContent = event.year ?? "";

    const text = document.createElement("p");
    text.className = "event-text";
    text.textContent = event.text ?? "";

    article.appendChild(year);
    article.appendChild(text);

    if (Array.isArray(event.pages) && event.pages.length > 0) {
        const linksWrapper = document.createElement("div");
        linksWrapper.className = "event-links";
        linksWrapper.setAttribute("aria-label", "Daha fazla bilgi");

        event.pages.slice(0, 2).forEach((page) => {
            const url = page?.content_urls?.desktop?.page;
            const title = page?.titles?.display || page?.title;
            if (!url || !title) return;

            const link = document.createElement("a");
            link.href = url;
            link.target = "_blank";
            link.rel = "noopener";
            link.className = "event-link";
            link.textContent = title;
            linksWrapper.appendChild(link);
        });

        if (linksWrapper.children.length > 0) {
            article.appendChild(linksWrapper);
        }
    }

    observer.observe(article);
    return article;
}

async function loadEvents(referenceDate = new Date()) {
    if (!eventsContainer) return;

    showStatus(
        "Olaylar yükleniyor",
        "Wikipedia'nın Tarihte Bugün arşivi çağrılıyor..."
    );

    const month = referenceDate.getMonth() + 1;
    const day = referenceDate.getDate();
    const endpoint = `https://en.wikipedia.org/api/rest_v1/feed/onthisday/events/${month}/${day}`;

    try {
        const response = await fetch(endpoint, {
            headers: { Accept: "application/json" },
        });

        if (!response.ok) {
            throw new Error("Yanıt alınamadı");
        }

        const data = await response.json();
        const events = Array.isArray(data.events) ? data.events : [];

        const sorted = events
            .filter((event) => event.text)
            .sort((a, b) => (b.year || 0) - (a.year || 0))
            .slice(0, 4);

        if (sorted.length === 0) {
            showStatus(
                "Olay bulunamadı",
                "Bugün için Wikipedia'da listelenen olay yok.",
                "alert"
            );
            return;
        }

        clearStatus();
        sorted.forEach((event) => {
            const card = createEventCard(event);
            eventsContainer.appendChild(card);
        });
    } catch (error) {
        console.error("Olaylar yüklenirken hata oluştu", error);
        showStatus(
            "Olaylar yüklenemedi",
            "Şu anda Wikipedia verilerine erişilemiyor. Lütfen daha sonra tekrar deneyin.",
            "alert"
        );
    }
}

document.addEventListener("DOMContentLoaded", () => {
    const now = new Date();
    if (todayElement) {
        todayElement.textContent = formatDate(now);
    }
    updateNavOnScroll();
    loadEvents(now);
});
