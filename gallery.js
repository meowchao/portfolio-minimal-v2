// Renders gallery/gallery.json into #clicks-grid. Captions go in via textContent (no HTML injection).
(async function () {
  const grid = document.getElementById("clicks-grid");
  if (!grid) return;

  let items;
  try {
    const res = await fetch("gallery/gallery.json", { cache: "no-cache" });
    if (!res.ok) throw new Error(res.status);
    items = await res.json();
  } catch (err) {
    grid.innerHTML = '<div class="clicks-empty">> could not load clicks.</div>';
    return;
  }

  if (!items.length) {
    grid.innerHTML = '<div class="clicks-empty">> nothing here yet.</div>';
    return;
  }

  // Lightbox (single instance)
  const box = document.createElement("div");
  box.className = "lightbox";
  box.innerHTML =
    '<img alt="" /><div class="lightbox-caption"></div><div class="lightbox-date"></div>';
  document.body.appendChild(box);
  const boxImg = box.querySelector("img");
  const boxCap = box.querySelector(".lightbox-caption");
  const boxDate = box.querySelector(".lightbox-date");
  const close = () => box.classList.remove("open");
  box.addEventListener("click", close);
  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape") close();
  });

  const fmt = (iso) => {
    const d = new Date(iso);
    const p = (n) => String(n).padStart(2, "0");
    return `${p(d.getDate())}.${p(d.getMonth() + 1)}.${d.getFullYear()}`;
  };

  grid.textContent = "";
  for (const it of items) {
    const fig = document.createElement("div");
    fig.className = "click-item";

    const img = document.createElement("img");
    img.src = it.thumb;
    img.alt = it.caption || "photo";
    img.loading = "lazy";

    const meta = document.createElement("div");
    meta.className = "click-meta";
    const date = document.createElement("span");
    date.className = "click-date";
    date.textContent = `[${fmt(it.date)}] `;
    meta.append(date, document.createTextNode(it.caption || ""));

    fig.append(img, meta);
    fig.addEventListener("click", () => {
      boxImg.src = it.file;
      boxImg.alt = it.caption || "photo";
      boxCap.textContent = it.caption || "";
      boxDate.textContent = fmt(it.date);
      box.classList.add("open");
    });
    grid.appendChild(fig);
  }
})();
