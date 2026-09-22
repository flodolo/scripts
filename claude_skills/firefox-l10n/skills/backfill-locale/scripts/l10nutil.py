#!/usr/bin/env python3
"""Shared helpers, built on ``moz.l10n``.

``moz.l10n`` parses `firefox-ios.xliff` into a ``Resource`` and serializes it
back. The round-trip is byte-for-byte faithful for every locale file in this
repository -- including the `xml:space="preserve"` attributes and the exact
`<file>`/`<header>` shape Pontoon expects -- so there is no reason to touch the
XML as text.

Shape of the parsed model, which drives everything else:

- one ``Section`` per ``<file>``; ``section.id`` is the ``original`` attribute
- one ``Entry`` per ``<trans-unit>``; ``entry.id`` is the unit id
- ``entry.value`` is the ``<target>``; **an empty pattern means untranslated**
- ``entry.meta["source"]`` is the English text, ``entry.comment`` the ``<note>``

A Pontoon entity key for this project is ``[file original, unit id]``, i.e.
exactly ``(*section.id, *entry.id)``.
"""

from __future__ import annotations

import os
from dataclasses import replace

from moz.l10n.model import (
    Entry,
    Expression,
    Markup,
    Message,
    Resource,
    Section,
)
from moz.l10n.resource import parse_resource, serialize_resource

# This repository holds one product, translated as a single Pontoon resource.
PROJECT_SLUG = "firefox-for-ios"
RESOURCE_PATH = "firefox-ios.xliff"
FILENAME = "firefox-ios.xliff"
REFERENCE_LOCALE = "en-US"

# Directories that are not Pontoon locales and must never be backfilled:
# `en-US` is the reference, and `es` is a generated copy of `es-ES`
# (see update_es.yml) that Pontoon does not know about.
NOT_PONTOON_LOCALES = {"en-US", "es", "templates"}


def locale_path(repo: str, locale: str) -> str:
    return os.path.join(repo, locale, FILENAME)


def reference_path(repo: str) -> str:
    return os.path.join(repo, REFERENCE_LOCALE, FILENAME)


def read(path: str) -> Resource:
    return parse_resource(path)


def entries(res: Resource):
    """Yield (section, entry) for every trans-unit, skipping comments."""
    for section in res.sections:
        for entry in section.entries:
            if isinstance(entry, Entry):
                yield section, entry


def entity_key(section: Section, entry: Entry) -> tuple:
    """The Pontoon entity key: the `<file original>` plus the unit id."""
    return (*section.id, *entry.id)


def entry_map(res: Resource) -> dict[tuple, Entry]:
    return {entity_key(s, e): e for s, e in entries(res)}


def source_text(entry: Entry) -> str:
    """The English `<source>`, which XLIFF keeps alongside the target."""
    for meta in entry.meta:
        if meta.key == "source":
            return str(meta.value)
    return ""


def is_translated(entry: Entry) -> bool:
    """A trans-unit with no `<target>` parses to an empty pattern."""
    return not entry.value.is_empty()


def write_resource(path: str, res: Resource) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        for chunk in serialize_resource(res):
            fh.write(chunk)


def subset(
    res: Resource, wanted: set[tuple], seed: dict[tuple, Entry] | None = None
) -> Resource:
    """A resource holding only `wanted` keys, keeping the `<file>` grouping.

    The grouping matters: the entity key includes the `<file original>`, so a
    unit moved into the wrong `<file>` would not match anything in Pontoon.

    With `seed` (normally the en-US reference, keyed the same way), each kept
    entry takes that entry's target. Untranslated units have no `<target>` at
    all, and an absent element is awkward to fill in by hand; seeding gives the
    English text to overwrite, with its placeholders already parsed.
    """
    sections = []
    for section in res.sections:
        keep = []
        for entry in section.entries:
            if not isinstance(entry, Entry):
                continue
            key = entity_key(section, entry)
            if key not in wanted:
                continue
            if seed and key in seed:
                entry = replace(entry, value=seed[key].value)
            keep.append(entry)
        if keep:
            sections.append(
                Section(section.id, keep, comment=section.comment, meta=section.meta)
            )
    return Resource(res.format, sections, comment=res.comment, meta=res.meta)


def pattern_placeholders(pattern) -> list[str]:
    """Every placeholder in a pattern, as it is spelled in the source.

    iOS format specifiers (`%@`, `%1$@`, `%d`) reach us as expressions that
    remember their original text, so comparing two patterns is exact rather
    than a regex guess.
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


def placeholders(msg: Message) -> list[str]:
    return pattern_placeholders(msg.pattern)


def message_text(msg: Message) -> str:
    """A message as a plain string, for reports and corpora."""
    return "".join(
        str(p.attributes.get("source") or p.arg or "")
        if isinstance(p, (Expression, Markup))
        else str(p)
        for p in msg.pattern
    )
