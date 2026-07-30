#!/usr/bin/env python3
"""Validate the module catalog.

Checks every file listed in ``modules/index.json`` against the documented
format, plus a few invariants the app relies on:

* ids are unique and match their filename
* categories are declared in index.json
* pins sit inside the declared footprint
* shape primitives use known types and keys
* colours are parseable
* the rotation maths in src/core/geometry.js round-trips

Exit status is non-zero if there is at least one error. Warnings never fail the
run, so this is safe to wire into CI.

    python tools/validate_catalog.py
    python tools/validate_catalog.py --strict   # warnings fail too
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MODULES = ROOT / "modules"

HEX = re.compile(r"^#(?:[0-9a-fA-F]{3}|[0-9a-fA-F]{4}|[0-9a-fA-F]{6}|[0-9a-fA-F]{8})$")
ID_RE = re.compile(r"^[a-z0-9][a-z0-9._-]*$")

PIN_TYPES = {"power", "gnd", "io", "analog", "in", "out", "signal", "nc"}
SHAPE_TYPES = {"rect", "circle", "ellipse", "line", "polygon", "path", "text"}
SHAPE_KEYS = {
    "type", "x", "y", "w", "h", "rx", "ry", "cx", "cy", "r", "x1", "y1", "x2", "y2",
    "points", "d", "text", "size", "anchor", "weight", "rotate", "color", "fill",
    "stroke", "strokeWidth", "linecap", "opacity",
}
TOP_KEYS = {
    "$schema", "id", "name", "subtitle", "category", "tags", "datasheet",
    "designator", "footprint", "resize", "pins", "body", "shapes", "label",
}
BODY_KEYS = {"x", "y", "w", "h", "rx", "fill", "stroke", "strokeWidth", "opacity"}
LABEL_KEYS = {"text", "x", "y", "size", "color", "weight", "rotate", "anchor"}

REQUIRED_SHAPE_FIELDS = {
    "rect": ("x", "y", "w", "h"),
    "circle": ("cx", "cy", "r"),
    "ellipse": ("cx", "cy", "rx", "ry"),
    "line": ("x1", "y1", "x2", "y2"),
    "polygon": ("points",),
    "path": ("d",),
    "text": ("text",),
}


class Report:
    def __init__(self):
        self.errors: list[str] = []
        self.warnings: list[str] = []

    def error(self, where, msg):
        self.errors.append(f"{where}: {msg}")

    def warn(self, where, msg):
        self.warnings.append(f"{where}: {msg}")


# ---------------------------------------------------------------------------
# Rotation invariant
# ---------------------------------------------------------------------------


def rotate_point(x, y, cols, rows, rotation):
    """Mirror of `rotatePoint` in src/core/geometry.js."""
    r = rotation % 360
    if r == 90:
        return rows - 1 - y, x
    if r == 180:
        return cols - 1 - x, rows - 1 - y
    if r == 270:
        return y, cols - 1 - x
    return x, y


def apply_svg_transform(x, y, cols, rows, rotation, col, row):
    """What the browser computes from `moduleTransform` in geometry.js.

    The transform list is applied right-to-left: rotate, then translate.
    """
    r = rotation % 360
    if r == 90:
        rx, ry = -y, x
        tx, ty = col + rows - 1, row
    elif r == 180:
        rx, ry = -x, -y
        tx, ty = col + cols - 1, row + rows - 1
    elif r == 270:
        rx, ry = y, -x
        tx, ty = col, row + cols - 1
    else:
        rx, ry = x, y
        tx, ty = col, row
    return rx + tx, ry + ty


def check_rotation_maths(rep: Report):
    """The SVG transform and the point maths must agree, or pads drift off holes."""
    for cols in range(1, 7):
        for rows in range(1, 7):
            for rot in (0, 90, 180, 270):
                for col, row in ((0, 0), (3, 5)):
                    for x in range(cols):
                        for y in range(rows):
                            a = rotate_point(x, y, cols, rows, rot)
                            a = (a[0] + col, a[1] + row)
                            b = apply_svg_transform(x, y, cols, rows, rot, col, row)
                            if a != b:
                                rep.error(
                                    "geometry.js",
                                    f"rotation {rot}° disagrees for {cols}x{rows} "
                                    f"point ({x},{y}) at ({col},{row}): "
                                    f"rotatePoint={a} transform={b}",
                                )
                                return

    # Rotating four times must be the identity.
    for cols, rows in ((2, 5), (4, 4), (1, 7)):
        for x in range(cols):
            for y in range(rows):
                p = (x, y)
                c, r = cols, rows
                for _ in range(4):
                    p = rotate_point(p[0], p[1], c, r, 90)
                    c, r = r, c
                if p != (x, y):
                    rep.error("geometry.js",
                              f"four 90° rotations of ({x},{y}) in {cols}x{rows} gave {p}")
                    return


# ---------------------------------------------------------------------------
# Module checks
# ---------------------------------------------------------------------------


def check_color(rep, where, key, value):
    if value is None:
        return
    if not isinstance(value, str):
        rep.error(where, f"{key} must be a string, got {type(value).__name__}")
        return
    if value in ("none", "transparent", "currentColor"):
        return
    if not HEX.match(value):
        rep.warn(where, f"{key}={value!r} is not a hex colour")


def check_module(path: Path, data, categories, seen, rep: Report):
    where = path.relative_to(ROOT).as_posix()

    if not isinstance(data, dict):
        rep.error(where, "top level is not an object")
        return

    unknown = set(data) - TOP_KEYS
    if unknown:
        rep.error(where, f"unknown top-level keys: {sorted(unknown)}")

    mid = data.get("id")
    if not isinstance(mid, str) or not mid:
        rep.error(where, "missing 'id'")
        return
    if not ID_RE.match(mid):
        rep.error(where, f"id {mid!r} must match {ID_RE.pattern}")
    if mid != path.stem:
        rep.error(where, f"id {mid!r} does not match filename {path.stem!r}")
    if mid in seen:
        rep.error(where, f"duplicate id {mid!r} (also in {seen[mid]})")
    else:
        seen[mid] = where

    if not isinstance(data.get("name"), str) or not data["name"]:
        rep.error(where, "missing 'name'")

    cat = data.get("category")
    if cat not in categories:
        rep.error(where, f"category {cat!r} is not declared in index.json")
    elif path.parent.name != cat:
        rep.error(where, f"lives in {path.parent.name}/ but declares category {cat!r}")

    fp = data.get("footprint")
    if not isinstance(fp, dict):
        rep.error(where, "missing 'footprint'")
        return
    if set(fp) - {"cols", "rows"}:
        rep.error(where, f"footprint has unexpected keys: {sorted(set(fp) - {'cols', 'rows'})}")
    cols, rows = fp.get("cols"), fp.get("rows")
    for k, v in (("cols", cols), ("rows", rows)):
        if not isinstance(v, int) or isinstance(v, bool) or v < 1:
            rep.error(where, f"footprint.{k} must be a positive integer, got {v!r}")
            return

    # -- pins
    pins = data.get("pins", [])
    if not isinstance(pins, list):
        rep.error(where, "'pins' must be an array")
        pins = []
    numbers = {}
    for i, p in enumerate(pins):
        pw = f"{where} pin[{i}]"
        if not isinstance(p, dict):
            rep.error(pw, "not an object")
            continue
        unknown = set(p) - {"col", "row", "name", "number", "type"}
        if unknown:
            rep.error(pw, f"unknown keys: {sorted(unknown)}")
        col, row = p.get("col"), p.get("row")
        if not isinstance(col, int) or isinstance(col, bool) or col < 0:
            rep.error(pw, f"col must be a non-negative integer, got {col!r}")
        elif col >= cols:
            rep.error(pw, f"col {col} is outside footprint cols={cols}")
        if not isinstance(row, int) or isinstance(row, bool) or row < 0:
            rep.error(pw, f"row must be a non-negative integer, got {row!r}")
        elif row >= rows:
            rep.error(pw, f"row {row} is outside footprint rows={rows}")
        t = p.get("type")
        if t is not None and t not in PIN_TYPES:
            rep.error(pw, f"type {t!r} is not one of {sorted(PIN_TYPES)}")
        n = p.get("number")
        if n is not None:
            if n in numbers:
                rep.warn(pw, f"pin number {n!r} reused (also pin[{numbers[n]}])")
            numbers[n] = i

    occupied = {(p.get("col"), p.get("row")) for p in pins if isinstance(p, dict)}
    if len(occupied) != len([p for p in pins if isinstance(p, dict)]):
        rep.warn(where, "two or more pins share the same hole")

    # -- resize
    rs = data.get("resize")
    if rs is not None:
        if not isinstance(rs, dict) or set(rs) != {"axis", "min", "max"}:
            rep.error(where, "resize must be {axis, min, max}")
        else:
            if rs["axis"] not in ("cols", "rows"):
                rep.error(where, f"resize.axis {rs['axis']!r} must be 'cols' or 'rows'")
            elif not isinstance(rs["min"], int) or not isinstance(rs["max"], int):
                rep.error(where, "resize.min/max must be integers")
            elif rs["min"] > rs["max"]:
                rep.error(where, f"resize.min {rs['min']} > max {rs['max']}")
            else:
                base = fp[rs["axis"]]
                if not rs["min"] <= base <= rs["max"]:
                    rep.error(where, f"footprint.{rs['axis']}={base} is outside "
                                     f"resize range {rs['min']}..{rs['max']}")
                if base <= 1:
                    rep.error(where, f"resizable on '{rs['axis']}' needs a base span > 1 "
                                     f"to scale from, got {base}")

    # -- body
    body = data.get("body")
    if body is not None:
        if not isinstance(body, dict):
            rep.error(where, "'body' must be an object")
        else:
            unknown = set(body) - BODY_KEYS
            if unknown:
                rep.error(where, f"body has unknown keys: {sorted(unknown)}")
            check_color(rep, where, "body.fill", body.get("fill"))
            check_color(rep, where, "body.stroke", body.get("stroke"))
            for k in ("w", "h"):
                if k in body and (not isinstance(body[k], (int, float)) or body[k] < 0):
                    rep.error(where, f"body.{k} must be a non-negative number")

    # -- shapes
    shapes = data.get("shapes", [])
    if not isinstance(shapes, list):
        rep.error(where, "'shapes' must be an array")
        shapes = []
    for i, s in enumerate(shapes):
        sw = f"{where} shape[{i}]"
        if not isinstance(s, dict):
            rep.error(sw, "not an object")
            continue
        t = s.get("type")
        if t not in SHAPE_TYPES:
            rep.error(sw, f"type {t!r} is not one of {sorted(SHAPE_TYPES)}")
            continue
        unknown = set(s) - SHAPE_KEYS
        if unknown:
            rep.error(sw, f"unknown keys: {sorted(unknown)}")
        for req in REQUIRED_SHAPE_FIELDS[t]:
            if s.get(req) is None:
                rep.error(sw, f"{t} is missing required field '{req}'")
        check_color(rep, sw, "fill", s.get("fill"))
        check_color(rep, sw, "stroke", s.get("stroke"))
        check_color(rep, sw, "color", s.get("color"))
        if t == "polygon":
            pts = s.get("points")
            if not isinstance(pts, list) or not pts:
                rep.error(sw, "polygon.points must be a non-empty array")
            elif any(not (isinstance(p, list) and len(p) == 2
                          and all(isinstance(v, (int, float)) for v in p)) for p in pts):
                rep.error(sw, "polygon.points entries must be [x, y] number pairs")
        if t == "line" and s.get("stroke") is None:
            rep.warn(sw, "line has no stroke and will be invisible")
        if t == "text" and not isinstance(s.get("text"), str):
            rep.error(sw, "text.text must be a string")

    # -- label
    label = data.get("label")
    if label is not None:
        if not isinstance(label, dict):
            rep.error(where, "'label' must be an object")
        else:
            unknown = set(label) - LABEL_KEYS
            if unknown:
                rep.error(where, f"label has unknown keys: {sorted(unknown)}")
            if not isinstance(label.get("text"), str):
                rep.error(where, "label.text must be a string")
            check_color(rep, where, "label.color", label.get("color"))

    # -- soft quality checks
    if not data.get("subtitle"):
        rep.warn(where, "no 'subtitle' — the palette shows it as secondary text")
    if not data.get("tags"):
        rep.warn(where, "no 'tags' — the part will be harder to find by search")
    if not pins and not data.get("body") and not shapes:
        rep.warn(where, "no pins and no artwork; nothing will be visible")
    if data.get("$schema") != "../_schema/module.schema.json":
        rep.warn(where, "missing the '$schema' pointer (editors lose autocomplete)")


# ---------------------------------------------------------------------------
# Bundle
# ---------------------------------------------------------------------------


def check_bundle(listed, rep: Report):
    """modules/catalog.json is what the app actually loads, so it must match.

    A stale bundle is the one failure mode that would not show up anywhere else:
    the files on disk look right, but the browser serves yesterday's parts.
    """
    where = "modules/catalog.json"
    path = MODULES / "catalog.json"
    if not path.exists():
        rep.warn(where, "missing — the app will fall back to one fetch per module; "
                        "run 'python tools/generate_catalog.py'")
        return
    try:
        bundle = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as err:
        rep.error(where, f"invalid JSON: {err}")
        return

    defs = bundle.get("definitions")
    if not isinstance(defs, dict):
        rep.error(where, "'definitions' must be an object keyed by module path")
        return

    stale = "re-run 'python tools/generate_catalog.py' to rebuild it"
    for rel in sorted(set(listed) - set(defs)):
        rep.error(where, f"index.json lists {rel} but the bundle omits it — {stale}")
    for rel in sorted(set(defs) - set(listed)):
        rep.error(where, f"bundles {rel}, which index.json does not list — {stale}")

    for rel in sorted(set(listed) & set(defs)):
        try:
            on_disk = json.loads((MODULES / rel).read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue          # already reported by the per-file pass
        on_disk.pop("$schema", None)
        if defs[rel] != on_disk:
            rep.error(where, f"bundled copy of {rel} differs from the file — {stale}")

    if bundle.get("categories") != json.loads(
            (MODULES / "index.json").read_text(encoding="utf-8")).get("categories"):
        rep.error(where, f"categories differ from index.json — {stale}")


# ---------------------------------------------------------------------------


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--strict", action="store_true", help="treat warnings as failures")
    ap.add_argument("--quiet", action="store_true", help="only print the summary")
    args = ap.parse_args()

    rep = Report()
    check_rotation_maths(rep)

    index_path = MODULES / "index.json"
    if not index_path.exists():
        print(f"FATAL: {index_path} not found", file=sys.stderr)
        return 2
    index = json.loads(index_path.read_text(encoding="utf-8"))

    categories = {c["id"] for c in index.get("categories", []) if isinstance(c, dict) and "id" in c}
    if not categories:
        rep.error("modules/index.json", "no categories declared")

    listed = index.get("modules", [])
    if not isinstance(listed, list) or not listed:
        rep.error("modules/index.json", "'modules' must be a non-empty array")
        listed = []

    seen: dict[str, str] = {}
    for rel in listed:
        path = MODULES / rel
        if not path.exists():
            rep.error("modules/index.json", f"lists {rel} but the file does not exist")
            continue
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as err:
            rep.error(rel, f"invalid JSON: {err}")
            continue
        check_module(path, data, categories, seen, rep)

    # Files on disk that index.json forgot.
    on_disk = set()
    for cat in sorted(categories):
        d = MODULES / cat
        if d.is_dir():
            for f in d.glob("*.json"):
                on_disk.add(f"{cat}/{f.name}")
    missing = on_disk - set(listed)
    for rel in sorted(missing):
        rep.error("modules/index.json",
                  f"{rel} exists but is not listed — run "
                  f"'python tools/generate_catalog.py --index'")

    check_bundle(listed, rep)

    if not args.quiet:
        for e in rep.errors:
            print(f"ERROR   {e}")
        for w in rep.warnings:
            print(f"warning {w}")
        if rep.errors or rep.warnings:
            print()

    print(f"{len(listed)} modules checked in {len(categories)} categories: "
          f"{len(rep.errors)} error(s), {len(rep.warnings)} warning(s)")

    if rep.errors:
        return 1
    if args.strict and rep.warnings:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
