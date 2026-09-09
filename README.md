# CON Orinoco site content

This repository contains the site-owned inputs for the Center for Open
Neuroscience website. It is intended to be imported as the `site-specific/`
subtree of an Orinoco Lite downstream while retaining this repository's focused
content history.

Earlier content and metadata came from the following sources:

- <https://github.com/con/dump-research-info/>
- <https://github.com/leej3/orinoco-lite-demo>
- <https://centerforopenneuroscience.org>

## Structure

| Path | Purpose |
| --- | --- |
| `metadata/records/` | Reviewed Things YAML records; preserve stable PIDs. |
| `metadata/overlays/annotations/` | Machine-managed provenance companions. |
| `site.yaml` | CON identity, navigation, and presentation choices. |
| `content/` | Editorial pages, group order, and Hugo page resources. |
| `assets/`, `static/` | Site-owned presentation and static assets. |
| `sources/`, `curation-records/` | Source declarations and reviewed curation decisions. |

The homepage is `content/_index.md`. Portraits live beside generated person
pages as `portrait.*`, and project artwork lives beside generated project pages
as `logo.*`. These are ordinary Hugo page resources and do not require a
downstream theme override.

Source declarations refer to executable adapters under
`extensions/source-adapters/` in the containing downstream. Adapter code is not
part of this content repository.

## Edit, validate, and preview

Run the following commands from the containing Orinoco Lite downstream:

```console
pixi run validate
pixi run build
pixi run serve
```

Review the source diff and rendered build. Do not commit or hand-edit generated
projection output.
