#!/usr/bin/env python3
"""Validate metadata/records/ against the curation rules in docs/metadata-curation.md.

This is the SECOND of two gates and it does not replace the first.
`tools/linkml_check.sh` validates the records against the
`demo-research-information` schema itself -- unknown slots, wrong classes,
wrong ranges.  What it cannot check is whether a date is backed by anything,
whether an evidence pointer still points where it did, or whether a bound
faces the right way, because none of that is in the schema.  It is also
weaker than it looks on dates: the upstream W3CISO8601 pattern leaves its
alternatives unanchored, so "April 2008" passes it.  This script covers that
gap.

What this gate is for: every date we put on a slide or a web page should be
traceable to something someone can check.  The mechanism is a JSON Pointer --
each evidence assertion names the exact slot it backs, and this script walks
the records looking for a dated slot nobody claimed.

Design notes, kept from the first version because they were learned the hard
way:

* A validator used as a PR gate must never crash.  The first version threw a
  bare AttributeError on an empty file and on `provenance:` written as a
  mapping instead of a list -- the two mistakes a first-time contributor
  actually makes -- and the traceback named this script rather than the
  offending YAML.  Every per-file failure is reported against the file.
* Rules are quoted by text, not by number.  Numbers drift against SCHEMA.md.
* "Lower bound" is expressible, not forbidden.  Most dates derived from a
  repository or a changelog can only ever mean "no later than".

Exit status is non-zero if anything fails.
"""
import json
import pathlib
import re
import sys

try:
    import yaml
except ImportError:
    sys.exit("PyYAML is required: pip install pyyaml")

HERE = pathlib.Path(__file__).resolve().parent.parent
RECORDS = HERE / "metadata/records"
OVERLAYS = HERE / "sources/curation-evidence"
# The machine-import overlay addresses whole containers (`path: /attributes`)
# rather than exact slots, and it covers the records this repo did not hand
# write.  A dated slot under a container it claims is already accounted for;
# demanding a second, hand-written entry for it would make the gate
# unpassable for 131 publication records nobody here curated.
MACHINE = HERE / "metadata/overlays/machine-provenance-annotations"

KINDS = {"debian-changelog", "upstream-git", "site-git-history",
         "copyright-extract", "publication", "registry", "correspondence",
         "recollection"}
CONF = {"certain", "approximate", "unverified"}
BOUND = {"exact", "lower", "upper"}
# The last HUMAN-AUTHORED revision of con.org's pages.  After this commit
# whoweare.html and projects.html are generated from these records, so
# site-git-history evidence taken from a later commit would be citing this
# store back to itself.  Any new site-git-history locator must be an ancestor
# of this.
SITE_HISTORY_FREEZE = "53e2e40"
SITE_HISTORY_FREEZE_DATE = "2026-10-08"

# Evidence kinds that survive only as artifacts: a repository, a changelog, a
# website's history.  They never show the event, only the oldest or newest
# trace of it, so the direction of the uncertainty is fixed by which end of a
# span the date sits at -- see BOUND_RULE below.
# A dated message -- an email, a mailing-list post, an issue comment -- is
# the same kind of trace: people writing to each other were already working
# together, so it bounds a `started` from above.
ARTIFACT_KINDS = {"site-git-history", "upstream-git", "debian-changelog",
                  "correspondence"}
# A `started` taken from the OLDEST surviving artifact can only be an upper
# bound: work before the artifact existed (or before an SVN conversion, or
# under another spelling of a name) leaves no trace, so the real date is at or
# BEFORE the recorded one.  An `ended` taken from the NEWEST artifact is the
# mirror image: involvement may have continued off the record, so the real
# date is at or AFTER.  Getting this backwards is easy -- the first draft of
# psychopy.yaml marked a first commit `lower` while marking a whois creation
# date `upper`, which are the same situation pointing opposite ways.
BOUND_RULE = {"started": "upper", "ended": "lower"}
# ...but that assumes the artifact is a TRACE of the work.  Some artifacts are
# a RECORD OF THE TRANSITION itself, and those behave differently: the commit
# that first files someone under "Emeritus" is written AFTER they left, so it
# is an upper bound on an `ended` where a last-commit date would be a lower
# one.  An assertion says which it is; `trace` is the default because it is
# the common case and the riskier one to get wrong.
#
#   trace   + started -> upper      trace  + ended -> lower
#   record  + either  -> upper      (the record is written after the event)
ARTIFACT_KIND = {"trace", "record"}
RECORD_RULE = {"started": "upper", "ended": "upper"}
# W3CISO8601, the subset things-properties actually accepts.
CURIE = re.compile(r"^[A-Za-z][\w.-]*:\S")
W3CISO = re.compile(
    r"^(\d{4})$|^(\d{4}-[01]\d)$|^(\d{4}-[01]\d-[0-3]\d)$|"
    r"^\d{4}-[01]\d-[0-3]\dT[0-2]\d:[0-5]\d(:[0-5]\d(\.\d+)?)?"
    r"([+-][0-2]\d:[0-5]\d|Z)$")

