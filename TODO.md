# Open findings from the 2026-10 metadata review

What the review found that still needs a source, a decision or a change outside this repository.
The rest was fixed together with the validator rules that keep it fixed: the red schema gate, asserted recollections, conflicting `skos:prefLabel`s, the NWB title, broken obfuscated `mailto:` links (now the addresses dartmouth.edu itself publishes), unlabelled entity roles, drifted attribute copies, the grant periods NIH RePORTER and NSF's award API give, the publications Crossref and F1000Research describe, and two publication records that described no real publication.

## Needs YOH

- `meta-brain-and-ai` has no award period and no public record to take one from.

## Upstream of this repository

- `con/dump-research-info` (`data/con_site/XYZPublication.json`, from a3c1109) still carries the two publication records removed here:
  - "Open Neuroscience" (Halchenko, Poldrack, Hanke 2022) with DOI 10.1146/annurev-neuro-100119-110036. That DOI is Charles et al. 2020, "Toward Community-Driven Big Open Brain Science", and no such paper is in Crossref, in YOH's ORCID record or in the CON Zotero library.
  - "Four aspects to make science open by design and not as an after-thought" with DOI 10.12688/f1000research.7628.1, which is Dirnagl & Przesdzing 2016, "A pocket guide to electronic laboratory notebooks". The paper is GigaScience 4:31, already here as `doi-10-1186-s13742-015-0072-7`.

  `curation-records/dump-research-info.yaml` still says `accept` for both, which keeps the unchanged candidates from being proposed again; correct the source anyway.
- `con/dump-research-info` also truncated `display_label` at 60 characters and emitted `display_label` identical to `title` on 224 records; both were removed here.
  `tools/validate_records.py` now fails on either, and on an attribute copy that differs from its slot, so a re-import that brings them back turns CI red instead of passing silently.
  The importer itself is unchanged (open question 2 in `docs/metadata-curation.md`).
- The CON Zotero group library (6197458) has two wrong items, which the next Zotero import would bring back:
  - W9MC83Q7 titles the HeuDiConv JOSS paper "...into structureddirectory layouts"; the validator will flag the drifted copy.
  - PPL6EUFK places the SfN 2016 poster in "Chicago, IL"; its F1000Research record says the 46th Annual Meeting, which was in San Diego.
- `con/talks` publishes `2026-mcgill-mechababs/slides.html` to datasets.datalad.org, but the file there answers 403 -- its annexed content looks unpublished.
  The record links the deck's source folder on GitHub until it is.
