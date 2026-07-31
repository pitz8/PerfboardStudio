"""Building blocks for the Perfboard Studio module catalog.

Everything here emits plain dicts that serialise straight to the module JSON
format documented in ``modules/_schema/module.schema.json``.

Geometry convention
-------------------
All coordinates are in HOLE UNITS (1 unit = one hole pitch = 2.54 mm).
(0, 0) is the anchor hole, i.e. the hole under pin 1.
"""

from __future__ import annotations

import math

# ---------------------------------------------------------------------------
# Palette
# ---------------------------------------------------------------------------

COL = {
    # plastics / packages
    "ic_body": "#1f242b",
    "ic_edge": "#0b0e12",
    "ic_mark": "#c9d2dc",
    "plastic_black": "#23272e",
    "plastic_edge": "#0e1116",
    "plastic_white": "#e9edf1",
    # printed circuit boards
    "pcb_green": "#12503c",
    "pcb_green_edge": "#0a3527",
    "pcb_blue": "#123a63",
    "pcb_blue_edge": "#0a2440",
    "pcb_black": "#1a1d22",
    "pcb_purple": "#33204d",
    "pcb_red": "#6b1622",
    "silk": "#e8eef4",
    # metals
    "gold": "#c9a227",
    "tin": "#b9c0c8",
    "steel": "#9aa2ab",
    "copper": "#c4763a",
    "lead": "#a8b0b8",
    # passives
    "resistor_body": "#d8c49b",
    "resistor_edge": "#a8916a",
    "elec_can": "#1d3163",
    "elec_edge": "#101c3a",
    "elec_stripe": "#c3cad4",
    "ceramic_disc": "#4a7fbf",
    "mlcc": "#b98a5a",
    "film": "#2f4f8f",
    # misc
    "terminal_green": "#2c7a45",
    "terminal_blue": "#1f5fa8",
    "relay_blue": "#1c4f96",
    "buzzer": "#15181c",
    "crystal": "#b3bac2",
    "heatsink": "#8c949d",
    "display_glass": "#0a0d12",
    "led_lens": "#cfd6de",
}

# Resistor colour-code bands, index == digit.
BAND = [
    "#14171a",  # 0 black
    "#6b4a2b",  # 1 brown
    "#cf2b28",  # 2 red
    "#e07b27",  # 3 orange
    "#e8c72c",  # 4 yellow
    "#2f8f4e",  # 5 green
    "#2b62c4",  # 6 blue
    "#7b4bb5",  # 7 violet
    "#8d949c",  # 8 grey
    "#f2f4f6",  # 9 white
]
BAND_GOLD = "#c9a227"
BAND_SILVER = "#c0c4c9"


# ---------------------------------------------------------------------------
# Shape helpers
# ---------------------------------------------------------------------------


def rect(x, y, w, h, fill, stroke=None, rx=None, sw=0.035, opacity=None):
    s = {"type": "rect", "x": r4(x), "y": r4(y), "w": r4(w), "h": r4(h), "fill": fill}
    if rx is not None:
        s["rx"] = r4(rx)
    if stroke:
        s["stroke"] = stroke
        s["strokeWidth"] = sw
    if opacity is not None:
        s["opacity"] = opacity
    return s


def circle(cx, cy, r, fill, stroke=None, sw=0.035, opacity=None):
    s = {"type": "circle", "cx": r4(cx), "cy": r4(cy), "r": r4(r), "fill": fill}
    if stroke:
        s["stroke"] = stroke
        s["strokeWidth"] = sw
    if opacity is not None:
        s["opacity"] = opacity
    return s


def ellipse(cx, cy, rx, ry, fill, stroke=None, sw=0.035):
    s = {"type": "ellipse", "cx": r4(cx), "cy": r4(cy), "rx": r4(rx), "ry": r4(ry), "fill": fill}
    if stroke:
        s["stroke"] = stroke
        s["strokeWidth"] = sw
    return s


def line(x1, y1, x2, y2, stroke, sw=0.12, linecap="round"):
    return {
        "type": "line",
        "x1": r4(x1),
        "y1": r4(y1),
        "x2": r4(x2),
        "y2": r4(y2),
        "stroke": stroke,
        "strokeWidth": r4(sw),
        "linecap": linecap,
    }


def polygon(points, fill, stroke=None, sw=0.035):
    s = {"type": "polygon", "points": [[r4(a), r4(b)] for a, b in points], "fill": fill}
    if stroke:
        s["stroke"] = stroke
        s["strokeWidth"] = sw
    return s


def path(d, fill=None, stroke=None, sw=0.035):
    s = {"type": "path", "d": d}
    if fill:
        s["fill"] = fill
    if stroke:
        s["stroke"] = stroke
        s["strokeWidth"] = sw
    return s


def text(x, y, txt, size=0.34, color=COL["silk"], anchor="middle", rotate=0, weight=600):
    s = {
        "type": "text",
        "x": r4(x),
        "y": r4(y),
        "text": txt,
        "size": r4(size),
        "color": color,
        "anchor": anchor,
        "weight": weight,
    }
    if rotate:
        s["rotate"] = rotate
    return s


def r4(v):
    """Round to 4 decimals and normalise -0.0 / integral floats."""
    if isinstance(v, bool) or not isinstance(v, (int, float)):
        return v
    v = round(float(v) + 0.0, 4)
    return int(v) if v == int(v) else v


# ---------------------------------------------------------------------------
# Pin helpers
# ---------------------------------------------------------------------------


def pin(col, row, name=None, number=None, ptype=None):
    p = {"col": col, "row": row}
    if name is not None:
        p["name"] = name
    if number is not None:
        p["number"] = number
    if ptype is not None:
        p["type"] = ptype
    return p


