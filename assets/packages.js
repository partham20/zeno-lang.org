// The packages page: the list of the registry, and a box that searches it.
//
// The page carries the list as it was when the site was built, so it shows
// something at once. Then the list is read again from the registry itself
// (github.com/zeno-src/packages, the file index.json), so a package that was
// published a minute ago is here without the site being built again.
//
// Everything in the list was written by whoever published a package, so it
// is only ever put on the page as text, and an address becomes a link only
// if it begins https://.

// The whole of it is inside one function, so that its names are its own:
// main.js, on the same page, has a `count` too.

(() => {
  const LIVE = "https://raw.githubusercontent.com/zeno-src/packages/main/index.json";

  const list = document.getElementById("pk-list");
  const box = document.getElementById("pk-search");
  const count = document.getElementById("pk-count");
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
    if (isNaN(at)) return dated;
    return at.toLocaleDateString("en-GB", { day: "numeric", month: "long", year: "numeric", timeZone: "UTC" });
  }

  function row(pkg) {
    const versions = pkg.versions || [];
    const newest = versions[versions.length - 1];
    const item = el("li", "pk-item");
    const head = el("div", "pk-head");
    head.append(el("h3", "pk-name", pkg.name), el("span", "pk-version", newest.version));
    item.append(head, el("p", "pk-about", pkg.about));

    const line = `needs ${pkg.name} at "${newest.version}"`;
    const need = el("div", "pk-need");
    const copy = el("button", "pk-copy", "Copy");
    copy.type = "button";
    copy.addEventListener("click", async () => {
      try {
        await navigator.clipboard.writeText(line);
        copy.textContent = "Copied";
      } catch (e) {
        copy.textContent = "Select and copy";
      }
      setTimeout(() => (copy.textContent = "Copy"), 1600);
    });
    need.append(el("code", null, line), copy);
    item.append(need);

    const facts = el("p", "pk-facts");
    const address = String(pkg.repository || "");
    if (address.startsWith("https://")) {
      const link = el("a", null, address.replace(/^https:\/\//, "").replace(/\.git$/, ""));
      link.href = address;
      link.rel = "noopener";
      facts.append(link);
    } else {
      facts.append(el("span", null, address));
    }
    facts.append(el("span", null, `published by ${pkg.owner}`), el("span", null, day(newest.dated)));
    if (versions.length > 1) {
      const older = versions.slice(0, -1).reverse().map((v) => v.version);
      facts.append(el("span", null, "older: " + older.slice(0, 6).join(", ") + (older.length > 6 ? ` and ${older.length - 6} more` : "")));
    }
    item.append(facts);
    return item;
  }

  function show() {
    const words = box.value.toLowerCase().split(/\s+/).filter(Boolean);
    const found = packages.filter((pkg) => {
      const text = `${pkg.name} ${pkg.about}`.toLowerCase();
      return (pkg.versions || []).length && words.every((word) => text.includes(word));
    });
    list.replaceChildren(...found.map(row));
    const all = packages.length;
    const one = (n) => (n === 1 ? "1 package" : `${n} packages`);
    document.getElementById("pk-empty").hidden = all !== 0;
    box.closest(".pk-find").hidden = all === 0;
    count.textContent = !words.length ? one(all) : found.length ? `${one(found.length)} of ${all}` : `No package has “${box.value.trim()}” in its name or in what it says it is for.`;
  }

  function take(data) {
    if (!data || !Array.isArray(data.packages)) return;
    packages = data.packages.filter((pkg) => pkg && typeof pkg.name === "string").sort((a, b) => a.name.localeCompare(b.name));
    show();
  }

  box.addEventListener("input", () => {
    show();
    const query = box.value.trim();
    history.replaceState(null, "", query ? `?q=${encodeURIComponent(query)}` : location.pathname);
  });
  box.value = new URLSearchParams(location.search).get("q") || "";

  try {
    take(JSON.parse(document.getElementById("pk-data").textContent));
  } catch (e) {}
  fetch(LIVE, { cache: "no-cache" })
    .then((answer) => (answer.ok ? answer.json() : null))
    .then(take)
    .catch(() => {});
})();
