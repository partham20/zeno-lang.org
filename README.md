# zeno-lang.org

The website of [Zeno](https://github.com/partham20/zeno-lang), a programming language that reads like plain English and is checked before it runs.

It is a static site with no build step and no dependencies:

```
index.html    the page
style.css     the styles, with a light and a dark theme
main.js       the Zeno highlighter, the tour tabs and the simulated board
favicon.svg   the mark: a bar that halves, and halves again
og.png        the picture shown when the link is shared
```

To look at it, open `index.html` in a browser, or serve the folder:

```sh
python3 -m http.server 8000
```

Every code sample on the page was run with `zeno run`, and the output under it is what Zeno printed. When the language changes, run the samples again and update both.
