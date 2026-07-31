/**
 * Application store.
 *
 * The state splits in two:
 *   doc  - the saved design (board, modules, wires). Every change goes through
 *          `commit`, which pushes the previous doc onto the undo stack.
 *   ui   - transient state (tool, selection, view box, toggles). Never undone,
 *          never saved.
 *
 * Subscribers get `(state, reason)` and re-render. There is no diffing: the
 * renderer is cheap enough to rebuild the layers it needs on each notification.
 */

import { defaultBoard, defaultWorkspace } from './board.js';
import { uid } from '../util/dom.js';

const HISTORY_LIMIT = 100;

export const WIRE_COLORS = [
  { id: 'red', label: 'Red', hex: '#e02b25' },
  { id: 'black', label: 'Black', hex: '#1b1f25' },
  { id: 'yellow', label: 'Yellow', hex: '#e8c72c' },
  { id: 'green', label: 'Green', hex: '#2fbf4e' },
  { id: 'blue', label: 'Blue', hex: '#2b7fe0' },
  { id: 'white', label: 'White', hex: '#eef2f6' },
  { id: 'orange', label: 'Orange', hex: '#e88227' },
  { id: 'brown', label: 'Brown', hex: '#8a5a32' },
  { id: 'violet', label: 'Violet', hex: '#9d5cd8' },
  { id: 'grey', label: 'Grey', hex: '#8d949c' },
  { id: 'cyan', label: 'Cyan', hex: '#2fd4d4' },
  { id: 'pink', label: 'Pink', hex: '#ef7fb0' },
];

export const WIRE_GAUGES = [
  { id: 'thin', label: 'Thin', width: 0.16 },
  { id: 'normal', label: 'Normal', width: 0.24 },
  { id: 'thick', label: 'Thick', width: 0.34 },
];

function emptyDoc() {
  return {
    name: 'Untitled design',
    workspace: defaultWorkspace(),
    boards: [defaultBoard()],
    modules: [],
    wires: [],
  };
}

export class Store {
  constructor() {
    this.doc = emptyDoc();
    this.ui = {
      side: 'front',
      tool: 'select',
      /** module id queued for placement, or null */
      placing: null,
      placingRotation: 0,
      selection: null, // { kind: 'module'|'wire', uid }
      hover: null, // { col, row } in grid coords
      wireDraft: null, // { points: [[col,row]], color, gauge }
      wireColor: WIRE_COLORS[0].hex,
      wireGauge: 'normal',
      showGhost: true,
      showLabels: true,
      showPinNames: false,
      showRulers: true,
      /** 0.1..1 — fades module artwork so wiring underneath stays visible. */
      moduleOpacity: 1,
      snapWires: true,
      view: null, // { x, y, w, h } in unit space; null = fit on next render
      dirty: false,
    };
    this.undoStack = [];
    this.redoStack = [];
    this.listeners = new Set();
  }

  subscribe(fn) {
    this.listeners.add(fn);
    return () => this.listeners.delete(fn);
  }

  emit(reason) {
    for (const fn of this.listeners) fn(this, reason);
  }

  // -- document mutation -----------------------------------------------------

  /** Apply `mutator(draft)` to a clone of the doc and record it for undo. */
  commit(label, mutator) {
    const before = structuredClone(this.doc);
    const draft = structuredClone(this.doc);
    const result = mutator(draft);
    if (result === false) return false; // mutator declined; nothing changed
    this.undoStack.push({ label, doc: before });
    if (this.undoStack.length > HISTORY_LIMIT) this.undoStack.shift();
    this.redoStack.length = 0;
    this.doc = draft;
    this.ui.dirty = true;
    this.emit('doc');
    return true;
  }

  /** Replace the whole document (open / new). Clears history. */
  load(doc, { markClean = true } = {}) {
    this.doc = doc;
    this.undoStack.length = 0;
    this.redoStack.length = 0;
    this.ui.selection = null;
    this.ui.wireDraft = null;
    this.ui.placing = null;
    this.ui.view = null;
    this.ui.dirty = !markClean;
    this.emit('load');
  }

