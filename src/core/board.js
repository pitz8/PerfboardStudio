/**
 * The workspace grid, the perfboards placed on it, and coordinate helpers.
 *
 * Coordinate systems
 * ------------------
 *  grid    - integer (col, row) hole indices on the WORKSPACE, not on any one
 *            board. col 0 is the leftmost column seen from the FRONT; row 0 is
 *            the top row. Boards, modules and wires all live in this one space,
 *            which is what lets a part sit beside a board rather than on it.
 *  display - grid, but mirrored horizontally when viewing the solder side.
 *  unit    - continuous coordinates in hole pitches, same axes as display.
 *
 * Hole names follow the usual perfboard convention: columns get letters
 * (A, B, ... Z, AA, AB, ...) and rows get numbers starting at 1. A hole inside a
 * board can also be read in that board's own frame — see `localHoleName`.
 */

/** Physical perfboard sizes commonly sold, with their usual hole counts. */
export const BOARD_PRESETS = [
  { id: '2x8', label: '2 × 8 cm', cols: 6, rows: 30 },
  { id: '3x7', label: '3 × 7 cm', cols: 10, rows: 26 },
  { id: '4x6', label: '4 × 6 cm', cols: 14, rows: 22 },
  { id: '5x7', label: '5 × 7 cm', cols: 18, rows: 24 },
  { id: '6x8', label: '6 × 8 cm', cols: 20, rows: 30 },
  { id: '7x9', label: '7 × 9 cm', cols: 24, rows: 35 },
  { id: '8x12', label: '8 × 12 cm', cols: 30, rows: 46 },
  { id: '9x15', label: '9 × 15 cm', cols: 34, rows: 58 },
  { id: '10x10', label: '10 × 10 cm', cols: 38, rows: 38 },
  { id: '12x18', label: '12 × 18 cm', cols: 46, rows: 70 },
];

export const BOARD_COLORS = [
  { id: 'phenolic', label: 'Phenolic (tan)', fill: '#c99b58', edge: '#9a7237', pad: '#d8b070' },
  { id: 'fr4-green', label: 'FR-4 green', fill: '#1c6b4e', edge: '#0f4633', pad: '#c8a45a' },
  { id: 'fr4-blue', label: 'FR-4 blue', fill: '#1b4a7a', edge: '#0e2f52', pad: '#c8a45a' },
  { id: 'fr4-black', label: 'FR-4 black', fill: '#22262c', edge: '#12151a', pad: '#c8a45a' },
  { id: 'fr4-white', label: 'FR-4 white', fill: '#dfe4ea', edge: '#a9b0b8', pad: '#c08a3a' },
  { id: 'fr4-red', label: 'FR-4 red', fill: '#7a1d29', edge: '#4d0f18', pad: '#c8a45a' },
];

/**
 * Backdrops for the workspace itself. A fixed palette rather than a free colour
 * picker, because each entry also has to carry a `dot` that stays legible
 * against its own `fill` — the alignment grid is useless if it disappears.
 *
 * The light entries exist for a practical reason: a black wire routed over bare
 * workspace is invisible on a dark desk.
 */
export const DESK_COLORS = [
  { id: 'graphite', label: 'Graphite', fill: '#161a21', edge: '#242a33', dot: '#39414d' },
  { id: 'slate', label: 'Slate', fill: '#3c434e', edge: '#4d5663', dot: '#767f8d' },
  { id: 'steel', label: 'Steel blue', fill: '#26374d', edge: '#33475f', dot: '#5d7695' },
  { id: 'mat', label: 'Cutting mat', fill: '#2c5849', edge: '#1f4436', dot: '#558b76' },
  { id: 'kraft', label: 'Kraft paper', fill: '#cfc3ab', edge: '#a99c84', dot: '#8d8168' },
  { id: 'paper', label: 'White paper', fill: '#eef1f5', edge: '#c2c9d2', dot: '#a2abb6' },
];

export const MIN_DIM = 2;
export const MAX_DIM = 120;

/** Bounds for the workspace itself, which has to hold every board. */
export const MIN_WORKSPACE = 4;
export const MAX_WORKSPACE = 400;

