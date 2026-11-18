// The packages page: the list of the registry, a box that searches it, and
// the page of one package.
//
// The page carries the list as it was when the site was built, so it shows
// something at once. Then the list is read again from the registry itself
// (github.com/zeno-src/packages, the file index.json), so a package that was
// published a minute ago is here without the site being built again.
//
// What is shown is in the address: /packages/ is the list, ?q=words is a
// search, ?p=name is one package. So the back button works, and an address
// can be sent to somebody.
//
// Everything in the list was written by whoever published a package, so it
// is only ever put on the page as text, and an address becomes a link only
// if it begins https://.
//
// The whole of it is inside one function, so that its names are its own:
// main.js, on the same page, has a `count` too.

(() => {
  const LIVE = "https://raw.githubusercontent.com/zeno-src/packages/main/index.json";

  const by = (id) => document.getElementById(id);
  const all = by("pk-all");
  const one = by("pk-one");
  const list = by("pk-list");
  const box = by("pk-search");
  const count = by("pk-count");
  const sort = by("pk-sort");
  let packages = [];

  function el(tag, cls, text) {
    const node = document.createElement(tag);
    if (cls) node.className = cls;
    if (text != null) node.textContent = text;
    return node;
  }

  // "18 November 2026", from "2026-11-18".
  function day(dated) {
    const at = new Date(dated + "T00:00:00Z");
    if (isNaN(at)) return String(dated || "");
    return at.toLocaleDateString("en-GB", { day: "numeric", month: "long", year: "numeric", timeZone: "UTC" });
  }

  const versions = (pkg) => (Array.isArray(pkg.versions) ? pkg.versions.filter((v) => v && typeof v.version === "string") : []);
  const newest = (pkg) => versions(pkg)[versions(pkg).length - 1];
  const needs = (pkg, version) => `needs ${pkg.name} at "${version}"`;

  // The address of a repository as a link, or as plain text if it is not
  // one a browser should follow.
  function address(text, shown) {
    const to = String(text || "");
    if (!to.startsWith("https://")) return el("span", null, shown || to);
    const link = el("a", null, shown || to.replace(/^https:\/\//, "").replace(/\.git$/, ""));
    link.href = to;
    link.rel = "noopener";
    return link;
  }

  function copier(button, line) {
    button.onclick = async () => {
      try {
        await navigator.clipboard.writeText(line());
        button.textContent = "Copied";
      } catch (e) {
        button.textContent = "Select and copy";
      }
      setTimeout(() => (button.textContent = "Copy"), 1600);
    };
  }

  // --- The address ----------------------------------------------------------

  const asked = () => new URLSearchParams(location.search);

  function go(params, replace) {
    const query = new URLSearchParams(params).toString();
    const to = location.pathname + (query ? "?" + query : "");
    if (replace) history.replaceState(null, "", to);
    else history.pushState(null, "", to);
  }

  // --- The list -------------------------------------------------------------

  function row(pkg) {
    const last = newest(pkg);
    const item = el("li", "pk-item");
    const head = el("div", "pk-head");
    const name = el("a", "pk-name", pkg.name);
    name.href = "?p=" + encodeURIComponent(pkg.name);
    name.addEventListener("click", (event) => {
      if (event.metaKey || event.ctrlKey || event.shiftKey || event.button) return;
      event.preventDefault();
      go({ p: pkg.name });
      show();
      scrollTo({ top: 0 });
    });
    head.append(el("h3", null), el("span", "pk-version", last.version));
    head.firstChild.append(name);
    item.append(head, el("p", "pk-about", pkg.about));

    const need = el("div", "pk-need");
    const copy = el("button", "pk-copy", "Copy");
    copy.type = "button";
    copier(copy, () => needs(pkg, last.version));
    need.append(el("code", null, needs(pkg, last.version)), copy);
    item.append(need);

    const facts = el("p", "pk-facts");
    facts.append(address(pkg.repository), el("span", null, `by ${pkg.owner}`), el("span", null, day(last.dated)));
    item.append(facts);
    return item;
  }

  function showList() {
    const words = box.value.toLowerCase().split(/\s+/).filter(Boolean);
    const found = packages.filter((pkg) => {
      const text = `${pkg.name} ${pkg.about}`.toLowerCase();
      return words.every((word) => text.includes(word));
    });
    if (sort.value === "new") found.sort((a, b) => String(newest(b).dated).localeCompare(String(newest(a).dated)) || a.name.localeCompare(b.name));
    else found.sort((a, b) => a.name.localeCompare(b.name));
    list.replaceChildren(...found.map(row));
    const total = packages.length;
    const some = (n) => (n === 1 ? "1 package" : `${n} packages`);
    by("pk-empty").hidden = total !== 0;
    by("pk-sort-box").hidden = total < 2;
    count.textContent = !total ? "" : !words.length ? some(total) : found.length ? `${some(found.length)} of ${total}` : `No package has “${box.value.trim()}” in its name or in what it says it is for.`;
  }

  // --- One package ----------------------------------------------------------

  function showOne(name) {
    const pkg = packages.find((p) => p.name === name);
    by("pk-one-name").textContent = name;
    by("pk-one-body").hidden = !pkg;
    by("pk-one-version").hidden = !pkg;
    if (!pkg) {
      by("pk-one-about").textContent = "There is no package of this name in the registry.";
      return;
    }
    const last = newest(pkg);
    by("pk-one-version").textContent = last.version;
    by("pk-one-about").textContent = pkg.about;
    by("pk-one-line").textContent = needs(pkg, last.version);
    copier(by("pk-one-copy"), () => by("pk-one-line").textContent);
    by("pk-one-repository").replaceChildren(address(pkg.repository));
    by("pk-one-owner").textContent = pkg.owner;
    by("pk-one-dated").textContent = `${last.version}, ${day(last.dated)}`;

    const repository = String(pkg.repository || "").replace(/\.git$/, "");
    const rows = versions(pkg).slice().reverse().map((v) => {
      const tr = el("tr");
      const commit = String(v.commit || "");
      const short = el("code", null, commit.slice(0, 10));
      const cell = el("td");
      // On GitHub a commit has a page of its own.
      if (repository.startsWith("https://github.com/") && /^[0-9a-f]{7,64}$/.test(commit)) {
        const link = address(`${repository}/tree/${commit}`, " ");
        link.replaceChildren(short);
        cell.append(link);
      } else {
        cell.append(short);
      }
      tr.append(el("td", "pk-v", v.version), el("td", null, day(v.dated)), cell);
      return tr;
    });
    by("pk-one-versions").replaceChildren(...rows);
  }

  // --- Which of the two -----------------------------------------------------

  function show() {
    const name = asked().get("p");
    // The page of one package has the package's name as its heading.
    const head = document.querySelector(".page-head");
    if (head) head.hidden = name != null;
    all.hidden = name != null;
    one.hidden = name == null;
    if (name != null) {
      showOne(name);
      document.title = `${name} · Packages · Zeno`;
    } else {
      box.value = asked().get("q") || "";
      showList();
      document.title = "Packages · Zeno";
    }
  }

  function take(data) {
    if (!data || !Array.isArray(data.packages)) return;
    packages = data.packages.filter((pkg) => pkg && typeof pkg.name === "string" && versions(pkg).length);
    show();
  }

  box.addEventListener("input", () => {
    const query = box.value.trim();
    go(query ? { q: query } : {}, true);
    showList();
  });
  sort.addEventListener("change", showList);
  by("pk-back").addEventListener("click", (event) => {
    if (event.metaKey || event.ctrlKey || event.shiftKey || event.button) return;
    event.preventDefault();
    go({});
    show();
  });
  addEventListener("popstate", show);

  try {
    take(JSON.parse(by("pk-data").textContent));
  } catch (e) {}
  fetch(LIVE, { cache: "no-cache" })
    .then((answer) => (answer.ok ? answer.json() : null))
    .then(take)
    .catch(() => {});
})();
