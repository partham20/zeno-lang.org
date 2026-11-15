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
import html
import os
import re
import subprocess
import sys
from pathlib import Path

import markdown

sys.path.insert(0, str(Path(__file__).resolve().parent))
from icons import icon  # noqa: E402

SITE = Path(__file__).resolve().parent.parent
TOOLS = SITE / "tools"
SNIPPETS = TOOLS / "snippets"
GITHUB = "https://github.com/partham20/zeno-lang"
ORIGIN = "https://zeno-lang.org"

ARGS = None
PAGES = []          # every path written, for the sitemap


# --- Running Zeno -------------------------------------------------------------

def run_zeno(path, lines=None):
    """What `zeno run` prints for a file, errors included, as on a terminal."""
    exe = Path(ARGS.zeno) / "target" / "release" / "zeno"
    try:
        done = subprocess.run([str(exe), "run", path.name], cwd=path.parent,
                              capture_output=True, text=True, timeout=lines and 3 or 30)
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

NAV = [("Learn", "/learn/"), ("Examples", "/examples/"), ("Docs", "/docs/"),
       ("Decisions", "/decisions/"), ("Roadmap", "/roadmap/"), ("About", "/about/")]

# The wordmark: the name in block capitals, with the Z drawn as an arrow and
# one dot the arrow never reaches. Letters take the text colour, the dot is cobalt.
MARK = ('<svg class="mark" viewBox="0 0 350 88" aria-hidden="true"><path fill-rule="evenodd" d="'
        'M0 0H80V18L28 70H67L84 79L67 88H0V70L52 18H0L9 9Z'
        'M92 0H150V18H110V35H140V53H110V70H150V88H92Z'
        'M163 88V0H184L217 55V0H235V88H214L181 33V88Z'
        'M288 0C310 0 328 18 328 44C328 70 310 88 288 88C266 88 248 70 248 44C248 18 266 0 288 0Z'
        'M288 18C276 18 266 29 266 44C266 59 276 70 288 70C300 70 310 59 310 44C310 29 300 18 288 18Z"/>'
        '<circle class="dot" cx="343.5" cy="79" r="6.5"/></svg>')


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
<meta property="og:title" content="{html.escape(full_title)}">
<meta property="og:description" content="{html.escape(description)}">
<meta property="og:type" content="website">
<meta property="og:url" content="{ORIGIN}{path}">
<meta property="og:image" content="{ORIGIN}/og.png">
<meta name="twitter:card" content="summary_large_image">
<meta name="theme-color" content="#f7f8fa" media="(prefers-color-scheme: light)">
<meta name="theme-color" content="#0a0a0a" media="(prefers-color-scheme: dark)">
<link rel="canonical" href="{ORIGIN}{path}">
<link rel="icon" href="/favicon.svg" type="image/svg+xml">
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
    <a class="button small ghost" href="{GITHUB}">{icon("github")}GitHub</a>
  </div>
</header>
<main id="content"{' class="home"' if home else ''}>
{body}
</main>
<footer class="foot">
<div class="foot-inner">
  <div class="chase" aria-hidden="true">
    <i class="tick" style="left:50%"></i><i class="tick" style="left:75%"></i><i class="tick" style="left:87.5%"></i>
    <span class="runner" id="runner"></span><span class="tortoise"></span>
  </div>
  <div class="chase-text"><p>Every journey is halfway done. Forever.</p><span id="chase-count">The runner has closed 0 of 1 halves</span></div>
  <p class="foot-about">Zeno of Elea said Achilles can never catch the tortoise: first he must cover half the distance, then half of what is left, without end. It suits a compiler that will always be almost finished. The bar at the top of each page works the same way.</p>
  <div class="foot-links">
    <div><h4>Learn</h4><a href="/learn/">The guide</a><a href="/learn/#install">Install</a><a href="/examples/">Examples</a></div>
    <div><h4>Understand</h4><a href="/docs/">How the compiler works</a><a href="/decisions/">Design decisions</a><a href="/roadmap/">Roadmap</a></div>
    <div><h4>Project</h4><a href="/about/">About</a><a href="{GITHUB}">Source on GitHub</a></div>
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

DOC_ICONS = {"The front end": "tree", "The engines": "play", "Memory": "memory",
             "Firmware and hardware": "cpu", "The type system": "copies", "More": "book"}

