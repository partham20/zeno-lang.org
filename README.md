# zeno-lang.org

The website of [Zeno](https://github.com/partham20/zeno-lang), a programming language that reads like plain English and is checked before it runs.

The pages are plain HTML, committed as they are, so any static host can serve this folder with no build step.

```
index.html          the home page
learn/              the guide: the whole language, a step at a time
examples/           every example program, with its output
docs/               how each stage of the compiler works
decisions/          every design decision, with its reason
roadmap/  about/    where Zeno stands, and what it is
404.html            the page for a link that goes nowhere
assets/style.css    the styles, with a light and a dark theme
assets/main.js      the Zeno highlighter, the tour tabs, the simulated board
tools/              the script that writes the pages, and the samples it runs
```

## Building the pages

The pages are written by `tools/build.py`. It runs every code sample through
`zeno run` and puts the real output under it, and it turns the `docs/` folder
of the language repository into the Docs and Decisions pages. When the
language changes, build again:

```sh
pip install markdown pymdown-extensions
(cd ../zeno-lang && cargo build --release)
python3 tools/build.py --zeno ../zeno-lang
```

The home page's text is in `tools/home.html`, the guide's text is in
`tools/build.py`, and the samples are in `tools/snippets/`. The line icons
are in `tools/icons.py` (write `<!--ICON:name-->` in `home.html`), and the
reasons behind the look, colours, type and motion are in `tools/DESIGN.md`.

To look at the site, serve the folder, since links start at the site root:

```sh
python3 -m http.server 8000
```
