// The benchmarks page: charts drawn from the JSON in #b-data.
(() => {
  const data = JSON.parse(document.getElementById("b-data").textContent);
  const $ = (s, r = document) => r.querySelector(s);
  const still = matchMedia("(prefers-reduced-motion: reduce)").matches;
  const state = { set: "compiled", view: "ratio", on: {} };
  for (const [k, s] of Object.entries(data.sets)) state.on[k] = new Set(s.on);

  const fmtS = (x) => (x < 0.1 ? (x * 1000).toFixed(0) + " ms" : x < 10 ? x.toFixed(2) + " s" : x.toFixed(1) + " s");
  const fmtR = (r) => (r < 0.995 ? `${(1 / r).toFixed(r < 0.5 ? 1 : 2)}× faster than C` : r < 1.005 ? "same as C" : r < 10 ? `${r.toFixed(2)}× C` : `${Math.round(r)}× C`);
  const geo = (xs) => Math.exp(xs.reduce((a, x) => a + Math.log(x), 0) / xs.length);

  // --- Tooltip
  const tip = document.createElement("div");
  tip.className = "b-tip";
  tip.setAttribute("role", "tooltip");
  document.body.append(tip);
  function showTip(el, html) {
    tip.innerHTML = html;
    tip.classList.add("on");
    const r = el.getBoundingClientRect();
    const w = tip.offsetWidth;
    tip.style.left = Math.max(8, Math.min(innerWidth - w - 8, r.left + r.width / 2 - w / 2)) + "px";
    tip.style.top = r.top + scrollY - tip.offsetHeight - 10 + "px";
  }
  const hideTip = () => tip.classList.remove("on");

  // --- Legend
  function legend() {
    const s = data.sets[state.set];
    $("#b-legend").innerHTML = s.engines.map((e) => {
      const d = data.engines[e];
      return `<button type="button" class="b-key ${d.tone}" data-engine="${e}" aria-pressed="${state.on[state.set].has(e)}"><i></i>${d.label}</button>`;
    }).join("");
    for (const b of document.querySelectorAll(".b-key")) {
      b.addEventListener("click", () => {
        const on = state.on[state.set];
        const e = b.dataset.engine;
        if (on.has(e)) { if (on.size > 1) on.delete(e); } else on.add(e);
        legend();
        board();
      });
    }
  }

  // --- The chart
  function board() {
    const s = data.sets[state.set];
    const order = s.engines.filter((e) => state.on[state.set].has(e));
    let maxR = 1;
    for (const p of data.programs) for (const e of order) {
      const t = s.times[p.key]?.[e], c = s.times[p.key]?.c;
      if (typeof t === "number" && c) maxR = Math.max(maxR, t / c);
    }
    const el = $("#b-board");
    hideTip();
    el.innerHTML = data.programs.map((p) => {
      const times = s.times[p.key] || {};
      const c = times.c;
      const maxT = Math.max(...order.map((e) => (typeof times[e] === "number" ? times[e] : 0)));
      const rows = order.map((e) => {
        const t = times[e];
        const d = data.engines[e];
        if (typeof t !== "number") return `<div class="b-bar ${d.tone}"><span class="b-name">${d.label}</span><span class="b-track"><span class="b-miss">did not run</span></span><span class="b-val">–</span></div>`;
        const r = t / c;
        const w = state.view === "ratio" ? 2 + 98 * Math.log(1 + r) / Math.log(1 + maxR) : 2 + 98 * t / maxT;
        const val = state.view === "ratio" ? (r < 10 ? r.toFixed(2) : Math.round(r)) + "×" : fmtS(t);
        const best = e !== "c" && r < 0.995;
        return `<div class="b-bar ${d.tone}${r < 0.995 ? " faster" : ""}" tabindex="0" data-tip="<b>${d.label}</b><span>${d.about}</span><em>${fmtS(t)} · ${fmtR(r)}</em>">
          <span class="b-name">${d.label}</span><span class="b-track"><span class="b-fill" style="--w:${w.toFixed(1)}%"></span></span><span class="b-val">${val}${best ? '<i class="b-best">beats C</i>' : ""}</span></div>`;
      }).join("");
      const cline = state.view === "ratio" ? `<span class="b-cline" style="--x:${(2 + 98 * Math.log(2) / Math.log(1 + maxR)).toFixed(1)}%" aria-hidden="true"></span>` : "";
      return `<article class="b-prog"><header><h3>${p.title}</h3><code>${p.key}</code><p>${p.about}</p></header><div class="b-bars">${cline}${rows}</div></article>`;
    }).join("");
    $("#b-note").innerHTML = state.view === "ratio"
      ? "Bars show how many times the time of C, on a scale that grows slowly, so 1× (the dashed line) and 1000× both fit. Shorter is faster."
      : "Bars show seconds, each program on its own scale. Shorter is faster.";
    for (const b of el.querySelectorAll("[data-tip]")) {
      b.addEventListener("mouseenter", () => showTip(b, b.dataset.tip));
      b.addEventListener("focus", () => showTip(b, b.dataset.tip));
      b.addEventListener("mouseleave", hideTip);
      b.addEventListener("blur", hideTip);
    }
    grow(el);
  }

  // Bars grow in when the chart is first seen, and on every change after.
  let seen = still || !("IntersectionObserver" in window);
  function grow(el) {
    if (!seen) return;
    for (const f of el.querySelectorAll(".b-fill")) f.classList.remove("grown");
    requestAnimationFrame(() => requestAnimationFrame(() => {
      for (const f of el.querySelectorAll(".b-fill")) f.classList.add("grown");
    }));
  }
  if (!seen) {
    new IntersectionObserver(([en], o) => { if (en.isIntersecting) { seen = true; grow($("#b-board")); o.disconnect(); } }, { threshold: 0.15 }).observe($("#b-board"));
  }

  // --- Controls
  for (const b of document.querySelectorAll("#b-set [data-set]")) {
    b.addEventListener("click", () => { state.set = b.dataset.set; $("#b-board").setAttribute("aria-labelledby", b.id); legend(); board(); });
  }
  for (const b of document.querySelectorAll("[data-view]")) {
    b.addEventListener("click", () => {
      state.view = b.dataset.view;
      for (const x of document.querySelectorAll("[data-view]")) x.setAttribute("aria-pressed", x === b);
      board();
    });
  }

  // --- Before and after
  const comp = data.sets.compiled.times;
  function ba() {
    const v = $("#b-slide").value / 100;
    $("#b-ba").innerHTML = data.programs.map((p) => {
      const before = data.before[p.key]?.zeno, now = comp[p.key]?.["zeno-owned"], c = comp[p.key]?.c;
      if (!before || !now) return "";
      const t = before + (now - before) * v;
      const max = Math.max(before, now, c) * 1.05;
      return `<div class="b-ba-row"><span class="b-name">${p.title}</span><span class="b-track"><span class="b-ba-fill" style="width:${(100 * t / max).toFixed(1)}%"></span><span class="b-ba-c" style="left:${(100 * c / max).toFixed(1)}%" title="C: ${fmtS(c)}"></span></span><span class="b-val">${fmtS(t)}</span></div>`;
    }).join("") + `<p class="b-ba-key"><i class="b-ba-sw"></i>Zeno <span>${v < 0.5 ? "before" : "now, owned"}</span><i class="b-ba-csw"></i>C</p>`;
  }
  $("#b-slide").addEventListener("input", ba);

  // --- Speed of each way to run
  const inter = data.sets.interpreted.times;
  const speedOf = (times, e) => geo(data.programs.filter((p) => times[p.key]?.[e] && times[p.key]?.c).map((p) => times[p.key][e] / times[p.key].c));
  for (const el of document.querySelectorAll("[data-mode]")) {
    const e = el.dataset.mode;
    const r = e === "run" || e === "vm" ? speedOf(inter, e) : speedOf(comp, e);
    el.textContent = `about ${r < 10 ? r.toFixed(1) : Math.round(r)}× the time of C`;
    el.style.setProperty("--s", Math.min(100, 8 + 92 * Math.log(r) / Math.log(600)).toFixed(0) + "%");
  }

  // --- Headline numbers count up once
  const counters = document.querySelectorAll("[data-count]");
  if (!still && "IntersectionObserver" in window) {
    for (const el of counters) {
      const to = parseFloat(el.dataset.count), dp = (el.dataset.count.split(".")[1] || "").length;
      el.textContent = (0).toFixed(dp);
      new IntersectionObserver(([en], o) => {
        if (!en.isIntersecting) return;
        o.disconnect();
        const t0 = performance.now();
        const step = (now) => {
          const k = Math.min(1, (now - t0) / 1100), e = 1 - Math.pow(1 - k, 3);
          el.textContent = (to * e).toFixed(dp);
          if (k < 1) requestAnimationFrame(step);
        };
        requestAnimationFrame(step);
      }).observe(el);
    }
  }

  legend();
  board();
  ba();
})();