/** Margin of bare board material around a board's hole grid, in hole units. */
export const BOARD_MARGIN = 1.0;
/** Extra room reserved outside the workspace for the row/column rulers. */
export const RULER_GUTTER = 1.4;

export function boardColor(id) {
  return BOARD_COLORS.find((c) => c.id === id) || BOARD_COLORS[0];
}

export function deskColor(id) {
  return DESK_COLORS.find((c) => c.id === id) || DESK_COLORS[0];
}

export function presetFor(cols, rows) {
  return BOARD_PRESETS.find((p) => p.cols === cols && p.rows === rows) || null;
}

/** 0 -> "A", 25 -> "Z", 26 -> "AA". */
export function colLabel(index) {
  let n = index;
  let out = '';
  do {
    out = String.fromCharCode(65 + (n % 26)) + out;
    n = Math.floor(n / 26) - 1;
  } while (n >= 0);
  return out;
}

/** Inverse of `colLabel`; returns -1 for anything unparseable. */
export function colIndex(label) {
  const s = String(label).trim().toUpperCase();
  if (!/^[A-Z]+$/.test(s)) return -1;
  let n = 0;
  for (const ch of s) n = n * 26 + (ch.charCodeAt(0) - 64);
  return n - 1;
}

export const rowLabel = (index) => String(index + 1);

/** Human-readable workspace hole name, e.g. (2, 5) -> "C6". */
export function holeName(col, row) {
  return `${colLabel(col)}${rowLabel(row)}`;
}

/**
 * Mirror a column index when the solder side is being viewed.
 * The mapping is its own inverse, so the same call converts either direction.
 */
export function displayCol(col, workspaceCols, mirrored) {
  return mirrored ? workspaceCols - 1 - col : col;
}

/** True when (col,row) is inside any `{cols, rows}` rectangle. */
export function inBounds(area, col, row) {
  return col >= 0 && row >= 0 && col < area.cols && row < area.rows;
}

/** The SVG viewBox that fits the whole workspace plus its rulers, in unit space. */
export function workspaceExtent(ws) {
  const pad = BOARD_MARGIN + RULER_GUTTER;
  return {
    x: -pad,
    y: -pad,
    w: ws.cols - 1 + 2 * pad,
    h: ws.rows - 1 + 2 * pad,
  };
}

/**
 * The workspace is the desk everything sits on: perfboards, modules that are
 * not on any board (a battery pack, a dev board on a stand-off) and the wiring
 * that runs between them.
 */
export function defaultWorkspace() {
  return { cols: 56, rows: 40, pitchMm: 2.54, colorId: DESK_COLORS[0].id };
}

let boardSeq = 0;

/**
 * A perfboard placed on the workspace. Boards carry no `side` of their own:
 * they are the substrate that both sides are seen through.
 */
export function makeBoard({
  col = 0, row = 0, cols = 18, rows = 24, colorId = 'phenolic', label = null,
} = {}) {
  boardSeq += 1;
  return {
    uid: `b${Date.now().toString(36).slice(-5)}${boardSeq.toString(36)}`,
    col,
    row,
    cols,
    rows,
    colorId,
    label,
  };
}

/** The board a fresh document starts with, sitting a little in from the corner. */
export function defaultBoard() {
  const p = BOARD_PRESETS.find((x) => x.id === '5x7');
  return makeBoard({ col: 3, row: 4, cols: p.cols, rows: p.rows, label: 'Board 1' });
}

/** Hole rectangle a board occupies on the workspace. */
export function boardBounds(b) {
  return { col: b.col, row: b.row, cols: b.cols, rows: b.rows };
}

/** True when the workspace hole (col,row) falls inside this board. */
export function boardCovers(b, col, row) {
  return col >= b.col && row >= b.row && col < b.col + b.cols && row < b.row + b.rows;
}

/** The topmost board under a workspace hole, or null when it is bare desk. */
export function boardAt(boards, col, row) {
  for (let i = boards.length - 1; i >= 0; i--) {
    if (boardCovers(boards[i], col, row)) return boards[i];
  }
  return null;
}

/** Hole name in a board's own frame, counted from that board's top-left hole. */
export function localHoleName(board, col, row) {
  return holeName(col - board.col, row - board.row);
}