def guess_pin_type(name):
    """Classify a pin from its label so pads get sensible tinting."""
    if not name:
        return "signal"
    n = name.strip().upper()
    if n in ("GND", "G", "VSS", "0V", "AGND", "DGND", "-", "GND1", "GND2", "K", "CATHODE"):
        return "gnd"
    if n in ("NC", "N/C", "-NC-"):
        return "nc"
    if n.startswith(("3V", "5V", "VCC", "VDD", "VIN", "VBUS", "VBAT", "V+", "VM", "VMOT", "VS")):
        return "power"
    if n in ("+", "VOUT", "OUT+", "ANODE", "A"):
        return "power"
    if n.startswith(("GPIO", "IO", "D", "P")) and any(c.isdigit() for c in n):
        return "io"
    if n.startswith("A") and any(c.isdigit() for c in n):
        return "analog"
    if n in ("SDA", "SCL", "MISO", "MOSI", "SCK", "SCLK", "CS", "CE", "TX", "RX", "DC", "RST", "RES", "EN", "CLK", "DIO", "DIN", "DOUT", "CSN", "IRQ", "INT", "SIG", "S", "DATA"):
        return "signal"
    return "signal"


def row_pins(names, col=0, start_row=0, numbers_from=None):
    """Vertical strip of pins going down a single column."""
    out = []
    for i, nm in enumerate(names):
        num = None if numbers_from is None else numbers_from + i
        out.append(pin(col, start_row + i, nm, num, guess_pin_type(nm)))
    return out


def col_pins(names, row=0, start_col=0, numbers_from=None):
    """Horizontal strip of pins going across a single row."""
    out = []
    for i, nm in enumerate(names):
        num = None if numbers_from is None else numbers_from + i
        out.append(pin(start_col + i, row, nm, num, guess_pin_type(nm)))
    return out


# ---------------------------------------------------------------------------
# Package factories
# ---------------------------------------------------------------------------


def dip(mid, name, subtitle, left_names, right_names, *, wide=False, category="ic",
        tags=None, datasheet=None, mark=None, designator="U"):
    """Through-hole DIP package.

    Pin 1 is top-left, numbering runs down the left side then up the right side
    (the physical convention).  ``left_names`` is read top-to-bottom;
    ``right_names`` is also given top-to-bottom for authoring convenience.
    """
    rows = max(len(left_names), len(right_names))
    span = 6 if wide else 3          # 0.6" or 0.3" between the two pin rows
    cols = span + 1
    n = rows * 2

    pins = []
    for i, nm in enumerate(left_names):
        pins.append(pin(0, i, nm, i + 1, guess_pin_type(nm)))
    for i, nm in enumerate(right_names):
        # right column is numbered bottom-to-top
        pins.append(pin(span, i, nm, n - i, guess_pin_type(nm)))

    body_w = span - 0.55 if wide else span - 0.5
    body_x = (span - body_w) / 2
    body_y = -0.36
    body_h = (rows - 1) + 0.72

    shapes = []
    # pin legs
    for i in range(rows):
        shapes.append(line(0, i, body_x, i, COL["tin"], 0.1))
        shapes.append(line(span, i, body_x + body_w, i, COL["tin"], 0.1))
    # pin-1 notch (top edge) and pin-1 dot
    shapes.append(circle(body_x + body_w / 2, body_y + 0.02, 0.19, COL["ic_edge"]))
    shapes.append(circle(body_x + 0.28, 0.0, 0.09, COL["ic_mark"]))

    return {
        "id": mid,
        "name": name,
        "subtitle": subtitle,
        "category": category,
        "tags": (tags or []) + [f"dip-{n}", "through-hole"],
        "designator": designator,
        **({"datasheet": datasheet} if datasheet else {}),
        "footprint": {"cols": cols, "rows": rows},
        "pins": pins,
        "body": {
            "x": r4(body_x),
            "y": r4(body_y),
            "w": r4(body_w),
            "h": r4(body_h),
            "rx": 0.1,
            "fill": COL["ic_body"],
            "stroke": COL["ic_edge"],
        },
        "shapes": shapes,
        "label": {
            "text": mark or name,
            "x": r4(span / 2),
            "y": r4((rows - 1) / 2),
            "size": 0.42,
            "color": COL["ic_mark"],
            "rotate": 90,
        },
    }