DOC_GROUPS = [
    ("The front end", "From text to a checked program.",
     ["lexer", "parser", "checker"]),
    ("The engines", "Four ways to run the same program.",
     ["interpreter", "vm", "compiler", "llvm"]),
    ("Memory", "A collector, owners, and a fixed pool.",
     ["memory", "ownership", "no-collector", "pool", "text", "temporaries", "one-owner", "unsafe"]),
    ("Firmware and hardware", "Errors as values, pins and clocks, sized numbers.",
     ["firmware", "board", "sized-ints"]),
    ("The type system", "Code written once for many types.",
     ["generics"]),
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


def build_examples():
    folder = Path(ARGS.zeno) / "examples"
    order = ["hello", "tour", "styles", "primes", "shapes", "sensor", "generics", "packet",
             "commands", "handlers", "signal", "blink", "buffer", "memory", "labels", "words",
             "scheduler", "driver"]
    names = [n for n in order if (folder / f"{n}.zeno").exists()]
    names += sorted(p.stem for p in folder.glob("*.zeno") if p.stem not in names)
    cards = ""
    for i, name in enumerate(names):
        path = folder / f"{name}.zeno"
        title = example_meta(path)
        code = path.read_text().rstrip("\n")
        lines = FOREVER.get(name)
        output = run_zeno(path, lines)
        note = (f'<p class="note-small">This program runs until it is stopped. The first {lines} lines are shown.</p>'
                if lines else "")
        prev_link = f'<a class="prev" href="/examples/{names[i-1]}/"><span>Previous</span>{names[i-1]}.zeno</a>' if i else "<span></span>"
        next_link = f'<a class="next" href="/examples/{names[i+1]}/"><span>Next</span>{names[i+1]}.zeno</a>' if i + 1 < len(names) else "<span></span>"
        page = f"""<div class="narrow">
  <p class="eyebrow">{icon("code")}<a href="/examples/">Examples</a></p>
  <h1 class="example-title">{esc(title)}</h1>
  <p class="lede small">The whole of <code>examples/{name}.zeno</code>, and what <code>zeno run</code> prints for it.</p>
  {window(f"{name}.zeno", code, output, f"zeno run examples/{name}.zeno")}
  {note}
  <p class="source">See it on GitHub: <a href="{GITHUB}/blob/main/examples/{name}.zeno">examples/{name}.zeno</a>.</p>
  <nav class="pager" aria-label="Previous and next">{prev_link}{next_link}</nav>
</div>"""
        layout(f"/examples/{name}/", f"{name}.zeno", f"{title}. A Zeno example, with its output.", page, "/examples/")
        lines_count = len(code.split("\n"))
        kind = "cpu" if name in FIRMWARE else "code"
        cards += (f'<li><a href="/examples/{name}/">{icon(kind)}<b>{esc(title)}</b>'
                  f'<span><code>{name}.zeno</code></span><small>{lines_count} lines</small></a></li>')
    body = page_head("Examples", "Programs to read and run",
                     "Every example in the language repository, from one line to a driver that works memory by hand. "
                     "Each page shows what <code>zeno run</code> printed. The chip marks a firmware program.", "code") + \
        f'<ul class="index examples">{cards}</ul>'
    layout("/examples/", "Examples", "Example Zeno programs, from one line to firmware, each with its output.", body, "/examples/")


# --- Learn -------------------------------------------------------------------

GUIDE = [
    ("install", "Install", None, """
<p>Zeno is built from source. You need <a href="https://rustup.rs">Rust</a>, and a C compiler if you want <code>zeno build</code>. For <code>zeno build --llvm</code> you also need clang 15 or later. There is nothing else to install.</p>
<figure class="window shell"><figcaption><!--ICON:terminal--><span class="file">Terminal</span><button class="copy" type="button" data-copy="install-cmd"><!--ICON:copy--><span>Copy</span></button></figcaption>
<pre id="install-cmd"><code>git clone https://github.com/partham20/zeno-lang
cd zeno-lang
cargo build --release
./target/release/zeno run examples/hello.zeno</code></pre></figure>
<p>The rest of this guide writes <code>zeno</code> for that program. Put <code>target/release</code> on your <code>PATH</code>, or use <code>cargo run --</code> in its place.</p>"""),
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
    ("classes", "Classes", "classes", """
<p>A class lists its fields at the top and gets a constructor for free, which takes the fields in order or by name. Methods name <code>self</code> explicitly.</p>"""),
    ("enums", "Enums and match", "shapes", """
<p>Each case of an enum can carry its own values, and <code>match</code> takes them apart. A <code>match</code> must handle every case. This one forgets <code>Dot</code>, so nothing runs.</p>"""),
    ("none", "Values that may be missing", "users", """
<p>A value can be <code>none</code> only if its type says <code>or none</code>. Before you use it, you check it with <code>is not none</code>, and inside that check it is the plain type.</p>"""),
    ("errors", "Errors", "ports", """
<p><code>try</code>, <code>except</code> and <code>raise</code> read as they do in Python. A function that can fail says so with <code>raises</code>, and the checker makes sure the error is handled or passed on. Any class can be raised, so an error can carry data.</p>"""),
    ("units", "Units", "delay", """
<p>A number can carry a unit: <code>500 ms</code>, <code>3.3 V</code>. The unit is part of the type, so a function that wants milliseconds will not take a bare number.</p>"""),
    ("sized", "Numbers with a size", "packet", """
<p><code>u8</code>, <code>u16</code>, <code>u32</code>, <code>i8</code>, <code>i16</code> and <code>i32</code> have a size, and <code>&amp;</code>, <code>|</code>, <code>^</code>, <code>~</code>, <code>&lt;&lt;</code> and <code>&gt;&gt;</code> work on their bits. Arithmetic gives a full <code>int</code>, <code>u8(n)</code> checks that <code>n</code> fits, and <code>u8.wrap(n)</code> keeps the low eight bits on purpose. A <code>u8</code> field is one byte in a compiled object.</p>"""),
    ("generics", "Generics", "stack", """
<p><code>class Stack[T]</code> and <code>function largest[T]</code> are written once, with <code>T</code> standing for a type. A call never says what <code>T</code> is: the checker works it out, and the compilers make one copy for each type used, so a <code>Stack[u8]</code> is as small as one written for bytes by hand.</p>"""),
    ("ownership", "Owned values", "frame", """
<p>Most values are shared, and a garbage collector frees them. A value marked <code>owned</code> has one owner instead, and is freed the moment its owner's block ends. A parameter only looks at what it is given, unless it says <code>take</code>. Giving the value away empties the old name, and the checker points at any later use.</p>"""),
    ("board", "Pins and time", "board", """
<p><code>from board import led, pin</code> and <code>from time import sleep, now</code> give a program pins and a clock. On a computer the board is simulated and prints each pin as it changes. A compiled program meets a real board through four C functions.</p>"""),
]


LESSON_ICONS = {"install": "terminal", "first": "play", "variables": "type", "typos": "scan", "numbers": "chart",
                "overflow": "gauge", "control": "loop", "truth": "check", "functions": "function", "closures": "braces",
                "lists": "words", "classes": "package", "enums": "layers", "none": "none", "errors": "alert",
                "units": "ruler", "sized": "memory", "generics": "copies", "ownership": "key", "board": "board"}


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
]
NEXT = [
    ("In progress", "An audit for clarity", "Every part of the language checked against one rule: unambiguous and intuitive. A parameter now looks, and <code>take</code> takes."),
    ("Planned", "Standard library", "Files, text and collections."),
    ("Planned", "Modules", "Programs across many files."),
    ("Planned", "Package manager", "Share and reuse code."),
    ("Planned", "Editor support", "A formatter and a language server."),
    ("Planned", "C interop", "Call C libraries, and be called from C."),
    ("Planned", "WebAssembly", "Zeno in the browser."),
    ("Planned", "async and await", "Servers and networking."),
]


