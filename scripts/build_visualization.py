#!/usr/bin/env python3
"""Fuse a codebase.json model into the self-contained viewer template.

Usage:
    python3 build_visualization.py codebase.json -o codecity.html [--open]
"""
import argparse
import json
import os
import subprocess
import sys

TEMPLATE = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                        "..", "assets", "viewer_template.html")
MARKER = "/*__DATA__*/null"


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("model", help="codebase.json produced by analyze_codebase.py")
    ap.add_argument("-o", "--output", default="codecity.html")
    ap.add_argument("--open", action="store_true",
                    help="Open the result in the default browser (macOS/Linux)")
    ap.add_argument("--view",
                    choices=["engine", "orbit", "circuit", "arc", "pipeline"],
                    default="engine",
                    help="Initial visualization mode (default: engine schematic)")
    args = ap.parse_args()

    with open(args.model, "r", encoding="utf-8") as f:
        model = json.load(f)
    with open(TEMPLATE, "r", encoding="utf-8") as f:
        html = f.read()

    if MARKER not in html:
        sys.exit("error: template is missing the data marker")
    # </script> inside JSON strings would terminate the script block early.
    payload = json.dumps(model).replace("</", "<\\/")
    html = html.replace(MARKER, payload, 1)
    html = html.replace('/*__MODE__*/"engine"', f'/*__MODE__*/"{args.view}"', 1)
    html = html.replace("<title>Shape Rotator</title>",
                        f"<title>{model.get('name', 'codebase')} - shape rotator</title>", 1)

    with open(args.output, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"wrote {args.output} ({os.path.getsize(args.output):,} bytes)")

    if args.open:
        opener = "open" if sys.platform == "darwin" else "xdg-open"
        subprocess.Popen([opener, os.path.abspath(args.output)],
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


if __name__ == "__main__":
    main()
