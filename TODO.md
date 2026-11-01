# Open findings from the 2026-10 metadata review

What the review found that still needs a source, a decision or a change outside this repository.
The rest -- the red schema gate, asserted recollections, conflicting `skos:prefLabel`s, the NWB title, broken obfuscated `mailto:` links (now the addresses dartmouth.edu itself publishes), unlabelled entity roles, drifted attribute copies -- was fixed together with the validator rules that keep it fixed.

## Facts that need a registry

The session that resolved the rest could not reach Crossref, NIH RePORTER or the NSF award search, so these are not guessed.

- Four grants have no award period: `nih-repronim-crnc`, `nsf-1429999`, `nsf-1912266` (NIH RePORTER and the NSF award search give them), and `meta-brain-and-ai` (no public record; YOH has the dates).
  Record them as `generated_by`/`invalidated_by`, with `registry` evidence like `XYZGrant/nih-dandi`'s.
- Three publications are stubs with no date, no `kind` and a single author:
  `doi-10-1093-cercor-bhaa115`, `doi-10-1146-annurev-neuro-100119-110036`, `doi-10-12688-f1000research-7628-1`.
  Crossref has all of it.

## Incomplete records

- `sfn2016-localizing-roi` has no DOI or locator, and its venue is contested: the record says San Diego, while the Zotero item (PPL6EUFK) and the Haxby lab's publication list say "Chicago, IL" with the same year 2016.
  SfN met in Chicago in 2015 and in San Diego in 2016.
  The poster appears to be F1000Research 2016, 5:2830, which would settle the venue and give it a DOI.
- `talk-2026-mcgill-mechababs` has no locator; unlike the other 2026 talks, its slides are not under `datasets.datalad.org/centerforopenneuroscience/talks/`.
- `andy-connolly` (Emeritus) has no position; it needs a current affiliation from a source.

## Upstream of this repository

- `con/dump-research-info` truncated `display_label` at 60 characters and emitted `display_label` identical to `title` on 224 records; both were removed here.
  `tools/validate_records.py` now fails on either, and on an attribute copy that differs from its slot, so a re-import that brings them back turns CI red instead of passing silently.
  The importer itself is unchanged (open question 2 in `docs/metadata-curation.md`).
- The Zotero group library's item W9MC83Q7 titles the HeuDiConv JOSS paper "...into structureddirectory layouts".
  The record is corrected; the Zotero item is not, so the next Zotero import will reintroduce the typo, and the validator will flag it as a drifted copy.
