#!/usr/bin/env python3
"""Analyze a codebase into a JSON model for 3D visualization.

Stdlib only. Walks a repo, measures source files, and extracts
import/dependency edges so the viewer can animate data flow.

Usage:
    python3 analyze_codebase.py /path/to/repo [-o out.json] [--max-files 400]
"""
import argparse
import json
import os
import re
import sys

SKIP_DIRS = {
    ".git", ".hg", ".svn", "node_modules", "vendor", "dist", "build", "out",
    "__pycache__", ".venv", "venv", "env", ".tox", ".mypy_cache", ".pytest_cache",
    "target", ".next", ".nuxt", "coverage", ".idea", ".vscode", "eggs",
    ".eggs", "site-packages", "bower_components", ".terraform", "Pods",
}

LANG_BY_EXT = {
    ".py": "python", ".js": "javascript", ".jsx": "javascript",
    ".ts": "typescript", ".tsx": "typescript", ".mjs": "javascript",
    ".cjs": "javascript", ".go": "go", ".rs": "rust", ".rb": "ruby",
    ".java": "java", ".kt": "kotlin", ".swift": "swift", ".c": "c",
    ".h": "c", ".cc": "cpp", ".cpp": "cpp", ".hpp": "cpp", ".cs": "csharp",
    ".php": "php", ".html": "html", ".css": "css", ".scss": "css",
    ".sh": "shell", ".sql": "sql", ".lua": "lua", ".ex": "elixir",
    ".exs": "elixir", ".vue": "vue", ".svelte": "svelte",
}

# "from . import a, b" / "from .. import c" - the module names live in the
# import list, so they need their own pattern and expansion.
PY_RELATIVE_FROM = re.compile(r"^\s*from\s+(\.+)\s+import\s+([\w\s,]+)", re.M)

ENTRY_HINTS = re.compile(
    r"(^|/)(main|index|app|cli|server|manage|__main__)\.[a-z]+$", re.I
)

# Per-language import patterns -> captured module string
IMPORT_PATTERNS = {
    "python": [
        re.compile(r"^\s*from\s+([\w\.]+)\s+import\b", re.M),
        re.compile(r"^\s*import\s+([\w\.]+)", re.M),
    ],
    "javascript": [
        re.compile(r"""(?:import|export)[^'"]*?from\s*['"]([^'"]+)['"]""", re.M),
        re.compile(r"""require\(\s*['"]([^'"]+)['"]\s*\)"""),
        re.compile(r"""import\s*\(\s*['"]([^'"]+)['"]\s*\)"""),
        re.compile(r"""^\s*import\s*['"]([^'"]+)['"]""", re.M),
    ],
    "go": [
        re.compile(r"""^\s*(?:import\s+)?(?:_\s+|\.\s+|\w+\s+)?"([^"]+)"\s*$""", re.M),
    ],
    "rust": [
        re.compile(r"^\s*(?:pub\s+)?use\s+(?:crate|self|super)::([\w:]+)", re.M),
        re.compile(r"^\s*mod\s+(\w+)\s*;", re.M),
    ],
    "ruby": [
        re.compile(r"""^\s*require(?:_relative)?\s+['"]([^'"]+)['"]""", re.M),
    ],
    "java": [
        re.compile(r"^\s*import\s+(?:static\s+)?([\w\.]+)", re.M),
    ],
    "php": [
        re.compile(r"""^\s*(?:require|include)(?:_once)?\s*\(?\s*['"]([^'"]+)['"]""", re.M),
        re.compile(r"^\s*use\s+([\w\\]+)", re.M),
    ],
}
IMPORT_PATTERNS["typescript"] = IMPORT_PATTERNS["javascript"]
IMPORT_PATTERNS["vue"] = IMPORT_PATTERNS["javascript"]
IMPORT_PATTERNS["svelte"] = IMPORT_PATTERNS["javascript"]


def find_files(root, max_files):
    files = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = sorted(
            d for d in dirnames if d not in SKIP_DIRS and not d.startswith(".")
        )
        for fn in sorted(filenames):
            ext = os.path.splitext(fn)[1].lower()
            if ext not in LANG_BY_EXT:
                continue
            full = os.path.join(dirpath, fn)
            try:
                if os.path.getsize(full) > 2_000_000:
                    continue
            except OSError:
                continue
            files.append(full)
    # If the repo is huge, keep the largest files (they dominate the skyline
    # anyway) so the viewer stays smooth.
    if len(files) > max_files:
        files.sort(key=lambda f: -os.path.getsize(f))
        files = files[:max_files]
    return files


def read_text(path):
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            return f.read()
    except OSError:
        return ""


def module_keys(rel_path):
    """Keys under which other files might import this file.

    e.g. src/utils/foo.py -> {"src.utils.foo", "utils.foo", "foo",
                              "src/utils/foo", "./foo", ...}
    """
    no_ext = os.path.splitext(rel_path)[0]
    parts = no_ext.replace("\\", "/").split("/")
    keys = set()
    for i in range(len(parts)):
        tail = parts[i:]
        keys.add("/".join(tail))
        keys.add(".".join(tail))
    if parts[-1] in ("index", "__init__", "mod") and len(parts) > 1:
        for i in range(len(parts) - 1):
            tail = parts[i:-1]
            keys.add("/".join(tail))
            keys.add(".".join(tail))
    return keys