def devboard(mid, name, subtitle, left_names, right_names, *, span, category="mcu",
             tags=None, datasheet=None, pcb=None, pcb_edge=None, mark=None,
             usb="top", designator="U", extra_shapes=None):
    """Two-row breakout / dev board with headers ``span`` holes apart."""
    rows = max(len(left_names), len(right_names))
    cols = span + 1
    pcb = pcb or COL["pcb_black"]
    pcb_edge = pcb_edge or COL["ic_edge"]

    pins = []
    for i, nm in enumerate(left_names):
        if nm:
            pins.append(pin(0, i, nm, None, guess_pin_type(nm)))
    for i, nm in enumerate(right_names):
        if nm:
            pins.append(pin(span, i, nm, None, guess_pin_type(nm)))

    pad = 0.45
    bx, by = -pad, -pad
    bw, bh = span + 2 * pad, (rows - 1) + 2 * pad

    shapes = []
    # header strips behind the pins
    shapes.append(rect(-0.32, -0.32, 0.64, (rows - 1) + 0.64, COL["plastic_black"],
                       COL["ic_edge"], rx=0.08))
    shapes.append(rect(span - 0.32, -0.32, 0.64, (rows - 1) + 0.64, COL["plastic_black"],
                       COL["ic_edge"], rx=0.08))
    # shield can / MCU block in the middle
    inner_w = max(0.9, span - 1.6)
    shapes.append(rect(span / 2 - inner_w / 2, 0.5, inner_w, max(1.2, bh * 0.38),
                       COL["steel"], "#6f767e", rx=0.1))
    # USB connector
    if usb == "top":
        shapes.append(rect(span / 2 - 0.42, by - 0.34, 0.84, 0.44, COL["tin"], "#7f868e", rx=0.07))
    elif usb == "bottom":
        shapes.append(rect(span / 2 - 0.42, by + bh - 0.1, 0.84, 0.44, COL["tin"], "#7f868e", rx=0.07))
    # pin-1 marker
    shapes.append(circle(-0.02, -0.02, 0.1, "#e8c72c"))
    if extra_shapes:
        shapes.extend(extra_shapes)

    return {
        "id": mid,
        "name": name,
        "subtitle": subtitle,
        "category": category,
        "tags": (tags or []) + ["board"],
        "designator": designator,
        **({"datasheet": datasheet} if datasheet else {}),
        "footprint": {"cols": cols, "rows": rows},
        "pins": pins,
        "body": {"x": r4(bx), "y": r4(by), "w": r4(bw), "h": r4(bh), "rx": 0.18,
                 "fill": pcb, "stroke": pcb_edge},
        "shapes": shapes,
        "label": {
            "text": mark or name,
            "x": r4(span / 2),
            "y": r4(bh * 0.78 - pad),
            "size": 0.36,
            "color": COL["silk"],
        },
    }


def breakout(mid, name, subtitle, names, *, cols=None, rows=None, category="sensor",
             tags=None, datasheet=None, pcb=None, pcb_edge=None, mark=None,
             designator="U", horizontal=True, extra_shapes=None, label_size=0.34):
    """Single-row breakout board (the classic 4-pin I2C module and friends)."""
    n = len(names)
    pcb = pcb or COL["pcb_blue"]
    pcb_edge = pcb_edge or COL["pcb_blue_edge"]

    if horizontal:
        w_holes = cols or n
        h_holes = rows or 3
        pins = col_pins(names, row=0, start_col=0)
        bx, by = -0.45, -0.45
        bw, bh = (w_holes - 1) + 0.9, (h_holes - 1) + 0.9
        hdr = rect(-0.32, -0.32, (n - 1) + 0.64, 0.64, COL["plastic_black"], COL["ic_edge"], rx=0.08)
        chip_w, chip_h = max(0.8, bw * 0.4), max(0.6, bh * 0.34)
        chip = rect(bx + bw / 2 - chip_w / 2, by + bh * 0.5, chip_w, chip_h,
                    COL["ic_body"], COL["ic_edge"], rx=0.08)
        lbl = {"x": r4(bx + bw / 2), "y": r4(by + bh - 0.3)}
    else:
        w_holes = cols or 3
        h_holes = rows or n
        pins = row_pins(names, col=0, start_row=0)
        bx, by = -0.45, -0.45
        bw, bh = (w_holes - 1) + 0.9, (h_holes - 1) + 0.9
        hdr = rect(-0.32, -0.32, 0.64, (n - 1) + 0.64, COL["plastic_black"], COL["ic_edge"], rx=0.08)
        chip_w, chip_h = max(0.8, bw * 0.42), max(0.6, bh * 0.34)
        chip = rect(bx + bw * 0.55, by + bh / 2 - chip_h / 2, chip_w, chip_h,
                    COL["ic_body"], COL["ic_edge"], rx=0.08)
        lbl = {"x": r4(bx + bw * 0.62), "y": r4(by + bh * 0.2)}

    shapes = [hdr, chip, circle(-0.02, -0.02, 0.1, "#e8c72c")]
    if extra_shapes:
        shapes.extend(extra_shapes)

    return {
        "id": mid,
        "name": name,
        "subtitle": subtitle,
        "category": category,
        "tags": (tags or []) + ["module"],
        "designator": designator,
        **({"datasheet": datasheet} if datasheet else {}),
        "footprint": {"cols": w_holes, "rows": h_holes},
        "pins": pins,
        "body": {"x": r4(bx), "y": r4(by), "w": r4(bw), "h": r4(bh), "rx": 0.16,
                 "fill": pcb, "stroke": pcb_edge},
        "shapes": shapes,
        "label": {"text": mark or name, "size": label_size, "color": COL["silk"], **lbl},
    }


# ---------------------------------------------------------------------------
# Passive factories
# ---------------------------------------------------------------------------


def resistor_bands(ohms):
    """4-band colour code (2 significant digits + multiplier + 5% tolerance)."""
    exp = math.floor(math.log10(ohms)) - 1
    sig = int(round(ohms / (10.0 ** exp)))
    if sig >= 100:            # rounding pushed us up a decade
        sig //= 10
        exp += 1
    d1, d2 = divmod(sig, 10)
    if exp == -1:
        mult = BAND_GOLD
    elif exp == -2:
        mult = BAND_SILVER
    else:
        mult = BAND[exp]
    return [BAND[d1], BAND[d2], mult, BAND_GOLD]


def fmt_ohms(ohms):
    for div, suf in ((1e6, "M"), (1e3, "k"), (1, "")):
        if ohms >= div:
            v = ohms / div
            s = f"{v:.10g}"
            return f"{s}{suf}Ω"
    return f"{ohms:.10g}Ω"


def fmt_ohms_ascii(ohms):
    for div, suf in ((1e6, "M"), (1e3, "k"), (1, "R")):
        if ohms >= div:
            v = ohms / div
            s = f"{v:.10g}".replace(".", "-")
            return f"{s}{suf}" if suf != "R" else f"{s}R"
    return f"{ohms:.10g}R"


