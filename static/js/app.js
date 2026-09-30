// PocketSmart AI - small vanilla-JS helpers (no frameworks).
// 1) Planner forms: send data to the FastAPI endpoint with fetch(), then open the saved result page.
// 2) Results page: dynamic sort + platform filter of the recommendation cards.

(function () {
  "use strict";

  // ---------- 1. planner forms ----------
  document.querySelectorAll(".planner-form").forEach(function (form) {
    form.addEventListener("submit", async function (ev) {
      ev.preventDefault();
      const errBox = document.getElementById("form-error");
      const loading = form.parentElement.querySelector(".loading");
      const btn = form.querySelector("button[type=submit]");
      errBox.hidden = true;

      let init;
      if (form.dataset.mode === "multipart") {
        const fd = new FormData(form);
        const file = fd.get("image");
        if (file && file.size === 0) fd.delete("image"); // no file chosen
        init = { method: "POST", body: fd };
      } else {
        const data = {};
        new FormData(form).forEach(function (v, k) { data[k] = v; });
        data.budget = parseFloat(data.budget);
        if (data.guests !== undefined) data.guests = parseInt(data.guests, 10);
        if (data.quantity !== undefined) data.quantity = parseInt(data.quantity, 10);
        if (form.elements.veg_only) data.veg_only = form.elements.veg_only.checked;
        init = { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(data) };
      }

      btn.disabled = true;
      loading.hidden = false;
      try {
        const resp = await fetch(form.dataset.endpoint, init);
        if (resp.status === 401) { window.location = "/login"; return; }
        const body = await resp.json().catch(function () { return {}; });
        if (!resp.ok) throw new Error(body.detail || "Something went wrong. Please try again.");
        window.location = "/history/" + body.history_id;
      } catch (e) {
        errBox.textContent = e.message;
        errBox.hidden = false;
        btn.disabled = false;
        loading.hidden = true;
        errBox.scrollIntoView({ behavior: "smooth", block: "center" });
      }
    });
  });

  // ---------- 2. sort / filter on results page ----------
  const grid = document.getElementById("item-grid");
  if (grid) {
    const sortSel = document.getElementById("sort-items");
    const platSel = document.getElementById("filter-platform");
    function apply() {
      const cards = Array.from(grid.children);
      const mode = sortSel.value;
      cards.sort(function (a, b) {
        if (mode === "price-asc") return a.dataset.price - b.dataset.price;
        if (mode === "price-desc") return b.dataset.price - a.dataset.price;
        return a.dataset.order - b.dataset.order;
      });
      cards.forEach(function (c) {
        c.hidden = platSel.value !== "" && c.dataset.platform !== platSel.value;
        grid.appendChild(c);
      });
    }
    sortSel.addEventListener("change", apply);
    platSel.addEventListener("change", apply);
  }
})();
