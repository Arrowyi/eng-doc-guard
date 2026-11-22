#!/usr/bin/env bash
set -eu

ENG_DOC_GUARD_REMOTE="${ENG_DOC_GUARD_REMOTE:-https://github.com/Arrowyi/eng-doc-guard.git}"
: "${ENG_DOC_GUARD_REF:=main}"

PYTHON="${PYTHON:-python3}"

if ! command -v "$PYTHON" >/dev/null 2>&1; then
  echo "eng-doc-guard: python3 is required but was not found on PATH" >&2
  exit 1
fi

version="$("$PYTHON" --version 2>&1)"
version="${version#Python }"
major="${version%%.*}"
rest="${version#*.}"
minor="${rest%%.*}"
case "$major" in
  ''|*[!0-9]*)
    echo "eng-doc-guard: could not parse python version '$version'" >&2
    exit 1
    ;;
esac
case "$minor" in
  ''|*[!0-9]*)
    echo "eng-doc-guard: could not parse python version '$version'" >&2
    exit 1
    ;;
esac
if [ "$major" -lt 3 ] || { [ "$major" -eq 3 ] && [ "$minor" -lt 9 ]; }; then
  echo "eng-doc-guard: python3 >= 3.9 is required (found $version)" >&2
  exit 1
fi

if [ -n "${ENG_DOC_GUARD_SRC_DIR:-}" ]; then
  script="$ENG_DOC_GUARD_SRC_DIR/scripts/install.py"
  if [ ! -f "$script" ]; then
    echo "eng-doc-guard: $script not found" >&2
    exit 1
  fi
  exec "$PYTHON" "$script" "$@"
fi

if ! command -v git >/dev/null 2>&1; then
  echo "eng-doc-guard: git is required for a remote install" >&2
  exit 1
fi

tmpdir="$(mktemp -d)"
trap 'rm -rf "$tmpdir"' EXIT
git init -q "$tmpdir"
git -C "$tmpdir" remote add origin "$ENG_DOC_GUARD_REMOTE"
git -C "$tmpdir" fetch --depth 1 origin "$ENG_DOC_GUARD_REF"
git -C "$tmpdir" checkout -q FETCH_HEAD
exec "$PYTHON" "$tmpdir/scripts/install.py" "$@"