def axial_resistor(ohms, span=4, watt="1/4 W"):
    """Horizontal axial resistor with a generated colour code."""
    label = fmt_ohms(ohms)
    mid = f"resistor-{fmt_ohms_ascii(ohms).lower()}"
    lead_len = 0.75
    bx = lead_len
    bw = (span - 1) - 2 * lead_len
    bh = 0.52
    by = -bh / 2

    shapes = [
        line(0, 0, bx + 0.04, 0, COL["lead"], 0.1),
        line((span - 1) - bx - 0.04, 0, span - 1, 0, COL["lead"], 0.1),
        rect(bx, by, bw, bh, COL["resistor_body"], COL["resistor_edge"], rx=0.16),
    ]
    bands = resistor_bands(ohms)
    bw_band = 0.11
    gap = 0.075
    total = len(bands) * bw_band + (len(bands) - 1) * gap
    start = bx + 0.16
    for i, c in enumerate(bands[:3]):
        shapes.append(rect(start + i * (bw_band + gap), by + 0.02, bw_band, bh - 0.04, c))
    shapes.append(rect(bx + bw - 0.16 - bw_band, by + 0.02, bw_band, bh - 0.04, bands[3]))

    return {
        "id": mid,
        "name": f"Resistor {label}",
        "subtitle": f"{watt} axial",
        "category": "passive",
        "tags": ["resistor", "axial", label.replace("Ω", "ohm"), watt],
        "designator": "R",
        "footprint": {"cols": span, "rows": 1},
        "resize": {"axis": "cols", "min": 3, "max": 12},
        "pins": [pin(0, 0, "1", 1, "signal"), pin(span - 1, 0, "2", 2, "signal")],
        "shapes": shapes,
        "label": {"text": label, "x": r4((span - 1) / 2), "y": -0.55, "size": 0.3,
                  "color": "#9fb0c0"},
    }


def electrolytic(uf, volts, diameter_holes=2, span=2):
    """Radial electrolytic capacitor, drawn from above."""
    mid = f"cap-elec-{_cap_slug(uf)}-{volts}v"
    label = _cap_label(uf)
    r = diameter_holes / 2.0
    cx = (span - 1) / 2.0
    shapes = [
        circle(cx, 0, r, COL["elec_can"], COL["elec_edge"], sw=0.05),
        # negative stripe on the pin-2 side
        path(f"M {r4(cx)} {r4(-r)} A {r4(r)} {r4(r)} 0 0 1 {r4(cx)} {r4(r)} Z",
             fill=COL["elec_stripe"]),
        circle(cx, 0, r * 0.62, COL["elec_can"], COL["elec_edge"], sw=0.03),
        line(cx - r * 0.42, 0, cx + r * 0.42, 0, COL["elec_edge"], 0.06),
        text(cx - r * 0.42, -r * 0.34, "−", size=0.34, color=COL["elec_can"], anchor="middle"),
    ]
    return {
        "id": mid,
        "name": f"Cap {label} {volts} V",
        "subtitle": "electrolytic, radial",
        "category": "passive",
        "tags": ["capacitor", "electrolytic", "polarised", label],
        "designator": "C",
        "footprint": {"cols": span, "rows": 1},
        "pins": [pin(0, 0, "+", 1, "power"), pin(span - 1, 0, "-", 2, "gnd")],
        "shapes": shapes,
        "label": {"text": label, "x": r4(cx), "y": r4(r + 0.36), "size": 0.3,
                  "color": "#9fb0c0"},
    }


def ceramic_cap(value, span=1, kind="disc"):
    mid = f"cap-{'cer' if kind == 'disc' else 'mlcc'}-{_cap_slug(value)}"
    label = _cap_label(value)
    code = _cap_code(value)
    cx = (span - 1) / 2.0
    if kind == "disc":
        shapes = [
            line(0, 0, cx, -0.1, COL["lead"], 0.09),
            line(span - 1, 0, cx, -0.1, COL["lead"], 0.09),
            circle(cx, -0.36, 0.44, COL["ceramic_disc"], "#2f5c92", sw=0.04),
            text(cx, -0.36, code, size=0.26, color="#dce6f2"),
        ]
        sub = "ceramic disc"
    else:
        shapes = [
            line(0, 0, cx, -0.1, COL["lead"], 0.09),
            line(span - 1, 0, cx, -0.1, COL["lead"], 0.09),
            rect(cx - 0.34, -0.72, 0.68, 0.62, COL["mlcc"], "#8b6540", rx=0.1),
            text(cx, -0.41, code, size=0.24, color="#3a2a18"),
        ]
        sub = "multilayer ceramic"
    return {
        "id": mid,
        "name": f"Cap {label}",
        "subtitle": sub,
        "category": "passive",
        "tags": ["capacitor", "ceramic", "non-polarised", label, code],
        "designator": "C",
        "footprint": {"cols": max(span, 2), "rows": 1},
        "pins": [pin(0, 0, "1", 1, "signal"), pin(max(span, 2) - 1, 0, "2", 2, "signal")],
        "shapes": shapes,
        "label": {"text": label, "x": r4(cx), "y": 0.44, "size": 0.28, "color": "#9fb0c0"},
    }


def _cap_label(uf):
    """0.1 -> '100nF', 1000 -> '1000uF'."""
    if uf < 0.001:
        return f"{_g(uf * 1e6)}pF"
    if uf < 1:
        return f"{_g(uf * 1000)}nF"
    return f"{_g(uf)}µF"


def _cap_slug(uf):
    return _cap_label(uf).replace("µ", "u").replace(".", "-").lower()