RULE = {
    "backed": "every dated slot needs an evidence assertion whose `path` points at it",
    "bound": "an artifact-derived `started` is an upper bound and an `ended` a "
             "lower bound -- the artifact shows the oldest/newest trace, not the event",
    "quarantine": "kind `recollection` requires confidence `unverified` and a `would_confirm`",
    "witness": ("a recollection is asserted only when it is first-hand: a "
                "`witness` naming a person who is an agent of the same record "
                "(an `associated_with` or `attributed_to` object), confidence "
                "`approximate`, and a `would_confirm`; any other recollection "
                "stays under `pending`"),
    "copy": ("an `attributes` copy of a top-level slot must equal that slot "
             "(skos:prefLabel: `display_label`, or `title` when there is none); "
             "a different label is an skos:altLabel"),
    "label": ("`display_label` must say something `title` does not: drop one "
              "that repeats `title` or truncates it -- every consumer reads "
              "`display_label or title`"),
    "pointer": "an evidence `path` must resolve in the record it names",
    "iso": "at_time must be W3CISO8601: YYYY, YYYY-MM, YYYY-MM-DD, or a full timestamp",
    "role": "a role must be an IRI (prefix:local), not a bare word",
    "pid": "a pid is the store's index key; two records cannot share one",
    "value": "an evidence `value` must equal what the record actually says",
    "freeze": (f"site-git-history evidence captured after the pages became "
               f"generated must name a commit at or before "
               f"{SITE_HISTORY_FREEZE} and say so with `predates_freeze: true` "
               f"-- otherwise the records are citing themselves"),
}


def is_index(tok):
    """RFC 6901 array index: ASCII digits, and no leading zero except "0"."""
    return (tok.isascii() and tok.isdigit()
            and (tok == "0" or not tok.startswith("0")))


def resolve(doc, pointer):
    """RFC 6901 JSON Pointer.  Returns (ok, value).

    Note "/" is NOT the whole document -- RFC 6901 reads it as the member
    whose key is the empty string.  Getting that wrong would make a typo
    resolve to the entire record and silently pass.
    """
    if pointer == "":
        return True, doc
    if not pointer.startswith("/"):
        return False, None
    cur = doc
    for tok in pointer[1:].split("/"):
        tok = tok.replace("~1", "/").replace("~0", "~")
        if isinstance(cur, list):
            if not is_index(tok) or int(tok) >= len(cur):
                return False, None
            cur = cur[int(tok)]
        elif isinstance(cur, dict):
            if tok not in cur:
                return False, None
            cur = cur[tok]
        else:
            return False, None
    return True, cur


# An XYZOrganization is an AgentMixin, so it has no top-level `started` and a
# founding date has to travel as an attribute.  Those dates are every bit as
# much a claim as an `at_time`, so the walker has to find them too -- and each
# needs to say which end of a span it behaves like, so the bound rule applies.
DATE_PREDICATES = {
    "schema:foundingDate": "started",
    "schema:dissolutionDate": "ended",
    "dcterms:created": "started",
    # An Attribution (an entity's agent) has no started/ended slot, unlike an
    # Association, so when a lead of an instrument or dataset is dated the
    # date travels as an attribute of the Attribution itself.
    "schema:startDate": "started",
    "schema:endDate": "ended",
}


