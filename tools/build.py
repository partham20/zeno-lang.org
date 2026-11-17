#!/usr/bin/env python3
"""Builds every page of zeno-lang.org.

    python3 tools/build.py --zeno ../zeno-lang

`--zeno` is a checkout of the zeno-lang repository, with the compiler built
(`cargo build --release`). The script:

  * runs every code sample with `zeno run` and puts the real output under it,
  * turns docs/*.md of the language repository into the Docs pages,
  * writes each page as plain HTML at the root of this repository.

The output is committed, so the site itself has no build step: any static
host can serve this folder as it is. Needs Python 3.9+, `markdown` and `pymdown-extensions`.
"""

import argparse
import shutil
import html
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

import markdown

sys.path.insert(0, str(Path(__file__).resolve().parent))
from icons import icon  # noqa: E402

SITE = Path(__file__).resolve().parent.parent
TOOLS = SITE / "tools"
SNIPPETS = TOOLS / "snippets"
GITHUB = "https://github.com/zeno-src/zeno-lang"
ORIGIN = "https://zeno-lang.org"

ARGS = None
PAGES = []          # every path written, for the sitemap


# --- Running Zeno -------------------------------------------------------------

def run_zeno(path, lines=None, typed=None):
    """What `zeno run` prints for a file, errors included, as on a terminal.
    `typed` is what is typed on the keyboard; with none, the keyboard is closed."""
    exe = Path(ARGS.zeno) / "target" / "release" / "zeno"
    try:
        done = subprocess.run([str(exe), "run", path.name], cwd=path.parent,
                              capture_output=True, text=True, timeout=lines and 3 or 30,
                              input=typed if typed is not None else "")
        out = done.stdout + done.stderr
    except subprocess.TimeoutExpired as stopped:
        out = (stopped.stdout or b"").decode() if isinstance(stopped.stdout, bytes) else (stopped.stdout or "")
    out = out.rstrip("\n")
    if lines:
        out = "\n".join(out.split("\n")[:lines])
    return out


def esc(text):
    return html.escape(text, quote=False)


def snippet(name):
    return (SNIPPETS / f"{name}.zeno").read_text().rstrip("\n")


def window(title, code, output=None, out_label="output", lang="zeno"):
    """A code window, and under it what Zeno printed."""
    cls = ' class="zeno"' if lang == "zeno" else ""
    body = f'<figure class="window"><figcaption>{icon("code")}<span class="file">{esc(title)}</span></figcaption>'
    body += f"<pre><code{cls}>{esc(code)}</code></pre>"
    if output is not None:
        body += f'<div class="out-label">{esc(out_label)}</div><pre class="out"><code>{esc(output)}</code></pre>'
    return body + "</figure>"


def sample(name, title=None):
    return window(title or f"{name}.zeno", snippet(name), run_zeno(SNIPPETS / f"{name}.zeno"))


# --- Layout ------------------------------------------------------------------

NAV = [("Learn", "/learn/"), ("Examples", "/examples/"), ("Book", "/book/"), ("Playground", "/playground/"), ("Benchmarks", "/benchmarks/"), ("Docs", "/docs/"),
       ("Decisions", "/decisions/"), ("Roadmap", "/roadmap/"), ("About", "/about/")]

# The wordmark, "Almost": the name in lowercase strokes, and an o whose ring
# stops just short of closing, with a dot where it would meet. Letters take
# the text colour, the dot is cobalt.
MARK = ('<svg class="mark" viewBox="-8 -8 291 82" aria-hidden="true"><g fill="none" stroke="currentColor" stroke-width="15" '
        'stroke-linejoin="miter" stroke-miterlimit="3"><polyline points="0,7.5 50,7.5 0,58.5 50,58.5"/>'
        '<path d="M69.5 33 H120.5 A25.5 25.5 0 1 0 115.09 48.7"/>'
        '<path d="M148.5 66 V0 M148.5 66 V27.5 A20 20 0 0 1 188.5 27.5 V66"/>'
        '<path d="M242 7.5 A25.5 25.5 0 1 1 219.48 21.03"/></g>'
        '<circle class="dot" cx="229.25" cy="10.92" r="7.5"/></svg>')


# Link previews: what a chat or a social site shows when a page is shared.
# Each kind of page has its own card, drawn by tools/og (card.html, render.js).
OG_KINDS = {"/playground/": "playground", "/benchmarks/": "benchmarks", "/book/": "book", "/download/": "download"}
OG_ALT = {
    "home": "Zeno, a programming language: code that reads like what it means.",
    "playground": "The Zeno playground: run Zeno in your browser.",
    "benchmarks": "Zeno benchmarks: the time of six programs against C.",
    "book": "The Zeno Book: the whole language, in one book.",
    "download": "Download Zeno for Windows, macOS and Linux.",
}


def social(path, title, description):
    """The Open Graph and Twitter tags for one page."""
    kind = next((k for prefix, k in OG_KINDS.items() if path.startswith(prefix)), "home")
    image = f"{ORIGIN}/og/{kind}.png"
    t, d, a = html.escape(title), html.escape(description), html.escape(OG_ALT[kind])
    return f"""<meta property="og:site_name" content="Zeno">
<meta property="og:title" content="{t}">
<meta property="og:description" content="{d}">
<meta property="og:type" content="website">
<meta property="og:url" content="{ORIGIN}{path}">
<meta property="og:locale" content="en_GB">
<meta property="og:image" content="{image}">
<meta property="og:image:secure_url" content="{image}">
<meta property="og:image:type" content="image/png">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta property="og:image:alt" content="{a}">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{t}">
<meta name="twitter:description" content="{d}">
<meta name="twitter:image" content="{image}">
<meta name="twitter:image:alt" content="{a}">"""


def add_social(file, path):
    """Put the preview tags into a page this script did not write (the playground, the book)."""
    page = file.read_text()
    if 'property="og:title"' in page:
        return
    title = re.search(r"<title>(.*?)</title>", page, re.S)
    desc = re.search(r'<meta name="description" content="([^"]*)"', page)
    title = html.unescape(title.group(1).strip()) if title else "Zeno"
    desc = html.unescape(desc.group(1)) if desc else "Zeno, a programming language."
    if path.startswith("/book/") and path != "/book/" and "Zeno" not in title:
        title = f"{title} · The Zeno Book"
    tags = social(path, title, desc) + f'\n<link rel="canonical" href="{ORIGIN}{path}">\n'
    if "rel=\"canonical\"" in page:
        tags = social(path, title, desc) + "\n"
    file.write_text(page.replace("</head>", tags + "</head>", 1))


def layout(path, title, description, body, active=None, home=False):
    nav = "".join(
        f'<a href="{href}"{" aria-current=\"page\"" if href == active else ""}>{name}</a>'
        for name, href in NAV)
    full_title = title if home else f"{title} · Zeno"
    page = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(full_title)}</title>
<meta name="description" content="{html.escape(description)}">
{social(path, full_title, description)}
<meta name="theme-color" content="#f7f8fa" media="(prefers-color-scheme: light)">
<meta name="theme-color" content="#0a0a0a" media="(prefers-color-scheme: dark)">
<link rel="canonical" href="{ORIGIN}{path}">
<link rel="icon" href="/favicon.ico" sizes="32x32">
<link rel="icon" href="/favicon.svg" type="image/svg+xml">
<link rel="apple-touch-icon" href="/apple-touch-icon.png">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Hanken+Grotesk:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
<link rel="stylesheet" href="/assets/style.css">
<script>document.documentElement.classList.add("js"); try {{ var t = localStorage.getItem("theme"); if (t) document.documentElement.dataset.theme = t; }} catch (e) {{}}</script>
</head>
<body>
<a class="skip" href="#content">Skip to the content</a>
<div class="progress" aria-hidden="true"><div class="progress-fill" id="progress"></div></div>
<header class="nav">
  <a class="brand" href="/" aria-label="Zeno, home">{MARK}</a>
  <nav aria-label="Main">{nav}</nav>
  <div class="nav-end">
    <button class="theme" id="theme" type="button" aria-label="Switch between light and dark">
      {icon("sun", "icon sun")}{icon("moon", "icon moon")}
    </button>
    <a class="button small ghost nav-gh" href="{GITHUB}">{icon("github")}GitHub</a>
    <a class="button small" href="/download/">{icon("download")}Download</a>
  </div>
</header>
<main id="content"{' class="home"' if home else ''}>
{body}
</main>
<footer class="foot">
<div class="foot-inner">
  <div class="chase" aria-hidden="true">
    <i class="tick" style="left:50%"></i><i class="tick" style="left:75%"></i><i class="tick" style="left:87.5%"></i>
    <span class="runner" id="runner"></span><svg class="tortoise" viewBox="0 44 128 80" aria-hidden="true"><g transform="translate(0 6)"><clipPath id="tortoise-shell"><path d="M10 82 A44 44 0 0 1 98 82 Z"/></clipPath><g fill="var(--signal)" clip-path="url(#tortoise-shell)"><rect x="10" y="30" width="41.5" height="60"/><rect x="56.5" y="30" width="17" height="60"/><rect x="78.5" y="30" width="19.5" height="60"/></g><path fill="currentColor" fill-rule="evenodd" d="M4 91 L12 87 H98 C98 76 104 69 111 69 C118 69 123 74 123 81 C123 90 115 96 106 96 H12 Z M22 96 H40 V106 a4 4 0 0 1 -4 4 H26 a4 4 0 0 1 -4 -4 Z M70 96 H88 V106 a4 4 0 0 1 -4 4 H74 a4 4 0 0 1 -4 -4 Z M113.5 77.2 a2.7 2.7 0 1 0 0.01 0 Z"/></g></svg>
  </div>
  <div class="chase-text"><p>Every journey is halfway done. Forever.</p><span id="chase-count">The runner has closed 0 of 1 halves</span></div>
  <p class="foot-about">Zeno of Elea said Achilles can never catch the tortoise: first he must cover half the distance, then half of what is left, without end. It suits a compiler that will always be almost finished. The bar at the top of each page works the same way.</p>
  <div class="foot-links">
    <div><h4>Learn</h4><a href="/learn/">The guide</a><a href="/download/">Download</a><a href="/examples/">Examples</a><a href="/book/">The Zeno Book</a><a href="/book/zeno-book.pdf">The book as a PDF</a></div>
    <div><h4>Understand</h4><a href="/docs/">How the compiler works</a><a href="/decisions/">Design decisions</a><a href="/roadmap/">Roadmap</a></div>
    <div><h4>Project</h4><a href="/about/">About</a><a href="/privacy/">Privacy</a><a href="{GITHUB}">Source on GitHub</a><a href="mailto:contact@zeno-lang.org">contact@zeno-lang.org</a></div>
  </div>
  <div class="foot-row"><span>Made by Partha</span><span>Plain HTML, no framework, no build step</span></div>
