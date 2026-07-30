/**
 * Board presets and coordinate helpers.
 *
 * Coordinate systems
 * ------------------
 *  grid    - integer (col, row) hole indices. col 0 is the leftmost column as
 *            seen from the FRONT of the board; row 0 is the top row.
 *  display - grid, but mirrored horizontally when viewing the solder side.
 *  unit    - continuous coordinates in hole pitches, same axes as display.
 *
 * Hole names follow the usual perfboard convention: columns get letters
 * (A, B, ... Z, AA, AB, ...) and rows get numbers starting at 1.
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

export const MIN_DIM = 2;
export const MAX_DIM = 120;

/** Margin of bare board around the hole grid, in hole units. */
export const BOARD_MARGIN = 1.0;
/** Extra room reserved outside the board for the row/column rulers. */
export const RULER_GUTTER = 1.4;

export function boardColor(id) {
  return BOARD_COLORS.find((c) => c.id === id) || BOARD_COLORS[0];
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

/** Human-readable hole name, e.g. (2, 5) -> "C6". */
export function holeName(col, row) {
  return `${colLabel(col)}${rowLabel(row)}`;
}

/**
 * Mirror a column index when the solder side is being viewed.
 * The mapping is its own inverse, so the same call converts either direction.
 */
export function displayCol(col, boardCols, mirrored) {
  return mirrored ? boardCols - 1 - col : col;
}

export function inBounds(board, col, row) {
  return col >= 0 && row >= 0 && col < board.cols && row < board.rows;
}

/** The SVG viewBox that fits the whole board plus its rulers, in unit space. */
export function boardExtent(board) {
  const pad = BOARD_MARGIN + RULER_GUTTER;
  return {
    x: -pad,
    y: -pad,
    w: board.cols - 1 + 2 * pad,
    h: board.rows - 1 + 2 * pad,
  };
}

/**
 * A board is described only by its hole counts, pitch and colour. Which preset
 * that corresponds to is derived on demand via `presetFor` rather than stored,
 * so there is no second source of truth to keep in sync.
 */
export function defaultBoard() {
  const p = BOARD_PRESETS.find((x) => x.id === '5x7');
  return {
    cols: p.cols,
    rows: p.rows,
    pitchMm: 2.54,
    colorId: 'phenolic',
  };
}
