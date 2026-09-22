#!/usr/bin/env python3
"""Shared helpers, built on ``moz.l10n``.

``moz.l10n`` parses an Android ``strings.xml`` into a ``Resource`` of messages
and serializes it back. The round-trip is byte-for-byte faithful for every file
in this repository (comments, ``tools:ignore`` attributes, the MPL header and
the ``xmlns`` declarations all survive), so there is no reason to manipulate
the XML as text.

Working on the parsed model also means placeholders are structured data rather
than something to match with a regex: each one is an ``Expression`` carrying
its original spelling in ``attributes["source"]``.
"""

from __future__ import annotations

import os

from moz.l10n.formats import Format
from moz.l10n.formats.android import android_serialize_message
from moz.l10n.model import (
    CatchallKey,
    Entry,
    Expression,
    Markup,
    Message,
    PatternMessage,
    Resource,
    Section,
    SelectMessage,
)
from moz.l10n.paths import L10nConfigPaths, get_android_locale
from moz.l10n.resource import parse_resource, serialize_resource

# CLDR plural categories, in the order Pontoon's `cldr_plurals` indexes them.
CLDR_CATEGORIES = ["zero", "one", "two", "few", "many", "other"]

# l10n.toml in the repository root -> Pontoon project slug.
PROJECT_SLUGS = {"firefox": "firefox-for-android", "focus": "focus-for-android"}


def project_slug(config: str) -> str:
    name = os.path.splitext(os.path.basename(config))[0]
    return PROJECT_SLUGS.get(name, name)


def plural_categories(cldr_plurals: str) -> list[str]:
    """Map Pontoon's `cldr_plurals` field (e.g. "1,5") to category names."""
    cats = []
    for part in str(cldr_plurals).split(","):
        index = part.strip()
        if index.isdigit() and int(index) < len(CLDR_CATEGORIES):
            cats.append(CLDR_CATEGORIES[int(index)])
    return cats or ["other"]


def reference_pairs(repo: str, config: str, locale: str):
    """Yield (reference path, target path, resource path) for one locale.

    Paths are absolute; `resource path` is the reference path relative to the
    repository root, which is exactly the resource path Pontoon uses.
    """
    paths = L10nConfigPaths(
        os.path.join(repo, config), locale_map={"android_locale": get_android_locale}
    )
    for (ref, tgt_template), _locales in paths.all().items():
        yield (
            os.path.abspath(ref),
            os.path.abspath(paths.format_target_path(tgt_template, locale)),
            os.path.relpath(os.path.abspath(ref), os.path.abspath(repo)),
        )


def android_dir(locale: str) -> str:
    """Pontoon locale code -> Android resource directory name."""
    return f"values-{get_android_locale(locale)}"


def entries(res: Resource) -> list[Entry]:
    """The resource's entries, without standalone comments."""
    return [e for s in res.sections for e in s.entries if isinstance(e, Entry)]


def entry_map(res: Resource) -> dict[tuple, Entry]:
    return {e.id: e for e in entries(res)}


def build_resource(reference: Resource, keep: list[Entry]) -> Resource:
    """A resource holding only `keep`, with the reference's header and attributes."""
    return Resource(
        Format.android,
        [Section((), list(keep))],
        comment=reference.comment,
        meta=reference.meta,
    )


def write_resource(path: str, res: Resource) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        for chunk in serialize_resource(res):
            fh.write(chunk)


def patterns(msg: Message):
    """Yield each pattern in a message: one for a string, one per plural form."""
    if isinstance(msg, SelectMessage):
        yield from msg.variants.values()
    else:
        yield msg.pattern


def pattern_placeholders(pattern) -> list[str]:
    """Every placeholder in one pattern, as it is spelled in the source.

    `%1$s`, `%2$,d` and `<xliff:g>` wrappers all reach us as expressions that
    remember their original text, so comparing two patterns is an exact
    comparison rather than a regex guess.
    """
    found = []
    for part in pattern:
        if isinstance(part, (Expression, Markup)):
            source = part.attributes.get("source")
            if source:
                found.append(str(source))
            elif isinstance(part, Expression) and part.arg is not None:
                found.append(str(part.arg))
    return sorted(found)


def placeholders_by_variant(msg: Message) -> dict[str | None, list[str]]:
    """Placeholders per plural category, keyed by `None` for a plain string.

    Comparing per variant matters: a locale with one plural form against an
    English source with two must not look like it dropped a placeholder.
    """
    if not isinstance(msg, SelectMessage):
        return {None: pattern_placeholders(msg.pattern)}
    return {
        category: pattern_placeholders(pattern)
        for category, pattern in zip(variant_categories(msg), msg.variants.values())
    }


def variant_categories(msg: Message) -> list[str]:
    """The plural categories a message defines, or [] for a plain string."""
    if not isinstance(msg, SelectMessage):
        return []
    return [
        key[0].value if isinstance(key[0], CatchallKey) else str(key[0])
        for key in msg.variants
    ]


def message_text(msg: Message) -> str:
    """A message as a single readable line, for reports and corpora."""
    if isinstance(msg, SelectMessage):
        return " | ".join(
            f"{cat}={android_serialize_message(PatternMessage(list(pattern)))}"
            for cat, pattern in zip(variant_categories(msg), msg.variants.values())
        )
    return android_serialize_message(msg)


def read(path: str) -> Resource:
    return parse_resource(path)