</div>
</footer>
<script src="/assets/main.js"></script>
</body>
</html>
"""
    out = SITE / path.lstrip("/")
    if path.endswith("/"):
        out = out / "index.html"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(page)
    PAGES.append(path)


def page_head(eyebrow, title, lede, ico=None):
    mark = icon(ico) if ico else ""
    return (f'<header class="page-head"><p class="eyebrow">{mark}{eyebrow}</p>'
            f"<h1>{title}</h1><p class=\"lede\">{lede}</p></header>")


# --- Markdown from the language repository -----------------------------------

def md_to_html(text, here="docs"):
    """Markdown to HTML, with links into the language repository made site links."""
    md = markdown.Markdown(extensions=["pymdownx.highlight", "pymdownx.superfences", "tables", "toc", "sane_lists"],
                           extension_configs={"toc": {"permalink": False, "toc_depth": "2-3"},
                                              "pymdownx.highlight": {"use_pygments": False}})
    body = md.convert(text)
    # Code blocks: a block marked zeno, or unmarked and plainly Zeno, gets the
    # Zeno highlighter; a block of compiler messages is shown as output.
    def block(m):
        lang, code = m.group(1) or "", m.group(2)
        plain = html.unescape(code)
        if lang in ("", "zeno") and plain.lstrip().startswith(("error:", "warning:")):
            return f'<pre class="out"><code>{code}</code></pre>'
        if lang == "zeno" or (lang == "" and re.search(r"^\s*(let|var|function|class|enum|print\(|for|if|from|owned|match)\b", plain, re.M)
                              and not re.search(r"[;]\s*$|^\s*#include|^\s*(define|declare|%)", plain, re.M)):
            return f'<pre><code class="zeno">{code}</code></pre>'
        return f"<pre><code>{code}</code></pre>"
    body = re.sub(r'<pre class="highlight"><code(?: class="language-([\w+-]+)")?>(.*?)</code></pre>', block, body, flags=re.S)

    def link(m):
        target = m.group(1)
        if re.match(r"^(https?:|mailto:|#)", target):
            return m.group(0)
        path, _, anchor = target.partition("#")
        anchor = "#" + anchor if anchor else ""
        name = Path(path).name
        if name == "decisions.md":
            return f'href="/decisions/{anchor}"'
        if name.endswith(".md") and (here == "docs" or "docs/" in path):
            if name == "README.md":
                return f'href="{GITHUB}#readme"'
            return f'href="/docs/{name[:-3]}/{anchor}"'
        if name.endswith(".zeno") and (SNIPPET_EXAMPLES / name).exists():
            return f'href="/examples/{name[:-5]}/"'
        if re.search(r"(^|/)examples/[\w-]+/?$", path) and (SNIPPET_EXAMPLES / name / "main.zeno").exists():
            return f'href="/examples/{name}/"'
        clean = re.sub(r"^(\.\./)+", "", path)
        return f'href="{GITHUB}/blob/main/{clean}{anchor}"'

    body = re.sub(r'href="([^"]+)"', link, body)
    return body, md.toc_tokens


def first_heading(text):
    m = re.search(r"^# (.+)$", text, re.M)
    return re.sub(r"[`*]", "", m.group(1)).strip() if m else ""


def first_paragraph(text):
    for block in re.split(r"\n\s*\n", text):
        block = block.strip()
        if block and not block.startswith(("#", "```", "|", "-", ">", "1.")):
            plain = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", block)
            plain = re.sub(r"[`*]", "", plain).replace("\n", " ")
            return plain if len(plain) < 260 else plain[:250].rsplit(" ", 1)[0] + "…"
    return ""


def toc_html(tokens, depth=2):
    items = []
    for t in tokens:
        if t["level"] > 3:
            continue
        sub = toc_html(t["children"], depth) if t["level"] < depth else ""
        items.append(f'<li><a href="#{t["id"]}">{t["name"]}</a>{sub}</li>')
    return f"<ul>{''.join(items)}</ul>" if items else ""


# --- Docs --------------------------------------------------------------------

# Pages about work on main that no release has yet, and the release it is
# coming in. Take an entry out when that version is published.
UNRELEASED = {}


def coming(name):
    version = UNRELEASED.get(name)
    if not version:
        return ""
    return (f'<p class="soon-note"><span class="soon">Coming in {version}</span>'
            f'This is on <a href="{GITHUB}">main</a> and not in a release yet: '
            f'build Zeno from source to try it, or wait for {version}.</p>')

DOC_ICONS = {"The front end": "tree", "The engines": "play", "Memory": "memory",
             "Firmware and hardware": "cpu", "The type system": "copies", "Memory by hand": "key",
             "The standard library": "package", "Programs in many files": "layers", "The web": "globe", "Other languages": "copies", "Tools": "terminal", "The audit and 0.1": "eye",
             "More": "book"}

DOC_GROUPS = [
    ("The front end", "From text to a checked program.",
     ["lexer", "parser", "checker"]),
    ("The engines", "Four ways to run the same program.",
     ["interpreter", "vm", "compiler", "llvm"]),
    ("Memory", "A collector, owners, and a fixed pool.",
     ["memory", "ownership", "no-collector", "pool", "text", "temporaries", "one-owner", "enums-and-none", "functions-and-errors"]),
    ("Firmware and hardware", "Errors as values, pins and clocks, sized numbers.",
     ["firmware", "board", "sized-ints"]),
    ("The type system", "Generics, interfaces and what a module keeps to itself.",
     ["generics", "interfaces", "private"]),
    ("Memory by hand", "Pointers and registers, inside unsafe blocks.",
     ["unsafe"]),
    ("The standard library", "Text, lists, files and input, maths, dictionaries and JSON.",
     ["library", "reading-and-writing", "math", "dict", "json"]),
    ("Programs in many files", "Modules, imports, folders and packages of Zeno code.",
     ["modules"]),
    ("The web", "A program in a web page, built to WebAssembly.",
     ["web", "playground"]),
    ("Other languages", "The program written in JavaScript, TypeScript, Python, PHP, Go, Java, C#, C++, Rust, a web page or WebAssembly.",
     ["targets"]),
    ("Tools", "Installers, packages for apt, Homebrew and the rest, releases, tests, the formatter and the language server.",
     ["install", "packages", "release", "new", "testing", "format", "lsp"]),
    ("The audit and 0.1", "Every feature checked, the gaps real programs found, and what 0.1 holds.",
     ["audit", "gaps", "version-0.1", "found-by-the-book"]),
]


def build_docs():
    docs_dir = Path(ARGS.zeno) / "docs"
    order = [name for _, _, names in DOC_GROUPS for name in names if (docs_dir / f"{name}.md").exists()]
    extra = sorted(p.stem for p in docs_dir.glob("*.md") if p.stem not in order and p.stem != "decisions")
    if extra:
        DOC_GROUPS.append(("More", "Other pages.", extra))
        order += extra
    meta = {}
    for name in order:
        text = (docs_dir / f"{name}.md").read_text()
        meta[name] = (first_heading(text) or name, first_paragraph(text), text)

    def sidebar(current):
        parts = []
        for group, _, names in DOC_GROUPS:
            links = "".join(
                f'<a href="/docs/{n}/"{" aria-current=\"page\"" if n == current else ""}>{esc(meta[n][0])}</a>'
                for n in names if n in meta)
            if links:
                parts.append(f"<h4>{group}</h4>{links}")
        return f'<nav class="doc-nav" aria-label="Docs">{"".join(parts)}</nav>'

    for i, name in enumerate(order):
        title, lede, text = meta[name]
        body_md = re.sub(r"^# .+\n", "", text, count=1)
        body, toc = md_to_html(body_md)
        prev_link = f'<a class="prev" href="/docs/{order[i-1]}/"><span>Previous</span>{esc(meta[order[i-1]][0])}</a>' if i else "<span></span>"
        next_link = f'<a class="next" href="/docs/{order[i+1]}/"><span>Next</span>{esc(meta[order[i+1]][0])}</a>' if i + 1 < len(order) else "<span></span>"
        on_this = f'<aside class="doc-toc"><h4>On this page</h4>{toc_html(toc)}</aside>' if toc else ""
        page = f"""<div class="doc-layout">
{sidebar(name)}
<article class="prose">
  <p class="eyebrow">{icon("book")}<a href="/docs/">Docs</a></p>
  <h1>{esc(title)}</h1>
  {coming(name)}
  {body}
  <p class="source">This page is <a href="{GITHUB}/blob/main/docs/{name}.md">docs/{name}.md</a> in the language repository.</p>
  <nav class="pager" aria-label="Previous and next">{prev_link}{next_link}</nav>
</article>
{on_this}
</div>"""
        layout(f"/docs/{name}/", title, lede or f"{title}, a walkthrough of the Zeno compiler.", page, "/docs/")

    groups = ""
    for group, blurb, names in DOC_GROUPS:
        items = "".join(
            f'<li><a href="/docs/{n}/"><b>{esc(meta[n][0])}</b><span>{esc(meta[n][1])}</span></a></li>'
            for n in names if n in meta)
        groups += (f'<section class="doc-group"><div class="doc-group-head">{icon(DOC_ICONS.get(group, "book"))}'
                   f'<h2>{group}</h2><p>{blurb}</p></div><ul class="index">{items}</ul></section>')
    body = page_head("Docs", "How the compiler works",
                     "Zeno is written in Rust with no dependencies, and each stage has a walkthrough. "
                     "Read them in order to see a language being built, from the first token to LLVM IR. "
                     "Most end with things to try.", "book") + groups
    layout("/docs/", "How the compiler works", "Walkthroughs of every stage of the Zeno compiler, from the lexer to the LLVM backend.", body, "/docs/")


def build_decisions():
    text = (Path(ARGS.zeno) / "docs" / "decisions.md").read_text()
    body_md = re.sub(r"^# .+\n", "", text, count=1)
    body, toc = md_to_html(body_md)
    count = len(re.findall(r"^### ", text, re.M))
    page = f"""<div class="doc-layout wide-toc">
<aside class="doc-nav decisions-nav" aria-label="Decisions">
  <h4>Contents</h4>
  {toc_html(toc, depth=2)}
</aside>
<article class="prose">
  <p class="eyebrow">{icon("scale")}Design decisions</p>
  <h1>Why Zeno is the way it is</h1>
  <p class="lede">Every choice in the language, the reason for it, and what was turned down. {count} decisions so far. Ones marked <em>provisional</em> may still change.</p>
  {body}
  <p class="source">This page is <a href="{GITHUB}/blob/main/docs/decisions.md">docs/decisions.md</a> in the language repository.</p>
</article>
</div>"""
    layout("/decisions/", "Design decisions", "Every design decision in the Zeno language, with the reason for it and the alternatives turned down.", page, "/decisions/")


# --- Examples ----------------------------------------------------------------

SNIPPET_EXAMPLES = Path(".")
FOREVER = {"blink": 24}     # programs that never stop: show their first lines
FIRMWARE = {"signal", "blink", "buffer", "memory", "scheduler", "driver", "packet", "commands", "handlers"}


def example_meta(path):
    lines = path.read_text().split("\n")
    comment = []
    for line in lines:
        if line.startswith("#"):
            comment.append(line[1:].strip())
        else:
            break
    title = comment[0] if comment else path.stem
    title = re.sub(rf"^{re.escape(path.name)}:\s*", "", title)
    title = title[0].upper() + title[1:] if title else path.stem
    title = title.rstrip(".").replace("`", "")
    return title


TYPED = {"logbook": "temp 21.5\ntemp 22.0\nhello\n"}   # keyboard input for programs that read it


def live_page(folder, name):
    """Build examples/<name>.html and .zeno into a page that runs in the browser, if the
    compiler's WebAssembly build is there. Returns True when /examples/<name>/live.html is written."""
    wasm = Path(ARGS.zeno) / "target" / "wasm32-unknown-unknown" / "release" / "zeno.wasm"
    if not (folder / f"{name}.html").exists():
        return False
    if not wasm.exists():
        print(f"  no live page for {name}: cargo build --release --target wasm32-unknown-unknown")
        return False
    zeno = Path(ARGS.zeno) / "target" / "release" / "zeno"
    with tempfile.TemporaryDirectory() as tmp:
        subprocess.run([str(zeno), "build", "--web", str(folder / f"{name}.zeno")], cwd=tmp, check=True,
                       env={**os.environ, "ZENO_WASM": str(wasm)}, capture_output=True)
        dest = SITE / "examples" / name
        dest.mkdir(parents=True, exist_ok=True)
        shutil.copy(Path(tmp) / f"{name}.web.html", dest / "live.html")
    return True


