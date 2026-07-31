# The module format

Every part in the palette is one JSON file under `modules/<category>/<id>.json`.
There is no build step: add a file, list it in `modules/index.json`, reload the
page, and it is live.

A JSON Schema lives at [`modules/_schema/module.schema.json`](../modules/_schema/module.schema.json).
Keep the `$schema` pointer at the top of your file and VS Code will give you
autocomplete and inline validation while you type.

---

## Coordinate system

**All geometry is in hole units. One unit = one hole pitch (2.54 mm).**

The origin `(0, 0)` is the *anchor hole* — the hole under pin 1. The footprint
extends right (`+x`, columns) and down (`+y`, rows).

```
        col 0   col 1   col 2   col 3
        ┌───────────────────────────────►  +x
row 0   │ ●(0,0)  ●       ●       ●
row 1   │ ●       ●       ●       ●
row 2   │ ●       ●       ●       ●
        ▼
        +y
```

Artwork is free to spill outside the footprint — a TO-220's body sits well above
its three pins, and that is exactly right. Negative coordinates are fine.

Because everything is expressed in pitches, nothing needs to know about pixels
or zoom levels: the renderer frames the workspace with an SVG `viewBox`.

---

## Minimal example

The smallest useful file — two pins and a coloured plate:

```json
{
  "$schema": "../_schema/module.schema.json",
  "id": "my-widget",
  "name": "My Widget",
  "subtitle": "does a thing",
  "category": "misc",
  "tags": ["widget", "example"],
  "designator": "U",
  "footprint": { "cols": 2, "rows": 1 },
  "pins": [
    { "col": 0, "row": 0, "name": "IN",  "number": 1, "type": "in" },
    { "col": 1, "row": 0, "name": "GND", "number": 2, "type": "gnd" }
  ],
  "body": { "x": -0.4, "y": -0.4, "w": 1.8, "h": 0.8, "fill": "#2a3038", "stroke": "#4a525c" },
  "label": { "text": "W1", "size": 0.35 }
}
```

Drop that in `modules/misc/my-widget.json`, run
`python tools/generate_catalog.py --index`, reload, and search for "widget".

The `--index` step is not optional: it rewrites `modules/index.json` (the
manifest) **and** `modules/catalog.json` (the bundle the app actually loads).
Editing a part file without re-running it means the browser keeps serving the
previous version — `tools/validate_catalog.py` fails loudly when that happens.

---

## Top-level fields

| Field | Required | Notes |
|---|---|---|
| `id` | ✅ | Unique, stable, lowercase. **Must match the filename.** Saved designs reference it — never change it once published. |
| `name` | ✅ | Shown in the palette. |
| `category` | ✅ | Must be declared in `modules/index.json` and match the folder name. |
| `footprint` | ✅ | `{ "cols": n, "rows": n }` — the rectangle of holes occupied. |
| `subtitle` | | Secondary line in the palette, e.g. `"1/4 W axial"`. |
| `tags` | | Searched by the palette's search box. Be generous. |
| `designator` | | Reference prefix for auto-naming placed parts (`R`, `C`, `U`, `Q`, `D`, `J`, `SW`…). Defaults to `U`. |
| `datasheet` | | URL; shown as a link in the inspector. |
| `pins` | | Electrical pins. The renderer draws a copper pad for each automatically. |
| `body` | | Shorthand for the main outline, drawn first. |
| `shapes` | | Artwork, drawn in order on top of `body`. |
| `label` | | Text drawn last, on top. Defaults to centred on the footprint. |
| `resize` | | Makes the part stretchable — see the caveat below. |

If you give neither `body` nor `shapes`, the renderer draws a plain grey plate
over the footprint so the part is still visible and grabbable.

---

## Pins

```json
{ "col": 0, "row": 3, "name": "GPIO4", "number": 12, "type": "io" }
```

`col` and `row` must be inside the footprint — `tools/validate_catalog.py`
enforces this. `type` tints the pad and colours the pin-name overlay:

| `type` | Meaning | Pad tint |
|---|---|---|
| `power` | supply in/out | orange |
| `gnd` | ground / return | grey |
| `analog` | analogue signal | teal |
| `io` | bidirectional digital | copper |
| `in`, `out`, `signal` | directional / generic | copper |
| `nc` | not connected | dark |

Pins are what make a part *useful*: they drive the pinout table in the
inspector, the pin-name overlay (**P**), and the wire-end checks in the tests.
A part with no pins still renders, but it is decoration.

---

## Shape primitives

`shapes` is an ordered array. Later entries paint over earlier ones.

