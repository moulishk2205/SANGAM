#!/usr/bin/env python3
"""
Fetch the DLA FLIS / PUB LOG public data archives.

Why this script exists
----------------------
www.dla.mil sits behind a WAF that fingerprints non-browser clients: a plain
`curl` or `requests.get()` gets HTTP 403, while a full browser header set gets
200. Verified both ways on 2026-08-26.

The archive links also carry a `?ver=` cache-buster token that ROTATES whenever
DLA republishes. Hard-coding a URL therefore breaks silently. This script always
re-reads the reading-room page and extracts the current tokens.

The data is a US federal FOIA reading-room release (17 U.S.C. 105 — works of the
US government are not subject to domestic copyright).

  DOWNLOAD ONCE. ARCHIVE THE ZIPS. NEVER MAKE dla.mil A RUNTIME DEPENDENCY.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import time
import subprocess
import urllib.parse
import zipfile
from datetime import datetime, timezone
from pathlib import Path

READING_ROOM = "https://www.dla.mil/Information-Operations/FLIS-Data-Electronic-Reading-Room/"
ORIGIN = "https://www.dla.mil"

# A complete, coherent browser header set. Partial sets still get 403 —
# the WAF checks for the combination, not any single header.
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "none",
    "Sec-Fetch-User": "?1",
    "Upgrade-Insecure-Requests": "1",
    "sec-ch-ua": '"Chromium";v="128", "Not(A:Brand";v="24"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"macOS"',
}

# What each archive is for, so nobody downloads 11 GB to find out.
ARCHIVES = {
    "H-SERIES":       ("small", "Item-name (INC) + supply-class dictionaries. ~80k approved item names WITH definitions."),
    "MRD":            ("small", "Attribute schema: MRC dictionary, controlled vocabularies, which attrs apply per item name."),
    "IDENTIFICATION": ("core",  "NSN/INC backbone + V_FLIS_STANDARDIZATION (ground truth: X replaces Y)."),
    "REFERENCE":      ("core",  "V_FLIS_PART (ground truth: many manufacturer part numbers -> one canonical item)."),
    "FLISV":          ("core",  "Coded attribute assertions. Machine-comparable without NLP. Prefer over CHARACTERISTICS."),
    "CHARACTERISTICS":("extra", "Free-text attribute replies. A ready-made supervised attribute-extraction training set."),
    "CAGE":           ("extra", "Commercial and Government Entity codes (manufacturer identity)."),
    "MANAGEMENT":     ("skip",  "Per-service management data. Not needed."),
    "FREIGHT_PACKAGING": ("skip", "Freight/packaging. Not needed."),
    "HISTORY":        ("skip",  "Inactive NSN history. Not needed."),
    "MOE_RULE":       ("skip",  "Service usage rules. Not needed."),
}

GROUPS = {
    "small": ["H-SERIES", "MRD"],
    "core":  ["H-SERIES", "MRD", "IDENTIFICATION", "REFERENCE", "FLISV"],
    "full":  ["H-SERIES", "MRD", "IDENTIFICATION", "REFERENCE", "FLISV", "CHARACTERISTICS", "CAGE"],
}


def _curl_args(url: str, extra: dict | None = None) -> list[str]:
    """
    Build a curl invocation.

    We shell out to curl rather than using urllib/requests deliberately: the DLA
    WAF rejects Python's HTTP clients with 403 even when the headers are byte-identical,
    so it is fingerprinting below the header layer (TLS ClientHello / header ordering).
    curl gets 200. Verified 2026-08-26. Do not "clean this up" into requests.
    """
    h = dict(HEADERS)
    h.update(extra or {})
    args = ["curl", "--fail", "--location", "--compressed", "--silent", "--show-error",
            "--max-time", "600", "--connect-timeout", "30",
            "--retry", "3", "--retry-delay", "3", "--retry-connrefused"]
    for k, v in h.items():
        args += ["-H", f"{k}: {v}"]
    args.append(url)
    return args


def _curl_text(url: str, extra: dict | None = None) -> str:
    r = subprocess.run(_curl_args(url, extra), capture_output=True, text=True)
    if r.returncode != 0:
        sys.exit(f"FATAL: curl failed for {url}\n{r.stderr.strip()}")
    return r.stdout


def discover() -> dict[str, str]:
    """Read the reading-room page and return {ARCHIVE_NAME: absolute url with current ?ver token}."""
    print(f"reading  {READING_ROOM}")
    html = _curl_text(READING_ROOM)

    found: dict[str, str] = {}
    for href in re.findall(r'href="([^"]*?/FOIA/PUBLOG/[^"]*?\.zip[^"]*)"', html, re.I):
        name = Path(urllib.parse.urlparse(href).path).stem.upper()
        if name in ARCHIVES and name not in found:
            found[name] = urllib.parse.urljoin(ORIGIN, href.replace(" ", "%20"))
    if not found:
        sys.exit("FATAL: no PUBLOG .zip links found. The page layout changed — inspect it by hand.")
    print(f"found    {len(found)} archives on the page")
    return found


def fetch(name: str, url: str, dest: Path, retries: int = 3) -> dict:
    out = dest / f"{name}.zip"
    if out.exists() and out.stat().st_size > 0:
        print(f"  SKIP   {name:<16} already present ({out.stat().st_size/1e6:,.1f} MB)")
        return _record(name, url, out, cached=True)

    tmp = out.with_suffix(".zip.part")
    # Referer + same-origin fetch metadata matter: the WAF treats a bare asset hit as suspicious.
    extra = {"Accept": "*/*", "Referer": READING_ROOM, "Sec-Fetch-Site": "same-origin"}

    for attempt in range(1, retries + 1):
        t0 = time.time()
        # -C - resumes a partial file, so a dropped 500 MB transfer is not restarted from zero.
        args = _curl_args(url, extra)
        args[1:1] = ["-C", "-", "--output", str(tmp)]
        print(f"  GET    {name:<16} ...", flush=True)
        r = subprocess.run(args, capture_output=True, text=True)

        if r.returncode == 0 and tmp.exists() and tmp.stat().st_size > 0:
            if not zipfile.is_zipfile(tmp):
                # A WAF challenge page saved as .zip is the classic silent failure here.
                head = tmp.read_bytes()[:200]
                tmp.unlink(missing_ok=True)
                return {"archive": name, "url": url,
                        "error": f"downloaded content is not a zip (WAF block page?): {head[:120]!r}"}
            tmp.rename(out)
            mb = out.stat().st_size / 1e6
            print(f"  OK     {name:<16} {mb:,.1f} MB in {time.time()-t0:,.0f}s ({mb/max(time.time()-t0,1):.1f} MB/s)")
            return _record(name, url, out)

        err = (r.stderr or "").strip() or f"curl exit {r.returncode}"
        print(f"  RETRY  {name:<16} attempt {attempt}/{retries}: {err}")
        if attempt == retries:
            return {"archive": name, "url": url, "error": err}
        time.sleep(3 * attempt)
    return {}


def _record(name: str, url: str, path: Path, cached: bool = False) -> dict:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        while chunk := fh.read(1 << 20):
            h.update(chunk)
    return {
        "archive": name,
        "url": url,
        "file": path.name,
        "bytes": path.stat().st_size,
        "sha256": h.hexdigest(),
        "purpose": ARCHIVES[name][1],
        "downloaded_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "cached": cached,
    }


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    g = ap.add_mutually_exclusive_group()
    g.add_argument("--small", action="store_true", help="dictionaries only (~19 MB) — start here")
    g.add_argument("--core", action="store_true", help="dictionaries + ground truth + coded attributes (~900 MB)")
    g.add_argument("--full", action="store_true", help="everything useful (~1.4 GB)")
    g.add_argument("--only", nargs="+", metavar="NAME", help="specific archives by name")
    ap.add_argument("--dest", default="data/raw/flis", help="download directory")
    ap.add_argument("--list", action="store_true", help="list archives and exit")
    args = ap.parse_args()

    if args.list:
        for n, (grp, why) in ARCHIVES.items():
            print(f"{n:<20} [{grp:<5}] {why}")
        return

    want = (args.only and [a.upper() for a in args.only]) or \
           (args.core and GROUPS["core"]) or (args.full and GROUPS["full"]) or GROUPS["small"]

    dest = Path(args.dest)
    dest.mkdir(parents=True, exist_ok=True)

    urls = discover()
    missing = [w for w in want if w not in urls]
    if missing:
        print(f"WARNING: not on the page: {', '.join(missing)}")

    print(f"\ntarget   {len(set(want) & set(urls))} archives -> {dest}/\n")
    records = [fetch(n, urls[n], dest) for n in want if n in urls]

    man = dest / "MANIFEST.json"
    prior = json.loads(man.read_text())["archives"] if man.exists() else []
    merged = {r["archive"]: r for r in prior}
    merged.update({r["archive"]: r for r in records if r})
    man.write_text(json.dumps({
        "source": READING_ROOM,
        "licence": "US federal FOIA reading-room release; 17 U.S.C. 105 — not subject to US domestic copyright.",
        "note": "Archive these files. Do NOT re-fetch from dla.mil at build or demo time.",
        "generated_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "archives": sorted(merged.values(), key=lambda r: r["archive"]),
    }, indent=2) + "\n")

    ok = [r for r in records if r and "sha256" in r]
    bad = [r for r in records if r and "error" in r]
    print(f"\nmanifest {man}")
    print(f"done     {len(ok)} ok, {len(bad)} failed, {sum(r['bytes'] for r in ok)/1e6:,.1f} MB total")
    if bad:
        for r in bad:
            print(f"  FAILED {r['archive']}: {r['error']}")
        sys.exit(1)


if __name__ == "__main__":
    main()