def build_examples():
    folder = Path(ARGS.zeno) / "examples"
    order = ["hello", "tour", "styles", "primes", "shapes", "sensor", "generics", "packet",
             "sentence", "faults", "channels", "instruments", "logbook", "ports", "station", "ring",
             "filters", "thermostat", "commands", "handlers",
             "signal", "blink", "buffer", "memory", "labels", "words", "scheduler", "driver"]
    found = {p.stem for p in folder.glob("*.zeno")} | {p.name for p in folder.iterdir() if (p / "main.zeno").exists()}
    names = [n for n in order if n in found] + sorted(found - set(order))
    label = lambda n: f"{n}/" if (folder / n).is_dir() else f"{n}.zeno"
    cards = ""
    for i, name in enumerate(names):
        many = (folder / name).is_dir()
        path = folder / name / "main.zeno" if many else folder / f"{name}.zeno"
        title = example_meta(path)
        lines = FOREVER.get(name)
        typed = TYPED.get(name)
        output = run_zeno(path, lines, typed)
        run_cmd = f"zeno run examples/{name}/main.zeno" if many else f"zeno run examples/{name}.zeno"
        if many:
            files = sorted([*(folder / name).rglob("*.zeno"), *(folder / name).rglob("zeno.package")],
                           key=lambda f: (f.name != "main.zeno", f.name == "zeno.package", str(f)))
            parts = [(str(f.relative_to(folder / name)).replace(os.sep, "/"), f.read_text().rstrip("\n")) for f in files]
            last_zeno = max(i for i, (rel, _) in enumerate(parts) if rel.endswith(".zeno"))
            windows = "".join(
                window(f"{name}/{rel}", code, output if i == last_zeno else None, run_cmd,
                       "zeno" if rel.endswith(".zeno") else "plain")
                for i, (rel, code) in enumerate(parts))
            whole = f"The {len(parts)} files of <code>examples/{name}/</code>, and what <code>{run_cmd}</code> prints."
            code_lines = sum(len(c.split("\n")) for _, c in parts)
            gh = f"{GITHUB}/tree/main/examples/{name}"
        else:
            code = path.read_text().rstrip("\n")
            windows = window(f"{name}.zeno", code, output, run_cmd)
            whole = f"The whole of <code>examples/{name}.zeno</code>, and what <code>zeno run</code> prints for it."
            code_lines = len(code.split("\n"))
            gh = f"{GITHUB}/blob/main/examples/{name}.zeno"
        note = ""
        live = live_page(folder, name)
        if live:
            note = (f'<p class="note-small">This program runs in a web page. <a href="/examples/{name}/live.html">Try it live</a>: '
                    f'<code>zeno build --web examples/{name}.zeno</code> built it from <code>examples/{name}.html</code>, with Zeno compiled to WebAssembly.</p>')
        if lines:
            note = f'<p class="note-small">This program runs until it is stopped. The first {lines} lines are shown.</p>'
        if typed:
            shown = ", ".join(f"<code>{esc(t)}</code>" for t in typed.strip().split("\n"))
            note = f'<p class="note-small">Run with these lines typed on the keyboard: {shown}. The keyboard is not echoed, so the prompts run together.</p>'
        prev_link = f'<a class="prev" href="/examples/{names[i-1]}/"><span>Previous</span>{label(names[i-1])}</a>' if i else "<span></span>"
        next_link = f'<a class="next" href="/examples/{names[i+1]}/"><span>Next</span>{label(names[i+1])}</a>' if i + 1 < len(names) else "<span></span>"
        page = f"""<div class="narrow">
  <p class="eyebrow">{icon("code")}<a href="/examples/">Examples</a></p>
  <h1 class="example-title">{esc(title)}</h1>
  <p class="lede small">{whole}</p>
  <div class="example-files">{windows}</div>
  {note}
  <p class="source">See it on GitHub: <a href="{gh}">examples/{label(name)}</a>.</p>
  <nav class="pager" aria-label="Previous and next">{prev_link}{next_link}</nav>
</div>"""
        layout(f"/examples/{name}/", label(name), f"{title}. A Zeno example, with its output.", page, "/examples/")
        kind = "layers" if many else "cpu" if name in FIRMWARE else "code"
        cards += (f'<li><a href="/examples/{name}/">{icon(kind)}<b>{esc(title)}</b>'
                  f'<span><code>{label(name)}</code></span><small>{code_lines} lines</small></a></li>')
    body = page_head("Examples", "Programs to read and run",
                     "Every example in the language repository, from one line to a thermostat built on a package. "
                     "Each page shows what <code>zeno run</code> printed. The chip marks a firmware program, "
                     "and the layers a program in several files.", "code") + \
        f'<ul class="index examples">{cards}</ul>'
    layout("/examples/", "Examples", "Example Zeno programs, from one line to firmware, each with its output.", body, "/examples/")


# --- Learn -------------------------------------------------------------------

GUIDE = [
    ("install", "Install", None, """
<p>Zeno 0.5 is out, open source under the MIT licence. Install it with one line on macOS and Linux, or a setup program on Windows. Both put <code>zeno</code> on your <code>PATH</code>, and offer a C compiler and git if the machine has none: <code>zeno build</code> needs the first, <code>zeno fetch</code> the second, and nothing else needs either.</p>
<h3>macOS and Linux</h3>
<figure class="window shell"><figcaption><!--ICON:terminal--><span class="file">Terminal</span><button class="copy" type="button" data-copy="install-cmd"><!--ICON:copy--><span>Copy</span></button></figcaption>
<pre id="install-cmd"><code>curl -fsSL https://github.com/zeno-src/zeno-lang/releases/latest/download/install.sh | sh
zeno new hello
zeno run hello/main.zeno</code></pre></figure>
<h3>Windows</h3>
<p>Download <a href="https://github.com/zeno-src/zeno-lang/releases/download/v0.5.1/zeno-0.5.1-windows-setup.exe">zeno-0.5.1-windows-setup.exe</a>, run it and press Next. One file covers x86-64, 32-bit x86 and ARM64. It is not signed, so Windows warns the first time: choose “More info”, then “Run anyway”.</p>
<h3>With a package manager</h3>
<p>There are packages for apt, pacman, snap and flatpak, installed from the file on the <a href="https://github.com/zeno-src/zeno-lang/releases/tag/v0.5.1">release page</a>, and a Homebrew tap:</p>
<figure class="window shell"><figcaption><!--ICON:terminal--><span class="file">Terminal</span><button class="copy" type="button" data-copy="pkg-cmd"><!--ICON:copy--><span>Copy</span></button></figcaption>
<pre id="pkg-cmd"><code>sudo apt install ./zeno_0.5.1_amd64.deb                  # Debian, Ubuntu, Raspberry Pi OS
sudo pacman -U zeno-lang-bin-0.5.1-1-x86_64.pkg.tar.zst  # Arch, Manjaro
sudo snap install --classic --dangerous zeno_0.5.1_amd64.snap
flatpak install --user zeno-0.5.1-x86_64.flatpak

brew tap zeno-src/zeno-lang https://github.com/zeno-src/zeno-lang
brew install zeno-src/zeno-lang/zeno                   # macOS and Linux</code></pre></figure>
<p>The <code>.deb</code> is also there for <code>arm64</code>, <code>armhf</code> and <code>i386</code>, the snap for <code>arm64</code> and <code>armhf</code>, and the flatpak for <code>aarch64</code>. Plain archives for ten kinds of machine, with <code>SHA256SUMS.txt</code>, are on the <a href="https://github.com/zeno-src/zeno-lang/releases/tag/v0.5.1">release page</a>. <a href="/docs/install/">How the installers work</a> and <a href="/docs/packages/">what each package is</a> are in the docs.</p>
<h3>From source</h3>
<figure class="window shell"><figcaption><!--ICON:terminal--><span class="file">Terminal</span><button class="copy" type="button" data-copy="src-cmd"><!--ICON:copy--><span>Copy</span></button></figcaption>
<pre id="src-cmd"><code>git clone https://github.com/zeno-src/zeno-lang
cd zeno-lang
cargo build --release
./target/release/zeno run examples/hello.zeno</code></pre></figure>
<p>You need <a href="https://rustup.rs">Rust</a>, and nothing else. Or skip installing for now, and try it in the <a href="/playground/">playground</a>.</p>"""),
    ("first", "Your first program", "hello", """
<p>A program is a file of statements, run from the top. There is no <code>main</code>, nothing to import for printing, and no semicolons: a line break ends a statement.</p>"""),
    ("variables", "Variables", "basics", """
<p>A variable says once whether it can change. <code>let</code> is set once. <code>var</code> can change, and a plain <code>=</code> updates it. <code>const</code> is fixed when the program is built. A type goes after the name, and only where you want one.</p>"""),
    ("typos", "A misspelt name is an error", "typo", """
<p>Because <code>=</code> only updates, assigning to a name that was never declared cannot quietly make a new variable. The checker stops before anything runs, and says what to write.</p>"""),
    ("numbers", "Numbers", "numbers", """
<p><code>/</code> always gives a float and <code>//</code> divides and rounds down, so you can see which one you meant. Comparisons chain as they do in maths. An <code>int</code> and a <code>float</code> can be mixed in arithmetic; nothing else converts by itself.</p>"""),
    ("overflow", "Overflow is an error", "overflow", """
<p>Whole-number arithmetic is checked. A sum that does not fit is an error you can catch, never a silent wrap to a negative number.</p>"""),
    ("control", "Choices and loops", "control", """
<p><code>if</code>, <code>else if</code>, <code>for</code> and <code>while</code> need no brackets around the condition and no colon after it. The brace opens the block, and the block always has braces, so a stray space can never change what the code does.</p>"""),
    ("truth", "Conditions are true or false", "truthy", """
<p>There is no truthiness. An empty list, zero and empty text are not quietly <code>false</code>: write what you mean, such as <code>len(items) &gt; 0</code>.</p>"""),
    ("functions", "Functions", "functions", """
<p>A function is declared with the word <code>function</code>. Types on parameters and the result are optional. Arguments can be named, parameters can have defaults, and a function with no name is written in place with <code>function(n) { }</code>.</p>"""),
    ("closures", "Functions that remember", "closures", """
<p>A function written inside another keeps the variables it can see, and can change them.</p>"""),
    ("lists", "Lists and text", "lists", """
<p>Lists are written with <code>[ ]</code>, and have <code>append</code>, <code>map</code>, <code>filter</code> and <code>reduce</code>. Comprehensions read like the sentence they stand for. Formatted text needs the <code>f</code> prefix, so a brace in ordinary text is just a brace.</p>"""),
    ("dicts", "Dictionaries", "dict", """
<p>A <code>dict</code> keeps one value under each key, written with the same square brackets as a list: <code>["temp": 85]</code>, and <code>[:]</code> for an empty one. Asking for a key that was never stored is an error, not a quiet zero; <code>get</code> gives <code>none</code> or a default instead.</p>"""),
    ("classes", "Classes", "classes", """
<p>A class lists its fields at the top and gets a constructor for free, which takes the fields in order or by name. Methods name <code>self</code> explicitly.</p>"""),
    ("enums", "Enums and match", "shapes", """
<p>Each case of an enum can carry its own values, and <code>match</code> takes them apart. A <code>match</code> must handle every case. This one forgets <code>Dot</code>, so nothing runs.</p>"""),
    ("none", "Values that may be missing", "users", """
<p>A value can be <code>none</code> only if its type says <code>or none</code>. Before you use it, you check it with <code>is not none</code>, and inside that check it is the plain type.</p>"""),
    ("errors", "Errors", "ports", """
<p><code>try</code>, <code>except</code> and <code>raise</code> read as they do in Python. A function that can fail says so with <code>raises</code>, and the checker makes sure the error is handled or passed on. Any class can be raised, so an error can carry data.</p>"""),
    ("files", "Files and input", "files", """
<p><code>import files</code> reads and writes files, <code>input()</code> reads a line from the keyboard, and <code>import program</code> gives the words a program was started with. A file that is not there is a <code>FileError</code> you can catch.</p>"""),
    ("units", "Units", "delay", """
<p>A number can carry a unit: <code>500 ms</code>, <code>3.3 V</code>. The unit is part of the type, so a function that wants milliseconds will not take a bare number.</p>"""),
    ("sized", "Numbers with a size", "packet", """
<p><code>u8</code>, <code>u16</code>, <code>u32</code>, <code>i8</code>, <code>i16</code> and <code>i32</code> have a size, and <code>&amp;</code>, <code>|</code>, <code>^</code>, <code>~</code>, <code>&lt;&lt;</code> and <code>&gt;&gt;</code> work on their bits. Arithmetic gives a full <code>int</code>, <code>u8(n)</code> checks that <code>n</code> fits, and <code>u8.wrap(n)</code> keeps the low eight bits on purpose. A <code>u8</code> field is one byte in a compiled object.</p>"""),
    ("generics", "Generics", "stack", """
<p><code>class Stack[T]</code> and <code>function largest[T]</code> are written once, with <code>T</code> standing for a type. A call never says what <code>T</code> is: the checker works it out, and the compilers make one copy for each type used, so a <code>Stack[u8]</code> is as small as one written for bytes by hand.</p>"""),
    ("ownership", "Owned values", "frame", """
<p>Most values are shared, and a garbage collector frees them. A value marked <code>owned</code> has one owner instead, and is freed the moment its owner's block ends. A parameter only looks at what it is given, unless it says <code>take</code>. Giving the value away empties the old name, and the checker points at any later use.</p>"""),
    ("modules", "Programs in several files", None, """
<p>A file is a module. <code>import sensors</code> brings in <code>sensors.zeno</code> from the same folder, and its names are written <code>sensors.check</code>; <code>from sensors import Reading</code> brings in one name to use as it is. A dot is a folder, so <code>import drivers.uart</code> is <code>drivers/uart.zeno</code>. There is nothing to declare and nothing to export: what a file declares at the top is what others can import. See the weather station in <a href="/examples/station/">examples/station</a>, four files with its output.</p>"""),
    ("board", "Pins and time", "board", """
<p><code>from board import led, pin</code> and <code>from time import sleep, now</code> give a program pins and a clock. On a computer the board is simulated and prints each pin as it changes. A compiled program meets a real board through four C functions.</p>"""),    ("speed", "Building for speed", None, """
<p><code>zeno run</code> runs a program straight away and checks everything. <code>zeno build</code> compiles it to C and keeps the checks: an index out of range, a division by zero and an overflow still stop the program with Zeno's message. When the tests pass, two choices make it faster. <code>--owned</code> gives every list and object one owner and frees it on the line its owner ends, with no collector at all. <code>--fast</code> leaves out the checks that a correct program never fails, as C does, and runs about as fast as C and Rust.</p>
<figure class="window shell"><figcaption><!--ICON:terminal--><span class="file">Terminal</span></figcaption>
<pre><code>zeno run main.zeno                  # straight away, every check
zeno build main.zeno                # compiled, every check kept
zeno build --fast --owned main.zeno # as fast as C, no collector</code></pre></figure>
<p>A wrong index in a <code>--fast</code> build is a wrong answer or a crash, exactly as in C, so build the ordinary way while a program is being written. <a href="/docs/memory-modes/">Choosing how memory is freed</a> and <a href="/benchmarks/">the benchmarks</a> say more.</p>"""),
    ("targets", "Other languages", None, """
<p><code>zeno build --target</code> writes your program in another language: JavaScript, TypeScript, Python, PHP, Go, Java, C#, C++ or Rust, a web page, or a WebAssembly file. The file needs nothing else, and it prints what <code>zeno run</code> prints, down to the same error on the same line.</p>
<figure class="window shell"><figcaption><!--ICON:terminal--><span class="file">Terminal</span></figcaption>
<pre><code>zeno build --target py main.zeno    # writes main.py
python3 main.py
zeno build --target js main.zeno    # writes main.js
node main.js</code></pre></figure>
<p>The same program gives the same file every time. A program that uses the board, a web page or memory by hand stays with Zeno's own builds. <a href="/docs/targets/">How the targets work</a>.</p>"""),
]


