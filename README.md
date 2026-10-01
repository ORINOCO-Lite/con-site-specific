# Center for Open Neuroscience site inputs

This directory is the declarative, site-owned layer of the Center for Open Neuroscience website and a presentation-independent store of reviewed CON metadata.
It is the repository root here and is integrated at `site-specific/` in the Orinoco Lite downstream as a DataLad subdataset (Git submodule).
Paths in this document are relative to this directory.

## Content provenance

The full provenance for this content is not yet consolidated.
Its history is spread across:

- [CON research information](https://github.com/con/dump-research-info/);
- [the Orinoco Lite demo](https://github.com/leej3/orinoco-lite-demo); and
- [the existing CON website](https://centerforopenneuroscience.org).

Additional context for the earlier trimming of `orinoco-lite-demo` is preserved in [this shared conversation](https://claude.ai/share/a2aeb683-48a5-4f41-aff1-db2287ef3566).

## Structure

| Path | Purpose |
| --- | --- |
| `metadata/records/` | Reviewed Things YAML records; preserve stable PIDs. |
| `metadata/overlays/machine-provenance-annotations/` | Machine-managed provenance companions. |
| `content/` | Editorial pages, group order, and Hugo page resources. |
| `assets/`, `static/` | Site-owned assets; binary media are stored in Git Annex. |
| `sources/`, `curation-records/` | Source declarations and reviewed curation decisions. |

Together, `metadata/records/` and `metadata/overlays/machine-provenance-annotations/` are the canonical metadata store for reviewed CON assertions and their machine provenance.
The Orinoco Lite website is one projection of those inputs.
Other consumers can derive different representations from the same metadata without depending on the website or treating generated output as canonical.

The downstream configures CON identity, navigation, and presentation in `pyproject.toml` (`tool.orinoco.site`).
The former `site.yaml` remains recoverable in this repository’s history.

The homepage is `content/_index.md`.
Portraits live beside generated person pages as `portrait.*`, and project artwork lives beside generated project pages as `logo.*`.
These are ordinary Hugo page resources and do not require a downstream theme override.

Source declarations refer to executable adapters under `extensions/source-adapters/` from the downstream repository root.
Adapter code and the Orinoco Lite scaffold remain outside this subdataset.

## DataLad integration and media

Install this dataset from a downstream with Git Annex in its Pixi environment:

```console
pixi run datalad install -d . \
  -s https://github.com/ORINOCO-Lite/con-site-specific.git site-specific
```

The downstream pins the content commit and sets `tool.orinoco.media.annex = true` in `pyproject.toml`.
Builds retrieve and verify media from the public [DataLad Hub sibling](https://hub.datalad.org/leej3/con-site-specific-annex).
No upload credential is needed to build.

Binary media under `assets/` and `static/` use Annex.
Metadata, reviewed decisions, configuration, editorial text, and the existing portrait and logo page resources under `content/` remain in Git.
The media storage conversion rewrote historical commits while preserving their authored changes and media bytes.
Use a fresh clone after this migration; do not merge an older checkout's history back into the repository.

Before publishing new media, upload its Annex content and publish the shared `git-annex` branch, then advance the downstream's content gitlink.
Follow the package's [Annex media guide](https://github.com/ORINOCO-Lite/orinoco-lite-dev/blob/main/docs/agents/annex-media.md) for native sibling configuration and publication commands.

## Edit, validate, and preview

Run these commands from the downstream repository root, not this directory:

```console
pixi run orinoco-lite validate
pixi run build
pixi run serve
```

Review the source diff and rendered build.
Do not commit or hand-edit generated projection output.

## Documentation above this layer

- [Orinoco Lite template](https://github.com/ORINOCO-Lite/orinoco-lite-template): downstream scaffold creation and maintenance.
- [Project design charter](https://github.com/ORINOCO-Lite/orinoco-lite-dev/blob/main/docs/project-design.md): system responsibilities and data flows.
- [Orinoco Lite package](https://github.com/ORINOCO-Lite/orinoco-lite-dev): commands and package integrity.
- [Orinoco Lite releases](https://github.com/ORINOCO-Lite/orinoco-lite-dev/releases): immutable package and template selections.

Those shared layers do not own CON records, site-specific policy, or this site's provenance.
