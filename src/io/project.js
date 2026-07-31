/**
 * Save / open the `.pbs.json` design file.
 *
 * Designs embed a snapshot of every module definition they use. That makes a
 * saved file self-contained: it still opens correctly years later even if the
 * catalog has been renamed, edited or trimmed. Definitions from the snapshot are
 * only registered for ids the live catalog does not already provide, so editing
 * a module JSON does propagate to existing designs.
 */

import { normalizeDef } from '../core/catalog.js';
import {
  BOARD_COLORS, DESK_COLORS, MAX_DIM, MAX_WORKSPACE, MIN_DIM, MIN_WORKSPACE,
  makeBoard,
} from '../core/board.js';
import { ROTATIONS, normalizeRotation } from '../core/geometry.js';
import { WIRE_GAUGES } from '../core/store.js';

export const FORMAT = 'perfboard-studio';
export const FORMAT_VERSION = 2;

/** Serialise the document plus the definitions it depends on. */
export function serialize(doc, catalog) {
  const usedIds = [...new Set(doc.modules.map((m) => m.moduleId))].sort();
  const snapshot = {};
  for (const id of usedIds) {
    const def = catalog.get(id);
    if (!def) continue;
    const clean = { ...def };
    delete clean._search;
    delete clean._source;
    snapshot[id] = clean;
  }

  return {
    format: FORMAT,
    version: FORMAT_VERSION,
    generator: 'Perfboard Studio',
    savedAt: new Date().toISOString(),
    name: doc.name || 'Untitled design',
    workspace: { ...doc.workspace },
    boards: doc.boards.map((b) => ({ ...b })),
    modules: doc.modules.map((m) => ({ ...m })),
    wires: doc.wires.map((w) => ({ ...w, points: w.points.map(([c, r]) => [c, r]) })),
    moduleDefs: snapshot,
  };
}

export function toJSON(doc, catalog) {
  return `${JSON.stringify(serialize(doc, catalog), null, 2)}\n`;
}

/**
 * Parse and validate a design file.
 * @returns {{doc: object, warnings: string[]}}
 * @throws {Error} when the payload is not a usable design
 */
export function deserialize(raw, catalog) {
  const warnings = [];
  let data;
  if (typeof raw === 'string') {
    try {
      data = JSON.parse(raw);
    } catch (err) {
      throw new Error(`Not valid JSON: ${err.message}`);
    }
  } else {
    data = raw;
  }
  if (!data || typeof data !== 'object') throw new Error('File does not contain an object');
  if (data.format !== FORMAT) {
    throw new Error(`Unrecognised file format${data.format ? ` "${data.format}"` : ''}`);
  }
  if (Number(data.version) > FORMAT_VERSION) {
    warnings.push(`File was written by a newer version (v${data.version}); opening anyway.`);
  }

  // Register embedded definitions we do not already have.
  let embedded = 0;
  for (const [id, def] of Object.entries(data.moduleDefs || {})) {
    if (catalog.get(id)) continue;
    const norm = normalizeDef({ ...def, id }, 'embedded');
    if (norm) { catalog.register(norm); embedded++; } else {
      warnings.push(`Embedded definition "${id}" is malformed and was skipped.`);
    }
  }
  if (embedded) {
    warnings.push(`${embedded} module definition(s) came from the file, not the catalog.`);
  }

  const seen = new Set();
  const { workspace, boards } = readLayout(data, warnings, seen);

  const modules = [];
  for (const [i, m] of (Array.isArray(data.modules) ? data.modules : []).entries()) {
    const inst = readModule(m, i, workspace, catalog, warnings, seen);
    if (inst) modules.push(inst);
  }

  const wires = [];
  for (const [i, w] of (Array.isArray(data.wires) ? data.wires : []).entries()) {
    const wire = readWire(w, i, workspace, warnings, seen);
    if (wire) wires.push(wire);
  }

  return {
    doc: {
      name: typeof data.name === 'string' && data.name.trim() ? data.name : 'Untitled design',
      workspace,
      boards,
      modules,
      wires,
    },
    warnings,
  };
}

/**
 * Read the workspace and the boards on it.
 *
 * v1 files had exactly one board and no workspace: positions were board-local
 * and (0,0) was the board's corner. Those files still open unchanged, because a
 * v1 board maps onto a workspace of the same size with the board at the origin —
 * every stored coordinate then means the same hole it always did.
 */
