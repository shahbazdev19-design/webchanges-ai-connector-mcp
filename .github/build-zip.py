#!/usr/bin/env python3
"""Build the distributable plugin zip, and refuse to produce a broken one.

Single source of truth for packaging: CI calls this, and so should you. Run
from the repo root:

    python .github/build-zip.py                 # build + verify
    python .github/build-zip.py --version 1.0.1 # also assert every version string matches

WordPress.org rejects hidden files, so every dot-file and dot-directory is
excluded -- which conveniently also drops .github/ and .wordpress-org/.
"""

import argparse
import os
import re
import sys
import zipfile

SLUG = "webchanges-ai-connector-mcp"
MAIN_FILE = f"{SLUG}.php"
# Dev artefacts that are tracked in git but must never ship.
SKIP_FILES = {"HANDOVER.md", "composer.lock"}

# WordPress reads only the first 8 KB of a file when looking for headers.
HEADER_BYTES = 8192


def plugin_name(path):
    """Replicate get_file_data()'s 'Name' lookup: a raw regex, not a PHP parse."""
    with open(path, "rb") as fh:
        chunk = fh.read(HEADER_BYTES)
    text = chunk.decode("utf-8", "replace").replace("\r\n", "\n").replace("\r", "\n")
    match = re.search(r"^[ \t/*#@]*Plugin Name:(.*)$", text, re.I | re.M)
    return re.sub(r"\s*(?:\*/|\?>).*", "", match.group(1)).strip() if match else ""


def file_header(path, label):
    with open(path, encoding="utf-8", errors="replace") as fh:
        text = fh.read()
    match = re.search(rf"^[ 	/*#@]*{label}\s*(.+)$", text, re.M)
    return match.group(1).strip() if match else None


def check_single_plugin_header(root):
    """Guard the bug fixed in 425925d.

    get_plugins('/<slug>') scans <root>/*.php AND <root>/*/*.php. If a second
    file in there looks like a plugin, Plugin_Upgrader::plugin_info() can pick
    it instead of the main file, and the install screen's "Activate Plugin"
    link then points at a path the global get_plugins() cannot see -- producing
    "The plugin does not have a valid header."
    """
    found = {}
    for entry in sorted(os.listdir(root)):
        if entry.startswith("."):
            continue
        path = os.path.join(root, entry)
        if os.path.isdir(path):
            for sub in sorted(os.listdir(path)):
                if sub.startswith(".") or not sub.endswith(".php"):
                    continue
                name = plugin_name(os.path.join(path, sub))
                if name:
                    found[f"{entry}/{sub}"] = name
        elif entry.endswith(".php"):
            name = plugin_name(path)
            if name:
                found[entry] = name
    return found


def build(root, out):
    # The output may legitimately sit inside the tree being walked (CI writes to
    # ./dist). Archiving it would add a partial copy of the zip to itself -- and
    # on Linux hangs outright, because zipfile reads to EOF while writing keeps
    # moving EOF. Skip the output path explicitly.
    out_real = os.path.realpath(out)
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as archive:
        for base, dirs, files in os.walk(root):
            dirs[:] = [d for d in dirs if not d.startswith(".")]
            for name in files:
                if name.startswith(".") or name in SKIP_FILES:
                    continue
                path = os.path.join(base, name)
                if os.path.realpath(path) == out_real:
                    continue
                rel = os.path.relpath(path, root).replace(os.sep, "/")
                archive.write(path, f"{SLUG}/{rel}")
    return out


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--version", help="assert every version string equals this")
    parser.add_argument("--out", default=None, help="output zip path")
    args = parser.parse_args()

    root = os.getcwd()
    if not os.path.isfile(os.path.join(root, MAIN_FILE)):
        sys.exit(f"Run from the repo root: {MAIN_FILE} not found here.")

    failures = []

    # 1. Exactly one file may advertise itself as a plugin.
    headers = check_single_plugin_header(root)
    if list(headers) != [MAIN_FILE]:
        failures.append(
            "get_plugins('/%s') would return %d entries, not 1:\n    %s\n"
            "    A non-main file carrying a literal 'Plugin Name:' breaks the\n"
            "    install screen's Activate link."
            % (SLUG, len(headers), "\n    ".join(f"{k} -> {v!r}" for k, v in headers.items()))
        )

    # 2. Version strings must agree with each other (and the tag, if given).
    versions = {
        "plugin header Version": file_header(MAIN_FILE, r"\*\s*Version:"),
        "WEBCHANGES_CONNECTOR_VERSION": (
            re.search(r"WEBCHANGES_CONNECTOR_VERSION',\s*'([^']+)'", open(MAIN_FILE, encoding="utf-8").read()) or [None, None]
        )[1],
        "readme.txt Stable tag": file_header("readme.txt", r"Stable tag:"),
    }
    want = args.version or versions["plugin header Version"]
    mismatched = {k: v for k, v in versions.items() if v != want}
    if mismatched:
        failures.append(
            "version strings disagree (expected %r):\n    %s"
            % (want, "\n    ".join(f"{k} = {v!r}" for k, v in versions.items()))
        )

    if failures:
        sys.exit("BUILD REFUSED\n\n  " + "\n\n  ".join(failures))

    out = args.out or os.path.join(os.path.dirname(root), f"{SLUG}.zip")
    build(root, out)

    # 3. Verify what actually came out.
    names = zipfile.ZipFile(out).namelist()
    tops = {n.split("/")[0] for n in names}
    hidden = [n for n in names if any(p.startswith(".") for p in n.split("/"))]
    if tops != {SLUG}:
        sys.exit(f"BUILD REFUSED: top-level folder(s) {sorted(tops)}, expected ['{SLUG}']")
    if hidden:
        sys.exit(f"BUILD REFUSED: hidden files in zip: {hidden[:5]}")
    if f"{SLUG}/{MAIN_FILE}" not in names:
        sys.exit(f"BUILD REFUSED: {MAIN_FILE} missing from zip")

    print(f"built {out}")
    print(f"  version   : {want}")
    print(f"  folder    : {SLUG}/")
    print(f"  files     : {len(names)}")
    print(f"  size      : {os.path.getsize(out) / 1048576:.2f} MB")
    print("  hidden    : none")
    print(f"  plugin hdr: {headers[MAIN_FILE]!r} (single)")


if __name__ == "__main__":
    main()
