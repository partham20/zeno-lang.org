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

The paradox appears twice and nowhere else: the thin bar at the top that
closes half the remaining distance as you scroll, and the runner in the
footer who never reaches the tortoise.

## Colour

| Name | Light | Dark | Use |
|---|---|---|---|
| Paper | `#f7f8fa` | `#0a0a0a` | page |
| Sheet | `#ffffff` | `#141414` | code, panels |
| Ink | `#0f1729` | `#ededed` | text |
| Slate | `#566176` | `#a1a1a1` | secondary text |
| Rule | `#e3e7ef` | `#262626` | lines |
| Cobalt | `#2f5bea` | `#7d9cff` | links, buttons, focus |
| Signal | `#f26b2b` | `#ff8a52` | the LED, warnings, nothing else |

In light mode the neutrals lean slightly toward navy, so the page reads as
one colour family. Dark mode is a plain neutral black and grey, as most
dark sites are (Partha's choice, 2026-11-15), with cobalt as the only colour. Cobalt comes from the blue of a schematic; Signal from
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
