/**
 * Placement geometry for module instances.
 *
 * A module definition is authored in its own local frame: pin 1 sits at (0,0)
 * and the footprint extends right/down over `cols` × `rows` holes. A placed
 * instance adds an anchor cell (col,row) plus a rotation of 0/90/180/270°.
 *
 * The SVG transforms below and the point maths in `rotatePoint` are two views of
 * the same operation, so they must stay in agreement — see the tests in
 * tools/validate_catalog.py for the invariant that keeps them honest.
 */

export const ROTATIONS = [0, 90, 180, 270];

/**
 * Resolve an instance against its definition, applying the resizable axis.
 *
 * Resizing stretches the part between its extreme holes: the artwork is scaled
 * along the axis and pin positions are scaled with it. That is the right
 * semantic for two-lead axial parts and plain plates, which is why `resize` is
 * only declared on those — a pin header must gain pins rather than stretch, so
 * headers ship as discrete sizes instead.
 */
export function resolveInstance(def, inst) {
  const base = def.footprint;
  let cols = base.cols;
  let rows = base.rows;
  let scaleX = 1;
  let scaleY = 1;
  let pins = def.pins || [];

  if (def.resize && Number.isFinite(inst?.span)) {
    const span = Math.min(def.resize.max, Math.max(def.resize.min, Math.round(inst.span)));
    if (def.resize.axis === 'cols') {
      const from = base.cols - 1;
      const to = span - 1;
      cols = span;
      scaleX = from > 0 ? to / from : 1;
      if (from > 0) pins = pins.map((p) => ({ ...p, col: Math.round(p.col * to / from) }));
    } else {
      const from = base.rows - 1;
      const to = span - 1;
      rows = span;
      scaleY = from > 0 ? to / from : 1;
      if (from > 0) pins = pins.map((p) => ({ ...p, row: Math.round(p.row * to / from) }));
    }
  }
  return { cols, rows, scaleX, scaleY, pins };
}

/** Footprint of an instance, honouring a resizable axis. */
export function footprintOf(def, inst) {
  const { cols, rows } = resolveInstance(def, inst);
  return { cols, rows };
}

/** Size on the board after rotation. */
export function rotatedSize(cols, rows, rotation) {
  return (((rotation / 90) | 0) % 2 === 0) ? { w: cols, h: rows } : { w: rows, h: cols };
}

/**
 * Map a point from module-local units to board units, relative to the anchor.
 * Works for both integer hole indices and continuous artwork coordinates.
 */
export function rotatePoint(x, y, cols, rows, rotation) {
  switch (normalizeRotation(rotation)) {
    case 90: return { x: rows - 1 - y, y: x };
    case 180: return { x: cols - 1 - x, y: rows - 1 - y };
    case 270: return { x: y, y: cols - 1 - x };
    default: return { x, y };
  }
}

export function normalizeRotation(rotation) {
  const r = ((Math.round((rotation || 0) / 90) * 90) % 360 + 360) % 360;
  return r;
}

/**
 * SVG transform placing a module's local frame onto the board.
 * Equivalent to `rotatePoint` followed by a translation to (col,row).
 */
export function moduleTransform(inst, cols, rows) {
  const { col, row } = inst;
  switch (normalizeRotation(inst.rotation)) {
    case 90: return `translate(${col + rows - 1} ${row}) rotate(90)`;
    case 180: return `translate(${col + cols - 1} ${row + rows - 1}) rotate(180)`;
    case 270: return `translate(${col} ${row + cols - 1}) rotate(270)`;
    default: return `translate(${col} ${row})`;
  }
}

/** Absolute board coordinates of a module-local point. */
export function toBoard(inst, cols, rows, x, y) {
  const p = rotatePoint(x, y, cols, rows, inst.rotation);
  return { x: p.x + inst.col, y: p.y + inst.row };
}

/** Every hole covered by the instance, as {col,row} in grid coordinates. */
export function occupiedCells(def, inst) {
  const { cols, rows } = footprintOf(def, inst);
  const out = [];
  for (let r = 0; r < rows; r++) {
    for (let c = 0; c < cols; c++) {
      const p = rotatePoint(c, r, cols, rows, inst.rotation);
      out.push({ col: p.x + inst.col, row: p.y + inst.row });
    }
  }
  return out;
}

/** Absolute grid positions of the instance's electrical pins. */
export function pinCells(def, inst) {
  const { cols, rows, pins } = resolveInstance(def, inst);
  return pins.map((p) => {
    const q = rotatePoint(p.col, p.row, cols, rows, inst.rotation);
    return { ...p, col: q.x + inst.col, row: q.y + inst.row };
  });
}

/** Bounding box of the occupied holes, in grid coordinates. */
export function boundsOf(def, inst) {
  const { cols, rows } = footprintOf(def, inst);
  const { w, h } = rotatedSize(cols, rows, inst.rotation);
  return { col: inst.col, row: inst.row, cols: w, rows: h };
}

/**
 * `area` is any `{cols, rows}` rectangle anchored at (0,0) — in practice the
 * workspace. Parts are held inside the workspace, never inside an individual
 * board: sitting a battery pack or a dev board off to the side of the perfboard
 * is a legitimate layout, not an error.
 */
export function fitsInArea(area, def, inst) {
  const b = boundsOf(def, inst);
  return b.col >= 0 && b.row >= 0
    && b.col + b.cols <= area.cols
    && b.row + b.rows <= area.rows;
}

/** Clamp an instance's anchor so its whole footprint stays inside `area`. */
export function clampToArea(area, def, inst) {
  const b = boundsOf(def, inst);
  return {
    col: Math.min(Math.max(0, inst.col), Math.max(0, area.cols - b.cols)),
    row: Math.min(Math.max(0, inst.row), Math.max(0, area.rows - b.rows)),
  };
}

/** Clamp a board's anchor so the whole board stays inside `area`. */
export function clampBoardToArea(area, board) {
  return {
    col: Math.min(Math.max(0, board.col), Math.max(0, area.cols - board.cols)),
    row: Math.min(Math.max(0, board.row), Math.max(0, area.rows - board.rows)),
  };
}

/** True when the two instances share at least one hole (and the same side). */
export function overlaps(defA, a, defB, b) {
  if (a.side !== b.side) return false;
  const ba = boundsOf(defA, a);
  const bb = boundsOf(defB, b);
  return ba.col < bb.col + bb.cols && bb.col < ba.col + ba.cols
    && ba.row < bb.row + bb.rows && bb.row < ba.row + ba.rows;
}

/** Squared distance from point (x,y) to segment (x1,y1)-(x2,y2). */
export function distToSegment(x, y, x1, y1, x2, y2) {
  const dx = x2 - x1;
  const dy = y2 - y1;
  const len2 = dx * dx + dy * dy;
  let t = len2 === 0 ? 0 : ((x - x1) * dx + (y - y1) * dy) / len2;
  t = Math.max(0, Math.min(1, t));
  const px = x1 + t * dx;
  const py = y1 + t * dy;
  return Math.hypot(x - px, y - py);
}

/** Shortest distance from a point to a wire polyline, in hole units. */
export function distToPolyline(x, y, points) {
  if (!points.length) return Infinity;
  if (points.length === 1) return Math.hypot(x - points[0][0], y - points[0][1]);
  let best = Infinity;
  for (let i = 1; i < points.length; i++) {
    const d = distToSegment(x, y, points[i - 1][0], points[i - 1][1], points[i][0], points[i][1]);
    if (d < best) best = d;
  }
  return best;
}
