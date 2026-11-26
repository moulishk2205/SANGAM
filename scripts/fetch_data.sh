#!/usr/bin/env bash
# Restore data/ from the SANGAM `data-v1` GitHub release, verifying every file.
#
#   scripts/fetch_data.sh            # dictionaries + FLIS slice + GSA extract  (~100 MB download)
#   scripts/fetch_data.sh --all      # ...plus the three large FLIS archives    (~1 GB download)
#
# Why a release and not git: three of the FLIS archives are over GitHub's
# 100 MB per-file limit, and none of this is needed to run the platform —
# the engine, the trained scorer and the database all start without it.
# It is needed to rebuild the FLIS slice, inspect real item-name templates
# (scripts/show_template.py) or re-run the Sprint 0 research.
#
# The archives are byte-identical to what DLA published on 2026-08-26;
# SHA-256 for each is pinned in datasets/flis/MANIFEST.json.
set -euo pipefail

REPO="${SANGAM_REPO:-moulishk2205/SANGAM}"
TAG="${SANGAM_DATA_TAG:-data-v1}"
BASE="https://github.com/${REPO}/releases/download/${TAG}"
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
MANIFEST="$ROOT/datasets/flis/MANIFEST.json"

SMALL=(H-SERIES.zip MRD.zip)
LARGE=(FLISV.zip IDENTIFICATION.zip REFERENCE.zip)
FILES=("${SMALL[@]}")
[[ "${1:-}" == "--all" ]] && FILES+=("${LARGE[@]}")

sha() { shasum -a 256 "$1" 2>/dev/null | cut -d' ' -f1 || sha256sum "$1" | cut -d' ' -f1; }
want() { python3 -c "import json,sys; m=json.load(open('$MANIFEST')); print(next(a['sha256'] for a in m['archives'] if a['file']=='$1'))"; }

fetch() {  # url dest expected-sha
  local url="$1" dest="$2" expect="$3"
  if [[ -f "$dest" && "$(sha "$dest")" == "$expect" ]]; then
    echo "  ok      $(basename "$dest")  (cached)"; return
  fi
  echo "  fetch   $(basename "$dest")"
  curl -fL --retry 3 --progress-bar -o "$dest.part" "$url"
  local got; got="$(sha "$dest.part")"
  if [[ "$got" != "$expect" ]]; then
    echo "  FAILED  $(basename "$dest"): sha256 $got, expected $expect" >&2; exit 1
  fi
  mv "$dest.part" "$dest"
  echo "  ok      $(basename "$dest")  sha256 verified"
}

mkdir -p "$ROOT/data/raw/flis" "$ROOT/data/raw/gsa" "$ROOT/data/interim/flis" "$ROOT/data/interim/slice"
cp "$MANIFEST" "$ROOT/data/raw/flis/MANIFEST.json"

echo "DLA FLIS archives  →  data/raw/flis/"
for f in "${FILES[@]}"; do fetch "$BASE/$f" "$ROOT/data/raw/flis/$f" "$(want "$f")"; done

echo "GSA NSN extract (CC0)  →  data/raw/gsa/"
fetch "$BASE/nsn-extract.xlsx" "$ROOT/data/raw/gsa/nsn-extract.xlsx" \
  eb596b780164db55da5cf99cdde285b9167a3863ade81bcb8fc4db2523da0098

echo "FLIS slice (5306/5305/5310/4820/… families)  →  data/interim/slice/"
SLICE_SHA="$(python3 -c "import json; print(json.load(open('$ROOT/datasets/flis/release.json'))['flis-slice.zip'])")"
fetch "$BASE/flis-slice.zip" "$ROOT/data/flis-slice.zip" "$SLICE_SHA"
unzip -oq "$ROOT/data/flis-slice.zip" -d "$ROOT/data/interim"

echo "Dictionaries  →  data/interim/flis/"
for f in "${SMALL[@]}"; do unzip -oq "$ROOT/data/raw/flis/$f" -d "$ROOT/data/interim/flis"; done

echo "done. $(du -sh "$ROOT/data" | cut -f1) in data/"
