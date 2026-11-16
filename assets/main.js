// zeno-lang.org. No libraries: a highlighter for Zeno, the hero, the tabs,
// the simulated board, the compiler diagram, the theme switch, and the two
// places where Zeno's paradox shows: the top bar and the runner in the footer.

const still = matchMedia("(prefers-reduced-motion: reduce)").matches;

// --- Highlighting -----------------------------------------------------------

const KEYWORDS = "let var const function return if else for in while match case enum class try except raise raises as and or not is none true false from import owned take self continue break unsafe";
const TYPES = "int float str bool list u8 u16 u32 i8 i16 i32 ms V pointer";
const TOKEN = new RegExp([
  "(#.*$)",                                            // 1 comment
  '(f?"(?:[^"\\\\]|\\\\.)*")',                         // 2 text
  "\\b(0x[0-9A-Fa-f]+|0b[01]+|\\d+(?:\\.\\d+)?(?: (?:ms|V)\\b)?)", // 3 number, with its unit
  "\\b(" + KEYWORDS.split(" ").join("|") + ")\\b",     // 4 keyword
  "\\b(" + TYPES.split(" ").join("|") + "|[A-Z][A-Za-z0-9]*)\\b", // 5 type or class
  "\\b([a-z_][a-z0-9_]*)(?=\\()",                      // 6 a name being called
].join("|"), "gm");
const KINDS = [null, "com", "str", "num", "key", "type", "fn"];

const escape = (text) => text.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");

function highlight(source) {
  let html = "", last = 0;
  for (const m of source.matchAll(TOKEN)) {
    const kind = KINDS[m.findIndex((group, i) => i > 0 && group !== undefined)];
    html += escape(source.slice(last, m.index)) + `<span class="t-${kind}">${escape(m[0])}</span>`;
    last = m.index + m[0].length;
  }
  return html + escape(source.slice(last));
}

for (const code of document.querySelectorAll("code.zeno, code.language-zeno")) code.innerHTML = highlight(code.textContent);

// In printed output, make the compiler's error line and its pointer stand out.
for (const code of document.querySelectorAll("pre.out code")) {
  code.innerHTML = code.textContent.split("\n").map((line) => {
    if (line.startsWith("error:")) return `<span class="err">${escape(line)}</span>`;
    if (/^\s*\|\s*\^/.test(line)) return `<span class="mark-line">${escape(line)}</span>`;
    return escape(line);
  }).join("\n");
}

// --- The hero: a line of C-style code loses its punctuation ------------------

const hero = document.querySelector(".hero");
const morph = document.getElementById("morph");
if (hero) requestAnimationFrame(() => hero.classList.add("ready"));

if (morph) {
  const code = document.getElementById("morph-code");
  const start = code.innerHTML;
  const counters = { sym: document.getElementById("n-sym"), word: document.getElementById("n-word"), char: document.getElementById("n-char") };
  let timers = [];

  const visibleLength = () => [...code.childNodes].reduce((n, node) => {
    if (node.nodeType === 3) return n + node.textContent.length;
    if (node.classList.contains("s")) return n + (node.classList.contains("off") ? 0 : node.textContent.length);
    if (node.classList.contains("w")) return n + (node.classList.contains("on") ? node.textContent.length : 0);
    return n + node.textContent.length;
  }, 0);

  function count(sym, word) {
    counters.sym.textContent = sym;
    counters.word.textContent = word;
    counters.char.textContent = visibleLength();
  }

  function finish() {
    document.getElementById("lang-c").classList.remove("on");
    document.getElementById("lang-z").classList.add("on");
    const zeno = [...code.childNodes].map((node) => {
      if (node.nodeType === 3) return node.textContent;
      if (node.classList.contains("s")) return "";
      return node.textContent;
    }).join("");
    code.innerHTML = highlight(zeno);
    code.classList.add("zeno");
  }

  function play() {
    timers.forEach(clearTimeout);
    timers = [];
    code.innerHTML = start;
    code.classList.remove("zeno");
    document.getElementById("lang-c").classList.add("on");
    document.getElementById("lang-z").classList.remove("on");
    const steps = [...new Set([...code.querySelectorAll("[data-step]")].map((el) => el.dataset.step))].sort();
    let sym = 0, word = 0;
    count(0, 0);
    if (still) {
      for (const el of code.querySelectorAll(".s")) { el.classList.add("off"); if (!el.classList.contains("long")) sym++; }
      for (const el of code.querySelectorAll(".w")) { el.classList.add("on"); word++; }
      count(sym, word);
      finish();
      return;
    }
    steps.forEach((step, i) => {
      timers.push(setTimeout(() => {
        for (const el of code.querySelectorAll(`[data-step="${step}"]`)) {
          if (el.classList.contains("s")) {
            el.style.setProperty("--r", (Math.random() * 50 - 25).toFixed(0) + "deg");
            el.classList.add("off");
            if (!el.classList.contains("long")) sym++;
          } else {
            el.classList.add("on");
            word++;
          }
        }
        count(sym, word);
      }, 1400 + i * 520));
    });
    timers.push(setTimeout(() => { count(sym, word); finish(); }, 1400 + steps.length * 520 + 700));
  }

  count(0, 0);
  document.getElementById("replay").addEventListener("click", play);
  play();
}

