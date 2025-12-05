// Typewriter effect for splash screen
const text = " ./spikeypear.sh";
let index = 0;

window.addEventListener("DOMContentLoaded", () => {
  const typewriterElement = document.getElementById("typewriter");

  function typeWriter() {
    if (index < text.length) {
      typewriterElement.textContent += text.charAt(index);
      index++;
      setTimeout(typeWriter, 100);
    }
  }

  setTimeout(typeWriter, 500);

  // Initialize welcome section as active after splash screen
  setTimeout(() => {
    showSection("welcome");
  }, 3500);
});

// Show sections
function showSection(sectionId) {
  // Hide all sections
  document
    .querySelectorAll(".section")
    .forEach((sec) => sec.classList.remove("active"));

  // Show selected section
  document.getElementById(sectionId).classList.add("active");

  // Remove active class from all nav items
  document.querySelectorAll(".nav-item").forEach((item) => {
    item.classList.remove("active");
  });

  // Map section IDs to nav item index (order matters!)
  const navMap = {
    about: 0, // [a] about
    projects: 1, // [p] projects
    links: 2, // [l] links
    blogs: 3, // [b] blogs
    notes: 4, // [n] leave note
    welcome: 5, // [q] home
  };

  // Add active class to the correct nav item
  if (navMap[sectionId] !== undefined) {
    const navItems = document.querySelectorAll(".nav-item");
    if (navItems[navMap[sectionId]]) {
      navItems[navMap[sectionId]].classList.add("active");
    }
  }
}

// Keyboard navigation
document.addEventListener("keydown", (e) => {
  if (e.target.tagName === "TEXTAREA") return;

  const key = e.key.toLowerCase();
  const sections = {
    a: "about",
    p: "projects",
    l: "links",
    b: "blogs",
    n: "notes",
    q: "welcome",
  };

  if (sections[key]) {
    showSection(sections[key]);
  }
});
