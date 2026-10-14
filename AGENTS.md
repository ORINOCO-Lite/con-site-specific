# Agent instructions

Before adding or changing anything under `metadata/` or `sources/curation-evidence/`, read [docs/metadata-curation.md](docs/metadata-curation.md).
It sets the rules for hand-curated records: how to encode timed associations and roles, the evidence every date needs, and which way a bound points.

Validate before committing:

```console
python3 tools/validate_records.py
THINGS_SCHEMAS=/path/to/things-schemas tools/linkml_check.sh
```

`git config core.hooksPath tools` runs the first one on every commit.

In a hand-written record, put each fact in one place:

- Do not repeat a top-level slot as an `attributes` entry: no `skos:prefLabel`, `dlthings:given_name`, `dlthings:family_name`, `dlthings:formatted_name`, `dlthings:short_name` or `dcterms:description` attribute.
  Imported records carry these copies because `con/dump-research-info` emits them, and nothing here reads them.
- Leave out `display_label` and `formatted_name` on a person when `given_name` and `family_name` already compose the name.
- Keep `description` (plain text) and, where links help, the `dlthings:description_html` attribute.
  The Orinoco Lite site renders the first and the centerforopenneuroscience.org pages render the second.

Append new entries to the end of a list such as `associated_with`.
Evidence addresses entries by index, so inserting one elsewhere re-points every later evidence entry.
