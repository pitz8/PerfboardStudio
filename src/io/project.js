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
import { BOARD_COLORS, MAX_DIM, MIN_DIM } from '../core/board.js';
import { ROTATIONS, normalizeRotation } from '../core/geometry.js';
import { WIRE_GAUGES } from '../core/store.js';

export const FORMAT = 'perfboard-studio';
export const FORMAT_VERSION = 1;

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
    board: { ...doc.board },
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

  const board = readBoard(data.board, warnings);
  const modules = [];
  const seen = new Set();
  for (const [i, m] of (Array.isArray(data.modules) ? data.modules : []).entries()) {
    const inst = readModule(m, i, board, catalog, warnings, seen);
    if (inst) modules.push(inst);
  }

  const wires = [];
  for (const [i, w] of (Array.isArray(data.wires) ? data.wires : []).entries()) {
    const wire = readWire(w, i, board, warnings, seen);
    if (wire) wires.push(wire);
  }

  return {
    doc: {
      name: typeof data.name === 'string' && data.name.trim() ? data.name : 'Untitled design',
      board,
      modules,
      wires,
    },
    warnings,
  };
}

function readBoard(raw, warnings) {
  const b = raw && typeof raw === 'object' ? raw : {};
  const cols = clampInt(b.cols, MIN_DIM, MAX_DIM, 18);
  const rows = clampInt(b.rows, MIN_DIM, MAX_DIM, 24);
  if (!Number.isFinite(b.cols) || !Number.isFinite(b.rows)) {
    warnings.push('Board size was missing or invalid; fell back to 18 × 24 holes.');
  }
  const colorId = BOARD_COLORS.some((c) => c.id === b.colorId) ? b.colorId : 'phenolic';
  if (b.colorId !== undefined && colorId !== b.colorId) {
    warnings.push(`Unknown board material "${b.colorId}"; used phenolic instead.`);
  }
  return {
    cols,
    rows,
    pitchMm: Number.isFinite(b.pitchMm) && b.pitchMm > 0 ? b.pitchMm : 2.54,
    colorId,
  };
}

function readModule(raw, i, board, catalog, warnings, seen) {
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

  const col = clampInt(raw.col, 0, board.cols - 1, 0);
  const row = clampInt(raw.row, 0, board.rows - 1, 0);
  if (col !== raw.col || row !== raw.row) {
    warnings.push(`${who} sat outside the board and was moved to `
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

function readWire(raw, i, board, warnings, seen) {
  if (!raw || typeof raw !== 'object') { warnings.push(`Wire #${i + 1} is not an object.`); return null; }
  const pts = Array.isArray(raw.points) ? raw.points : [];
  const usable = pts.filter((p) => Array.isArray(p) && Number.isFinite(p[0]) && Number.isFinite(p[1]));
  if (usable.length !== pts.length) {
    warnings.push(`Wire #${i + 1} had ${pts.length - usable.length} unreadable point(s).`);
  }

  let moved = 0;
  const points = usable.map((p) => {
    const c = clampInt(p[0], 0, board.cols - 1, 0);
    const r = clampInt(p[1], 0, board.rows - 1, 0);
    if (c !== p[0] || r !== p[1]) moved++;
    return [c, r];
  });
  if (moved) {
    warnings.push(`Wire #${i + 1} had ${moved} point(s) off the board; pulled to the edge.`);
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
