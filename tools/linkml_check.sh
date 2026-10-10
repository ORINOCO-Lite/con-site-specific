#!/bin/bash
# Validate a records tree against demo-research-information, one class per dir.
#
# NOTE: linkml-validate exits 0 even when it reports [ERROR], and its
# --config form silently validated nothing at all here (four injected faults
# all came back "No issues found").  So: direct -s/-C invocation, and grep
# for [ERROR].
S=/tmp/claude-1000/-home-yoh-proj-CON-talks/9372e983-51fc-4ade-b85b-a091af7b3932/scratchpad
SCHEMA=$S/schemas/demo-research-information/unreleased.yaml
ROOT="$1"; rc=0
for d in "$ROOT"/XYZ*/; do
  [ -d "$d" ] || continue
  cls=$(basename "$d")
  mapfile -t files < <(find "$d" -name '*.yaml' -not -name '.*' | sort)
  [ ${#files[@]} -eq 0 ] && continue
  out=$(uv run --quiet --with linkml linkml-validate -s "$SCHEMA" -C "$cls" "${files[@]}" 2>&1)
  vrc=$?
  if [ $vrc -ne 0 ]; then
    printf '%-18s %2d file(s)  FAIL (validator exited %d)\n' "$cls" "${#files[@]}" "$vrc"
    echo "$out" | tail -8 | sed 's/^/    /'; rc=1; continue
  fi
  # A crash, an unparseable file or any non-zero exit must NOT read as OK.
  # linkml-validate exits 0 even when it prints [ERROR], so both are checked.
  if echo "$out" | grep -qE '\[ERROR\]|Traceback|Error:|error:' ; then
    printf '%-18s %2d file(s)  FAIL\n' "$cls" "${#files[@]}"
    echo "$out" | grep '\[ERROR\]' | head -12 | sed 's/^/    /'; rc=1
  else
    printf '%-18s %2d file(s)  OK\n' "$cls" "${#files[@]}"
  fi
done
exit $rc