function readLayout(data, warnings, seen) {
  if (Array.isArray(data.boards) || (data.workspace && typeof data.workspace === 'object')) {
    const workspace = readWorkspace(data.workspace, warnings);
    const boards = [];
    for (const [i, b] of (Array.isArray(data.boards) ? data.boards : []).entries()) {
      const board = readBoard(b, i, workspace, warnings, seen);
      if (board) boards.push(board);
    }
    return { workspace, boards };
  }

  const legacy = readBoard(data.board, 0, { cols: MAX_WORKSPACE, rows: MAX_WORKSPACE }, warnings, seen);
  const pitchMm = Number(data.board?.pitchMm);
  const workspace = {
    cols: legacy.cols,
    rows: legacy.rows,
    pitchMm: Number.isFinite(pitchMm) && pitchMm > 0 ? pitchMm : 2.54,
    colorId: DESK_COLORS[0].id,
  };
  legacy.col = 0;
  legacy.row = 0;
  legacy.label = 'Board 1';
  warnings.push('Opened a single-board file; it became one board on a workspace '
    + 'of the same size. Enlarge the workspace to place parts beside it.');
  return { workspace, boards: [legacy] };
}

function readWorkspace(raw, warnings) {
  const w = raw && typeof raw === 'object' ? raw : {};
  const cols = clampInt(w.cols, MIN_WORKSPACE, MAX_WORKSPACE, 56);
  const rows = clampInt(w.rows, MIN_WORKSPACE, MAX_WORKSPACE, 40);
  if (!Number.isFinite(w.cols) || !Number.isFinite(w.rows)) {
    warnings.push('Workspace size was missing or invalid; fell back to 56 × 40 holes.');
  }

  // An unknown backdrop is cosmetic, so fall back quietly rather than warn.
  const colorId = DESK_COLORS.some((c) => c.id === w.colorId) ? w.colorId : DESK_COLORS[0].id;

  return {
    cols,
    rows,
    pitchMm: Number.isFinite(w.pitchMm) && w.pitchMm > 0 ? w.pitchMm : 2.54,
    colorId,
  };
}

function readBoard(raw, i, area, warnings, seen) {
  const b = raw && typeof raw === 'object' ? raw : {};
  const who = b.label || `Board #${i + 1}`;

  const cols = clampInt(b.cols, MIN_DIM, MAX_DIM, 18);
  const rows = clampInt(b.rows, MIN_DIM, MAX_DIM, 24);
  if (!Number.isFinite(b.cols) || !Number.isFinite(b.rows)) {
    warnings.push(`${who} had no valid size; fell back to 18 × 24 holes.`);
  }

  const col = clampInt(b.col, 0, Math.max(0, area.cols - cols), 0);
  const row = clampInt(b.row, 0, Math.max(0, area.rows - rows), 0);
  if ((b.col !== undefined && col !== b.col) || (b.row !== undefined && row !== b.row)) {
    warnings.push(`${who} hung off the workspace and was pulled back to `
      + `column ${col + 1}, row ${row + 1}.`);
  }

  const colorId = BOARD_COLORS.some((c) => c.id === b.colorId) ? b.colorId : 'phenolic';
  if (b.colorId !== undefined && colorId !== b.colorId) {
    warnings.push(`${who} had unknown material "${b.colorId}"; used phenolic instead.`);
  }

  // Pitch is a property of the whole workspace, not of one board — everything
  // shares a single grid. A v1 file's board pitch is lifted out by `readLayout`.
  const board = makeBoard({ col, row, cols, rows, colorId });
  board.uid = uniqueUid(b.uid, `b${i}`, seen);
  board.label = typeof b.label === 'string' ? b.label : null;
  return board;
}

