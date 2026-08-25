# en-CA style rules

Derived from a full comparison of the en-CA locale against en-US
(2026-08-25, 20,492 source strings). See `analysis.md` for the evidence
behind each rule and for the parts of the corpus that are inconsistent.

The one-sentence summary: **en-CA is en-US with Canadian spelling and a
handful of terminology fixes.** 98.9% of strings are byte-identical to the
source. Do not paraphrase, do not "improve" wording, do not change tone,
capitalisation, or sentence structure.

## 1. Spelling

### Change (Canadian forms)

| en-US | en-CA | notes |
|---|---|---|
| color, colors, colorful, colorway(s) | colour, colours, colourful, colourway(s) | value text only, never IDs or CSS |
| behavior(s), behavioral | behaviour(s), behavioural | |
| favorite(s), favor(s) | favourite(s), favour(s) | |
| neighbor, neighborhood | neighbour, neighbourhood | |
| honor, humor, labor, flavor, rumor, armor, vapor, harbor, endeavor, odor | + `u` | |
| center, centered | centre, centred | not in code, e.g. `center-x,center-y` |
| millimeter, centimeter, kilometer, liter, fiber, theater | millimetre, centimetre, kilometre, litre, fibre, theatre | |
| license (noun), defense, offense, pretense | licence, defence, offence, pretence | verb stays *license*; *licensed/licensing/licensor* unchanged |
| gray | grey | |
| canceled, canceling, cancelation | cancelled, cancelling, cancellation | |
| labeled, labeling | labelled, labelling | |
| traveled, traveling, traveler | travelled, travelling, traveller | |
| modeled, signaled, fueled, totaled, dialed, petaled | doubled `l` | |
| jewelry | jewellery | |
| enrollment(s) | enrolment(s) | note: *fewer* `l`s here |

### Keep as in en-US

- **`-ize` / `-yze` endings.** Canadian English keeps them: *customize,
  organize, recognize, personalize, synchronize, initialize, analyze*.
  There are 85 `-ize` strings in en-CA and zero `-ise` conversions.
- *program*, *dialog* (the UI widget), *check*, *draft*, *aluminum*,
  *meter* when it means an instrument ("Password quality meter").
- Anything inside a placeable `{ $var }` / `{ -brand-name }`, a printf
  placeholder `%1$S`, markup (`<a data-l10n-name="colors-link">`), a URL, a
  file name, a CSS/DOM identifier (`color-scheme`, `background-color`), or a
  proper name (*Firefox Color*, *Mozilla Public License*). Message IDs are
  never touched, so `newtab-wallpaper-color` keeps its US spelling.

## 2. Terminology

| en-US | en-CA |
|---|---|
| e-mail, E-Mail | email, Email |
| ZIP code | Postal Code |
| Cert (in security/certificate errors) | Certificate |
| moveable | movable |
| Bangalore | Bengaluru |
| Login (as a verb) | Log in |

Address forms keep *State* and *Province* as separate strings — do not merge
or swap them.

Obvious en-US slips are fixed rather than copied: *Javascript* → *JavaScript*,
`eg.` → `e.g.`, `peers’s` → `peer’s`, `developer.mozilla.org/en-US/…` →
`developer.mozilla.org/…`.

## 3. Punctuation and whitespace

- **Apostrophes are always typographic**: `don't` → `don’t`, `users'` →
  `users’`. The en-CA tree contains zero straight apostrophes in prose.
- **Straight double quotes stay straight** when they are code (`<area
  shape="rect">`, `data-l10n-name="…"`); en-US and en-CA both have 302 of them.
- **`‘…’` → `“…”`.** en-US quotes code tokens in devtools/DOM error strings
  with single curly quotes; en-CA prefers double curly quotes (88 strings
  converted, 40 legacy strings not yet — convert in new work).
- **One space after a sentence**, never the two that some en-US strings use
  (19 of 19 such strings are collapsed in en-CA).
- Em dash `—`, en dash `–` and `…` are used exactly as in en-US.
- Keep the en-US line structure of multi-line Fluent patterns (106 of 125
  keep it).

## 4. Structure

- Same message IDs, same attributes, same `{ $var ->` selectors and plural
  categories (`[one] / *[other]`) as en-US.
- Copy the en-US comments (`#`, `##`) along with a new string, verbatim.
- Put a new string at the same position it has in en-US.
- **Access keys**: reuse the en-US letter, unless the en-CA label no longer
  contains it (e.g. after *Color* → *Colour*), in which case pick another
  letter from the label. Existing en-CA access keys and `.key` shortcuts
  sometimes differ from en-US in case only — that is historical noise, leave
  it alone.
- Never delete a string that exists only in en-CA (obsolete entries are kept
  on purpose).
- `intl.accept_languages` is locale data (`en-CA, en-US, en`), not a
  translation.