// --- Tabs: the tour and the four styles -------------------------------------
// A white thumb slides under the chosen tab, so the eye follows the change.

for (const group of document.querySelectorAll(".segmented[role=tablist]")) {
  const tabs = [...group.querySelectorAll('[role="tab"]')];
  const thumb = document.createElement("span");
  thumb.className = "thumb";
  thumb.setAttribute("aria-hidden", "true");
  group.prepend(thumb);
  const vertical = () => getComputedStyle(group).flexDirection === "column";

  function place(tab) {
    if (vertical()) {
      thumb.style.width = "";
      thumb.style.height = tab.offsetHeight + "px";
      thumb.style.transform = `translateY(${tab.offsetTop}px)`;
    } else {
      thumb.style.height = "";
      thumb.style.width = tab.offsetWidth + "px";
      thumb.style.transform = `translateX(${tab.offsetLeft}px)`;
    }
  }

  function select(tab, focus) {
    for (const other of tabs) {
      const on = other === tab;
      other.setAttribute("aria-selected", on);
      other.tabIndex = on ? 0 : -1;
      const panel = document.getElementById(other.getAttribute("aria-controls"));
      panel.hidden = !on;
      panel.classList.toggle("show", on);
    }
    place(tab);
    if (focus) tab.focus();
    tab.scrollIntoView({ block: "nearest", inline: "nearest", behavior: still ? "auto" : "smooth" });
  }

  tabs.forEach((tab, i) => {
    tab.addEventListener("click", () => select(tab));
    tab.addEventListener("keydown", (event) => {
      const step = { ArrowRight: 1, ArrowDown: 1, ArrowLeft: -1, ArrowUp: -1 }[event.key];
      if (!step) return;
      event.preventDefault();
      select(tabs[(i + step + tabs.length) % tabs.length], true);
    });
  });
  const current = () => tabs.find((t) => t.getAttribute("aria-selected") === "true") || tabs[0];
  place(current());
  addEventListener("resize", () => place(current()));
  document.fonts?.ready.then(() => place(current()));
}

// --- The simulated board ----------------------------------------------------
// The same state machine as examples/signal.zeno: red 40 ms, green 30 ms,
// amber 10 ms, shown 25 times slower. It runs only while it can be seen.

const log = document.querySelector("#log code");
if (log) {
  const lamp = (name) => document.getElementById("lamp-" + name);
  const LIGHTS = [{ pin: 2, hold: 40 }, { pin: 4, hold: 30 }, { pin: 3, hold: 10 }];
  const lines = ["pin 2 on", "led on"];
  let light = 0, led = true, timer = null;

  function set(name, on) {
    lamp(name).classList.toggle("on", on);
    lines.push(`${name === "led" ? "led" : "pin " + name} ${on ? "on" : "off"}`);
    log.textContent = lines.slice(-14).join("\n");
  }

  function step() {
    set(LIGHTS[light].pin, false);
    light = (light + 1) % LIGHTS.length;
    set(LIGHTS[light].pin, true);
    led = !led;
    set("led", led);
    timer = setTimeout(step, LIGHTS[light].hold * 25);
  }

  lamp(2).classList.add("on");
  lamp("led").classList.add("on");
  if (!still && "IntersectionObserver" in window) {
    new IntersectionObserver(([entry]) => {
      if (entry.isIntersecting && !timer) timer = setTimeout(step, 600);
      if (!entry.isIntersecting && timer) { clearTimeout(timer); timer = null; }
    }).observe(document.querySelector(".device"));
  }
}

