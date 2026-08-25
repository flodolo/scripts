#!/usr/bin/env python3
"""Mechanically adapt en-US source text to en-CA style.

Implements the deterministic subset of reference/style-rules.md: spelling
substitutions, punctuation normalisation, and whitespace cleanup. Anything
that needs judgement is reported as a warning instead of being changed.

Usage:
    ca_adapt.py "some en-US text"      # adapt one string, print result
    ca_adapt.py --stdin < file         # adapt each line
    ca_adapt.py --selftest
"""

import re
import sys

# --- Substitutions applied to translatable text only -----------------------
# (pattern, replacement) applied case-insensitively with case preserved.
WORD_RULES = [
    # -our
    (r"\bcolor(s|ful|way|ways|less)?\b", r"colour\1"),
    (r"\bbehavior(s|al)?\b", r"behaviour\1"),
    (r"\bfavorit(e|es|ed|ing)\b", r"favourit\1"),
    (r"\bfavor(s|ed|ing|able|ably)?\b", r"favour\1"),
    (r"\bneighbor(s|hood|hoods|ing)?\b", r"neighbour\1"),
    (r"\bhonor(s|ed|ing|able)?\b", r"honour\1"),
    (r"\bhumor(s|ous)?\b", r"humour\1"),
    (r"\blabor(s|ed|ing)?\b", r"labour\1"),
    (r"\bflavor(s|ed|ing)?\b", r"flavour\1"),
    (r"\brumor(s)?\b", r"rumour\1"),
    (r"\barmor(s|ed)?\b", r"armour\1"),
    (r"\bvapor(s)?\b", r"vapour\1"),
    (r"\bharbor(s)?\b", r"harbour\1"),
    (r"\bendeavor(s|ed|ing)?\b", r"endeavour\1"),
    (r"\bodor(s)?\b", r"odour\1"),
    # -re
    (r"\bcenter(s|ed|ing)?\b", r"centre\1"),  # see AMBIGUOUS: "center" in code
    (r"\bmillimeter(s)?\b", r"millimetre\1"),
    (r"\bcentimeter(s)?\b", r"centimetre\1"),
    (r"\bkilometer(s)?\b", r"kilometre\1"),
    (r"\bliter(s)?\b", r"litre\1"),
    (r"\bfiber(s)?\b", r"fibre\1"),
    (r"\btheater(s)?\b", r"theatre\1"),
    # -ce nouns
    (r"\blicense(s)?\b", r"licence\1"),  # noun only, see AMBIGUOUS
    (r"\bdefense(s)?\b", r"defence\1"),
    (r"\boffense(s)?\b", r"offence\1"),
    (r"\bpretense(s)?\b", r"pretence\1"),
    # doubled consonant before a suffix
    (r"\bcancel(ed|ing|ation)\b", lambda m: "cancell" + m.group(1)),
    (r"\blabel(ed|ing)\b", lambda m: "labell" + m.group(1)),
    (r"\btravel(ed|ing|er|ers)\b", lambda m: "travell" + m.group(1)),
    (r"\bmodel(ed|ing)\b", lambda m: "modell" + m.group(1)),
    (r"\bsignal(ed|ing)\b", lambda m: "signall" + m.group(1)),
    (r"\bfuel(ed|ing)\b", lambda m: "fuell" + m.group(1)),
    (r"\btotal(ed|ing)\b", lambda m: "totall" + m.group(1)),
    (r"\bdial(ed|ing)\b", lambda m: "diall" + m.group(1)),
    (r"\bpetal(ed)\b", lambda m: "petall" + m.group(1)),
    (r"\bjewelry\b", "jewellery"),
    # single consonant where en-US doubles
    (r"\benrollment(s)?\b", r"enrolment\1"),
    # terminology / house style
    (r"\bgray(s|ish)?\b", r"grey\1"),
    (r"\be-mail(s)?\b", r"email\1"),
    (r"\bE-Mail(s)?\b", r"Email\1"),
    (r"\bmoveable\b", "movable"),
    (r"\bZIP code\b", "Postal Code"),
    (r"(?<![.\w])eg\.", "e.g."),
    (r"(?<![.\w])ie\.", "i.e."),
]

# Words we deliberately do NOT change (documented so the checker agrees).
KEEP_AS_IS = [
    "analyze/analyse", "organize", "customize", "recognize", "personalize",
    "synchronize", "initialize", "optimize", "summarize",  # -ize is Canadian
    "program", "dialog", "check", "draft", "aluminum",
    "meter (instrument, e.g. password quality meter)",
]

# Substrings that must never be touched by the spelling rules.
PROTECT = re.compile(
    r"""
      \{[^{}]*\}                    # Fluent placeables {$var}, {-term}, {"lit"}
    | %(?:[0-9]+\$)?[Ssd]           # printf placeholders in .properties
    | </?[A-Za-z][^>]*>             # HTML/XML markup incl. data-l10n-name
    | '[^'\s]+'                     # straight-quoted code token: 'unsafe-eval'
    | [“][a-z0-9][a-z0-9._:-]*[”]    # quoted lowercase identifier: “background-color”
    | https?://\S+                  # URLs
    | \b[A-Za-z-]+\.(?:ftl|html|js|css|json|png|pdf)\b
    | \b(?:color-scheme|background-color|current-color|border-color|text-color)\b
    | \bcenter-[xy]\b                # code/format literals
    | (?:Mozilla|General|Lesser)\ Public\ License   # proper names
    | Firefox\ Color
    """,
    re.VERBOSE,
)