function readModule(raw, i, area, catalog, warnings, seen) {
  if (!raw || typeof raw !== 'object') { warnings.push(`Module #${i + 1} is not an object.`); return null; }
  if (!raw.moduleId) { warnings.push(`Module #${i + 1} has no moduleId.`); return null; }
  if (!Number.isFinite(raw.col) || !Number.isFinite(raw.row)) {
    warnings.push(`Module #${i + 1} (${raw.moduleId}) has no valid position.`);
    return null;
  }
  const uid = uniqueUid(raw.uid, `m${i}`, seen);
  const def = catalog.get(raw.moduleId);
  const who = `${raw.label || raw.moduleId}`;
  if (!def) {
    warnings.push(`Module "${raw.moduleId}" is not in the catalog; shown as a placeholder.`);
  }

  const col = clampInt(raw.col, 0, area.cols - 1, 0);
  const row = clampInt(raw.row, 0, area.rows - 1, 0);
  if (col !== raw.col || row !== raw.row) {
    warnings.push(`${who} sat outside the workspace and was moved to `
      + `column ${col + 1}, row ${row + 1}.`);
  }

  const rotation = normalizeRotation(raw.rotation);
  if (raw.rotation !== undefined && raw.rotation !== rotation) {
    warnings.push(`${who} had rotation ${raw.rotation}°, snapped to ${rotation}°.`);
  }

  const side = raw.side === 'solder' ? 'solder' : 'front';
  if (raw.side !== undefined && raw.side !== side) {
    warnings.push(`${who} had side "${raw.side}"; placed on the front.`);
  }

  const inst = {
    uid,
    moduleId: String(raw.moduleId),
    col,
    row,
    rotation: ROTATIONS.includes(rotation) ? rotation : 0,
    side,
    label: typeof raw.label === 'string' ? raw.label : null,
  };
  if (Number.isFinite(raw.span)) inst.span = Math.max(1, Math.round(raw.span));
  return inst;
}

function readWire(raw, i, area, warnings, seen) {
  if (!raw || typeof raw !== 'object') { warnings.push(`Wire #${i + 1} is not an object.`); return null; }
  const pts = Array.isArray(raw.points) ? raw.points : [];
  const usable = pts.filter((p) => Array.isArray(p) && Number.isFinite(p[0]) && Number.isFinite(p[1]));
  if (usable.length !== pts.length) {
    warnings.push(`Wire #${i + 1} had ${pts.length - usable.length} unreadable point(s).`);
  }

  let moved = 0;
  const points = usable.map((p) => {
    const c = clampInt(p[0], 0, area.cols - 1, 0);
    const r = clampInt(p[1], 0, area.rows - 1, 0);
    if (c !== p[0] || r !== p[1]) moved++;
    return [c, r];
  });
  if (moved) {
    warnings.push(`Wire #${i + 1} had ${moved} point(s) off the workspace; pulled to the edge.`);
  }
  if (points.length < 2) {
    warnings.push(`Wire #${i + 1} has fewer than two valid points and was dropped.`);
    return null;
  }

  const color = typeof raw.color === 'string' && /^#[0-9a-f]{3,8}$/i.test(raw.color)
    ? raw.color : '#e02b25';
  if (raw.color !== undefined && color !== raw.color) {
    warnings.push(`Wire #${i + 1} had colour "${raw.color}"; used red instead.`);
  }

  const gauge = WIRE_GAUGES.some((g) => g.id === raw.gauge) ? raw.gauge : 'normal';
  if (raw.gauge !== undefined && gauge !== raw.gauge) {
    warnings.push(`Wire #${i + 1} had gauge "${raw.gauge}"; used normal.`);
  }

  const side = raw.side === 'solder' ? 'solder' : 'front';
  if (raw.side !== undefined && side !== raw.side) {
    warnings.push(`Wire #${i + 1} had side "${raw.side}"; placed on the front.`);
  }

  return {
    uid: uniqueUid(raw.uid, `w${i}`, seen),
    points,
    color,
    gauge,
    side,
    label: typeof raw.label === 'string' ? raw.label : null,
  };
}

function uniqueUid(candidate, fallback, seen) {
  let id = typeof candidate === 'string' && candidate ? candidate : fallback;
  while (seen.has(id)) id = `${id}_`;
  seen.add(id);
  return id;
}

function clampInt(v, lo, hi, fallback) {
  if (!Number.isFinite(v)) return fallback;
  return Math.min(hi, Math.max(lo, Math.round(v)));
}

/** Suggested download filename for a design. */
export function filenameFor(doc) {
  const base = (doc.name || 'design')
    .trim()
    .replace(/[^\w\s.-]+/g, '')
    .replace(/\s+/g, '-')
    .replace(/^-+|-+$/g, '')
    .slice(0, 60) || 'design';
  return `${base}.pbs.json`;
}