// --- The compiler diagram ---------------------------------------------------
// Lines join each stage to the next, and the checker to every engine. A dot
// of light runs along them: the path a program takes.

const diagram = document.getElementById("diagram");
if (diagram) {
  const svg = diagram.querySelector("svg.lines");
  function draw() {
    const box = diagram.getBoundingClientRect();
    const stages = [...diagram.querySelectorAll(".stages .node")].map((n) => n.getBoundingClientRect());
    const engines = [...diagram.querySelectorAll(".engines .node")].map((n) => n.getBoundingClientRect());
    if (!stages.length || getComputedStyle(svg).display === "none") return;
    const x = (v) => (v - box.left).toFixed(1), y = (v) => (v - box.top).toFixed(1);
    const paths = [];
    for (let i = 0; i + 1 < stages.length; i++) {
      const a = stages[i], b = stages[i + 1], mid = a.top + a.height / 2;
      paths.push(`M${x(a.right)} ${y(mid)}H${x(b.left)}`);
    }
    const c = stages[stages.length - 1];
    const fromX = c.left + c.width / 2, fromY = c.bottom, gap = (engines[0].top - c.bottom) / 2;
    for (const e of engines) {
      const toX = e.left + e.width / 2;
      paths.push(`M${x(fromX)} ${y(fromY)}V${y(fromY + gap)}H${x(toX)}V${y(e.top)}`);
    }
    svg.innerHTML = paths.map((d) => `<path d="${d}"/>`).join("") +
      (still ? "" : paths.map((d, i) => `<path class="pulse" d="${d}" style="animation-delay:${(i * 0.45).toFixed(2)}s"/>`).join(""));
  }
  draw();
  addEventListener("resize", draw);
  document.fonts?.ready.then(draw);
}

// --- Copy buttons -------------------------------------------------------------

for (const button of document.querySelectorAll("[data-copy]")) {
  button.addEventListener("click", async () => {
    const label = button.querySelector("span") || button;
    try {
      await navigator.clipboard.writeText(document.getElementById(button.dataset.copy).textContent);
      label.textContent = "Copied";
    } catch (e) {
      label.textContent = "Select and copy";
    }
    setTimeout(() => (label.textContent = "Copy"), 1600);
  });
}

// --- Theme ------------------------------------------------------------------

document.getElementById("theme")?.addEventListener("click", () => {
  const root = document.documentElement;
  const dark = root.dataset.theme ? root.dataset.theme === "dark" : matchMedia("(prefers-color-scheme: dark)").matches;
  root.dataset.theme = dark ? "light" : "dark";
  try { localStorage.setItem("theme", root.dataset.theme); } catch (e) {}
});

// --- The bar that never arrives ----------------------------------------------
// Scrolling to the end closes seven halvings: 1/2, 3/4, 7/8 ... 127/128.

const bar = document.getElementById("progress");
function progress() {
  const room = document.documentElement.scrollHeight - innerHeight;
  const done = room > 0 ? scrollY / room : 0;
  bar.style.width = (1 - Math.pow(2, -7 * done)) * 100 + "%";
}
addEventListener("scroll", progress, { passive: true });
addEventListener("resize", progress);
progress();

// --- The runner who never reaches the tortoise -------------------------------
// Each second the runner covers half of what is left. The counter keeps the
// score; the gap never closes.

