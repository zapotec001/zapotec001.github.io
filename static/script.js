const nav = document.querySelector(".nav");
let statusElement = document.getElementById("status");
const eventsContainer = document.getElementById("events");
const todayElement = document.querySelector("[data-date]");
const refreshButton = document.querySelector("[data-refresh]");
const refreshDefaultLabel = refreshButton?.textContent?.trim() || "";

const LENGTH_LIMIT = 240;
const MAX_EVENTS = 9;
const CATEGORY_LABELS = {
    selected: "Öne Çıkanlar",
    events: "Olay",
    births: "Doğum",
    deaths: "Ölüm",
    holidays: "Özel Gün",
    observances: "Anma",
};

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

function setRefreshLoading(isLoading) {
    if (!refreshButton) return;
    refreshButton.disabled = isLoading;
    refreshButton.classList.toggle("is-loading", isLoading);
    if (refreshDefaultLabel) {
        refreshButton.textContent = isLoading
            ? "Yenileniyor..."
            : refreshDefaultLabel;
    }
}

function clearStatus() {
    if (statusElement) {
        statusElement.remove();
        statusElement = null;
    }
}

function formatCategory(category) {
    if (!category) return "";
    return CATEGORY_LABELS[category] || category;
}

function createEventCard(event) {
    const article = document.createElement("article");
    article.className = "event-card will-animate";

    const meta = document.createElement("header");
    meta.className = "event-meta";

    if (event.category) {
        const badge = document.createElement("span");
        badge.className = `event-category event-category--${event.category}`;
        badge.textContent = formatCategory(event.category);
        meta.appendChild(badge);
    }

    const year = document.createElement("span");
    year.className = "event-year";
    year.textContent = event.year ?? "";
    meta.appendChild(year);

    article.appendChild(meta);

    const text = document.createElement("p");
    text.className = "event-text";
    text.textContent = event.text ?? "";

    if (event.image?.src) {
        const figure = document.createElement("figure");
        figure.className = "event-media";

        const img = document.createElement("img");
        img.src = event.image.src;
        img.alt = event.image.alt || "Olay görseli";
        img.loading = "lazy";

        if (event.image.url) {
            const imageLink = document.createElement("a");
            imageLink.href = event.image.url;
            imageLink.target = "_blank";
            imageLink.rel = "noopener";
            imageLink.className = "event-image-link";
            imageLink.appendChild(img);
            figure.appendChild(imageLink);
        } else {
            figure.appendChild(img);
        }

        if (event.image.caption) {
            const figcaption = document.createElement("figcaption");
            figcaption.textContent = event.image.caption;
            figure.appendChild(figcaption);
        }

        article.appendChild(figure);
    }
    article.appendChild(text);

    if (Array.isArray(event.pages) && event.pages.length > 0) {
        const linksWrapper = document.createElement("div");
        linksWrapper.className = "event-links";
        linksWrapper.setAttribute("aria-label", "Daha fazla bilgi");

        event.pages.slice(0, 2).forEach((page) => {
            const url = page?.url;
            const title = page?.title;
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

    eventsContainer.innerHTML = "";
    statusElement = null;
    showStatus(
        "Olaylar yükleniyor",
        "Wikipedia'nın Tarihte Bugün arşivi çağrılıyor..."
    );

    const month = referenceDate.getMonth() + 1;
    const day = referenceDate.getDate();
    const endpoint = `https://tr.wikipedia.org/api/rest_v1/feed/onthisday/all/${month}/${day}`;

    setRefreshLoading(true);
    try {
        const response = await fetch(endpoint, {
            headers: {
                Accept: "application/json",
                "Accept-Language": "tr",
            },
        });

        if (!response.ok) {
            throw new Error("Yanıt alınamadı");
        }

        const data = await response.json();
        const categories = [
            { key: "selected", items: data.selected },
            { key: "events", items: data.events },
            { key: "births", items: data.births },
            { key: "deaths", items: data.deaths },
            { key: "holidays", items: data.holidays },
            { key: "observances", items: data.observances },
        ];

        const aggregated = categories.flatMap(({ key, items }) => {
            if (!Array.isArray(items)) return [];
            return items.map((item) => ({ ...item, category: key }));
        });

        const filtered = aggregated
            .filter((event) => {
                const text = event?.text?.trim();
                return text && text.length <= LENGTH_LIMIT;
            })
            .sort((a, b) => (b.year || 0) - (a.year || 0));

        const deduplicated = [];
        const seen = new Set();
        for (const event of filtered) {
            const key = `${event.year || "unknown"}-${event.text}`.toLowerCase();
            if (seen.has(key)) continue;
            seen.add(key);
            deduplicated.push(event);
            if (deduplicated.length >= MAX_EVENTS) {
                break;
            }
        }

        if (deduplicated.length === 0) {
            showStatus(
                "Olay bulunamadı",
                "Bugün için Wikipedia'da listelenen olay yok.",
                "alert"
            );
            return;
        }

        clearStatus();
        const normalisedEvents = deduplicated.map((event) => {
            const pages = Array.isArray(event.pages)
                ? event.pages
                      .map((page) => {
                          const desktopUrl =
                              page?.content_urls?.desktop?.page ||
                              page?.content_urls?.mobile?.page;
                          const title = (page?.titles?.display || page?.title || "")
                              .replace(/\s+/g, " ")
                              .trim();
                          const description = (page?.description || "").trim();
                          const imageSource =
                              page?.originalimage?.source || page?.thumbnail?.source || "";

                          if (!desktopUrl || !title) {
                              return null;
                          }

                          return {
                              title,
                              url: desktopUrl,
                              description,
                              imageSource,
                          };
                      })
                      .filter(Boolean)
                : [];

            const directImageSrc =
                event?.originalimage?.source || event?.thumbnail?.source || "";
            const directImageUrl =
                event?.content_urls?.desktop?.page || event?.content_urls?.mobile?.page || "";

            let image = null;
            if (directImageSrc) {
                image = {
                    src: directImageSrc,
                    alt: event.text?.trim() || "Olay görseli",
                    url: directImageUrl || pages[0]?.url || null,
                    caption: event?.extract ? event.extract.trim() : null,
                };
            } else {
                const pageWithImage = pages.find((page) => page.imageSource);
                if (pageWithImage) {
                    image = {
                        src: pageWithImage.imageSource,
                        alt: pageWithImage.title,
                        url: pageWithImage.url,
                        caption: pageWithImage.description || null,
                    };
                }
            }

            return {
                year: event.year,
                text: event.text?.trim() || "",
                category: event.category,
                pages: pages.slice(0, 3).map(({ title, url }) => ({ title, url })),
                image,
            };
        });

        normalisedEvents.forEach((event) => {
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
    } finally {
        setRefreshLoading(false);
    }
}

document.addEventListener("DOMContentLoaded", () => {
    const now = new Date();
    if (todayElement) {
        todayElement.textContent = formatDate(now);
    }
    updateNavOnScroll();
    loadEvents(now);
    refreshButton?.addEventListener("click", () => {
        const refreshedDate = new Date();
        if (todayElement) {
            todayElement.textContent = formatDate(refreshedDate);
        }
        loadEvents(refreshedDate);
    });
});