def dated_slots(doc, prefix=""):
    """Every dated pointer in a record, with the span-end it behaves like.

    Yields (pointer, value, role) where role is "started", "ended" or None.

    Keying on the *key* rather than on the leaf matters: an earlier version
    recursed first and tested `prefix.endswith("/at_time")` only at a scalar,
    so `at_time: {}` or `at_time: [2008]` walked straight past the test and
    was never checked or required to be backed.
    """
    if isinstance(doc, dict):
        for k, v in doc.items():
            here = f"{prefix}/{k}"
            if k == "at_time":
                role = next((r for r in ("started", "ended") if f"/{r}/" in here
                             or here.endswith(f"/{r}")), None)
                yield here, v, role
                continue
            if (k == "value" and isinstance(doc.get("predicate"), str)
                    and doc["predicate"] in DATE_PREDICATES):
                yield here, v, DATE_PREDICATES[doc["predicate"]]
                continue
            yield from dated_slots(v, here)
    elif isinstance(doc, list):
        for i, v in enumerate(doc):
            yield from dated_slots(v, f"{prefix}/{i}")


# Attribute copies of top-level slots.  con/dump-research-info and zotero emit
# them and nothing here reads them, so they can drift unnoticed -- four had.
# Each must equal its slot.  skos:prefLabel is the slot_uri of
# `display_label`, so a second, different prefLabel is two prefLabels on one
# resource, which SKOS forbids per language: that one is an skos:altLabel.
COPY_SLOTS = {
    "dlthings:title": "title",
    "dcterms:description": "description",
    "dlthings:given_name": "given_name",
    "dlthings:family_name": "family_name",
    "dlthings:formatted_name": "formatted_name",
    "dlthings:short_name": "short_name",
}
# The dump-research-info importer cut `display_label` at this many characters,
# mid-word ("DANDI: Distributed Archives for Neurophysiology Data Integra").
IMPORTER_LABEL_CUT = 60


def label_problems(doc):
    """Attribute copies that disagree with their slot, and redundant labels."""
    label = doc.get("display_label")
    title = doc.get("title")
    if isinstance(label, str) and isinstance(title, str):
        if label == title:
            yield f"display_label repeats title -- {RULE['label']}"
        elif (len(label) == IMPORTER_LABEL_CUT and len(title) > len(label)
              and title.startswith(label)):
            yield (f"display_label {label!r} is title cut at "
                   f"{IMPORTER_LABEL_CUT} characters -- {RULE['label']}")
    attrs = doc.get("attributes")
    if not isinstance(attrs, list):
        return
    for n, attr in enumerate(attrs):
        if not isinstance(attr, dict):
            continue
        pred = attr.get("predicate")
        if pred == "skos:prefLabel":
            slot = "display_label" if "display_label" in doc else "title"
        elif pred in COPY_SLOTS:
            slot = COPY_SLOTS[pred]
        else:
            continue
        if attr.get("value") != doc.get(slot):
            yield (f"/attributes/{n} {pred} is {attr.get('value')!r}, "
                   f"`{slot}` is {doc.get(slot)!r} -- {RULE['copy']}")


def agents(doc):
    """Every agent a record names: associated_with and attributed_to objects."""
    out = set()
    for key in ("associated_with", "attributed_to"):
        for entry in doc.get(key) or []:
            if isinstance(entry, dict) and isinstance(entry.get("object"), str):
                out.add(entry["object"])
    return out


def load(path, fails):
    try:
        doc = yaml.safe_load(path.read_text())
    except Exception as exc:                      # malformed YAML, any flavour
        fails.append((path, f"not parseable as YAML: {exc}"))
        return None
    if doc is None:
        fails.append((path, "file is empty"))
        return None
    if not isinstance(doc, dict):
        fails.append((path, f"top level must be a mapping, found {type(doc).__name__}"))
        return None
    return doc


