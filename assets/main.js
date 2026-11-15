// zeno-lang.org. No libraries: a highlighter for Zeno, the tour tabs,
// the simulated board, the theme switch and the bar that never arrives.

// --- Highlighting -----------------------------------------------------------

const KEYWORDS = "let var const function return if else for in while match case enum class try except raise raises as and or not is none true false from import owned borrow self continue break";
const TYPES = "int float str bool list u8 u16 u32 i8 i16 i32 ms V";
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

// --- Tour tabs --------------------------------------------------------------

const tabs = [...document.querySelectorAll('[role="tab"]')];
function select(tab) {
  for (const other of tabs) {
    const on = other === tab;
    other.setAttribute("aria-selected", on);
    other.tabIndex = on ? 0 : -1;
    document.getElementById(other.getAttribute("aria-controls")).hidden = !on;
  }
}
for (const [i, tab] of tabs.entries()) {
  tab.addEventListener("click", () => select(tab));
  tab.addEventListener("keydown", (event) => {
    const step = { ArrowRight: 1, ArrowLeft: -1 }[event.key];
    if (!step) return;
    const next = tabs[(i + step + tabs.length) % tabs.length];
    select(next);
    next.focus();
  });
}

// --- The simulated board ----------------------------------------------------
// The same state machine as examples/signal.zeno: red 40 ms, green 30 ms,
// amber 10 ms, shown 25 times slower.

const log = document.querySelector("#log code");
if (log) {
const lamp = (name) => document.getElementById("lamp-" + name);
const LIGHTS = [{ pin: 2, hold: 40 }, { pin: 4, hold: 30 }, { pin: 3, hold: 10 }];
const lines = ["pin 2 on", "led on"];
let light = 0, led = true;

function set(name, on) {
  lamp(name).classList.toggle("on", on);
  lines.push(`${name === "led" ? "led" : "pin " + name} ${on ? "on" : "off"}`);
  log.textContent = lines.slice(-18).join("\n");
}

function step() {
  set(LIGHTS[light].pin, false);
  light = (light + 1) % LIGHTS.length;
  set(LIGHTS[light].pin, true);
  led = !led;
  set("led", led);
  setTimeout(step, LIGHTS[light].hold * 25);
}

lamp(2).classList.add("on");
lamp("led").classList.add("on");
if (!matchMedia("(prefers-reduced-motion: reduce)").matches) setTimeout(step, 1000);
}

// --- Copy button ------------------------------------------------------------

for (const button of document.querySelectorAll("[data-copy]")) {
  button.addEventListener("click", async () => {
    await navigator.clipboard.writeText(document.getElementById(button.dataset.copy).textContent);
    button.textContent = "Copied";
    setTimeout(() => (button.textContent = "Copy"), 1500);
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