LESSON_ICONS = {"install": "terminal", "first": "play", "variables": "type", "typos": "scan", "numbers": "chart",
                "overflow": "gauge", "control": "loop", "truth": "check", "functions": "function", "closures": "braces",
                "lists": "words", "classes": "package", "enums": "layers", "none": "none", "errors": "alert",
                "units": "ruler", "sized": "memory", "generics": "copies", "ownership": "key", "board": "board",
                "dicts": "key", "files": "edit", "modules": "layers", "speed": "zap", "targets": "copies"}


def icons_in(text):
    return re.sub(r"<!--ICON:([\w-]+)-->", lambda m: icon(m.group(1)), text)


def build_learn():
    toc = "".join(f'<li><a href="#{sid}">{title}</a></li>' for sid, title, _, _ in GUIDE)
    toc += '<li><a href="#commands">The commands</a></li><li><a href="#next">Where next</a></li>'
    sections = ""
    for i, (sid, title, snip, prose) in enumerate(GUIDE, 1):
        code = sample(snip) if snip else ""
        wide = "" if snip else " wide"
        sections += f"""<section class="lesson{wide}" id="{sid}">
  <div class="lesson-text"><div class="lesson-head">{icon(LESSON_ICONS.get(sid, "book"))}Step {i} of {len(GUIDE)}</div><h2>{title}</h2>{icons_in(prose)}</div>
  <div class="lesson-code">{code}</div>
</section>"""
    commands = """
<section class="lesson" id="commands"><div class="lesson-text"><div class="lesson-head"><!--ICON:terminal-->Reference</div><h2>The commands</h2>
<p>One program, <code>zeno</code>, does everything. Every command checks the program first, and nothing runs if the check fails.</p></div>
<div class="lesson-code"><dl class="cmd-list">
<dt><code>zeno run file.zeno</code></dt><dd>Check it, then run it with the interpreter.</dd>
<dt><code>zeno run --vm file.zeno</code></dt><dd>The same, compiled to bytecode and run by the VM.</dd>
<dt><code>zeno check file.zeno</code></dt><dd>Only look for mistakes.</dd>
<dt><code>zeno check --strict file.zeno</code></dt><dd>Every type must be known, as firmware needs.</dd>
<dt><code>zeno build file.zeno</code></dt><dd>Compile to C, then to a program.</dd>
<dt><code>zeno build --llvm file.zeno</code></dt><dd>Compile to LLVM IR, then to a program with clang.</dd>
<dt><code>zeno build --firmware</code></dt><dd>Errors as return values, no <code>setjmp</code>.</dd>
<dt><code>zeno build --no-collector</code></dt><dd>No garbage collector and no heap: one fixed pool.</dd>
<dt><code>zeno build --memory</code></dt><dd>The program reports its memory use as it ends.</dd>
<dt><code>zeno test</code></dt><dd>Run the tests in a file or a folder.</dd>
<dt><code>zeno format file.zeno</code></dt><dd>Lay the file out the one standard way.</dd>
<dt><code>zeno new name</code></dt><dd>Make a folder with a new program; <code>--package</code> makes a package.</dd>
<dt><code>zeno fetch</code></dt><dd>Get the packages the program needs.</dd>
<dt><code>zeno join file.zeno</code></dt><dd>Show the one program a file and its imports join into.</dd>
<dt><code>zeno lsp</code></dt><dd>The language server, for editors.</dd>
<dt><code>zeno bytecode</code>, <code>parse</code>, <code>tokens</code></dt><dd>Look inside: the instructions, the syntax tree, the tokens.</dd>
</dl></div></section>
<section class="next-steps" id="next"><h2>Where next</h2><div class="cards">
<a class="card" href="/examples/"><!--ICON:code--><b>Read the examples</b><span>Whole programs, each with its output.</span></a>
<a class="card" href="/docs/"><!--ICON:book--><b>See how it works</b><span>A walkthrough of every compiler stage.</span></a>
<a class="card" href="/decisions/"><!--ICON:scale--><b>Read the reasons</b><span>Why each part of the language is the way it is.</span></a>
</div></section>"""
    body = f"""<div class="learn-layout">
<aside class="learn-toc"><h4>The guide</h4><ol>{toc}</ol></aside>
<div class="learn-main">
{page_head("Learn", "The Zeno guide", "Everything in the language, a step at a time. Every sample on this page was run with <code>zeno run</code>, and what is under it is exactly what Zeno printed, error messages included. If you know Python or C, you can read it in twenty minutes.", "compass")}
{sections}{icons_in(commands)}
</div></div>"""
    layout("/learn/", "The Zeno guide", "Learn Zeno: install it, then the whole language a step at a time, with the real output of every sample.", body, "/learn/")


# --- Roadmap, About, 404 -----------------------------------------------------

DONE = [
    ("Lexer", "Source text becomes tokens.", "lexer"),
    ("Parser", "Tokens become a syntax tree.", "parser"),
    ("Interpreter", "<code>zeno run</code> walks the syntax tree.", "interpreter"),
    ("Type checker", "Gradual types: checked where written, worked out where left out.", "checker"),
    ("Compile to C", "The whole language, as portable C.", "compiler"),
    ("Garbage collector", "A small mark-and-sweep collector in the compiled program.", "memory"),
    ("Errors as values", "<code>--firmware</code>: no <code>setjmp</code>, every caller tests.", "firmware"),
    ("Owned values", "Freed at a line you can point to.", "ownership"),
    ("No collector", "<code>--no-collector</code> leaves the collector out.", "no-collector"),
    ("Bytecode VM", "<code>zeno run --vm</code>, two to three times as fast.", "vm"),
    ("LLVM backend", "<code>zeno build --llvm</code>, with every flag.", "llvm"),
    ("Board and time", "Pins, <code>sleep</code> and <code>now</code>, on a simulated board.", "board"),
    ("Sized numbers", "<code>u8</code> to <code>i32</code> and the bit operators.", "sized-ints"),
    ("Generics", "<code>class Stack[T]</code>, one compiled copy per type.", "generics"),
    ("A fixed memory pool", "No <code>malloc</code> in a firmware build.", "pool"),
    ("Kept text", "Text that is built and kept, with no collector.", "text"),
    ("Statement-owned values", "A list nobody keeps is freed by its statement.", "temporaries"),
    ("One owner", "Whoever receives a value owns it, with no collector.", "one-owner"),
    ("Enums, none, closures and errors with one owner", "The whole language builds with no collector.", "one-owner"),
    ("Memory by hand", "<code>unsafe { }</code>, raw pointers, <code>allocate</code>, <code>free</code> and registers.", "unsafe"),
    ("An audit for clarity", "Every feature checked: a parameter looks, and <code>take</code> takes.", "audit"),
    ("Text and lists", "<code>find</code>, <code>slice</code>, <code>sort</code>, <code>join</code> and more.", "library"),
    ("Files, input and arguments", "<code>import files</code>, <code>input()</code> and <code>import program</code>.", "reading-and-writing"),
    ("More maths", "Angles, logarithms, powers and rounding in <code>math</code>.", "math"),
    ("Dictionaries", "<code>dict[str, int]</code>, written <code>[&quot;a&quot;: 1]</code>.", "dict"),
    ("Programs in several files", "<code>import sensors</code>, and folders as modules.", "modules"),
    ("private", "What a module keeps to itself.", "private"),
    ("Interfaces", "A type says what it can do, and the checker holds it to that.", "interfaces"),
    ("Packages", "<code>zeno.package</code>, and code shared between programs.", "packages"),
    ("Tests", "<code>test</code>, <code>assert</code> and <code>zeno test</code>.", "testing"),
    ("Starting a program", "<code>zeno new</code>.", "new"),
    ("The formatter and the language server", "<code>zeno format</code>, and an editor that knows Zeno.", "lsp"),
    ("The gaps programs found", "<code>+=</code> and a format on a quantity.", "gaps"),
    ("Version 0.1", "Every provisional decision read again. The list is done.", "version-0.1"),
    ("A program in a web page", "<code>import web</code> and <code>zeno build --web</code>.", "web"),
    ("Installers", "A setup program for Windows, one line for macOS and Linux, and packages for apt, pacman, snap, flatpak and Homebrew.", "install"),
    ("A page that does more", "Events, styles, a canvas, timers and the network.", "web"),
    ("A playground", "Write and run Zeno in the browser, with nothing installed.", "playground"),
    ("What 0.1 left, taken up", "<code>min</code> and <code>max</code> on quantities, <code>zeno test --only</code>, field hover.", "testing"),
    ("JSON", "<code>json.parse</code> and <code>json.write</code>.", "json"),
    ("Owners and the fast build (0.3, 0.4)", "<code>--owned</code>, a program with no collector, and <code>zeno build --fast</code>, as fast as C and Rust.", "memory-modes"),
    ("Other languages (0.5)", "<code>zeno build --target</code>: JavaScript, TypeScript, Python, PHP, Go, Java, C#, C++, Rust, a web page and WebAssembly, each printing what <code>zeno run</code> prints.", "targets"),
]
NEXT = [
    ("Next", "Reading from a board", "Pins, an ADC and a UART read on real hardware: the one item held back from 0.1."),
    ("Planned", "Bytes", "A <code>list[u8]</code> at one byte an item, <code>u64</code>, and files read as bytes."),
    ("Planned", "More with no collector", "Dicts of lists and objects, and <code>list[int or none]</code>."),
    ("Planned", "C interop", "Call C libraries, and be called from C."),
    ("Planned", "async and await", "Servers and networking."),
]


