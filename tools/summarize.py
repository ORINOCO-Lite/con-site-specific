#!/usr/bin/env python3
"""Summarise the record store: what exists, and how it is connected.

Written to be run before deciding anything, because counts in a commit
message go stale and a graph you cannot see is a graph you cannot review.

Reports, in order:
  1. inventory per class
  2. the relation graph -- which slots actually carry links, and how many
  3. projects, grouped by whether they are the Center's own
  4. instruments, grouped by the project that generated them
  5. people, by how many things they are associated with
  6. organizations
  7. dangling references: a pid pointed at by something but with no record
"""
import argparse
import collections
import pathlib
import sys

try:
    import yaml
except ImportError:
    sys.exit("PyYAML is required")

HERE = pathlib.Path(__file__).resolve().parent.parent
RECORDS = HERE / "metadata/records"
# slots that carry a reference to another Thing
LINKS = ("associated_with", "influenced_by", "generated_by", "attributed_to",
         "derived_from", "alternate_of", "specialization_of", "part_of",
         "informed_by", "used", "about", "depiction", "characterized_by")


def load_all():
    recs = {}
    for cls_dir in sorted(RECORDS.glob("XYZ*")):
        for f in sorted(cls_dir.glob("*.yaml")):
            if f.name.startswith("."):
                continue
            try:
                d = yaml.safe_load(f.read_text())
            except Exception as exc:
                print(f"!! {f}: {exc}", file=sys.stderr)
                continue
            if isinstance(d, dict) and d.get("pid"):
                recs[d["pid"]] = (cls_dir.name, f, d)
    return recs


def refs(doc):
    """(slot, target_pid, roles) for every outgoing link in a record."""
    for slot in LINKS:
        v = doc.get(slot)
        if v is None:
            continue
        for item in (v if isinstance(v, list) else [v]):
            if isinstance(item, str):
                yield slot, item, []
            elif isinstance(item, dict):
                tgt = item.get("object")
                if tgt:
                    yield slot, tgt, item.get("roles") or []


def label(entry):
    _, _, d = entry
    return (d.get("display_label") or d.get("title") or d.get("name")
            or d.get("short_name") or d["pid"])


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--section", help="only this section number")
    a = ap.parse_args()
    recs = load_all()
    out = {}

    # 1. inventory
    inv = collections.Counter(cls for cls, _, _ in recs.values())
    out["1"] = ["INVENTORY", ""] + [
        f"  {c:22s} {n:4d}" for c, n in sorted(inv.items(), key=lambda x: -x[1])
    ] + [f"  {'TOTAL':22s} {len(recs):4d}"]

    # 2. relation graph
    edges = collections.Counter()
    incoming = collections.Counter()
    for pid, (cls, _, d) in recs.items():
        for slot, tgt, _ in refs(d):
            tcls = recs[tgt][0] if tgt in recs else "(no record)"
            edges[(cls, slot, tcls)] += 1
            incoming[tgt] += 1
    out["2"] = ["RELATION GRAPH", ""] + [
        f"  {s:18s} {a_:16s} -> {b:16s} {n:4d}"
        for (a_, s, b), n in sorted(edges.items(), key=lambda x: (-x[1], x[0]))
    ]

    # 3. projects
    own, other = [], []
    for pid, (cls, f, d) in sorted(recs.items()):
        if cls != "XYZProject" or pid == "xyzrins:.":
            continue
        parents = [p for p in (d.get("part_of") or []) if p != "xyzrins:."]
        row = (f"  {label((cls, f, d))[:34]:34s} "
               f"{'<- ' + ', '.join(recs[p][2].get('short_name', p) if p in recs else p for p in parents) if parents else ''}")
        (own if "xyzrins:." in (d.get("part_of") or []) else other).append(row)
    out["3"] = ([f"PROJECTS: the Center's own ({len(own)})", ""] + sorted(own) +
                ["", f"PROJECTS: collaborating / not ours ({len(other)})", ""] +
                ["  " + ", ".join(sorted(r.strip() for r in other))])

    # 4. instruments by generating project
    by_proj = collections.defaultdict(list)
    for pid, (cls, f, d) in sorted(recs.items()):
        if cls != "XYZInstrument":
            continue
        gens = [t for s, t, _ in refs(d) if s == "generated_by"] or ["(none)"]
        spec = [t for s, t, _ in refs(d) if s == "specialization_of"]
        kind = d.get("kind", "")
        tag = " [service]" if kind == "schema:Service" else ""
        if spec:
            tag += " <deployment of " + ", ".join(
                recs[t][2].get("name", t) if t in recs else t for t in spec) + ">"
        for g in gens:
            by_proj[g].append(f"{label((cls, f, d))}{tag}")
    out["4"] = ["INSTRUMENTS, by the project that generated them", ""]
    for g, items in sorted(by_proj.items()):
        name = recs[g][2].get("short_name") or recs[g][2].get("title", g) if g in recs else g
        out["4"].append(f"  {name}")
        out["4"] += [f"      {i}" for i in sorted(items)]

    # 5. people
    people = collections.Counter()
    roles_by = collections.defaultdict(collections.Counter)
    for pid, (cls, _, d) in recs.items():
        for slot, tgt, rr in refs(d):
            if tgt in recs and recs[tgt][0] == "XYZPerson":
                people[tgt] += 1
                for r in rr:
                    roles_by[tgt][r] += 1
    out["5"] = [f"PEOPLE, by number of things referencing them "
                f"({len(recs and [p for p in recs if recs[p][0]=='XYZPerson'])} records)", ""]
    for pid, n in people.most_common(12):
        rs = ", ".join(f"{r.split(':')[-1]}x{c}" for r, c in roles_by[pid].most_common(3))
        out["5"].append(f"  {label(recs[pid])[:32]:32s} {n:4d}   {rs}")
    silent = [label(recs[p]) for p in recs if recs[p][0] == "XYZPerson" and p not in people]
    out["5"] += ["", f"  referenced by nothing: {len(silent)}"] + (
        ["    " + ", ".join(sorted(silent))] if silent else [])

    # 6. organizations
    out["6"] = ["ORGANIZATIONS", ""]
    for pid, (cls, f, d) in sorted(recs.items()):
        if cls != "XYZOrganization":
            continue
        leads = [recs[t][2].get("display_label", t) if t in recs else t
                 for s, t, rr in refs(d) if "marcrel:led" in rr]
        out["6"].append(f"  {label((cls, f, d))[:40]:40s} "
                        f"{'led by ' + ', '.join(leads) if leads else ''}")

    # 7. dangling
    dangling = collections.Counter()
    for pid, (cls, _, d) in recs.items():
        for slot, tgt, _ in refs(d):
            if tgt not in recs and not tgt.startswith(("http", "obo:", "marcrel:",
                                                       "FRAPO:", "ror:", "sio:",
                                                       "fabio:", "schema:",
                                                       "dlthings:", "ISSN:")):
                dangling[tgt] += 1
    out["7"] = [f"DANGLING REFERENCES ({len(dangling)} distinct)", ""] + [
        f"  {n:3d}x  {t}" for t, n in dangling.most_common()
    ]

    for k in sorted(out):
        if a.section and k != a.section:
            continue
        print(f"\n{'='*72}\n{k}. " + out[k][0] + f"\n{'='*72}")
        print("\n".join(out[k][1:]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
