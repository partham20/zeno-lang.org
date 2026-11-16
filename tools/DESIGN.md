# Design notes for zeno-lang.org

What the site should feel like, and why each choice was made, so later
changes keep to the same idea.

## The subject

Zeno is a programming language whose two rules are "words over symbols"
and "punctuation has to earn its place", built firmware-first, and named
after Zeno's paradox of the runner who closes half the distance forever.
Every visual choice comes from one of those three things.

## The one memorable thing

The first screen shows a line of C-style code losing its punctuation:
`;`, `&&`, `!`, `( )` lift off and fade, and the words `and`, `not`
take their place, until the line is Zeno. It is the language's whole
argument in four seconds. Everything else on the page stays quiet.

The paradox appears three times and nowhere else: the logo, the thin bar
at the top that closes half the remaining distance as you scroll, and the
runner in the footer who never reaches the tortoise.

## Logo

"Almost": the name in lowercase strokes of one weight, with an o whose
ring stops just short of closing and a dot where the ends would meet. It
is the paradox in one letter: nearly there, never quite. The letters take
the text colour and the dot is Cobalt, so the logo needs no colours of its
own. The icon is "Checked": a Z whose diagonal is a tick, for a language
that checks every program before it runs, in the light text colour with a
Cobalt tick on the dark page colour, because four letters do not survive
16 pixels. Both were the most-voted of twenty concepts (2026-11-15); the
tortoise, joint top among the marks, stays as the footer mascot.

`favicon.svg` is the source. `favicon.ico` (16, 32 and 48 pixels) and
`apple-touch-icon.png` (180 pixels, square, because iOS rounds the corners
itself) are the same drawing for browsers that do not take an SVG icon.

## Colour

| Name | Light | Dark | Use |
|---|---|---|---|
| Paper | `#f7f8fa` | `#0a0a0a` | page |
| Sheet | `#ffffff` | `#141414` | code, panels |
| Ink | `#0f1729` | `#ededed` | text |
| Slate | `#566176` | `#a1a1a1` | secondary text |
| Rule | `#e3e7ef` | `#262626` | lines |
| Accent (Windows blue) | `#0078d4` | `#0078d4` | buttons (white text), icons, bars, focus |
| Accent text | `#0078d4` | `#4ca3ff` | links and small blue text, lighter in dark mode so it reads on black; soft tint `#e5f1fb` / `#101a24`, keywords `#0078d4` / `#6cb6ff` |
| Signal | `#f26b2b` | `#ff8a52` | the LED, warnings, nothing else |

In light mode the neutrals lean slightly toward navy, so the page reads as
one colour family. Dark mode is a plain neutral black and grey, as most
dark sites are (Partha's choice, 2026-11-15), with the accent as the only colour. The accent is the Windows accent blue, chosen by Partha on 2026-11-16 (it replaced the earlier cobalt #2f5bea); the same blue in both modes, with white text on filled buttons; only small text and links use the lighter `--cobalt-text` in dark mode, for contrast on black. The CSS variable is still called `--cobalt`. Signal comes from
the amber LED on a development board.

## Type

Hanken Grotesk for everything you read: a clean grotesque, close to the
system faces of large product sites without being one of the defaults.
Headlines are set large, at weight 600, with tight spacing. JetBrains Mono
only for code, because code is the content here.

## Layout

Left-aligned, with a wide measure for headlines and under 70 characters
for paragraphs. Sections vary: a split hero, a two-column ledger, an
interactive tour, a list with rules instead of a grid of cards, a full
dark band for firmware, a diagram, a strip of milestones.

## Motion

One orchestrated moment (the hero), and motion only where it carries
meaning: the simulated board blinks because the program does, the
compiler diagram pulses along the path a program takes, tabs slide to
show what changed. Nothing fades in just for arriving. Everything stops
for reduced motion.

## Avoided on purpose

Gradient text, a coloured word inside a headline, all-caps labels above
headings, monospace for small labels, an arrow after every link, identical
icon cards, big-number stat rows, glass panels, and the cream-and-serif look.
