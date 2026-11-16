// The benchmarks page: charts drawn from the JSON in #b-data.
(() => {
  const data = JSON.parse(document.getElementById("b-data").textContent);
  const $ = (s, r = document) => r.querySelector(s);
  const still = false; // see main.js: the small animations always play
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

  // --- Version by version
  // Each cell: a version's time over C's time in the same record (or
  // Python's, for the ways that interpret). "Fastest build" takes the
  // quickest compiled engine that version had.
  const BUILDS = ["zeno", "zeno-llvm", "zeno-nc", "zeno-release", "zeno-owned"];
  const VER = {
    zeno: { size: "big", base: "c", baseName: "C", pick: (t) => t.zeno },
    best: { size: "big", base: "c", baseName: "C", pick: (t) => Math.min(...BUILDS.map((e) => t[e]).filter((x) => typeof x === "number")) },
    vm: { size: "small", base: "python", baseName: "Python", pick: (t) => t.vm },
    run: { size: "small", base: "python", baseName: "Python", pick: (t) => t.run },
  };
  let verMode = "zeno";
  function versions() {
    const el = $("#b-vers");
    if (!el || !data.versions?.length) return;
    const m = VER[verMode];
    const cell = (v, p) => {
      const t = v[m.size]?.[p.key];
      if (!t || !t[m.base]) return null;
      const x = m.pick(t);
      return typeof x === "number" && isFinite(x) ? x / t[m.base] : null;
    };
    const rows = data.versions.map((v) => {
      const rs = data.programs.map((p) => cell(v, p));
      const have = rs.filter((r) => r !== null);
      return { v, rs, mean: have.length ? geo(have) : null };
    });
    const all = rows.flatMap((r) => [...r.rs, r.mean]).filter((r) => r !== null);
    const hi = Math.max(2, ...all);
    const fmt = (r) => (r < 10 ? r.toFixed(2) : Math.round(r)) + "×";
    const shade = (r) => Math.min(1, Math.log(Math.max(r, 0.25) / 0.25) / Math.log(hi / 0.25));
    const td = (r, prev, label) => {
      if (r === null) return `<td class="b-v-miss" title="This version could not run it this way">–</td>`;
      const d = prev ? r / prev : 1;
      const move = prev && d < 0.87 ? `<i class="b-v-up">${(1 / d).toFixed(1)}× faster</i>` : prev && d > 1.15 ? `<i class="b-v-down">${d.toFixed(1)}× slower</i>` : "";
      return `<td style="--h:${shade(r).toFixed(2)}" title="${label}: ${fmt(r)} the time of ${m.baseName}">${fmt(r)}${move}</td>`;
    };
    el.innerHTML = `<table class="b-v-table"><thead><tr><th scope="col">Version</th>${data.programs.map((p) => `<th scope="col">${p.title}</th>`).join("")}<th scope="col">All six</th></tr></thead><tbody>` +
      rows.map((row, i) => {
        const prev = i ? rows[i - 1] : null;
        return `<tr><th scope="row"><b>${row.v.version}</b><small>${row.v.released ? "released" : "main, not released yet"}</small></th>` +
          row.rs.map((r, j) => td(r, prev?.rs[j], data.programs[j].title)).join("") + td(row.mean, prev?.mean, "All six (geometric mean)") + "</tr>";
      }).join("") + "</tbody></table>";
    $("#b-vers-note").textContent = `Times ${m.baseName}'s time, at the ${m.size === "big" ? "full" : "small"} sizes. Darker is slower; "faster" and "slower" compare a version with the one above it, when the change is more than the 15 % that times move by from run to run.`;
  }
  for (const b of document.querySelectorAll("[data-ver]")) {
    b.addEventListener("click", () => { verMode = b.dataset.ver; $("#b-vers").hidden = false; versions(); });
  }

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
  versions();
})();