def build_roadmap():
    done = "".join(
        f'<li><a href="/docs/{doc}/">{icon("check")}<b>{t}</b><span>{d}</span></a></li>' for t, d, doc in DONE)
    upcoming = "".join(
        f'<li class="{s.split()[0].lower()}">{icon("clock" if s in ("In progress", "Next") else "map")}<i>{s}</i><b>{t}</b><span>{d}</span></li>'
        for s, t, d in NEXT)
    body = page_head("Roadmap", "Where Zeno stands",
                     "Zeno 0.5 is out: zeno build --target writes a program in eleven other languages, zeno build --fast makes it as fast as C and Rust, and a program can choose how its memory is freed. "
                     "The goal is one language for every job you would reach for C, C++, Python, JavaScript, Java or Rust to do. "
                     "Each use case arrives with a piece of the compiler. This is the order they have come in, and the order the rest will.", "map") + f"""
<div class="roadmap">
  <section><h2>{icon("check")}Done</h2><p class="muted">{len(DONE)} stages, each with a walkthrough. Every test program is run on all four engines and must print the same.</p><ol class="done-list">{done}</ol></section>
  <section><h2>{icon("clock")}Coming</h2><p class="muted">In order. The syntax may still change before a first release.</p><ul class="next-list">{upcoming}</ul></section>
</div>"""
    layout("/roadmap/", "Roadmap", "What the Zeno compiler can do today, and what comes next.", body, "/roadmap/")


def lines_of_code():
    root = Path(ARGS.zeno)
    files = list((root / "src").rglob("*.rs")) + list(root.glob("runtime/*.[ch]")) + list((root / "src").rglob("*.c"))
    total = sum(len(f.read_text(errors="ignore").splitlines()) for f in set(files))
    return f"{round(total, -3):,}"


def build_about():
    body = f"""<div class="narrow prose about">
<p class="eyebrow">{icon("info")}About</p>
<h1>A language built to learn from</h1>
<p class="lede">Zeno is a programming language built from scratch by Partha, a firmware engineer, to learn how languages work by making one. It takes what he likes from C, C++, Python, JavaScript, Java and Rust, and leaves out what gets in the way.</p>
<h2>The rule above the rules</h2>
<blockquote><p>The entire language must be unambiguous and intuitive.</p></blockquote>
<p>In practice that means one obvious way to write each thing, no syntax that can be read two ways, no surprising behaviour behind your back, keywords that are plain words, and error messages that say what to write instead. Every feature is checked against it, and the reasoning is written down in the <a href="/decisions/">design decisions</a>.</p>
<h2>Why firmware first</h2>
<p>Most new languages start on a laptop and reach a microcontroller late, if ever. Zeno went the other way: the same source builds with no garbage collector, no heap and no <code>setjmp</code>, memory comes from one pool of a size you choose, and a <code>u8</code> really is one byte. If a language is clear enough for firmware, it is clear enough for a script.</p>
<h2>The name</h2>
<p>Zeno of Elea argued that Achilles can never catch a tortoise: before he reaches it he must cover half the distance, then half of what is left, forever. The quantum Zeno effect says a system watched closely enough never changes. Both suit a compiler that will always be almost finished. The bar at the top of every page closes half the distance that is left as you scroll, and never arrives.</p>
<h2>Status</h2>
<p>Zeno 0.5 is released, with installers for Windows, macOS and Linux, and the code is open source under the MIT licence. It runs programs, checks them, and compiles them to C, to LLVM, to a web page and to eleven other languages, has a standard library, programs in many files, packages, tests, a formatter and a language server. Version 0.1 means every open question about the language has an answer, though a change can still come before 1.0. It is a language to read, learn from and experiment with. See the <a href="/roadmap/">roadmap</a>.</p>
<h2>The code</h2>
<p>The compiler is plain Rust with no dependencies, about {lines_of_code()} lines with its C runtime, in <a href="{GITHUB}">zeno-src/zeno-lang</a>, under the MIT licence. This website is plain HTML, CSS and a little JavaScript, built by a short script that runs every sample through Zeno.</p>
<h2 id="contact">Contact</h2>
<p>There are four addresses, one for each kind of mail.</p>
<ul>
<li><b>Stuck installing or using Zeno?</b> Write to <a href="mailto:help@zeno-lang.org">help@zeno-lang.org</a>, with what you typed and what Zeno printed.</li>
<li><b>A bug in Zeno</b> is best reported as an <a href="{GITHUB}/issues">issue on GitHub</a>, where others can see it and its answer. With no GitHub account, write to <a href="mailto:issues@zeno-lang.org">issues@zeno-lang.org</a>.</li>
<li><b>A security problem</b> goes to <a href="mailto:security@zeno-lang.org">security@zeno-lang.org</a>, in private, and not into a public issue. <a href="{GITHUB}/blob/main/SECURITY.md">SECURITY.md</a> says what to send.</li>
<li><b>Anything else</b>, an idea, the website, the book: <a href="mailto:contact@zeno-lang.org">contact@zeno-lang.org</a>.</li>
</ul>
</div>"""
    layout("/about/", "About", "Zeno is a programming language built from scratch by a firmware engineer, to learn by building.", body, "/about/")


# --- Download ----------------------------------------------------------------

RELEASES_API = "https://api.github.com/repos/zeno-src/zeno-lang/releases"
RELEASES_CACHE = TOOLS / "releases.json"

# The marks of the three systems, filled, on a 24 by 24 grid.
OS_MARKS = {
    "windows": '<path d="M3 5.1l7.4-1v7.2H3zM11.4 3.9L21 2.6v8.7h-9.6zM3 12.6h7.4v7.3L3 18.9zM11.4 12.6H21v8.8l-9.6-1.3z"/>',
    "macos": '<path d="M16.4 12.7c0-2.5 2-3.7 2.1-3.8-1.2-1.7-3-1.9-3.6-2-1.5-.2-3 .9-3.8.9-.8 0-2-.9-3.3-.9-1.7 0-3.3 1-4.2 2.5-1.8 3.1-.5 7.7 1.3 10.2.9 1.2 1.9 2.6 3.2 2.6 1.3-.1 1.8-.8 3.3-.8s2 .8 3.3.8c1.4 0 2.3-1.3 3.1-2.5 1-1.4 1.4-2.8 1.4-2.9-.1 0-2.8-1-2.8-4.1zM13.9 5.2c.7-.8 1.2-2 1-3.2-1 .1-2.3.7-3 1.5-.7.8-1.2 2-1.1 3.1 1.2.1 2.3-.6 3.1-1.4z"/>',
    "linux": '<path d="M12 2c-2.3 0-3.6 1.9-3.6 4.4 0 1.3.2 2.2-.5 3.4-.9 1.5-2.6 3.6-2.6 6.3 0 .8.2 1.5.5 2.1-.9.4-1.8 1-1.8 1.8 0 1.1 1.9 1.4 3.4 1.8 1.2.3 2 .9 3 .9.8 0 1.3-.4 1.6-.9h0c.3.5.8.9 1.6.9 1 0 1.8-.6 3-.9 1.5-.4 3.4-.7 3.4-1.8 0-.8-.9-1.4-1.8-1.8.3-.6.5-1.3.5-2.1 0-2.7-1.7-4.8-2.6-6.3-.7-1.2-.5-2.1-.5-3.4C15.6 3.9 14.3 2 12 2zm-1.6 3.6c.5 0 .8.6.8 1.2 0 .3-.1.6-.2.8l-.8-.2c.1-.2.1-.4.1-.6 0-.3-.1-.5-.2-.5-.2 0-.3.3-.3.6v.2l-.7-.3c0-.7.6-1.2 1.3-1.2zm3.2 0c.7 0 1.3.5 1.3 1.2l-.7.3v-.2c0-.3-.1-.6-.3-.6-.1 0-.2.2-.2.5 0 .2 0 .4.1.6l-.8.2c-.1-.2-.2-.5-.2-.8 0-.6.3-1.2.8-1.2zM12 8.3c.9 0 2.2.6 2.2 1 0 .3-1.4 1.2-2.2 1.2S9.8 9.6 9.8 9.3c0-.4 1.3-1 2.2-1zm-1.9 3c.6.3 1.2.5 1.9.5s1.3-.2 1.9-.5c.9 1.2 1.7 2.8 1.7 4.6 0 2.1-1.6 3.2-3.6 3.2s-3.6-1.1-3.6-3.2c0-1.8.8-3.4 1.7-4.6z"/>',
}
ARCH = {"x86_64": "x64", "amd64": "x64", "arm64": "Arm64", "aarch64": "Arm64", "armv7": "Arm32",
        "armhf": "Arm32", "armv6": "ArmV6", "x86": "x86", "i386": "x86"}
ARCH_ORDER = ["x64", "Arm64", "Arm32", "ArmV6", "x86"]


def releases():
    """Every published release of Zeno, newest first. Read from GitHub when the
    build can reach it, and kept in tools/releases.json for when it cannot."""
    import json, urllib.request
    try:
        req = urllib.request.Request(RELEASES_API, headers={"Accept": "application/vnd.github+json", "User-Agent": "zeno-lang.org build"})
        with urllib.request.urlopen(req, timeout=15) as r:
            data = json.load(r)
        keep = [{"tag": d["tag_name"], "name": d["name"], "date": d["published_at"][:10], "url": d["html_url"],
                 "assets": [{"name": a["name"], "size": a["size"], "url": a["browser_download_url"],
                             "sha256": (a.get("digest") or "").removeprefix("sha256:")} for a in d["assets"]]}
                for d in data if not d["draft"] and not d["prerelease"]]
        RELEASES_CACHE.write_text(json.dumps(keep, indent=1) + "\n")
        return keep
    except Exception as e:
        print(f"  releases: GitHub not reachable ({e}); using tools/releases.json")
        return json.loads(RELEASES_CACHE.read_text())


def classify(name):
    """(system, format, arch label) for a release file, or None."""
    m = re.fullmatch(r"zeno-[\d.]+-windows-setup\.exe", name)
    if m: return ("windows", "setup", "all")
    m = re.fullmatch(r"zeno-[\d.]+-(linux|macos|windows)-(\w+)\.(tar\.gz|zip)", name)
    if m: return (m[1], m[3], ARCH.get(m[2], m[2]))
    m = re.fullmatch(r"zeno_[\d.]+_(\w+)\.(deb|snap)", name)
    if m: return ("linux", m[2], ARCH.get(m[1], m[1]))
    m = re.fullmatch(r"zeno-[\d.]+-(\w+)\.flatpak", name)
    if m: return ("linux", "flatpak", ARCH.get(m[1], m[1]))
    m = re.fullmatch(r"zeno(?:-lang)?-bin-[\d.]+-\d+-(\w+)\.pkg\.tar\.zst", name)
    if m: return ("linux", "pacman", ARCH.get(m[1], m[1]))
    if name == "install.sh": return ("any", "install.sh", "")
    if name == "SHA256SUMS.txt": return ("any", "sums", "")
    return None


def human_size(n):
    return f"{n / 1048576:.1f} MB" if n >= 1048576 else f"{n / 1024:.0f} KB"


def human_date(d):
    y, m, day = d.split("-")
    return f"{int(day)} {['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'][int(m)-1]} {y}"