def _cap_code(uf):
    """EIA 3-digit code, e.g. 100 nF -> 104."""
    pf = uf * 1e6
    if pf < 100:
        return _g(pf)
    exp = 0
    while pf >= 100:
        pf /= 10.0
        exp += 1
    return f"{int(round(pf))}{exp}"


def _g(v):
    return f"{v:.10g}"


def led(color_name, hexcol, size_mm=5, span=2):
    r = 0.52 if size_mm == 5 else 0.36
    cx = (span - 1) / 2.0
    mid = f"led-{size_mm}mm-{color_name.lower()}"
    shapes = [
        line(0, 0, cx, 0, COL["lead"], 0.1),
        line(span - 1, 0, cx, 0, COL["lead"], 0.1),
        circle(cx, 0, r, hexcol, _darken(hexcol), sw=0.05),
        circle(cx, 0, r * 0.6, _lighten(hexcol), None),
        circle(cx - r * 0.28, -r * 0.28, r * 0.2, "#ffffff", None, opacity=0.75),
        # flat side marks the cathode (pin 2)
        line(cx + r * 0.86, -r * 0.5, cx + r * 0.86, r * 0.5, _darken(hexcol), 0.09, "butt"),
    ]
    return {
        "id": mid,
        "name": f"LED {size_mm} mm {color_name}",
        "subtitle": "through-hole indicator",
        "category": "discrete",
        "tags": ["led", "diode", color_name.lower(), f"{size_mm}mm"],
        "designator": "D",
        "footprint": {"cols": span, "rows": 1},
        "pins": [pin(0, 0, "A", 1, "power"), pin(span - 1, 0, "K", 2, "gnd")],
        "shapes": shapes,
        "label": {"text": color_name, "x": r4(cx), "y": r4(r + 0.34), "size": 0.26,
                  "color": "#9fb0c0"},
    }


def battery_cell(mid, name, subtitle, *, volts, span=4, diam=0.9, wrap=None,
                  edge=None, cap_color="#c9ced6", tags=None, category="misc",
                  designator="BT"):
    """Loose cylindrical cell (AA, AAA, C, D, 18650, 14500...), side view.

    Drawn with flying leads rather than a holder's spring contacts, since a bare
    cell is soldered or clipped directly. Pin 1 is the flat negative end, pin 2
    the button-topped positive end — same convention as a real cell.
    """
    wrap = wrap or COL["pcb_black"]
    edge = edge or _darken(wrap)
    lead_len = 0.7
    r = diam / 2
    bx = lead_len
    bw = (span - 1) - 2 * lead_len
    by = -r
    cap_w = min(0.22, bw * 0.18)
    return {
        "id": mid,
        "name": name,
        "subtitle": subtitle,
        "category": category,
        "tags": (tags or []) + ["battery", "cell"],
        "designator": designator,
        "footprint": {"cols": span, "rows": 1},
        "pins": [pin(0, 0, "-", 1, "gnd"), pin(span - 1, 0, "+", 2, "power")],
        "shapes": [
            line(0, 0, bx + 0.02, 0, "#1b1f25", 0.09),
            line(span - 1, 0, (span - 1) - bx - 0.02, 0, "#d84040", 0.09),
            rect(bx, by, bw, diam, wrap, edge, rx=r * 0.9),
            rect(bx, by, cap_w, diam, "#8d949c", edge, rx=0.05),
            rect((span - 1) - bx - cap_w, by, cap_w, diam, cap_color, edge, rx=0.05),
        ],
        "label": {"text": f"{volts} V", "x": r4((span - 1) / 2), "y": r4(-r - 0.28),
                  "size": 0.28, "color": "#9fb0c0"},
    }


def axial_diode(mid, name, subtitle, band_color="#d8d8d8", body="#2a2f36", span=3, tags=None):
    lead_len = 0.62
    bx = lead_len
    bw = (span - 1) - 2 * lead_len
    bh = 0.42
    by = -bh / 2
    return {
        "id": mid,
        "name": name,
        "subtitle": subtitle,
        "category": "discrete",
        "tags": (tags or []) + ["diode", "axial"],
        "designator": "D",
        "footprint": {"cols": span, "rows": 1},
        "resize": {"axis": "cols", "min": 2, "max": 8},
        "pins": [pin(0, 0, "A", 1, "power"), pin(span - 1, 0, "K", 2, "gnd")],
        "shapes": [
            line(0, 0, bx + 0.04, 0, COL["lead"], 0.1),
            line((span - 1) - bx - 0.04, 0, span - 1, 0, COL["lead"], 0.1),
            rect(bx, by, bw, bh, body, _darken(body), rx=0.08),
            rect(bx + bw - 0.22, by + 0.02, 0.12, bh - 0.04, band_color),
        ],
        "label": {"text": name.split()[0], "x": r4((span - 1) / 2), "y": -0.5, "size": 0.26,
                  "color": "#9fb0c0"},
    }


def to92(mid, name, subtitle, pin_names, *, category="discrete", tags=None,
         datasheet=None, designator="Q", mark=None):
    """TO-92: three pins on 0.1" centres, D-shaped body."""
    return {
        "id": mid,
        "name": name,
        "subtitle": subtitle,
        "category": category,
        "tags": (tags or []) + ["to-92", "through-hole"],
        "designator": designator,
        **({"datasheet": datasheet} if datasheet else {}),
        "footprint": {"cols": 3, "rows": 1},
        "pins": col_pins(pin_names, row=0, start_col=0, numbers_from=1),
        "shapes": [
            line(0, 0, 0, -0.35, COL["tin"], 0.1),
            line(1, 0, 1, -0.35, COL["tin"], 0.1),
            line(2, 0, 2, -0.35, COL["tin"], 0.1),
            path("M -0.02 -0.4 A 1.02 1.02 0 0 1 2.02 -0.4 L 2.02 -0.62 "
                 "A 1.02 1.02 0 0 0 -0.02 -0.62 Z", fill=COL["plastic_black"],
                 stroke=COL["plastic_edge"], sw=0.04),
            path("M -0.02 -0.4 A 1.02 1.02 0 0 1 2.02 -0.4 Z",
                 fill=COL["plastic_black"], stroke=COL["plastic_edge"], sw=0.04),
            text(1, -0.72, mark or name, size=0.3, color=COL["ic_mark"]),
        ],
    }


