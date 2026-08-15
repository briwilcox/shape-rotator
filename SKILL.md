---
name: shape-rotator
description: Visualize a codebase as an interactive machine showing how the program works, inputs to outputs, with five selectable modes: a jet-engine-style 2D schematic (labeled INTAKE/STAGE/CORE phases, dependency ribbons that heat up blue to red as flow moves deeper), a freely tumbling 3D orbit constellation, a circuit-board schematic, an arc-diagram skyline, and a rotatable 3D staged pipeline; all with click-to-trace dependency inspection and dual animated flows (gold logic calls out, blue data returns) along imports. Use this whenever the user wants to "see" or understand a codebase visually: 3D or visual maps of code structure or architecture, "shape rotate" a repo, visualize dependencies or data flow, understand how a program fits together or where execution flows, even if they don't say "3D" explicitly.
---

# Shape Rotator: codebase to dependency machine

Turn any codebase into a single self-contained interactive HTML file that
shows how the program works. Files are staged by dependency depth: the
intake holds entrypoints and scripts nothing else imports, each next stage
holds what the previous stage imports, and the core is what the whole
program leans on. The analyzer condenses import cycles (SCC) so cycle
members share a stage. Five modes render that model, cycleable in the
viewer and selectable at build time with `--view`:

- `engine` (default): a jet-engine cross-section schematic. Horizontal
  phase bands labeled `INTAKE » STAGE n » CORE`, files as blade rows
  grouped and tagged by folder, a nacelle silhouette, and dependency
  ribbons flowing left to right that heat up from blue through orange to
  red as they move deeper. Return flows loop under the engine as a dashed
  bypass duct.
- `orbit`: a 3D constellation. Every folder is a cluster of solids (cubes
  for code, gem octahedra for support files) on a sphere, freely tumblable
  to any angle with flick momentum.
- `circuit`: a PCB schematic. Folders are chips, files are pads, imports
  are copper traces with signal pulses.
- `arc`: an arc-diagram skyline. Files sit on one baseline ordered by
  stage; forward imports arc above and backward ones dip below.
- `pipeline` (3D flow): the same stages as a rotatable 3D scene on a
  labeled engine bed, with particles running the imports.

Every mode draws two visually distinct flows on the same import edges.
Warm gold pulses are logic: calls running from importer to imported, the
direction the arrowheads on every edge point. Cool blue droplets are data:
results returning the opposite way, imported back to importer. The legend
explains both, and the bottom-left language legend shows each language's
share of total LOC as a percentage plus a thin stacked bar in language
colors.

The output loads nothing from the network and needs no build step, so it
works offline, as a Claude artifact, or anywhere a browser exists.

## Workflow

Two commands, run from anywhere (`SKILL_DIR` = this skill's directory):

```bash
python3 "$SKILL_DIR/scripts/analyze_codebase.py" /path/to/repo -o codebase.json
python3 "$SKILL_DIR/scripts/build_visualization.py" codebase.json -o codeflow.html --open
# optional: --view engine|orbit|circuit|arc|pipeline sets the starting mode (default engine)
```

1. Analyze. `analyze_codebase.py` walks the repo (skipping `.git`,
   `node_modules`, virtualenvs, build dirs, etc.), measures every
   recognized source file, and extracts import edges for Python, JS/TS,
   Go, Rust, Ruby, Java, and PHP. It prints a one-line summary; check it.
   If it reports 0 files or 0 edges, see Troubleshooting below before
   proceeding.
2. Build. `build_visualization.py` injects the JSON into
   `assets/viewer_template.html` and writes a standalone HTML file. Use
   `--open` in interactive/local sessions so the user sees it immediately;
   skip `--open` in headless environments and deliver the file instead
   (artifact, file send, or a path the user can open).
3. Ask or infer the mode if it matters. Default to the engine schematic;
   if the user wants something they can spin in 3D, build with
   `--view orbit` or `--view pipeline`. All modes ship in every output
   anyway; the flag only sets the opening view.
4. Narrate the machine. Deliver the file and explain what the pipeline
   shape says about their program: what's at the intake (the entrypoints,
   where execution starts), how many stages deep the flow runs, and what
   sits in the core (the most-depended-on modules, the highest-risk places
   to change). Mention the biggest buildings, any standalone files parked
   in the bypass row (no tracked imports: dead code candidates or glue
   invoked some other way), and where the water converges. Two or three
   concrete observations beat a feature tour.

