# Open findings from the 2026-10 metadata review

Findings from reviewing `metadata/records/` that need a decision or a source before they can be fixed.
The mechanical ones (duplicated or truncated `display_label`, a dangling `part_of`, stale description copies, award periods on projects) were fixed with this file.

## Schema gate is red on `main`

Since 139ad75 ("leads of the STAMPED instruments") `tools/linkml_check.sh` fails, and so does the "LinkML schema" CI job:

    XYZInstrument/stamped-checklist.yaml  Additional properties are not allowed ('associated_with' was unexpected)
    XYZInstrument/stamped-examples.yaml   (same)
    XYZInstrument/stamped-paper.yaml      (same)

An instrument is a PROV entity, and `associated_with` exists only on activities.
Other instruments name their lead with `attributed_to` and `marcrel:led` (e.g. `dandi-api-webshots-tools`), but `Attribution` has no `started`, so converting drops the leads' start dates and their evidence.
Decide whether to accept that loss, or to time the lead some other way.

## Recollections asserted, against rule 3

Rule 3 of `docs/metadata-curation.md` says `kind: recollection` lives under `pending`, with `confidence: unverified`.
19 such entries sit under `assertions` instead, most with `confidence: approximate`:

- `XYZProject/site-root.yaml`: `/associated_with/{2,11,12,13,15,16,25,27,40}/started/at_time`
- `XYZProject/bids.yaml`: `/associated_with/1/started/at_time`, `/associated_with/1/ended/at_time`
- `XYZProject/bep028.yaml`: `/started/at_time`
- `XYZProject/dandi.yaml`: `/associated_with/0/started/at_time`
- `XYZProject/region-localization.yaml`: `/started/at_time`
- `XYZPublication/sfn2015-shared-representations.yaml`, `XYZPublication/sfn2016-localizing-roi.yaml`: `/generated_by/0/at_time`

They pass because `tools/validate_records.py` (the `pending` loop near line 339) checks recollections only under `pending`.
Either relax the rule (e.g. allow a first-hand recollection by the person concerned to be asserted as `approximate`) or move these to `pending`; then make the validator enforce whichever rule stands.

## Grants

- `hrf-models` and `hyperalignment-infrastructure` still carry their award period as the project's own `started`/`ended`.
  That is right only if the project *is* the award; if so, say so, otherwise move the period to the grant as was done for DANDI, OpenNeuro, EMBER and ReproNim.
- Six grants have no award period: `nih-hrf`, `nih-hyperalignment`, `nih-repronim-crnc`, `nsf-1429999`, `nsf-1912266`, `meta-brain-and-ai`.
  NIH RePORTER and the NSF award search give the dates; record them as `generated_by`/`invalidated_by` (single-valued on `XYZGrant`).
- No grant has a `description`, and `meta-brain-and-ai` has no identifier.

## Incomplete records

- Three publications are stubs with no date, no `kind` and a single author:
  `doi-10-1093-cercor-bhaa115`, `doi-10-1146-annurev-neuro-100119-110036`, `doi-10-12688-f1000research-7628-1`.
  Crossref has all of it.
- `sfn2016-localizing-roi` and `talk-2026-mcgill-mechababs` have no DOI, homepage or locator.
- Persons: `brock-wester` and `sylvestre-ledru` have no `dlthings:tier`, `dlthings:position` or `dlthings:description_html`; `ben-dichter` has no position or HTML bio; `andy-connolly` has no position.
- `XYZEntityRole/funding.yaml` and `XYZEntityRole/long-term-goal.yaml` have no label at all.

## Labels

- `display_label` has `slot_uri: skos:prefLabel`, and 31 records also carry a `skos:prefLabel` attribute with a *different* value (e.g. BIDS: `Brain Imaging Data Structure (BIDS)` vs `BIDS`; DICOM, HED, NIDM, the BEPs).
  In RDF that is two `skos:prefLabel`s on one resource, which SKOS forbids per language.
  Pick one, or make the other an `skos:altLabel`.
- The NWB title is still the retired "Neurodata Without Borders: Neurophysiology", both top-level and in the importer-vouched `dlthings:title` attribute.
  The current name is "Neurodata Without Borders".

## Emails

`vcard:Email` and `vcard:hasEmail` disagree on five people:

- `matthijs-van-der-meer`, `tor-wager`: `hasEmail` is an obfuscated `mailto:… at … dot edu`, which is not a working link.
  It may be deliberate anti-scraping carried over from the old site; if so, keep it out of `mailto:`.
- `cody-baker`, `john-lee`, `vadim-melnik`: `hasEmail` adds `?Subject=Hello … @CON`.
  Harmless, but not an email address.

## Importer

- `con/dump-research-info` truncated `display_label` to 60 characters (seven grant labels ended mid-word), and emitted `display_label` identical to `title` on 224 records.
  Both were removed here; the next import will put them back unless the importer is fixed or curation runs after import (open question 2 in `docs/metadata-curation.md`).
- Imported records keep attribute copies of top-level slots (`dcterms:description`, `dlthings:title`, …) that nothing reads.
  Four had already drifted from the top-level value.
  Drop them, or have `validate_records.py` require that each copy equals its slot.