def to220(mid, name, subtitle, pin_names, *, category="power", tags=None,
          datasheet=None, designator="U", mark=None):
    """TO-220 standing upright: three pins on 0.1" centres plus the metal tab."""
    return {
        "id": mid,
        "name": name,
        "subtitle": subtitle,
        "category": category,
        "tags": (tags or []) + ["to-220", "through-hole"],
        "designator": designator,
        **({"datasheet": datasheet} if datasheet else {}),
        "footprint": {"cols": 3, "rows": 1},
        "pins": col_pins(pin_names, row=0, start_col=0, numbers_from=1),
        "shapes": [
            line(0, 0, 0, -0.4, COL["tin"], 0.11),
            line(1, 0, 1, -0.4, COL["tin"], 0.11),
            line(2, 0, 2, -0.4, COL["tin"], 0.11),
            rect(-0.5, -1.62, 3.0, 1.22, COL["plastic_black"], COL["plastic_edge"], rx=0.08),
            rect(-0.5, -1.98, 3.0, 0.4, COL["heatsink"], "#6b737b", rx=0.06),
            circle(1.0, -1.78, 0.14, "#4c5359"),
            text(1.0, -1.02, mark or name, size=0.32, color=COL["ic_mark"]),
        ],
    }


def header(n, *, female=False, rows=1):
    kind = "female" if female else "male"
    mid = f"header-{rows}x{n}-{kind}"
    pins = []
    shapes = []
    if rows == 1:
        cols_, rows_ = 1, n
        shapes.append(rect(-0.36, -0.36, 0.72, (n - 1) + 0.72,
                           COL["plastic_black"], COL["plastic_edge"], rx=0.08))
        for i in range(n):
            pins.append(pin(0, i, str(i + 1), i + 1, "signal"))
            if female:
                shapes.append(rect(-0.2, i - 0.2, 0.4, 0.4, "#0c0f13", COL["gold"], sw=0.05))
            else:
                shapes.append(rect(-0.12, i - 0.12, 0.24, 0.24, COL["gold"]))
    else:
        cols_, rows_ = 2, n
        shapes.append(rect(-0.36, -0.36, 1.72, (n - 1) + 0.72,
                           COL["plastic_black"], COL["plastic_edge"], rx=0.08))
        num = 1
        for i in range(n):
            for c in (0, 1):
                pins.append(pin(c, i, str(num), num, "signal"))
                num += 1
                if female:
                    shapes.append(rect(c - 0.2, i - 0.2, 0.4, 0.4, "#0c0f13", COL["gold"], sw=0.05))
                else:
                    shapes.append(rect(c - 0.12, i - 0.12, 0.24, 0.24, COL["gold"]))
    return {
        "id": mid,
        "name": f"Header {rows}×{n} {kind}",
        "subtitle": "2.54 mm pin header",
        "category": "connector",
        "tags": ["header", "connector", kind, f"{rows}x{n}"],
        "designator": "J",
        # No `resize`: a header must gain pins rather than stretch, so the
        # catalogue ships discrete sizes instead.
        "footprint": {"cols": cols_, "rows": rows_},
        "pins": pins,
        "shapes": shapes,
    }


def ic_socket(n, *, wide=False):
    """DIP socket: `n` contacts in two rows, numbered like the IC it holds.

    Same geometry as `dip` so a socket and its chip drop onto the same holes.
    """
    rows = n // 2
    span = 6 if wide else 3
    pins = []
    shapes = [
        rect(-0.42, -0.42, span + 0.84, (rows - 1) + 0.84,
             COL["plastic_black"], COL["plastic_edge"], rx=0.08),
        # open channel down the middle, where the chip body sits
        rect(0.3, -0.24, span - 0.6, (rows - 1) + 0.48, "#0c0f13", None, rx=0.06),
    ]
    for i in range(rows):
        pins.append(pin(0, i, str(i + 1), i + 1, "signal"))
        pins.append(pin(span, i, str(n - i), n - i, "signal"))
        shapes.append(rect(-0.19, i - 0.19, 0.38, 0.38, "#14171a", COL["gold"], sw=0.05))
        shapes.append(rect(span - 0.19, i - 0.19, 0.38, 0.38, "#14171a", COL["gold"], sw=0.05))
    # pin-1 end notch
    shapes.append(circle(span / 2, -0.42, 0.2, "#3a4048"))
    return {
        "id": f"ic-socket-{n}",
        "name": f"IC socket DIP-{n}",
        "subtitle": f"{'0.6' if wide else '0.3'} in, {n} contacts",
        "category": "connector",
        "tags": ["socket", "dip", f"dip-{n}", "ic", "through-hole"],
        "designator": "XU",
        "footprint": {"cols": span + 1, "rows": rows},
        "pins": pins,
        "shapes": shapes,
    }


