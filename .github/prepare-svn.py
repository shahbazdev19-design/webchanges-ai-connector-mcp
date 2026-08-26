#!/usr/bin/env python3
"""Stage a WordPress.org SVN working copy from a built release zip.

The layout WordPress.org expects is easy to get wrong: trunk/ takes the
*contents* of the zip's inner folder, not the folder itself, and assets/ sits
beside trunk/ rather than inside it. This does that and then verifies it.

    python .github/prepare-svn.py --svn ../svn-webchanges --zip ../webchanges-ai-connector-mcp.zip

Afterwards it prints the svn commands to run. It never invokes svn itself, so
nothing is committed without you doing it.
"""

import argparse
import os
import re
import shutil
import sys
import zipfile

SLUG = "webchanges-ai-connector-mcp"
MAIN_FILE = f"{SLUG}.php"


def die(msg):
    sys.exit(f"REFUSED: {msg}")


def header(path, label):
    with open(path, encoding="utf-8", errors="replace") as fh:
        text = fh.read()
    m = re.search(rf"^[ \t/*#@]*{label}\s*(.+)$", text, re.M)
    return m.group(1).strip() if m else None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--svn", required=True, help="path to the SVN checkout")
    ap.add_argument("--zip", required=True, help="path to the built release zip")
    ap.add_argument("--assets", default=".wordpress-org", help="directory holding the directory assets")
    args = ap.parse_args()

    svn = os.path.abspath(args.svn)
    if not os.path.isdir(svn):
        die(f"{svn} does not exist. Run `svn co https://plugins.svn.wordpress.org/{SLUG}` first.")
    if not os.path.isdir(os.path.join(svn, ".svn")):
        die(f"{svn} is not an SVN working copy (no .svn directory).")

    # --- trunk: the CONTENTS of the zip's inner folder ----------------------
    trunk = os.path.join(svn, "trunk")
    if os.path.isdir(trunk):
        for name in os.listdir(trunk):
            if name == ".svn":
                continue
            p = os.path.join(trunk, name)
            shutil.rmtree(p) if os.path.isdir(p) else os.remove(p)
    else:
        os.makedirs(trunk)

    with zipfile.ZipFile(args.zip) as z:
        names = z.namelist()
        tops = {n.split("/")[0] for n in names}
        if tops != {SLUG}:
            die(f"zip has top-level {sorted(tops)}, expected ['{SLUG}']")
        for n in names:
            rel = n[len(SLUG) + 1:]
            if not rel:
                continue
            dest = os.path.join(trunk, rel.replace("/", os.sep))
            os.makedirs(os.path.dirname(dest), exist_ok=True)
            with z.open(n) as src, open(dest, "wb") as out:
                shutil.copyfileobj(src, out)

    # --- assets: beside trunk, never inside it -----------------------------
    assets_src = os.path.abspath(args.assets)
    assets_dst = os.path.join(svn, "assets")
    os.makedirs(assets_dst, exist_ok=True)
    copied = []
    for name in sorted(os.listdir(assets_src)):
        shutil.copy2(os.path.join(assets_src, name), os.path.join(assets_dst, name))
        copied.append(name)

    # --- verify -------------------------------------------------------------
    problems = []
    if not os.path.isfile(os.path.join(trunk, MAIN_FILE)):
        problems.append(f"trunk/{MAIN_FILE} missing -- you copied the folder, not its contents")
    if not os.path.isfile(os.path.join(trunk, "readme.txt")):
        problems.append("trunk/readme.txt missing (it must sit at the root of trunk)")

    version = header(os.path.join(trunk, MAIN_FILE), r"\*\s*Version:")
    stable = header(os.path.join(trunk, "readme.txt"), r"Stable tag:")
    if stable == "trunk":
        problems.append("Stable tag is 'trunk' -- WordPress.org requires a version number")
    if version != stable:
        problems.append(f"plugin Version {version!r} != readme Stable tag {stable!r}")

    hidden = []
    for base, dirs, files in os.walk(trunk):
        dirs[:] = [d for d in dirs if d != ".svn"]
        hidden += [f for f in files if f.startswith(".")]
        hidden += [d for d in dirs if d.startswith(".")]
    if hidden:
        problems.append(f"hidden files in trunk: {sorted(set(hidden))[:5]}")

    if problems:
        die("\n  - " + "\n  - ".join(problems))

    n_trunk = sum(len(f) for _, _, f in os.walk(trunk))
    print(f"staged {svn}")
    print(f"  trunk/   {n_trunk} files   (version {version})")
    print(f"  assets/  {len(copied)} files: {', '.join(copied)}")
    print(f"  Stable tag {stable} -- tag {stable} must exist before this is correct")
    print()
    print("Next, from the SVN checkout:")
    print("  svn add --force trunk assets")
    print(f'  svn ci -m "Webchanges - AI Connector (MCP) {version}"')
    print(f'  svn cp trunk tags/{version}')
    print(f'  svn ci -m "Tag {version}"')


if __name__ == "__main__":
    main()