Put intermediate files (`codebase.json`) in a scratch/temp directory; put
the final `.html` somewhere the user can keep it (their repo root or
wherever they asked), unless they say otherwise.

## What the viewer gives the user

- The `mode` menu switches between engine schematic, orbit, circuit, arc,
  and 3D flow, so the user picks how they want to see it; `--view` sets
  the default.
- Engine mode: labeled phases, folder-grouped blade rows, heat-gradient
  ribbons, gold entrypoint beacons, and standalone files in an `auxiliary`
  tray (dead-code candidates or files loaded outside the import system;
  say so).
- Orbit mode: folder clusters as tumbling solids. Drag to rotate to any
  angle, over the poles too; flick for momentum.
- Logic vs data: every edge carries gold logic pulses (calls, in the
  arrowhead direction) and blue data droplets (returns, the opposite way).
- Click any building to trace it: the rest dims, what it calls into
  lights cyan, what calls it lights orange, and a side panel lists both.
  The panel entries are clickable, so the user can walk the graph file by
  file.
- The `view: folder rivers` toggle (3D flow): per-file streams aggregate
  into thick folder-to-folder rivers, the architecture-level flow.
- Hover tooltips (path, LOC, language, depends-on/used-by counts), gold
  beacons on entrypoints, a language legend with per-language LOC
  percentages and a stacked share bar, auto-rotate, drag/scroll/touch
  camera, a "how to read this" overlay, and pause controls (space bar).

Mention the click-to-trace and the two toggles in one short line; the
on-screen "how to read this" overlay covers the rest.

## Options and scaling

- `--max-files N` (default 400): for very large repos the analyzer keeps
  the N largest files so the viewer stays smooth. Say so when it kicks in
  ("showing the 400 largest of 2,310 files"). For monorepos, a better
  picture often comes from pointing the analyzer at one package or
  service at a time.
- To visualize a subdirectory, pass that subdirectory as the root.
- The particle budget is capped in the viewer (~240 particles, heaviest
  edges first), so dense dependency graphs stay readable and fast
  automatically.

## Troubleshooting

- 0 files found: the repo's language may not be in the extension map, or
  everything lives in skipped directories. Open `analyze_codebase.py` and
  extend `LANG_BY_EXT` or adjust `SKIP_DIRS` for this run. It's a plain
  stdlib script; editing a local copy is expected usage.
- 0 or very few edges: import extraction is regex-based and best-effort.
  Some ecosystems (C/C++ headers, C#, Swift) have no patterns yet. The
  buildings still render, but the pipeline collapses to one stage and
  there's no water. Tell the user that, and offer to add a pattern for
  their language (add a regex to `IMPORT_PATTERNS` that captures the
  module string; resolution to in-repo files is automatic).
- Everything lands in one or two stages: normal for flat scripts or repos
  where most imports go through one `__init__`/`index` barrel. The orbit
  constellation and rivers view usually tell the story better there; say
  so.
- Blank page: open the browser console. The only moving part is the JSON
  injection; check the output HTML still contains `const DATA = {`.

## Design constraints (keep these if you modify the viewer)

The template is hand-rolled canvas 3D on purpose: zero network requests,
so the output is portable to sandboxed contexts (artifacts, air-gapped
machines). Don't swap in a CDN-loaded library. Keep everything in one
file. The first frame renders synchronously (not waiting for
requestAnimationFrame) so throttled or embedded contexts still show the
scene.