def build_download():
    rels = releases()
    latest = rels[0]
    v = latest["tag"].lstrip("v")
    files = {}
    for a in latest["assets"]:
        c = classify(a["name"])
        if c:
            files.setdefault((c[0], c[1]), {})[c[2]] = a

    def mark(os_):
        return f'<svg class="os-mark" viewBox="0 0 24 24" aria-hidden="true" fill="currentColor">{OS_MARKS[os_]}</svg>'

    def chips(os_, fmt, label, note=""):
        got = files.get((os_, fmt), {})
        if not got:
            return ""
        links = "".join(f'<a class="chip" href="{got[a]["url"]}" title="{esc(got[a]["name"])}, {human_size(got[a]["size"])}">{a}</a>'
                        for a in ARCH_ORDER if a in got)
        return f'<div class="dl-row"><span class="dl-fmt">{label}{f"<small>{note}</small>" if note else ""}</span><span class="dl-chips">{links}</span></div>'

    def big(os_, fmt, arch, title, sub):
        a = files.get((os_, fmt), {}).get(arch)
        if not a:
            return ""
        return (f'<a class="dl-big" href="{a["url"]}">{icon("download")}<span><b>{title}</b>'
                f'<small>{sub} · {human_size(a["size"])}</small></span></a>')

    win = (big("windows", "setup", "all", "Windows setup", "x64, Arm64 and x86 in one")
           + chips("windows", "zip", ".zip"))
    mac = (big("macos", "tar.gz", "Arm64", "Apple silicon", "M1 and later, .tar.gz")
           + big("macos", "tar.gz", "x64", "Intel", ".tar.gz")
           + '<div class="dl-row"><span class="dl-fmt">Homebrew</span><a class="chip" href="#terminal" data-tab="t-brew">brew install</a></div>')
    lin = (big("linux", "deb", "x64", ".deb", "Debian, Ubuntu, Raspberry Pi OS")
           + chips("linux", "deb", ".deb", "apt")
           + chips("linux", "tar.gz", ".tar.gz", "any")
           + chips("linux", "snap", ".snap")
           + chips("linux", "flatpak", ".flatpak")
           + chips("linux", "pacman", ".pkg.tar.zst", "Arch"))
    cards = "".join(
        f'<section class="dl-card" data-os="{os_}"><div class="dl-head">{mark(os_)}<h2>{name}</h2><p>{req}</p></div>'
        f'<span class="dl-yours">Your system</span>{body}</section>'
        for os_, name, req, body in [("windows", "Windows", "Windows 10 and 11", win),
                                     ("macos", "macOS", "macOS 11 and later", mac),
                                     ("linux", "Linux", "Any distribution, glibc or not", lin)])

    def f(os_, fmt, arch):
        return files.get((os_, fmt), {}).get(arch, {}).get("name", "")
    rel = f"https://github.com/zeno-src/zeno-lang/releases/download/{latest['tag']}"
    terminal = [
        ("sh", "macOS and Linux", "One line. It picks the right <code>zeno</code>, puts it on your <code>PATH</code>, and offers a C compiler and git if they are missing.",
         "curl -fsSL https://github.com/zeno-src/zeno-lang/releases/latest/download/install.sh | sh"),
        ("brew", "Homebrew", "On macOS and Linux.",
         "brew tap zeno-src/zeno-lang https://github.com/zeno-src/zeno-lang\nbrew install zeno-src/zeno-lang/zeno"),
        ("apt", "apt", "Debian, Ubuntu, Raspberry Pi OS. apt brings a C compiler and git along if the machine has none. For a Raspberry Pi use the <code>arm64</code> or <code>armhf</code> file.",
         f"curl -LO {rel}/{f('linux','deb','x64')}\nsudo apt install ./{f('linux','deb','x64')}"),
        ("pacman", "pacman", "Arch, Manjaro.",
         f"curl -LO {rel}/{f('linux','pacman','x64')}\nsudo pacman -U {f('linux','pacman','x64')}"),
        ("snap", "snap", "Until Zeno is in the Snap Store, a snap installed from its file needs <code>--dangerous</code>.",
         f"curl -LO {rel}/{f('linux','snap','x64')}\nsudo snap install --classic --dangerous {f('linux','snap','x64')}"),
        ("flatpak", "flatpak", "Installed for you alone.",
         f"curl -LO {rel}/{f('linux','flatpak','x64')}\nflatpak install --user {f('linux','flatpak','x64')}"),
        ("win", "Windows", "In PowerShell, to download the setup program and run it. Or use the button above.",
         f"curl.exe -LO {rel}/{f('windows','setup','all')}\n.\\{f('windows','setup','all')}"),
        ("src", "From source", "With <a href=\"https://rustup.rs\">Rust</a> installed.",
         "git clone https://github.com/zeno-src/zeno-lang\ncd zeno-lang\ncargo build --release"),
    ]
    tabs = "".join(f'<button role="tab" aria-selected="{"true" if i == 0 else "false"}" aria-controls="p-{k}" id="t-{k}"{"" if i == 0 else " tabindex=\"-1\""}>{t}</button>'
                   for i, (k, t, _, _) in enumerate(terminal))
    panels = "".join(
        f'<div class="dl-panel" role="tabpanel" id="p-{k}" aria-labelledby="t-{k}"{"" if i == 0 else " hidden"}><p>{note}</p>'
        f'<figure class="window shell"><figcaption>{icon("terminal")}<span class="file">Terminal</span>'
        f'<button class="copy" type="button" data-copy="c-{k}">{icon("copy")}<span>Copy</span></button></figcaption>'
        f'<pre id="c-{k}"><code>{esc(cmd)}</code></pre></figure></div>'
        for i, (k, _, note, cmd) in enumerate(terminal))

    groups = [("Windows", "windows", ["setup", "zip"]), ("macOS", "macos", ["tar.gz"]),
              ("Linux", "linux", ["deb", "tar.gz", "snap", "flatpak", "pacman"]), ("Any system", "any", ["install.sh", "sums"])]
    olds = ""
    for i, r in enumerate(rels):
        rows = ""
        for gname, os_, fmts in groups:
            items = [(classify(a["name"]), a) for a in r["assets"]]
            items = [(c, a) for c, a in items if c and c[0] == os_ and c[1] in fmts]
            items.sort(key=lambda ca: (fmts.index(ca[0][1]), ARCH_ORDER.index(ca[0][2]) if ca[0][2] in ARCH_ORDER else 9))
            for c, a in items:
                sha = (f'<button class="sha" type="button" data-sha="{a["sha256"]}" title="Copy the SHA-256">{a["sha256"][:12]}…</button>'
                       if a["sha256"] else "")
                rows += (f'<tr><td>{gname}</td><td><a href="{a["url"]}">{esc(a["name"])}</a></td>'
                         f'<td>{c[2] if c[2] not in ("all", "") else ""}</td><td>{human_size(a["size"])}</td><td>{sha}</td></tr>')
        tag = r["tag"].lstrip("v")
        olds += (f'<details class="dl-old"{" open" if i == 0 else ""}><summary><b>Zeno {tag}</b>'
                 f'{"<em>Latest</em>" if i == 0 else ""}<span>{human_date(r["date"])}</span></summary>'
                 f'<p class="dl-old-links"><a href="{r["url"]}">Release notes</a>'
                 f'<a href="https://github.com/zeno-src/zeno-lang/releases/download/{r["tag"]}/SHA256SUMS.txt">SHA256SUMS.txt</a>'
                 f'<a href="https://github.com/zeno-src/zeno-lang/tree/{r["tag"]}">Source at {r["tag"]}</a></p>'
                 f'<div class="dl-table"><table><thead><tr><th>System</th><th>File</th><th>CPU</th><th>Size</th><th>SHA-256</th></tr></thead>'
                 f'<tbody>{rows}</tbody></table></div></details>')

    body = f"""<div class="dl">
<header class="dl-hero">
  <p class="eyebrow">{icon("download")}Download</p>
  <h1>Download Zeno</h1>
  <p class="lede">Free and open source under the MIT licence.<br>Version {v}, released {human_date(latest["date"])}.</p>
  <p class="dl-hero-actions"><a class="button" id="dl-primary" href="#systems">{icon("download")}<span>Choose your system</span></a><a class="button ghost" href="/playground/">Try it in the browser</a></p>
  <p class="dl-hero-note" id="dl-note">One file, a few megabytes, and nothing else needed to run, check and test programs.</p>
</header>
<div class="dl-cards" id="systems">{cards}</div>
<p class="dl-sums">Every file's SHA-256 is in <a href="{rel}/SHA256SUMS.txt">SHA256SUMS.txt</a>. Windows and macOS warn about Zeno the first time, because it is not signed yet: on Windows choose “More info”, then “Run anyway”; on macOS run <code>xattr -d com.apple.quarantine zeno</code>.</p>

<section class="dl-section" id="terminal">
  <h2>{icon("terminal")}Install from a terminal</h2>
  <div class="segmented" role="tablist" aria-label="How to install" data-group="install">{tabs}</div>
  {panels}
  <p class="muted">Each command installs version {v}. What the installers do, step by step, is in <a href="/docs/install/">the installer docs</a>, and what each package holds in <a href="/docs/packages/">the package docs</a>. If an install does not work, write to <a href="mailto:help@zeno-lang.org">help@zeno-lang.org</a> with the message it stopped at and the name of your system.</p>
</section>

<section class="dl-section dl-needs">
  <h2>{icon("package")}What Zeno needs</h2>
  <div class="cards">
    <div class="card">{icon("play")}<b>Nothing, to run</b><span><code>zeno run</code>, <code>check</code>, <code>test</code>, <code>format</code> and <code>lsp</code> are all in the one file.</span></div>
    <div class="card">{icon("cpu")}<b>A C compiler, to build</b><span><code>zeno build</code> uses <code>cc</code>, <code>gcc</code> or <code>clang</code>. <code>--llvm</code> needs clang.</span></div>
    <div class="card">{icon("globe")}<b>git, for packages</b><span><code>zeno fetch</code> gets packages with git. <code>zeno build --web</code> needs only <code>zeno.wasm</code>, which comes with every install.</span></div>
  </div>
</section>

<section class="dl-section" id="previous">
  <h2>{icon("clock")}Every version</h2>
  <p class="muted">Each release keeps all of its files. Older versions stay here for anyone who needs to match one.</p>
  {olds}
</section>
</div>"""
    layout("/download/", "Download", f"Download Zeno {v} for Windows, macOS and Linux: installers, packages, archives, and every earlier version.", body, "/download/")


def build_privacy():
    body = f"""<div class="narrow prose about">
<p class="eyebrow">{icon("check")}Privacy</p>
<h1>Privacy</h1>
<p class="lede">Zeno collects nothing about you.</p>
<h2>The compiler and its tools</h2>
<p><code>zeno</code> sends nothing anywhere. It has no telemetry, no crash reports and no update checks. The only time it uses the network is when you ask it to: <code>zeno fetch</code> runs git to download the packages your <code>zeno.package</code> names, from the addresses written there.</p>
<h2>The installers</h2>
<p>The Windows setup program and <code>install.sh</code> download Zeno's files from GitHub, and offer to install a C compiler and git through your system's own package manager. They send nothing about you or your machine.</p>
<h2>The playground and built pages</h2>
<p>The playground runs your program in your browser. Nothing you write is sent to a server. A link made with “Copy link” holds the program in the part of the address after <code>#</code>, which browsers do not send to a server. A page made with <code>zeno build --web</code> uses the network only if its program calls <code>web.fetch</code> or <code>web.post</code>.</p>
<h2>This website</h2>
<p>zeno-lang.org is plain pages served by Cloudflare Pages. It sets no cookies and has no analytics or trackers. It loads its fonts from Google Fonts, and Cloudflare and Google may keep the usual server logs of requests, such as IP addresses. Your choice of light or dark is kept in your own browser.</p>
<h2>Downloads</h2>
<p>Files are downloaded from GitHub Releases, under <a href="https://docs.github.com/en/site-policy/privacy-policies/github-general-privacy-statement">GitHub's privacy statement</a>.</p>
<h2>Mail</h2>
<p>If you write to one of Zeno's addresses, Cloudflare forwards your mail to Partha's inbox. Your address and what you wrote are used to answer you, and for nothing else.</p>
<p class="muted">Questions: write to <a href="mailto:contact@zeno-lang.org">contact@zeno-lang.org</a>.</p>
</div>"""
    layout("/privacy/", "Privacy", "Zeno, its installers and this website collect nothing about you.", body)


# --- Benchmarks ----------------------------------------------------------------

BENCH_PROGRAMS = [
    ("fib", "Function calls", "The slow recursive Fibonacci of a number: millions of calls and additions."),
    ("loop", "A tight loop", "Whole-number arithmetic in a while loop, a billion times round."),
    ("sort", "Sorting a list", "A quicksort written in the program, over ten million made-up numbers."),
    ("strings", "Building text", "Ten million numbers turned to text, joined, then read a character at a time."),
    ("trees", "Many small objects", "The binary-trees test: make and drop millions of small trees."),
    ("nbody", "Floating point", "Five planets moved ten million small steps, as in the benchmarks game."),
]