# Flag, don't auto-fix: needs a human/model decision.
AMBIGUOUS = [
    (re.compile(r"\blicen[cs]e\b", re.I),
     "‘licence’ is the noun, ‘license’ the verb — check part of speech"),
    (re.compile(r"\bcert\b", re.I),
     "en-CA spells out ‘certificate’ in security strings"),
    (re.compile(r"\benroll(s|ed|ing)?\b", re.I),
     "en-CA uses ‘enrol/enrolled/enrolment’; verify against neighbouring strings"),
    (re.compile(r"\bpractice\b", re.I),
     "noun ‘practice’ / verb ‘practise’"),
    (re.compile(r"\bmeter\b", re.I),
     "‘metre’ for the unit, ‘meter’ for the instrument"),
    (re.compile(r"\bstate\b", re.I),
     "address forms: en-CA keeps ‘State’ and ‘Province’ as separate strings"),
]


def _preserve_case(src: str, out: str) -> str:
    if src.isupper() and len(src) > 1:
        return out.upper()
    if src[:1].isupper():
        return out[:1].upper() + out[1:]
    return out


def _apply_words(text: str) -> str:
    for pattern, repl in WORD_RULES:
        def sub(m, repl=repl):
            new = repl(m) if callable(repl) else m.expand(repl)
            return _preserve_case(m.group(0), new)
        text = re.sub(pattern, sub, text, flags=re.IGNORECASE)
    return text


def adapt_text(text: str, quotes: bool = True) -> str:
    """Adapt one translatable string (no keys, no comments) to en-CA.

    quotes=False skips the ‘…’ -> “…” conversion, which is the one rule the
    existing corpus applies inconsistently.
    """
    # 1. quote style first, so quoted identifiers can be protected below
    if quotes:
        text = re.sub(r"‘([^‘’]*)[‘’]", r"“\1”", text)

    # 2. protect code-ish spans
    kept = []

    def stash(m):
        kept.append(m.group(0))
        return f"\x00{len(kept) - 1}\x00"

    protected = PROTECT.sub(stash, text)

    # 3. spelling
    protected = _apply_words(protected)

    # 4. punctuation
    protected = re.sub(r"(?<=\w)'(?=\w)", "’", protected)      # don't -> don’t
    protected = re.sub(r"(?<=s)'(?=\s|$)", "’", protected)      # users' -> users’
    protected = re.sub(r"\bJavascript\b", "JavaScript", protected)
    protected = re.sub(r"\. {2,}(?=\S)", ". ", protected)         # single space after .
    protected = re.sub(r"\? {2,}(?=\S)", "? ", protected)
    protected = re.sub(r"! {2,}(?=\S)", "! ", protected)
    protected = protected.replace("developer.mozilla.org/en-US/", "developer.mozilla.org/")

    # 5. restore
    return re.sub(r"\x00(\d+)\x00", lambda m: kept[int(m.group(1))], protected)


def warnings(text: str) -> list:
    return [msg for rx, msg in AMBIGUOUS if rx.search(text)]


def _selftest():
    cases = [
        ("Assorted color of hot air balloons", "Assorted colour of hot air balloons"),
        ("Download canceled", "Download cancelled"),
        ("Toggle color-scheme simulation", "Toggle color-scheme simulation"),
        ("Closest to: {$colorName}", "Closest to: {$colorName}"),
        ("<a data-l10n-name=\"colors-link\">Manage colors</a>",
         "<a data-l10n-name=\"colors-link\">Manage colours</a>"),
        ("Couldn't open it.  Try again.", "Couldn’t open it. Try again."),
        ("The ‘content’ attribute is deprecated.", "The “content” attribute is deprecated."),
        ("stored web and e-mail passwords", "stored web and email passwords"),
        ("Bio enrollment", "Bio enrolment"),
        ("Gray theme", "Grey theme"),
        ("Behavior", "Behaviour"),
        ("Blocked “javascript:” URI", "Blocked “javascript:” URI"),
        ("Ignoring 'unsafe-hashes'", "Ignoring 'unsafe-hashes'"),
        ("Stylesheets modified from Javascript.", "Stylesheets modified from JavaScript."),
        ("The user's data", "The user’s data"),
    ]
    ok = True
    for src, want in cases:
        got = adapt_text(src)
        if got != want:
            ok = False
            print(f"FAIL {src!r}\n  got  {got!r}\n  want {want!r}")
    print("selftest:", "ok" if ok else "FAILED")
    return 0 if ok else 1


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        sys.exit(_selftest())
    if "--stdin" in sys.argv:
        for line in sys.stdin:
            print(adapt_text(line.rstrip("\n")))
    else:
        text = " ".join(a for a in sys.argv[1:] if not a.startswith("--"))
        print(adapt_text(text))
        for w in warnings(text):
            print("warning:", w, file=sys.stderr)