def squares_path(cells, half):
    """One path holding a small square at each (x, y) — cheap bulk hole artwork.

    A solderless breadboard has hundreds of holes. Emitting a shape per hole
    would dwarf every other file in the catalogue, so they collapse into a
    single path with one subpath per hole.
    """
    s = r4(half * 2)
    parts = []
    for x, y in cells:
        parts.append(f"M{r4(x - half)} {r4(y - half)}h{s}v{s}h{-s}z")
    return "".join(parts)


def breadboard(mid, name, subtitle, *, strips, rails=True, tags=None):
    """Solderless breadboard, drawn from above.

    Deliberately has NO pins: a breadboard is not soldered to anything, it is a
    surface you push parts into. Modelling it as artwork keeps the file small
    and stops it claiming holes that belong to whatever is plugged into it.

    Vertical layout, in hole units (matching a real board's 0.3 in channel):
        0,1     + and - power rails
        3..7    rows A..E
        8,9     centre channel
        10..14  rows F..J
        16,17   + and - power rails
    """
    pad = 1
    body_rows = 18 if rails else 12
    cols = strips + 2 * pad
    rows = body_rows

    top = 0 if rails else -3          # shift when there are no rails to draw
    a_row, f_row = top + 3, top + 10

    terminal = [(pad + c, r)
                for c in range(strips)
                for r in list(range(a_row, a_row + 5)) + list(range(f_row, f_row + 5))]

    shapes = [
        # plastic body
        rect(-0.55, -0.55, (cols - 1) + 1.1, (rows - 1) + 1.1, "#e9edf1", "#b8bec6",
             rx=0.25),
        # centre channel
        rect(-0.3, top + 7.5, (cols - 1) + 0.6, 1.0, "#dfe4ea", "#c2c8d0", rx=0.08),
        {"type": "path", "d": squares_path(terminal, 0.17), "fill": "#5c6269"},
    ]

    if rails:
        for r, colr in ((0, "#d84040"), (1, "#1b1f25")):
            for y, c in ((r, colr), (rows - 2 + r, colr)):
                shapes.append(line(pad - 0.4, y, cols - pad - 0.6, y, c, 0.07, "butt"))
        rail_cells = [(pad + c, y)
                      for c in range(strips) if c % 6 != 5
                      for y in (0, 1, rows - 2, rows - 1)]
        shapes.append({"type": "path", "d": squares_path(rail_cells, 0.15),
                       "fill": "#5c6269"})

    # column numbers every five positions, and the A..J row letters
    for c in range(4, strips, 5):
        shapes.append(text(pad + c, a_row - 0.75, str(c + 1), size=0.34, color="#7a828c"))
    for i, letter in enumerate("ABCDE"):
        shapes.append(text(pad - 0.75, a_row + i, letter, size=0.32, color="#7a828c"))
    for i, letter in enumerate("FGHIJ"):
        shapes.append(text(pad - 0.75, f_row + i, letter, size=0.32, color="#7a828c"))

    return {
        "id": mid,
        "name": name,
        "subtitle": subtitle,
        "category": "misc",
        "tags": (tags or []) + ["breadboard", "solderless", "prototyping"],
        "designator": "BB",
        "footprint": {"cols": cols, "rows": rows},
        "pins": [],
        "shapes": shapes,
        "label": {"text": name, "x": r4((cols - 1) / 2), "y": r4(top + 8.0),
                  "size": 0.5, "color": "#8d949c"},
    }


def shield_board(mid, name, subtitle, *, cols, rows, top, bottom, category="mcu",
                 tags=None, datasheet=None, pcb=None, pcb_edge=None, mark=None,
                 extra_pins=None, extra_shapes=None):
    """Arduino-style board: headers along the top and bottom edges.

    `top` and `bottom` are lists of `(col, name)` pairs, so the gaps between
    header blocks are explicit. Real Arduino headers have a 0.16 in jog between
    D7 and D8 that no 0.1 in grid can express; these sit on whole holes, which
    is what you would actually solder a perfboard shield to.
    """
    pcb = pcb or COL["pcb_blue"]
    pcb_edge = pcb_edge or COL["pcb_blue_edge"]
    top_row, bottom_row = 1, rows - 2

    pins = []
    n = 1
    for c, nm in top:
        pins.append(pin(c, top_row, nm, n, guess_pin_type(nm)))
        n += 1
    for c, nm in bottom:
        pins.append(pin(c, bottom_row, nm, n, guess_pin_type(nm)))
        n += 1
    # Blocks that are not on the top or bottom edge, e.g. the Mega's 2x18.
    for c, r, nm in (extra_pins or []):
        pins.append(pin(c, r, nm, n, guess_pin_type(nm)))
        n += 1

    def strip(cells, y):
        runs = []
        for c, _ in cells:
            if runs and c == runs[-1][1] + 1:
                runs[-1][1] = c
            else:
                runs.append([c, c])
        return [rect(a - 0.32, y - 0.32, (b - a) + 0.64, 0.64,
                     COL["plastic_black"], COL["ic_edge"], rx=0.08) for a, b in runs]

    shapes = strip(top, top_row) + strip(bottom, bottom_row)
    shapes += [
        # USB socket and barrel jack hang off the left edge, as on the real board
        rect(-1.3, 2.2, 1.9, 3.0, COL["tin"], "#7f868e", rx=0.1),
        rect(-1.3, rows - 6.4, 1.9, 2.6, COL["plastic_black"], "#3a4048", rx=0.14),
        rect(cols * 0.32, rows * 0.36, cols * 0.34, rows * 0.28,
             COL["ic_body"], COL["ic_edge"], rx=0.1),
    ]
    if extra_shapes:
        shapes.extend(extra_shapes)

    return {
        "id": mid,
        "name": name,
        "subtitle": subtitle,
        "category": category,
        "tags": (tags or []) + ["board", "shield"],
        "designator": "U",
        **({"datasheet": datasheet} if datasheet else {}),
        "footprint": {"cols": cols, "rows": rows},
        "pins": pins,
        "body": {"x": -0.6, "y": -0.6, "w": (cols - 1) + 1.2, "h": (rows - 1) + 1.2,
                 "rx": 0.5, "fill": pcb, "stroke": pcb_edge},
        "shapes": shapes,
        "label": {"text": mark or name, "x": r4((cols - 1) / 2), "y": r4(rows * 0.72),
                  "size": 0.6, "color": COL["silk"]},
    }