def bench_results(name):
    import json
    path = Path(ARGS.zeno) / "bench" / "results" / f"{name}.json"
    return json.loads(path.read_text()) if path.exists() else None


def bench_cell(value, c):
    """A time, how many times C it is, and a bar for that."""
    if not isinstance(value, (int, float)):
        return '<td class="bench-fail">did not run</td>'
    ratio = value / c if c else 0
    # The bar is on a log scale: 1x C is a sliver, 30x C is the whole cell.
    import math
    width = max(3, min(100, 3 + 97 * math.log(max(ratio, 1)) / math.log(30)))
    tone = "good" if ratio <= 1.15 else ("ok" if ratio <= 3 else "slow")
    return (f'<td><span class="bench-bar {tone}" style="width:{width:.0f}%"></span>'
            f'<b>{value:.2f} s</b><i>{ratio:.1f}× C</i></td>')


def bench_table(results, engines):
    head = "".join(f"<th>{esc(label)}</th>" for _, label in engines)
    rows = ""
    for key, title, _ in BENCH_PROGRAMS:
        times = results["times"].get(key, {})
        c = times.get("c")
        cells = "".join(bench_cell(times.get(e), c) for e, _ in engines)
        rows += f'<tr><th scope="row">{esc(title)}<small>{key}.zeno</small></th>{cells}</tr>'
    return f'<div class="bench-table"><table><thead><tr><th></th>{head}</tr></thead><tbody>{rows}</tbody></table></div>'


BENCH_ENGINES = {
    # key: (label, what it is, colour class)
    "c": ("C", "cc -O2. The line every other bar is measured against.", "e-c"),
    "rust": ("Rust", "rustc -C opt-level=3.", "e-rust"),
    "python": ("Python 3", "CPython, the usual python3.", "e-py"),
    "zeno": ("Zeno", "zeno build: C, with the garbage collector and every overflow check.", "e-z1"),
    "zeno-llvm": ("Zeno LLVM", "zeno build --llvm: the same program through LLVM instead of C.", "e-zl"),
    "zeno-release": ("Zeno release", "zeno build --release: no overflow checks, as in Rust's release builds.", "e-z2"),
    "zeno-owned": ("Zeno owned", "zeno build --release --owned: one owner for each value and no collector.", "e-z3"),
    "zeno-fast": ("Zeno fast", "zeno build --fast --owned: no checks a correct program never fails, as in C, and -O3.", "e-z4"),
    "zeno-fast-gc": ("Zeno fast, collector", "zeno build --fast: the same, with the garbage collector.", "e-z4"),
    "zeno-owned-checked": ("Zeno owned, checked", "zeno build --owned: one owner, overflow checks kept.", "e-z2"),
    "zeno-nc": ("Zeno, no collector", "The old build for a chip, with one fixed pool.", "e-z2"),
    "vm": ("zeno run --vm", "The bytecode virtual machine.", "e-vm"),
    "run": ("zeno run", "The interpreter that walks the syntax tree.", "e-run"),
}


def bench_versions(now_big, now_small):
    """Each released version's record (bench/results/versions), oldest
    first, then main as it is now. Times only; the page divides each by
    the C (or Python) time of the same record."""
    import json
    folder = Path(ARGS.zeno) / "bench" / "results" / "versions"
    def key(path):
        return tuple(int(x) for x in path.stem.split("."))
    out = []
    for path in sorted(folder.glob("*.json"), key=key) if folder.exists() else []:
        r = json.loads(path.read_text())
        out.append({"version": r["version"], "date": r["machine"]["date"], "released": True,
                    "big": r["big"]["times"], "small": r["small"]["times"]})
    current = now_big["machine"]["zeno"].split()[-1]
    if not any(v["version"] == current for v in out):
        out.append({"version": current, "date": now_big["machine"]["date"], "released": False,
                    "big": now_big["times"], "small": now_small["times"]})
    return out


def bench_targets():
    """The newest release record with a `targets` table (0.5 on): each program
    written in another language by `zeno build --target` and run there.
    Returns (version, record) or None."""
    import json
    folder = Path(ARGS.zeno) / "bench" / "results" / "versions"
    best = None
    for path in folder.glob("*.json") if folder.exists() else []:
        r = json.loads(path.read_text())
        if "targets" in r:
            v = tuple(int(x) for x in path.stem.split("."))
            if best is None or v > best[0]:
                best = (v, r)
    return (best[1]["version"], best[1]) if best else None


def bench_targets_html(programs):
    """A table: for each target, its time against C on each program, and the geometric mean."""
    import math
    found = bench_targets()
    if not found:
        return ""
    version, record = found
    t = record["targets"]
    engines = [e for e in t["engines"] if e != "c"]
    rows = []
    for e in engines:
        ratios = {k: t["times"][k][e] / t["times"][k]["c"] for k in t["times"]
                  if isinstance(t["times"][k].get(e), (int, float)) and t["times"][k].get("c")}
        if not ratios:
            continue
        mean = math.exp(sum(math.log(r) for r in ratios.values()) / len(ratios))
        rows.append((mean, e, ratios))
    rows.sort()
    top = max(m for m, _, _ in rows)
    def width(r):
        return max(3, round(100 * math.log10(max(r, 1)) / math.log10(top)))
    head = "".join(f"<th>{esc(p['title'])}</th>" for p in programs if p["key"] in t["times"])
    body = ""
    for mean, e, ratios in rows:
        label = t["engines"][e]
        flag, _, how = label.partition(", ")
        cells = "".join(f"<td><b>{ratios[p['key']]:.0f}× C</b></td>" if p["key"] in ratios else "<td>–</td>"
                        for p in programs if p["key"] in t["times"])
        tone = "good" if mean < 15 else "ok" if mean < 60 else "slow"
        body += (f'<tr><th scope="row">{esc(flag)}<small>{esc(how)}</small></th>'
                 f'<td><span class="bench-bar {tone}" style="width:{width(mean)}%"></span><b>{mean:.0f}× C</b><i>on average</i></td>{cells}</tr>')
    return f"""<section class="b-section" id="targets">
  <h2>The program in other languages</h2>
  <p class="b-sub">New in 0.5: <a href="/docs/targets/"><code>zeno build --target</code></a> writes a program in another language. Here each one is run with that language's own tools, at the small sizes, so the times include starting Node, the JVM or .NET. Every cell is a time divided by the time of the same program in C. Smaller is faster. From the record of {esc(version)}.</p>
  <div class="bench-table"><table><thead><tr><th></th><th>Average</th>{head}</tr></thead><tbody>{body}</tbody></table></div>
  <p class="b-note">A written program carries Zeno's rules with it, so it does what <code>zeno run</code> does, checks and all, in a language that was not built for them. <code>zeno run --vm</code> is in the table as a guide. The targets are for reading, keeping and running a program where Zeno is not; for speed, <code>zeno build --fast</code> is the way.</p>
</section>
"""