const runner = document.getElementById("runner");
if (runner) {
  const counter = document.getElementById("chase-count");
  const chase = document.querySelector(".chase"), tortoise = chase.querySelector(".tortoise");
  let halves = 0, timer = null;
  const place = () => {
    // The goal is the tortoise's tail, less the runner's own half width.
    const goal = (chase.clientWidth - tortoise.getBoundingClientRect().width - 10) / chase.clientWidth * 100;
    runner.style.left = (goal - goal / Math.pow(2, halves)).toFixed(4) + "%";
    const gap = 1 / Math.pow(2, halves);
    counter.textContent = halves === 0 ? "Watch the runner"
      : `${halves} ${halves === 1 ? "half" : "halves"} closed, ${gap < 0.0001 ? gap.toExponential(1) : gap.toFixed(4).replace(/0+$/, "")} of the way still to go`;
  };
  addEventListener("resize", place);
  const tick = () => { halves++; place(); if (halves >= 40) { clearInterval(timer); timer = null; } };
  place();
  if (!still && "IntersectionObserver" in window) {
    new IntersectionObserver(([entry]) => {
      if (entry.isIntersecting && !timer && halves < 40) timer = setInterval(tick, 1100);
      if (!entry.isIntersecting && timer) { clearInterval(timer); timer = null; }
    }).observe(chase);
  } else if (still) {
    halves = 10; place();
  }
}

// --- Contents that follow the reader -----------------------------------------
// In a page's table of contents, mark the section being read.

const tocLinks = [...document.querySelectorAll(".doc-toc a, .decisions-nav a, .learn-toc a")];
if (tocLinks.length && "IntersectionObserver" in window) {
  const byId = new Map(tocLinks.map((a) => [decodeURIComponent(a.hash.slice(1)), a]));
  const seen = new Set();
  const watch = new IntersectionObserver((entries) => {
    for (const e of entries) e.isIntersecting ? seen.add(e.target.id) : seen.delete(e.target.id);
    const first = [...byId.keys()].find((id) => seen.has(id));
    if (!first) return;
    for (const a of tocLinks) a.classList.toggle("on", a === byId.get(first));
  }, { rootMargin: "-15% 0px -70% 0px" });
  for (const id of byId.keys()) {
    const el = document.getElementById(id);
    if (el) watch.observe(el);
  }
}

// --- Download -------------------------------------------------------------------
// Find the visitor's system, mark its card, and point the big button at it.

if (document.getElementById("systems")) {
  const ua = navigator.userAgent;
  const plat = (navigator.userAgentData && navigator.userAgentData.platform) || navigator.platform || "";
  const mobile = /Android|iPhone|iPad|iPod/i.test(ua);
  const os = mobile ? null : /Win/i.test(plat + ua) ? "windows" : /Mac/i.test(plat + ua) ? "macos" : /Linux|X11|CrOS/i.test(plat + ua) ? "linux" : null;
  const primary = document.getElementById("dl-primary");
  const note = document.getElementById("dl-note");
  if (os) {
    const card = document.querySelector(`.dl-card[data-os="${os}"]`);
    card.classList.add("yours");
    const first = card.querySelector(".dl-big");
    const names = { windows: "Windows", macos: "macOS", linux: "Linux" };
    if (os === "linux") {
      primary.href = "#terminal";
      primary.querySelector("span").textContent = "Install on Linux";
      note.textContent = "One line in a terminal, or a .deb, snap, flatpak or archive below.";
    } else if (first) {
      primary.href = first.href;
      primary.querySelector("span").textContent = `Download for ${names[os]}`;
      note.textContent = os === "macos" ? "For Apple silicon. Intel Macs, Homebrew and the one-line installer are below."
                                        : "The setup program, for every Windows PC. The .zip files are below.";
    }
    if (window.matchMedia("(max-width: 60rem)").matches) card.parentNode.prepend(card);
  } else if (mobile) {
    note.textContent = "Zeno runs on Windows, macOS and Linux. On a phone, try it in the playground.";
  }
  // A link to a tab of the terminal section opens that tab.
  for (const link of document.querySelectorAll("[data-tab]")) {
    link.addEventListener("click", () => document.getElementById(link.dataset.tab)?.click());
  }
  // Copy a file's SHA-256.
  for (const b of document.querySelectorAll(".sha")) {
    b.addEventListener("click", async () => {
      const shown = b.textContent;
      try { await navigator.clipboard.writeText(b.dataset.sha); b.textContent = "Copied"; } catch (e) { b.textContent = b.dataset.sha; return; }
      setTimeout(() => (b.textContent = shown), 1400);
    });
  }
}