# Standard Raspberry Pi 40-pin GPIO header, odd pins then even pins.
RPI_ODD = ["3V3", "GPIO2", "GPIO3", "GPIO4", "GND", "GPIO17", "GPIO27", "GPIO22",
           "3V3", "GPIO10", "GPIO9", "GPIO11", "GND", "ID_SD", "GPIO5", "GPIO6",
           "GPIO13", "GPIO19", "GPIO26", "GND"]
RPI_EVEN = ["5V", "5V", "GND", "GPIO14", "GPIO15", "GPIO18", "GND", "GPIO23",
            "GPIO24", "GND", "GPIO25", "GPIO8", "GPIO7", "ID_SC", "GND", "GPIO12",
            "GND", "GPIO16", "GPIO20", "GPIO21"]


def sbc_board(mid, name, subtitle, *, cols, rows, header_col=2, gpio=40,
              tags=None, datasheet=None, pcb=None, mark=None, extra_shapes=None):
    """Raspberry Pi-style single-board computer: a 2×20 GPIO header on one edge.

    Only the GPIO header is electrically modelled — the USB, HDMI and Ethernet
    connectors are drawn as artwork, because nothing on a perfboard solders to
    them.
    """
    pcb = pcb or COL["pcb_green"]
    n_pairs = gpio // 2

    pins = []
    for i in range(n_pairs):
        pins.append(pin(header_col + i, 0, RPI_ODD[i], 2 * i + 1, guess_pin_type(RPI_ODD[i])))
        pins.append(pin(header_col + i, 1, RPI_EVEN[i], 2 * i + 2, guess_pin_type(RPI_EVEN[i])))

    shapes = [
        rect(header_col - 0.35, -0.35, (n_pairs - 1) + 0.7, 1.7,
             COL["plastic_black"], COL["ic_edge"], rx=0.08),
        # SoC package, roughly centred
        rect(cols * 0.34, rows * 0.42, cols * 0.22, rows * 0.22,
             COL["ic_body"], COL["ic_edge"], rx=0.08),
    ]
    if extra_shapes:
        shapes.extend(extra_shapes)

    return {
        "id": mid,
        "name": name,
        "subtitle": subtitle,
        "category": "mcu",
        "tags": (tags or []) + ["raspberry pi", "sbc", "linux", "gpio"],
        "designator": "U",
        **({"datasheet": datasheet} if datasheet else {}),
        "footprint": {"cols": cols, "rows": rows},
        "pins": pins,
        "body": {"x": -0.7, "y": -0.7, "w": (cols - 1) + 1.4, "h": (rows - 1) + 1.4,
                 "rx": 0.9, "fill": pcb, "stroke": COL["pcb_green_edge"]},
        "shapes": shapes,
        "label": {"text": mark or name, "x": r4((cols - 1) / 2), "y": r4(rows * 0.78),
                  "size": 0.7, "color": COL["silk"]},
    }


def dc_motor(mid, name, subtitle, *, span=2, body_w=6.0, body_h=4.0, tags=None,
             leads=("+", "-"), category="motor", shaft=True):
    """Two-terminal DC motor seen from the side, terminals at the bottom."""
    cx = (span - 1) / 2.0
    bx, by = cx - body_w / 2, -body_h - 0.6
    shapes = [
        line(0, 0, cx - 0.3, by + body_h, "#d84040", 0.1),
        line(span - 1, 0, cx + 0.3, by + body_h, "#1b1f25", 0.1),
        rect(bx, by, body_w, body_h, "#8d949c", "#5c6269", rx=0.5),
        rect(bx + 0.3, by + 0.3, body_w - 0.6, body_h - 0.6, "#a9b0b8", None, rx=0.35),
        circle(cx, by + body_h / 2, min(body_w, body_h) * 0.22, "#5c6269", "#3a4048", sw=0.06),
    ]
    if shaft:
        shapes.append(rect(cx - 0.16, by - 1.4, 0.32, 1.4, "#c9ced6", "#8d949c", rx=0.1))
    return {
        "id": mid,
        "name": name,
        "subtitle": subtitle,
        "category": category,
        "tags": (tags or []) + ["motor"],
        "designator": "M",
        "footprint": {"cols": span, "rows": 1},
        "pins": [pin(0, 0, leads[0], 1, "power"), pin(span - 1, 0, leads[1], 2, "gnd")],
        "shapes": shapes,
        "label": {"text": name.split()[0], "x": r4(cx), "y": 0.5, "size": 0.3,
                  "color": "#9fb0c0"},
    }


# ---------------------------------------------------------------------------
# Small colour utilities
# ---------------------------------------------------------------------------


def _hex_to_rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def _rgb_to_hex(rgb):
    return "#%02x%02x%02x" % tuple(max(0, min(255, int(round(c)))) for c in rgb)


def _darken(h, f=0.6):
    return _rgb_to_hex([c * f for c in _hex_to_rgb(h)])


def _lighten(h, f=0.35):
    return _rgb_to_hex([c + (255 - c) * f for c in _hex_to_rgb(h)])