def resolve_edges(file_infos, root):
    """Best-effort resolution of import strings to files inside the repo."""
    key_to_idx = {}
    for idx, fi in enumerate(file_infos):
        for k in module_keys(fi["path"]):
            # First writer wins; ties are rare and harmless for viz purposes.
            key_to_idx.setdefault(k, idx)

    edge_weights = {}
    for idx, fi in enumerate(file_infos):
        patterns = IMPORT_PATTERNS.get(fi["lang"])
        if not patterns:
            continue
        text = read_text(os.path.join(root, fi["path"]))
        seen_targets = set()
        if fi["lang"] == "python":
            for m in PY_RELATIVE_FROM.finditer(text):
                dots = m.group(1)
                for name in m.group(2).split(","):
                    name = name.strip().split()[0] if name.strip() else ""
                    if not name:
                        continue
                    target = resolve_one(dots + name, fi["path"], key_to_idx)
                    if target is not None and target != idx:
                        seen_targets.add(target)
        for pat in patterns:
            for m in pat.finditer(text):
                mod = m.group(1).strip()
                target = resolve_one(mod, fi["path"], key_to_idx)
                if target is not None and target != idx:
                    seen_targets.add(target)
        for t in seen_targets:
            key = (idx, t)
            edge_weights[key] = edge_weights.get(key, 0) + 1
    return [
        {"from": a, "to": b, "weight": w} for (a, b), w in sorted(edge_weights.items())
    ]


def resolve_one(mod, importer_path, key_to_idx):
    mod = mod.strip()
    # Relative path style: ./foo, ../bar/baz
    if mod.startswith("."):
        base = os.path.dirname(importer_path)
        # python relative: .foo / ..foo
        if re.match(r"^\.+[\w\.]*$", mod) and "/" not in mod:
            dots = len(mod) - len(mod.lstrip("."))
            rest = mod.lstrip(".")
            parts = base.replace("\\", "/").split("/") if base else []
            parts = parts[: len(parts) - (dots - 1)] if dots > 1 else parts
            candidate = ".".join([p for p in parts if p] + rest.split(".")) if rest else ".".join(p for p in parts if p)
        else:
            candidate = os.path.normpath(os.path.join(base, mod)).replace("\\", "/")
        # ES modules import with the extension ("./api.js"); keys are stored
        # extension-less, so try the stripped form too.
        stripped = os.path.splitext(candidate)[0]
        for k in (candidate, stripped, candidate.replace("/", "."),
                  stripped.replace("/", "."), candidate + "/index",
                  stripped + "/index"):
            if k in key_to_idx:
                return key_to_idx[k]
        return None
    # Absolute-ish module path: try full string then progressively shorter tails
    norm = mod.replace("\\", "/")
    candidates = [norm, norm.replace("/", "."), norm.replace(".", "/")]
    for c in candidates:
        if c in key_to_idx:
            return key_to_idx[c]
    # Tail match: pkg.sub.mod -> sub.mod -> mod
    parts = re.split(r"[./]|::|\\\\", norm)
    for i in range(1, len(parts)):
        tail_dot = ".".join(parts[i:])
        tail_slash = "/".join(parts[i:])
        if tail_dot in key_to_idx:
            return key_to_idx[tail_dot]
        if tail_slash in key_to_idx:
            return key_to_idx[tail_slash]
    return None


def analyze(root, max_files):
    root = os.path.abspath(root)
    paths = find_files(root, max_files)
    file_infos = []
    for p in paths:
        rel = os.path.relpath(p, root).replace("\\", "/")
        ext = os.path.splitext(p)[1].lower()
        text = read_text(p)
        loc = text.count("\n") + (1 if text and not text.endswith("\n") else 0)
        file_infos.append({
            "path": rel,
            "dir": os.path.dirname(rel).replace("\\", "/") or ".",
            "loc": loc,
            "lang": LANG_BY_EXT[ext],
            "entry": bool(ENTRY_HINTS.search(rel)),
        })
    edges = resolve_edges(file_infos, root)
    # Deliberately no absolute "root" path in the model: outputs get shared,
    # and machine paths (usernames, company dirs) don't belong in them.
    return {
        "name": os.path.basename(root.rstrip("/")) or "codebase",
        "files": file_infos,
        "edges": edges,
        "totals": {
            "files": len(file_infos),
            "loc": sum(f["loc"] for f in file_infos),
            "edges": len(edges),
        },
    }


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("root", help="Path to the codebase to analyze")
    ap.add_argument("-o", "--output", default="codebase.json")
    ap.add_argument("--max-files", type=int, default=400,
                    help="Cap on rendered files; largest kept (default 400)")
    args = ap.parse_args()

    if not os.path.isdir(args.root):
        sys.exit(f"error: {args.root} is not a directory")
    model = analyze(args.root, args.max_files)
    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(model, f)
    t = model["totals"]
    print(f"{model['name']}: {t['files']} files, {t['loc']} LOC, "
          f"{t['edges']} dependency edges -> {args.output}")
    if t["files"] == 0:
        print("warning: no recognized source files found", file=sys.stderr)


if __name__ == "__main__":
    main()
