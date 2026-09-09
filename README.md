# Center for Open Neuroscience site inputs

This directory is the declarative, site-owned layer of the Center for Open Neuroscience website.
It is the repository root here and is integrated at `site-specific/` in the Orinoco Lite downstream through `git subtree`.
Paths in this document are relative to this directory.

## Structure

| Path | Purpose |
| --- | --- |
| `metadata/records/` | Reviewed Things YAML records; preserve stable PIDs. |
| `metadata/overlays/annotations/` | Machine-managed provenance companions. |
| `site.yaml` | CON identity, navigation, and presentation choices. |
| `content/` | Editorial pages, group order, and Hugo page resources. |
| `assets/`, `static/` | Site-owned presentation and static assets. |
| `sources/`, `curation-records/` | Source declarations and reviewed curation decisions. |

The homepage is `content/_index.md`.
Portraits live beside generated person pages as `portrait.*`, and project artwork lives beside generated project pages as `logo.*`.
These are ordinary Hugo page resources and do not require a downstream theme override.

Source declarations refer to executable adapters under `extensions/source-adapters/` from the downstream repository root.
Adapter code and the Orinoco Lite scaffold remain outside this subtree.

## Subtree integration

Import this history into a new downstream without squashing it:

```console
git subtree add \
  --prefix=site-specific \
  git@github.com:ORINOCO-Lite/con-site-specific.git \
  main
```

Pull a reviewed content update into an existing downstream with:

```console
git subtree pull \
  --prefix=site-specific \
  git@github.com:ORINOCO-Lite/con-site-specific.git \
  main
```

Do not add `--squash`; the focused history in this repository is part of the subtree's value.

## Edit, validate, and preview

Run these commands from the downstream repository root, not this directory:

```console
pixi run validate
pixi run build
pixi run serve
```

Review the source diff and rendered build.
Do not commit or hand-edit generated projection output.
