#! /usr/bin/env python3
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

"""Shared helpers for the backfill-en-ca skill."""

import os
import sys

from lxml import etree

NS = "urn:oasis:names:tc:xliff:document:1.2"
NS_MAP = {"x": NS}


def repo_root():
    # .claude/skills/backfill-en-ca/scripts/ -> repo root
    return os.path.abspath(
        os.path.join(os.path.dirname(os.path.abspath(__file__)), *([os.pardir] * 4))
    )


def locale_path(locale):
    return os.path.join(repo_root(), locale, "firefox-ios.xliff")


def write_xliff(root, filename):
    """Reuse the repo's writer so formatting matches Pontoon's output."""
    sys.path.insert(0, os.path.join(repo_root(), ".github", "scripts"))
    from functions import write_xliff as _write_xliff

    _write_xliff(root, filename)


def parse(locale):
    return etree.parse(locale_path(locale))


def units(tree):
    """Yield (file_original, trans_unit) for every trans-unit, in document order."""
    for file_node in tree.getroot().iterfind("x:file", NS_MAP):
        original = file_node.get("original")
        for unit in file_node.iterfind("x:body/x:trans-unit", NS_MAP):
            yield original, unit


def text_of(unit, tag):
    node = unit.find(f"x:{tag}", NS_MAP)
    return None if node is None else (node.text or "")


def index(tree):
    """(file_original, id) -> (source, target or None)."""
    return {
        (original, unit.get("id")): (text_of(unit, "source"), text_of(unit, "target"))
        for original, unit in units(tree)
    }