def build_roadmap():
    done = "".join(
        f'<li><a href="/docs/{doc}/">{icon("check")}<b>{t}</b><span>{d}</span></a></li>' for t, d, doc in DONE)
    upcoming = "".join(
        f'<li class="{s.split()[0].lower()}">{icon("clock" if s == "In progress" else "map")}<i>{s}</i><b>{t}</b><span>{d}</span></li>'
        for s, t, d in NEXT)
    body = page_head("Roadmap", "Where Zeno stands",
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
<p>Zeno is young. It runs programs, checks them, and compiles them to C and to LLVM, but the syntax can still change and there is no standard library yet. It is a language to read, learn from and experiment with. See the <a href="/roadmap/">roadmap</a>.</p>
<h2>The code</h2>
<p>The compiler is plain Rust with no dependencies, about {lines_of_code()} lines with its C runtime, in <a href="{GITHUB}">partham20/zeno-lang</a>. This website is plain HTML, CSS and a little JavaScript, built by a short script that runs every sample through Zeno.</p>
</div>"""
    layout("/about/", "About", "Zeno is a programming language built from scratch by a firmware engineer, to learn by building.", body, "/about/")


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

def build_home():
    source = (TOOLS / "home.html").read_text()

    def code(m):
        name, skip = m.group(1), int(m.group(2) or 0)
        lines = snippet(name).split("\n")[skip:]
        return esc("\n".join(lines))

    source = re.sub(r"<!--CODE:(\w+)(?::(\d+))?-->", code, source)
    source = re.sub(r"<!--OUT:(\w+)-->", lambda m: esc(run_zeno(SNIPPETS / f"{m.group(1)}.zeno")), source)
    source = re.sub(r"<!--WINDOW:(\w+)-->", lambda m: sample(m.group(1)), source)
    source = icons_in(source)
    assert "<!--" not in source.replace("<!-- ", "")
    layout("/", "Zeno: code that reads like what it means",
           "Zeno is a small programming language that reads like plain English and is checked before it runs. "
           "Whole-word keywords, optional types, and builds small enough for a microcontroller.",
           source, home=True)


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
    build_404()
    build_sitemap()
    print(f"wrote {len(PAGES)} pages")


if __name__ == "__main__":
    main()