def build_benchmarks():
    import json, math
    now_big, now_small = bench_results("now-big"), bench_results("now-small")
    before_big = bench_results("before-big")
    if now_big is None or now_small is None or before_big is None:
        print("  benchmarks: no results in bench/results; page skipped")
        return
    m = now_big["machine"]
    sets = {
        "compiled": {"title": "Compiled", "res": now_big,
                     "engines": ["c", "rust", "zeno", "zeno-llvm", "zeno-release", "zeno-owned", "zeno-fast", "zeno-fast-gc"],
                     "on": ["c", "rust", "zeno", "zeno-owned", "zeno-fast"]},
        "interpreted": {"title": "Interpreted", "res": now_small,
                        "engines": ["c", "python", "vm", "run", "zeno", "zeno-owned"],
                        "on": ["c", "python", "vm", "run"]},
    }
    data = {
        "programs": [{"key": k, "title": t, "about": d} for k, t, d in BENCH_PROGRAMS],
        "engines": {k: {"label": v[0], "about": v[1], "tone": v[2]} for k, v in BENCH_ENGINES.items()},
        "sets": {name: {"title": s["title"], "engines": [e for e in s["engines"] if any(e in t for t in s["res"]["times"].values())],
                        "on": s["on"], "times": s["res"]["times"], "sizes": s["res"].get("sizes", {})}
                 for name, s in sets.items()},
        "before": before_big["times"],
        "machine": m,
        "versions": bench_versions(now_big, now_small),
    }
    (SITE / "benchmarks").mkdir(exist_ok=True)
    (SITE / "benchmarks" / "data.json").write_text(json.dumps(data, indent=1) + "\n")

    # Headline numbers, worked out from the results so they stay true.
    t = now_big["times"]
    def ratio(p, e): return t[p][e] / t[p]["c"]
    keys = [k for k, _, _ in BENCH_PROGRAMS if k in t]
    best = "zeno-fast" if all("zeno-fast" in t[k] for k in keys) else "zeno-owned"
    geo = math.exp(sum(math.log(ratio(k, best)) for k in keys) / len(keys))
    trees = t["trees"]["c"] / t["trees"]["zeno-owned"]
    gain = before_big["times"]["trees"]["zeno"] / t["trees"]["zeno-owned"]
    py = math.exp(sum(math.log(now_small["times"][k]["python"] / now_small["times"][k]["zeno-owned"]) for k in keys) / len(keys))
    stats = [
        (f"{geo:.2f}", "× the time of C", f"{'zeno build --fast' if best == 'zeno-fast' else 'Zeno owned'}, across all six programs (geometric mean)"),
        (f"{trees:.1f}", "× faster than C", "on many small objects, where its pool beats malloc"),
        (f"{gain:.1f}", "× faster than before", "on the same objects, since the paged collector and owned memory"),
        (f"{py:.0f}", "× faster than Python", "compiled Zeno, on average"),
    ]
    stat_html = "".join(f'<div class="b-stat"><b data-count="{n}">{n}</b><span>{u}</span><small>{d}</small></div>' for n, u, d in stats)

    noscript = f"<noscript>{bench_table(now_big, [(e, BENCH_ENGINES[e][0]) for e in sets['compiled']['on']])}</noscript>"
    modes = [
        ("run", "zeno run", "Walks the syntax tree", "Every step looks at a node of the tree and decides what it means. Simple, exact errors, and slow.", "tree"),
        ("vm", "zeno run --vm", "Runs bytecode", "The tree is turned into a flat list of small instructions once, then a loop runs them. Two to three times faster.", "layers"),
        ("zeno", "zeno build", "Compiles to C", "The program becomes C and then machine code. Each value is found by a garbage collector, and each <code>+</code> checks for overflow.", "cpu"),
        ("zeno-owned", "--release --owned", "No collector, no overflow checks", "Each value has one owner and is freed at a line you can point to, from a pool that hands out a block in a few instructions.", "memory"),
        ("zeno-fast", "--fast --owned", "No checks a correct program never fails", "No index checks either, a float divided by zero is infinity, and the C compiler tries its hardest. As fast as C, and as unforgiving.", "zap"),
    ]
    mode_html = "".join(
        f'<li class="b-mode {BENCH_ENGINES[k][2]}"><span class="b-mode-ico">{icon(ic)}</span><code>{esc(cmd)}</code><b>{head}</b><p>{txt}</p>'
        f'<span class="b-mode-speed" data-mode="{k}"></span></li>' for k, cmd, head, txt, ic in modes)

    body = f"""<div class="b">
<header class="b-hero">
  <p class="eyebrow">{icon("chart")}Benchmarks</p>
  <h1>How fast is Zeno?</h1>
  <p class="lede">Six programs, written once in Zeno, C, Rust and Python, doing the same steps. Every time was measured, and counts only if the program printed exactly what C printed.</p>
  <div class="b-stats">{stat_html}</div>
</header>

<section class="b-section" id="chart">
  <div class="b-controls">
    <div class="segmented" role="tablist" aria-label="Which programs" id="b-set">
      <button role="tab" aria-selected="true" data-set="compiled" aria-controls="b-board" id="b-t-compiled">Compiled</button>
      <button role="tab" aria-selected="false" data-set="interpreted" aria-controls="b-board" id="b-t-interpreted" tabindex="-1">Interpreted</button>
    </div>
    <div class="b-view" role="group" aria-label="Show">
      <button type="button" data-view="ratio" aria-pressed="true">× C</button><button type="button" data-view="seconds" aria-pressed="false">Seconds</button>
    </div>
  </div>
  <div class="b-legend" id="b-legend" aria-label="Show or hide a language"></div>
  <div class="b-board" id="b-board" role="tabpanel" aria-labelledby="b-t-compiled"></div>
  <p class="b-note" id="b-note"></p>
  {noscript}
</section>

<section class="b-section b-split">
  <div>
    <h2>Before and after</h2>
    <p>Drag to compare. Before is the first run, when the collector kept every block in one table that it sorted on each collection. Now it keeps them in pages, and a program can choose <code>memory owned</code> instead (<a href="/decisions/">decision 22.5</a>).</p>
    <label class="b-slider"><span>Before</span><input type="range" min="0" max="100" value="100" id="b-slide" aria-label="Before or now"><span>Now</span></label>
  </div>
  <div class="b-ba" id="b-ba"></div>
</section>

{bench_targets_html([{"key": k, "title": t} for k, t, _ in BENCH_PROGRAMS])}
<section class="b-section" id="versions">
  <h2>Version by version</h2>
  <p class="b-sub">Each release keeps a record of its times, made with <a href="{GITHUB}/blob/main/bench/record.py"><code>bench/record.py</code></a>. Every cell is a time divided by the time of C (or of Python, for the ways that interpret) in the same run, so records made on different days still line up. Smaller is faster.</p>
  <div class="b-controls">
    <div class="segmented" role="tablist" aria-label="Which way to run" id="b-ver-set">
      <button role="tab" aria-selected="true" data-ver="zeno" aria-controls="b-vers" id="b-v-zeno">zeno build</button>
      <button role="tab" aria-selected="false" data-ver="best" aria-controls="b-vers" id="b-v-best" tabindex="-1">Fastest build</button>
      <button role="tab" aria-selected="false" data-ver="vm" aria-controls="b-vers" id="b-v-vm" tabindex="-1">zeno run --vm</button>
      <button role="tab" aria-selected="false" data-ver="run" aria-controls="b-vers" id="b-v-run" tabindex="-1">zeno run</button>
    </div>
  </div>
  <div class="b-vers" id="b-vers" role="tabpanel"></div>
  <p class="b-note" id="b-vers-note"></p>
</section>

<section class="b-section">
  <h2>Five ways to run a program</h2>
  <p class="b-sub">The same file, run five ways. Each step down does more work before the program starts, and less while it runs.</p>
  <ol class="b-modes">{mode_html}</ol>
</section>

<section class="b-section b-why">
  <h2>What the numbers say</h2>
  <div class="cards">
    <div class="card">{icon("zap")}<b>Owned memory matches C and Rust</b><span>On programs that make many objects it is faster: its pool hands out and takes back a block in a few instructions, where C calls <code>malloc</code> and <code>free</code>.</span></div>
    <div class="card">{icon("check")}<b>Checks cost a little</b><span>Most of the gap on arithmetic is the overflow check on every <code>+</code>, which <code>--release</code> drops, as Rust's release builds do. Index checks stay.</span></div>
    <div class="card">{icon("memory")}<b>A collector costs more</b><span>It has to look at what is still in use, again and again: about two times C on many small objects. That is why a program can choose.</span></div>
    <div class="card">{icon("zap")}<b><code>--fast</code> runs the instructions C runs</b><span>It tells the C compiler what a C program tells it: a whole number does not overflow. On the loop of whole numbers it runs 300.27 million instructions where C runs 300.26 million (decision 23.6).</span></div>
    <div class="card">{icon("layers")}<b>Where Rust leads, and why</b><span>On nbody, Rust's compiler knows there are exactly five bodies and builds the loop for five. With the number hidden from it, Rust is behind both C and Zeno. Zeno does not chase a benchmark (decision 23.4).</span></div>
    <div class="card">{icon("gauge")}<b>Text and floats are level with C</b><span><code>for ch in text</code> walks the text without making a list of it, and a field a function never writes is read once, as a C programmer would by hand (decisions 22.7 and 22.8).</span></div>
  </div>
  <p class="b-sub">Choose once, in <code>zeno.package</code>, with <code>memory owned</code>, or for one build with <code>zeno build --owned</code>. See <a href="/docs/memory-modes/">Choosing how memory is freed</a>.</p>
</section>

<section class="b-section b-method">
  <h2>How it was measured</h2>
  <p>Wall-clock time of the whole program, best of three. Compiled programs at full size, interpreted ones at a tenth of it. {esc(m["cpu"])}, {m["cores"]} cores, Linux, on {esc(m["date"])}. {esc(m["zeno"])}, {esc(m["cc"].split(" (")[0])} {esc(m["cc"].split(") ")[-1])} with <code>-O2</code>, {esc(m["rustc"].split(" (")[0])} with <code>-C opt-level=3</code>, Python {esc(m["python"])}.</p>
  <p>The programs and the script are in <a href="{GITHUB}/tree/main/bench"><code>bench/</code></a>. The numbers on this page are in <a href="/benchmarks/data.json">data.json</a>.</p>
  <figure class="window shell"><figcaption>{icon("terminal")}<span class="file">Terminal</span><button class="copy" type="button" data-copy="b-cmd">{icon("copy")}<span>Copy</span></button></figcaption>
  <pre id="b-cmd"><code>cargo build --release
python3 bench/run.py --size big --engines c,rust,zeno,zeno-release,zeno-owned</code></pre></figure>
</section>
<script id="b-data" type="application/json">{json.dumps(data).replace("</", "<\\/")}</script>
<script src="/assets/bench.js" defer></script>
</div>"""
    layout("/benchmarks/", "Benchmarks", "Zeno next to C, Rust and Python on six programs, measured, with interactive charts.", body, "/benchmarks/")


def build_404():
    body = f"""<div class="narrow lost">
<p class="eyebrow">{icon("compass")}404</p>
<h1>Halfway there, forever</h1>
<p class="lede">This page does not exist. Like Achilles, you got close.</p>
<figure class="window"><figcaption>{icon("terminal")}<span class="file">zeno run</span></figcaption><pre class="out"><code>error: this page is not declared. Create it with `let` or `var` first</code></pre></figure>
<p class="actions"><a class="button" href="/">Go home</a><a class="button ghost" href="/learn/">Read the guide</a></p>
</div>"""
    layout("/404.html", "Page not found", "This page does not exist.", body)


# --- Home --------------------------------------------------------------------

def target_js(name):
    """The program part of what `zeno build --target js` writes for a snippet (the runtime above it is left out)."""
    zeno = Path(ARGS.zeno) / "target" / "release" / "zeno"
    with tempfile.TemporaryDirectory() as tmp:
        shutil.copy(SNIPPETS / f"{name}.zeno", tmp)
        subprocess.run([str(zeno), "build", "--target", "js", f"{name}.zeno"], cwd=tmp, check=True, capture_output=True)
        text = (Path(tmp) / f"{name}.js").read_text()
    program = text.split("// The program.\n", 1)[1].rstrip()
    return window(f"{name}.js", "// … Zeno's rules for JavaScript, then:\n" + program, lang="js")


TARGET_NAMES = {"js": "JavaScript", "ts": "TypeScript", "html": "A web page", "py": "Python", "go": "Go",
                "java": "Java", "cs": "C#", "cpp": "C++", "rust": "Rust", "wasm": "WebAssembly", "php": "PHP",
                "rb": "Ruby", "ruby": "Ruby", "lua": "Lua", "dart": "Dart", "kt": "Kotlin", "kotlin": "Kotlin"}
COUNT_WORDS = ["zero", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine", "ten",
               "eleven", "twelve", "thirteen", "fourteen", "fifteen", "sixteen"]


def targets():
    """The targets of `zeno build --target`, from the table in docs/targets.md: (flag, name, how to run it)."""
    text = (Path(ARGS.zeno) / "docs" / "targets.md").read_text()
    rows = re.findall(r"^\| `([a-z]+)` \| [^|]+ \| ([^|]+) \|$", text, re.M)
    out = []
    for flag, run in rows:
        run = re.sub(r"\s*\(.*?\)", "", run).strip()
        run = re.findall(r"`([^`]+)`", run)[0] if "`" in run else run
        out.append((flag, TARGET_NAMES.get(flag, flag), run.split(" && ")[0]))
    return out


def target_grid():
    return '<ul class="target-grid">' + "".join(
        f"<li><b>{esc(name)}</b><code>--target {flag}</code><span>{esc(run)}</span></li>" for flag, name, run in targets()) + "</ul>"


def build_home():
    source = (TOOLS / "home.html").read_text()

    def code(m):
        name, skip = m.group(1), int(m.group(2) or 0)
        lines = snippet(name).split("\n")[skip:]
        return esc("\n".join(lines))

    source = re.sub(r"<!--CODE:(\w+)(?::(\d+))?-->", code, source)
    source = re.sub(r"<!--OUT:(\w+)-->", lambda m: esc(run_zeno(SNIPPETS / f"{m.group(1)}.zeno")), source)
    source = re.sub(r"<!--WINDOW:(\w+)-->", lambda m: sample(m.group(1)), source)
    source = re.sub(r"<!--TARGET-JS:(\w+)-->", lambda m: target_js(m.group(1)), source)
    source = source.replace("<!--TARGET-GRID-->", target_grid()).replace("<!--TARGET-COUNT-->", COUNT_WORDS[len(targets())])
    source = icons_in(source)
    assert "<!--" not in source.replace("<!-- ", "")
    layout("/", "Zeno: code that reads like what it means",
           "Zeno is a small programming language that reads like plain English and is checked before it runs. "
           "Whole-word keywords, optional types, and builds small enough for a microcontroller.",
           source, home=True)


def build_playground():
    """/playground/: the page `zeno playground` writes, to try Zeno with nothing installed."""
    wasm = Path(ARGS.zeno) / "target" / "wasm32-unknown-unknown" / "release" / "zeno.wasm"
    if not wasm.exists():
        sys.exit("build the WebAssembly compiler first: cargo build --release --target wasm32-unknown-unknown")
    zeno = Path(ARGS.zeno) / "target" / "release" / "zeno"
    with tempfile.TemporaryDirectory() as tmp:
        subprocess.run([str(zeno), "playground"], cwd=tmp, check=True,
                       env={**os.environ, "ZENO_WASM": str(wasm)}, capture_output=True)
        dest = SITE / "playground"
        dest.mkdir(exist_ok=True)
        shutil.copy(Path(tmp) / "playground.html", dest / "index.html")
    add_social(dest / "index.html", "/playground/")
    PAGES.append("/playground/")


def build_book():
    """Copy The Zeno Book, built in the language repository, to /book/."""
    src = Path(ARGS.zeno) / "book" / "dist" / "html"
    if not (src / "index.html").exists():
        sys.exit("build the book first: python3 book/tools/build.py")
    dest = SITE / "book"
    shutil.rmtree(dest, ignore_errors=True)
    shutil.copytree(src, dest)
    for page in sorted(dest.glob("*.html")):
        path = "/book/" if page.name == "index.html" else f"/book/{page.name}"
        add_social(page, path)
        PAGES.append(path)


def build_sitemap():
    urls = "".join(f"<url><loc>{ORIGIN}{p}</loc></url>" for p in PAGES if p != "/404.html")
    (SITE / "sitemap.xml").write_text(
        f'<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">{urls}</urlset>\n')
    (SITE / "robots.txt").write_text(f"User-agent: *\nAllow: /\nSitemap: {ORIGIN}/sitemap.xml\n")


def main():
    global ARGS, SNIPPET_EXAMPLES
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--zeno", required=True, help="a checkout of zeno-lang, built with cargo build --release")
    ARGS = parser.parse_args()
    SNIPPET_EXAMPLES = Path(ARGS.zeno) / "examples"
    if not (Path(ARGS.zeno) / "target" / "release" / "zeno").exists():
        sys.exit("build the compiler first: cargo build --release")
    build_home()
    build_learn()
    build_examples()
    build_docs()
    build_decisions()
    build_roadmap()
    build_about()
    build_book()
    build_playground()
    build_download()
    build_benchmarks()
    build_privacy()
    build_404()
    build_sitemap()
    print(f"wrote {len(PAGES)} pages")


if __name__ == "__main__":
    main()
