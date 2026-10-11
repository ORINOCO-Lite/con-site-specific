#!/bin/bash
# Validate a records tree against demo-research-information, one class per dir.
#
# Usage:  tools/linkml_check.sh [records-dir]
#         THINGS_SCHEMAS=/path/to/things-schemas tools/linkml_check.sh
#
# The schema imports siblings by URL prefix (dlschemas:things-prov/v1), which
# linkml cannot resolve offline, so a copy is made with the imports rewritten
# to relative paths -- the same rewrite the upstream Makefile's `imports-local`
# target performs.  The copy is cached and rebuilt when the source is newer.
#
# NOTE on reading the result: linkml-validate exits 0 even when it prints
# [ERROR], and its --config form silently validated nothing at all here (four
# deliberately broken records all came back "No issues found").  So: direct
# -s/-C invocation, and a non-zero exit or a traceback is a failure.
set -e
ROOT=$(cd "$(dirname "$0")/.." && pwd)
RECORDS="${1:-$ROOT/metadata/records}"

# Locate things-schemas: an explicit override, a sibling checkout, or the
# ORINOCO-Lite submodule tree.
if [ -z "$THINGS_SCHEMAS" ]; then
  for c in "$ROOT/../orinoco-lite-dev/submodules/things-schemas" \
           "$ROOT/../things-schemas" \
           "$HOME/proj/orinoco-lite/orinoco-lite-dev/submodules/things-schemas"; do
    [ -d "$c/src/demo-research-information" ] && THINGS_SCHEMAS=$(cd "$c" && pwd) && break
  done
fi
if [ ! -d "$THINGS_SCHEMAS/src/demo-research-information" ]; then
  echo "things-schemas not found; set THINGS_SCHEMAS=/path/to/things-schemas" >&2
  exit 3
fi

CACHE="${TMPDIR:-/tmp}/con-linkml-schemas-$(id -u)"
SCHEMA="$CACHE/demo-research-information/unreleased.yaml"
if [ ! -f "$SCHEMA" ] || [ "$THINGS_SCHEMAS/src/demo-research-information/unreleased.yaml" -nt "$SCHEMA" ]; then
  rm -rf "$CACHE"
  cp -r "$THINGS_SCHEMAS/src" "$CACHE"
  # dlschemas:things-prov/v1  ->  ../things-prov/v1
  sed -i -e 's,- dlschemas:\(.*/.*\)$,- ../\1,' "$CACHE"/*/*.yaml
fi

rc=0
for d in "$RECORDS"/XYZ*/; do
  [ -d "$d" ] || continue
  cls=$(basename "$d")
  mapfile -t files < <(find "$d" -name '*.yaml' -not -name '.*' | sort)
  [ ${#files[@]} -eq 0 ] && continue
  out=$(uv run --quiet --with linkml linkml-validate -s "$SCHEMA" -C "$cls" "${files[@]}" 2>&1)
  vrc=$?
  if [ $vrc -ne 0 ] || echo "$out" | grep -qE '\[ERROR\]|Traceback'; then
    printf '%-20s %3d file(s)  FAIL\n' "$cls" "${#files[@]}"
    echo "$out" | grep -E '\[ERROR\]|Error' | head -10 | sed 's/^/    /'
    rc=1
  else
    printf '%-20s %3d file(s)  OK\n' "$cls" "${#files[@]}"
  fi
done
exit $rc