| `type` | Required fields | Optional |
|---|---|---|
| `rect` | `x`, `y`, `w`, `h` | `rx`, `ry` |
| `circle` | `cx`, `cy`, `r` | |
| `ellipse` | `cx`, `cy`, `rx`, `ry` | |
| `line` | `x1`, `y1`, `x2`, `y2` | `linecap` |
| `polygon` | `points`: `[[x,y], …]` | |
| `path` | `d` (SVG path data, in hole units) | |
| `text` | `text` | `x`, `y`, `size`, `color`, `anchor`, `rotate`, `weight` |

All shapes accept `fill`, `stroke`, `strokeWidth` (default `0.035`) and
`opacity`. Colours are hex strings, or `"none"`.

A few conventions that keep the catalog looking consistent:

```json
{ "type": "line",   "x1": 0, "y1": 0, "x2": 0.25, "y2": 0,
  "stroke": "#b9c0c8", "strokeWidth": 0.1, "linecap": "round" }   // a pin leg
{ "type": "circle", "cx": 0.53, "cy": 0, "r": 0.09, "fill": "#c9d2dc" }  // pin-1 dot
{ "type": "rect",   "x": 0.25, "y": -0.36, "w": 2.5, "h": 3.72,
  "rx": 0.1, "fill": "#1f242b", "stroke": "#0b0e12" }             // an IC body
```

### Why text is special

Text in `shapes` and in `label` is **not** drawn inside the geometry group. The
solder-side view mirrors the whole workspace horizontally so that wiring
underneath reads correctly — and mirrored text is unreadable. The renderer
therefore collects all text, computes its absolute position itself, and emits it
into a separate unmirrored layer.

The consequence for you as an author: text positions and rotations behave
exactly as you would expect, and you never need to think about the flip.

---

## Rotation

Placed parts rotate in 90° steps. You do not need to do anything — the renderer
transforms your artwork, and pin positions are transformed by the same maths.

The invariant that keeps pads sitting on real holes is verified two ways:
`tools/validate_catalog.py` re-implements the maths in Python and cross-checks
it, and `tools/integration.html` measures the actual rendered pad positions in a
browser against the expected hole centres, for every rotation and both sides.

---

## Resizable parts — read this before adding `resize`

```json
"resize": { "axis": "cols", "min": 3, "max": 12 }
```

`resize` means **stretch**: the artwork is scaled along the axis and pin
positions are scaled with it, proportionally.

That is the correct semantic for a two-lead axial part — a resistor's body and
leads should grow as you span more holes — and for plain plates.

It is the *wrong* semantic for anything whose pins repeat at a fixed pitch. A
1×4 pin header stretched to 8 holes should grow **four more pins**, not four
stretched ones. There is no declarative way to express repetition, so the
catalog ships headers as discrete sizes (`header-1x2-male` … `header-1x40-male`)
and does not mark them resizable.

Rule of thumb: only add `resize` if the part has exactly two pins at its
extremes, or no pins at all. The base `footprint` value on the resize axis must
be greater than 1 (there needs to be a span to scale from) and must fall inside
`min`…`max`. The validator checks both.

---

## Categories

Declared once in `modules/index.json`:

```json
{ "id": "sensor", "name": "Sensors", "color": "#73daca" }
```

The `color` tints the group header in the palette. A module's `category` must
match both a declared id and its parent folder name.

---

## Adding parts in bulk

For families — resistor values, LED colours, DIP packages — hand-authoring is
tedious and drifts out of style. `tools/catalog_lib.py` has factories for the
common packages:

```python
dip("ne555", "NE555", "Timer",
    ["GND", "TRIG", "OUT", "RST"],       # left column, top to bottom
    ["VCC", "DIS", "THR", "CTRL"],       # right column, top to bottom
    mark="555", tags=["timer", "oscillator"])

axial_resistor(4700)          # colour bands are computed from the value
to220("lm7805", "LM7805", "5 V linear regulator", ["IN", "GND", "OUT"])
breakout("bme280", "BME280", "pressure / temp / humidity",
         ["VCC", "GND", "SCL", "SDA"], cols=4, rows=5)
```

Add your entries to the relevant `build_*()` function in
`tools/generate_catalog.py` and run:

```bash
python tools/generate_catalog.py    # rewrite the families it owns
python tools/validate_catalog.py    # check everything
```

**The generator overwrites the files it owns.** If you hand-edit a generated
file, either move your change into the generator, or rename the module so the
generator no longer claims it.

---

## Checklist for a new part

- [ ] `id` matches the filename and is lowercase
- [ ] `category` matches the folder and is declared in `index.json`
- [ ] every pin is inside the footprint
- [ ] `subtitle` and `tags` filled in, so it can be found
- [ ] `designator` set (`R`, `C`, `U`…)
- [ ] registered and bundled (`python tools/generate_catalog.py --index`)
- [ ] `python tools/validate_catalog.py` is clean
- [ ] it looks right in the palette and on the workspace at all four rotations
