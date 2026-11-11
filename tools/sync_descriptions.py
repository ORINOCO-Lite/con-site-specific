#!/usr/bin/env python3
"""Rewrite `description` from `dlthings:description_html` where it is derived.

The HTML is what people write; `description` is its lead as plain text (see
DERIVED_DESCRIPTION and lead_text in validate_records.py, which enforces the
result).  Run after editing a description_html.  Only the `description`
lines of a record change, so the diff shows the new text and nothing else.
"""
import sys

import yaml

from validate_records import (DERIVED_DESCRIPTION, RECORDS, description_html,
                              lead_text)


def replace_description(text, value):
    """Swap the top-level `description:` block of a record for `value`."""
    new = yaml.safe_dump({"description": value}, allow_unicode=True, width=88)
    lines, out, skip, done = text.splitlines(keepends=True), [], False, False
    for line in lines:
        if line.startswith("description:"):
            skip, done = True, True
            out.append(new)
            continue
        if skip and line.startswith(" "):
            continue
        skip = False
        out.append(line)
    if not done:
        # keys are sorted, so it goes before the first key that sorts after it
        i = next((n for n, line in enumerate(out)
                  if not line.startswith((" ", "-")) and line.split(":")[0] > "description"),
                 len(out))
        out.insert(i, new)
    return "".join(out)


def main():
    changed = 0
    for path in sorted(RECORDS.rglob("*.yaml")):
        text = path.read_text()
        doc = yaml.safe_load(text)
        markup = description_html(doc) if isinstance(doc, dict) else None
        if not isinstance(markup, str) or doc.get("schema_type") not in DERIVED_DESCRIPTION:
            continue
        want = lead_text(markup)
        if doc.get("description") != want:
            path.write_text(replace_description(text, want))
            print(path.relative_to(RECORDS))
            changed += 1
    print(f"{changed} description(s) rewritten", file=sys.stderr)


if __name__ == "__main__":
    main()
