"use strict";

const toggle = document.querySelector("#open-only");
if (toggle) {
  toggle.hidden = false;
  toggle.addEventListener("click", () => {
    const active = toggle.getAttribute("aria-pressed") !== "true";
    toggle.setAttribute("aria-pressed", String(active));
    toggle.textContent = active ? "Показать все места" : "Только открытые сейчас";
    const cards = [...document.querySelectorAll("#places .card")];
    cards.forEach((card) => {
      card.hidden = active && !card.querySelector(".status-open");
    });
    document.querySelector("#no-open-places").hidden =
      !active || cards.some((card) => !card.hidden) || cards.length === 0;
  });
}