  reset() {
    this.load(emptyDoc());
  }

  undo() {
    const entry = this.undoStack.pop();
    if (!entry) return false;
    this.redoStack.push({ label: entry.label, doc: structuredClone(this.doc) });
    this.doc = entry.doc;
    this.ui.selection = null;
    this.ui.wireDraft = null;
    this.ui.dirty = true;
    this.emit('doc');
    return true;
  }

  redo() {
    const entry = this.redoStack.pop();
    if (!entry) return false;
    this.undoStack.push({ label: entry.label, doc: structuredClone(this.doc) });
    this.doc = entry.doc;
    this.ui.selection = null;
    this.ui.wireDraft = null;
    this.ui.dirty = true;
    this.emit('doc');
    return true;
  }

  get canUndo() { return this.undoStack.length > 0; }
  get canRedo() { return this.redoStack.length > 0; }
  get undoLabel() { return this.undoStack.at(-1)?.label ?? null; }
  get redoLabel() { return this.redoStack.at(-1)?.label ?? null; }

  // -- transient state -------------------------------------------------------

  /** Patch the UI slice. Pass `{silent:true}` in `opts` to skip notifying. */
  setUI(patch, opts = {}) {
    let changed = false;
    for (const [k, v] of Object.entries(patch)) {
      if (this.ui[k] !== v) { this.ui[k] = v; changed = true; }
    }
    if (changed && !opts.silent) this.emit(opts.reason || 'ui');
    return changed;
  }

  // -- lookups ---------------------------------------------------------------

  moduleByUid(id) { return this.doc.modules.find((m) => m.uid === id) || null; }
  wireByUid(id) { return this.doc.wires.find((w) => w.uid === id) || null; }
  boardByUid(id) { return this.doc.boards.find((b) => b.uid === id) || null; }

  itemByPick(sel) {
    if (!sel) return null;
    if (sel.kind === 'module') return this.moduleByUid(sel.uid);
    if (sel.kind === 'wire') return this.wireByUid(sel.uid);
    if (sel.kind === 'board') return this.boardByUid(sel.uid);
    return null;
  }

  get selected() {
    const sel = this.ui.selection;
    const item = this.itemByPick(sel);
    return item ? { kind: sel.kind, item } : null;
  }

  /** Next free "Board N" name. */
  nextBoardLabel() {
    const used = new Set(
      this.doc.boards
        .map((b) => b.label)
        .filter((l) => typeof l === 'string' && l.startsWith('Board '))
        .map((l) => Number.parseInt(l.slice(6), 10))
        .filter(Number.isFinite),
    );
    let n = 1;
    while (used.has(n)) n++;
    return `Board ${n}`;
  }

  /**
   * Next free reference designator for a definition, e.g. "R4".
   * Scans existing labels so numbering survives deletes without reuse gaps
   * mattering.
   */
  nextDesignator(def) {
    const prefix = def.designator || 'U';
    const used = new Set(
      this.doc.modules
        .map((m) => m.label)
        .filter((l) => typeof l === 'string' && l.startsWith(prefix))
        .map((l) => Number.parseInt(l.slice(prefix.length), 10))
        .filter(Number.isFinite),
    );
    let n = 1;
    while (used.has(n)) n++;
    return `${prefix}${n}`;
  }
}

/** Factory for a placed-module record. */
export function makeInstance(def, { col, row, rotation = 0, side = 'front', label, span }) {
  const inst = {
    uid: uid('m'),
    moduleId: def.id,
    col,
    row,
    rotation,
    side,
    label: label ?? null,
  };
  if (def.resize) inst.span = span ?? def.footprint[def.resize.axis];
  return inst;
}

/** Factory for a wire record. */
export function makeWire({ points, color, gauge = 'normal', side = 'front' }) {
  return {
    uid: uid('w'),
    points: points.map(([c, r]) => [c, r]),
    color,
    gauge,
    side,
    label: null,
  };
}