def main():
    fails = []

    records = {}
    dated_by_pid = {}        # pid -> {pointer: role}, built as records load
    for path in sorted(RECORDS.rglob("*.yaml")):
        if path.name.startswith("."):
            continue                              # .dumpthings.yaml is config
        doc = load(path, fails)
        if doc is None:
            continue
        pid = doc.get("pid")
        if not pid:
            fails.append((path, "record has no `pid`"))
            continue
        if pid in records:
            # Not pedantry: `pid` is the index key, filenames are not, so two
            # files can collide on pid without colliding on path.  The record
            # store raises on this (dump_things_service/backends/
            # record_dir_index.py: "Duplicated IRI"), and silently dropping one
            # here would hide dated slots from every check below.
            fails.append((path, f"pid {pid} is already used by "
                                f"{records[pid][0].relative_to(HERE)} -- {RULE['pid']}"))
            continue
        records[pid] = (path, doc)

        for msg in label_problems(doc):
            fails.append((path, msg))

        dated_by_pid[pid] = {ptr: role for ptr, _, role in dated_slots(doc)}
        for pointer, value, _ in dated_slots(doc):
            if not isinstance(value, str) or not W3CISO.match(value):
                fails.append((path, f"{pointer}: {value!r} -- {RULE['iso']}"))

        for assoc in doc.get("associated_with") or []:
            if not isinstance(assoc, dict):
                fails.append((path, "associated_with entries must be mappings"))
                continue
            if not assoc.get("object"):
                fails.append((path, "an Association without `object` names no agent"))
            roles = assoc.get("roles")
            if roles is None:
                roles = []
            elif not isinstance(roles, list):
                # A bare string here would otherwise be iterated character by
                # character, one failure per character.
                fails.append((path, f"`roles` must be a list, found "
                                    f"{type(roles).__name__}"))
                roles = []
            for role in roles:
                if not isinstance(role, str) or not CURIE.match(role):
                    fails.append((path, f"role {role!r} -- {RULE['role']}"))

    covered = {}
    machine = {}             # pid -> [container pointers claimed by the importer]
    for path in sorted(MACHINE.rglob("*.yaml")):
        if path.name.startswith("."):
            continue
        doc = load(path, fails)
        if doc is None:
            continue
        for entry in doc.get("assertions") or []:
            if isinstance(entry, dict) and isinstance(entry.get("path"), str):
                machine.setdefault(doc.get("record"), set()).add(entry["path"])
    for path in sorted(OVERLAYS.rglob("*.yaml")):
        if path.name.startswith("."):
            continue                              # store config, not an overlay
        doc = load(path, fails)
        if doc is None:
            continue
        pid = doc.get("record")
        if pid not in records:
            fails.append((path, f"`record: {pid}` matches no record under {RECORDS.name}/"))
            continue
        _, target = records[pid]
        dated = dated_by_pid.get(pid, {})

        for entry in doc.get("assertions") or []:
            if not isinstance(entry, dict):
                fails.append((path, "assertions entries must be mappings"))
                continue
            pointer = entry.get("path")
            # An absent, empty or non-string `path` used to default to "",
            # which resolved to the whole document: the entry passed the
            # pointer check AND was counted as coverage for a slot it never
            # named.  A `path:` with nothing after it crashed the resolver.
            if not isinstance(pointer, str) or not pointer:
                fails.append((path, f"assertion has no usable `path` "
                                    f"({pointer!r}) -- {RULE['pointer']}"))
                continue
            ok, found = resolve(target, pointer)
            if not ok:
                fails.append((path, f"path {pointer!r} -- {RULE['pointer']}"))
                continue
            covered.setdefault(pid, {}).setdefault(pointer, []).append(entry)

            # The whole point of an index-based pointer is that it is precise;
            # it is also positionally fragile, so insert one association and
            # every later assertion quietly re-points at a different claim.
            # Comparing the value turns that from silent corruption into a
            # failure, and is what the upstream overlay's assertion_sha256
            # does for a coarse path.
            if "value" in entry and entry["value"] != found:
                fails.append((path, f"{pointer}: evidence says {entry['value']!r}, "
                                    f"record has {found!r} -- {RULE['value']}"))

            # A site-git-history citation must predate the freeze, or it is
            # the records quoting themselves.
            if (entry.get("kind") == "site-git-history"
                    and entry.get("captured", "") > SITE_HISTORY_FREEZE_DATE
                    and not entry.get("predates_freeze")):
                fails.append((path, f"{pointer}: {RULE['freeze']}"))

            kind = entry.get("kind")
            if kind not in KINDS:
                fails.append((path, f"{pointer}: kind {kind!r} not one of {sorted(KINDS)}"))
            # A recollection is testimony.  The record may assert it only when
            # the person recalling took part -- an agent of this very record --
            # and says how sure they are and what would settle it.  A
            # recollection by anyone else, or one that claims more than
            # `approximate`, stays quarantined under `pending`.
            witness = entry.get("witness")
            if kind == "recollection":
                who = records.get(witness, (None, {}))[1] if isinstance(witness, str) else {}
                if (not isinstance(witness, str)
                        or who.get("schema_type") != "xyzri:XYZPerson"
                        or witness not in agents(target)
                        or entry.get("confidence") != "approximate"
                        or not entry.get("would_confirm")):
                    fails.append((path, f"{pointer}: {RULE['witness']}"))
            elif witness is not None:
                fails.append((path, f"{pointer}: `witness` qualifies a "
                                    f"recollection; this entry is {kind!r}"))
            if entry.get("artifact") not in (None,) and \
                    entry.get("artifact") not in ARTIFACT_KIND:
                fails.append((path, f"{pointer}: artifact "
                                    f"{entry.get('artifact')!r} not one of "
                                    f"{sorted(ARTIFACT_KIND)}"))
            if entry.get("artifact") == "record" and not entry.get("note"):
                fails.append((path, f"{pointer}: `artifact: record` inverts the "
                                    f"bound rule, so it needs a `note` saying why"))
            if entry.get("confidence") not in CONF:
                fails.append((path, f"{pointer}: confidence {entry.get('confidence')!r} "
                                    f"not one of {sorted(CONF)}"))
            # `bound` is a temporal notion.  Requiring it on a role IRI or a
            # trigger IRI only forced a meaningless `exact` to be written.
            if pointer in dated:
                if entry.get("bound") not in BOUND:
                    fails.append((path, f"{pointer}: bound {entry.get('bound')!r} "
                                        f"not one of {sorted(BOUND)}"))
            elif "bound" in entry:
                fails.append((path, f"{pointer}: `bound` means nothing on a "
                                    f"non-date slot"))

        for entry in doc.get("pending") or []:
            if not isinstance(entry, dict):
                fails.append((path, "pending entries must be mappings"))
                continue
            if entry.get("kind") == "recollection":
                if entry.get("confidence") != "unverified" or not entry.get("would_confirm"):
                    fails.append((path, f"pending {entry.get('proposed_path')!r} -- "
                                        f"{RULE['quarantine']}"))

    # Coverage, and the bound rule, checked against the records themselves.
    for pid, (path, doc) in records.items():
        for pointer, _, role in dated_slots(doc):
            entries = (covered.get(pid) or {}).get(pointer)
            if not entries:
                claimed = machine.get(pid) or set()
                if any(pointer == c or pointer.startswith(c.rstrip("/") + "/")
                       for c in claimed):
                    continue      # the importer vouches for this container
                fails.append((path, f"{pointer} -- {RULE['backed']}"))
                continue
            # An entry that calls itself a record of the transition is judged
            # by RECORD_RULE instead.  Mixed support falls back to the
            # stricter trace rule, since one careless `record` should not
            # excuse the rest.
            arts_all = [e for e in entries if e.get("kind") in ARTIFACT_KINDS]
            as_record = arts_all and all(e.get("artifact") == "record"
                                         for e in arts_all)
            want = (RECORD_RULE if as_record else BOUND_RULE).get(role)
            # The kind test used to sit INSIDE the all(), so a single
            # non-artifact entry beside the artifact ones made the conjunction
            # False and suppressed the rule entirely -- which is how a
            # backwards bound shipped next to a whois citation.
            arts = [e for e in entries if e.get("kind") in ARTIFACT_KINDS]
            if want and arts and not any(e.get("bound") == want for e in arts):
                kinds = sorted({e.get("kind") for e in arts})
                fails.append((path, f"{pointer}: supported by {kinds} yet no such "
                                    f"entry says `bound: {want}` -- {RULE['bound']}"))

    for path, msg in fails:
        print(f"{path.relative_to(HERE)}: {msg}")
    print(f"\n{len(records)} record(s), "
          f"{sum(len(v) for v in covered.values())} slot(s) with evidence, "
          f"{len(fails)} failure(s)")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
