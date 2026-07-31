/**
 * Right-hand panel: board setup, view options, and properties of whatever is
 * selected.
 */

import { clear, el, on } from '../util/dom.js';
import {
  BOARD_COLORS, BOARD_PRESETS, DESK_COLORS, MAX_DIM, MAX_WORKSPACE, MIN_DIM,
  MIN_WORKSPACE, deskColor, holeName, makeBoard, presetFor,
} from '../core/board.js';
import { WIRE_COLORS, WIRE_GAUGES } from '../core/store.js';
import { boundsOf, clampBoardToArea, footprintOf, pinCells } from '../core/geometry.js';
import { modulePreview } from '../render/preview.js';

export class Inspector {
  constructor(root, store, catalog, { canvas, onStatus } = {}) {
    this.root = root;
    this.store = store;
    this.catalog = catalog;
    this.canvas = canvas;
    this.onStatus = onStatus || (() => {});

    this.boardBox = el('section', { class: 'pbs-panel-section' });
    this.viewBox = el('section', { class: 'pbs-panel-section' });
    this.selBox = el('section', { class: 'pbs-panel-section' });
    this.root.append(this.boardBox, this.viewBox, this.selBox);

    this.renderBoard();
    this.renderView();
    this.renderSelection();
  }

  render() {
    this.renderBoard();
    this.renderView();
    this.renderSelection();
  }

  // -- workspace -------------------------------------------------------------

  renderBoard() {
    const { workspace, boards } = this.store.doc;
    clear(this.boardBox);

    const nameInput = el('input', {
      class: 'pbs-input', type: 'text', value: this.store.doc.name,
      'aria-label': 'Design name', maxlength: '80',
    });
    on(nameInput, 'change', () => {
      const v = nameInput.value.trim() || 'Untitled design';
      this.store.commit('Rename design', (doc) => { doc.name = v; });
    });

    const colsInput = numberInput(workspace.cols, MIN_WORKSPACE, MAX_WORKSPACE,
      (v) => this.resizeWorkspace(v, workspace.rows));
    const rowsInput = numberInput(workspace.rows, MIN_WORKSPACE, MAX_WORKSPACE,
      (v) => this.resizeWorkspace(workspace.cols, v));

    const addBtn = el('button', {
      class: 'pbs-btn pbs-btn-wide', type: 'button', text: '＋ Add perfboard',
    });
    on(addBtn, 'click', () => this.addBoard());

    const list = el('div', { class: 'pbs-board-list' });
    for (const b of boards) list.append(this.boardRow(b));
    if (!boards.length) {
      list.append(el('p', { class: 'pbs-empty', text: 'No boards — parts sit straight on the workspace.' }));
    }

    this.boardBox.append(
      heading('Workspace'),
      field('Design name', nameInput),
      el('div', { class: 'pbs-field-row' }, [
        field('Columns (A…)', colsInput),
        field('Rows (1…)', rowsInput),
      ]),
      el('p', {
        class: 'pbs-note',
        text: `${workspace.cols * workspace.rows} holes · ${workspace.pitchMm} mm pitch · `
          + `${mm(workspace.cols, workspace.pitchMm)} × ${mm(workspace.rows, workspace.pitchMm)} mm`,
      }),
      field('Background', this.deskSwatches(workspace.colorId)),
      el('p', {
        class: 'pbs-note',
        text: `${deskColor(workspace.colorId).label}. Lighter backgrounds make dark `
          + 'wiring off the boards easier to follow.',
      }),
      el('div', { class: 'pbs-field-label', text: `Boards (${boards.length})` }),
      list,
      addBtn,
    );
  }

  /** Preset backdrops for the workspace grid. */
  deskSwatches(current) {
    const row = el('div', { class: 'pbs-swatches' });
    for (const c of DESK_COLORS) {
      const b = el('button', {
        type: 'button',
        class: `pbs-swatch${c.id === current ? ' is-active' : ''}`,
        style: `--swatch:${c.fill}`,
        title: c.label,
        'aria-label': `Background: ${c.label}`,
      });
      on(b, 'click', () => {
        if (c.id === this.store.doc.workspace.colorId) return;
        this.store.commit('Change background', (doc) => { doc.workspace.colorId = c.id; });
      });
      row.append(b);
    }
    return row;
  }

  /** One clickable row per board, so boards are reachable without hunting. */
  boardRow(board) {
    const sel = this.store.ui.selection;
    const btn = el('button', {
      class: `pbs-board-row${sel?.kind === 'board' && sel.uid === board.uid ? ' is-active' : ''}`,
      type: 'button',
      title: `Select ${board.label || 'board'}`,
    }, [
      el('span', { class: 'pbs-board-chip', style: `--chip:${boardFill(board.colorId)}` }),
      el('span', { class: 'pbs-board-name', text: board.label || 'Board' }),
      el('span', {
        class: 'pbs-board-meta',
        text: `${board.cols}×${board.rows} @ ${holeName(board.col, board.row)}`,
      }),
    ]);
    on(btn, 'click', () => this.store.setUI({ selection: { kind: 'board', uid: board.uid } }));
    return btn;
  }

  addBoard() {
    const { workspace } = this.store.doc;
    const preset = BOARD_PRESETS.find((p) => p.id === '4x6');
    const board = makeBoard({
      cols: preset.cols,
      rows: preset.rows,
      label: this.store.nextBoardLabel(),
    });
    // Drop it in the first free column band so it does not land on an existing
    // board; falling back to the origin if the workspace is already full.
    const used = this.store.doc.boards;
    let col = 0;
    while (col + board.cols <= workspace.cols
      && used.some((b) => col < b.col + b.cols && b.col < col + board.cols)) {
      col = Math.max(...used.filter((b) => b.col + b.cols > col).map((b) => b.col + b.cols)) + 1;
    }
    board.col = col + board.cols <= workspace.cols ? col : 0;
    const at = clampBoardToArea(workspace, board);
    board.col = at.col;
    board.row = at.row;

    this.store.commit(`Add ${board.label}`, (doc) => { doc.boards.push(board); });
    this.store.setUI({ selection: { kind: 'board', uid: board.uid } });
    this.onStatus(`Added ${board.label} — drag it into place`);
  }

  resizeWorkspace(cols, rows) {
    const c = clampWorkspace(cols);
    const r = clampWorkspace(rows);
    const { workspace } = this.store.doc;
    if (c === workspace.cols && r === workspace.rows) return;

    // Warn before shrinking away someone's work rather than silently dropping it.
    const lost = this.itemsOutside(c, r);
    if (lost.modules || lost.wires || lost.boards) {
      const parts = [];
      if (lost.boards) parts.push(`${lost.boards} board(s)`);
      if (lost.modules) parts.push(`${lost.modules} module(s)`);
      if (lost.wires) parts.push(`${lost.wires} wire(s)`);
      const ok = window.confirm(
        `Shrinking to ${c} × ${r} holes leaves ${parts.join(', ')} off the workspace.\n\n`
        + 'They will be removed. Continue?',
      );
      if (!ok) { this.renderBoard(); return; }
    }

    this.store.commit('Resize workspace', (doc) => {
      doc.workspace.cols = c;
      doc.workspace.rows = r;
      doc.boards = doc.boards.filter((b) => b.col + b.cols <= c && b.row + b.rows <= r);
      doc.modules = doc.modules.filter((m) => {
        const def = this.catalog.get(m.moduleId);
        const b = def ? boundsOf(def, m) : { col: m.col, row: m.row, cols: 1, rows: 1 };
        return b.col + b.cols <= c && b.row + b.rows <= r;
      });
      doc.wires = doc.wires.filter((w) => w.points.every(([x, y]) => x < c && y < r));
    });
    this.store.setUI({ view: null });
  }

  itemsOutside(cols, rows) {
    let m = 0;
    let w = 0;
    let bd = 0;
    for (const board of this.store.doc.boards) {
      if (board.col + board.cols > cols || board.row + board.rows > rows) bd++;
    }
    for (const inst of this.store.doc.modules) {
      const def = this.catalog.get(inst.moduleId);
      const b = def ? boundsOf(def, inst) : { col: inst.col, row: inst.row, cols: 1, rows: 1 };
      if (b.col + b.cols > cols || b.row + b.rows > rows) m++;
    }
    for (const wire of this.store.doc.wires) {
      if (wire.points.some(([x, y]) => x >= cols || y >= rows)) w++;
    }
    return { boards: bd, modules: m, wires: w };
  }

  // -- view ------------------------------------------------------------------

  renderView() {
    const { ui } = this.store;
    clear(this.viewBox);
    this.viewBox.append(
      heading('View'),
      toggle('Module labels', ui.showLabels, (v) => this.store.setUI({ showLabels: v })),
      toggle('Pin names', ui.showPinNames, (v) => this.store.setUI({ showPinNames: v })),
      toggle('Show other side (ghosted)', ui.showGhost, (v) => this.store.setUI({ showGhost: v })),
      toggle('Row / column rulers', ui.showRulers, (v) => this.store.setUI({ showRulers: v })),
      slider(
        'Module opacity', ui.moduleOpacity,
        // 'opacity' keeps main.js from rebuilding this panel on every input
        // event, which would tear the slider out from under the pointer.
        (v) => this.store.setUI({ moduleOpacity: v }, { reason: 'opacity' }),
        { min: 0.1, max: 1, step: 0.05 },
      ),
      el('p', {
        class: 'pbs-note',
        text: 'Fades module bodies so you can follow wires routed underneath. '
          + 'Pads, designators and pin names stay solid.',
      }),
    );
  }

  // -- selection -------------------------------------------------------------

  renderSelection() {
    clear(this.selBox);
    const sel = this.store.selected;
    if (!sel) {
      this.selBox.append(
        heading('Selection'),
        el('p', {
          class: 'pbs-empty',
          text: 'Nothing selected. Click a board, module or wire on the workspace.',
        }),
      );
      return;
    }
    if (sel.kind === 'module') this.renderModuleProps(sel.item);
    else if (sel.kind === 'board') this.renderBoardProps(sel.item);
    else this.renderWireProps(sel.item);
  }

  renderBoardProps(board) {
    const { workspace } = this.store.doc;
    this.selBox.append(heading('Perfboard'));

    const nameInput = el('input', {
      class: 'pbs-input', type: 'text', value: board.label || '',
      placeholder: 'Board 1', maxlength: '40',
    });
    on(nameInput, 'change', () => this.patchBoard(board.uid, 'Rename board', (b) => {
      b.label = nameInput.value.trim() || null;
    }));

    const preset = el('select', { class: 'pbs-select' });
    preset.append(el('option', { value: '', text: 'Custom size…' }));
    for (const p of BOARD_PRESETS) {
      preset.append(el('option', { value: p.id, text: `${p.label} — ${p.cols} × ${p.rows}` }));
    }
    preset.value = presetFor(board.cols, board.rows)?.id ?? '';
    on(preset, 'change', () => {
      const p = BOARD_PRESETS.find((x) => x.id === preset.value);
      if (p) this.resizeBoard(board.uid, p.cols, p.rows);
    });

    const colsInput = numberInput(board.cols, MIN_DIM, MAX_DIM,
      (v) => this.resizeBoard(board.uid, v, board.rows));
    const rowsInput = numberInput(board.rows, MIN_DIM, MAX_DIM,
      (v) => this.resizeBoard(board.uid, board.cols, v));

    const colInput = numberInput(board.col, 0, Math.max(0, workspace.cols - board.cols),
      (v) => this.moveBoard(board.uid, v, board.row));
    const rowInput = numberInput(board.row, 0, Math.max(0, workspace.rows - board.rows),
      (v) => this.moveBoard(board.uid, board.col, v));

    const colorSelect = el('select', { class: 'pbs-select' });
    for (const c of BOARD_COLORS) {
      colorSelect.append(el('option', { value: c.id, text: c.label }));
    }
    colorSelect.value = board.colorId;
    on(colorSelect, 'change', () => this.patchBoard(board.uid, 'Change board colour', (b) => {
      b.colorId = colorSelect.value;
    }));

    const del = el('button', { class: 'pbs-btn pbs-btn-danger pbs-btn-wide', type: 'button', text: 'Delete board' });
    on(del, 'click', () => this.canvas?.deleteItem({ kind: 'board', uid: board.uid }));

    this.selBox.append(
      field('Name', nameInput),
      field('Size preset', preset),
      el('div', { class: 'pbs-field-row' }, [
        field('Columns', colsInput),
        field('Rows', rowsInput),
      ]),
      el('div', { class: 'pbs-field-row' }, [
        field('Column', colInput),
        field('Row', rowInput),
      ]),
      field('Material', colorSelect),
      el('p', {
        class: 'pbs-note',
        text: `Top-left hole at ${holeName(board.col, board.row)} · `
          + `${mm(board.cols, workspace.pitchMm)} × ${mm(board.rows, workspace.pitchMm)} mm`,
      }),
      el('p', {
        class: 'pbs-note',
        text: 'Deleting a board leaves the parts and wiring on it where they are.',
      }),
      del,
    );
  }

  patchBoard(uid, label, mutate) {
    this.store.commit(label, (doc) => {
      const b = doc.boards.find((x) => x.uid === uid);
      if (!b) return false;
      mutate(b);
    });
  }

  resizeBoard(uid, cols, rows) {
    const c = clampDim(cols);
    const r = clampDim(rows);
    this.patchBoard(uid, 'Resize board', (b) => {
      if (b.cols === c && b.rows === r) return;
      b.cols = c;
      b.rows = r;
      const at = clampBoardToArea(this.store.doc.workspace, b);
      b.col = at.col;
      b.row = at.row;
    });
  }

  moveBoard(uid, col, row) {
    this.patchBoard(uid, 'Move board', (b) => {
      const at = clampBoardToArea(this.store.doc.workspace, { ...b, col, row });
      b.col = at.col;
      b.row = at.row;
    });
  }

  renderModuleProps(inst) {
    const def = this.catalog.get(inst.moduleId);
    this.selBox.append(heading('Module'));

    if (!def) {
      this.selBox.append(
        el('p', { class: 'pbs-warn', text: `"${inst.moduleId}" is not in the catalog.` }),
        this.deleteButton(),
      );
      return;
    }

    const fp = footprintOf(def, inst);
    const b = boundsOf(def, inst);

    const labelInput = el('input', {
      class: 'pbs-input', type: 'text', value: inst.label || '',
      placeholder: def.designator ? `${def.designator}1` : 'U1', maxlength: '16',
    });
    on(labelInput, 'change', () => {
      const v = labelInput.value.trim();
      this.patch('Rename module', (m) => { m.label = v || null; });
    });

    const rotSelect = el('select', { class: 'pbs-select' });
    for (const r of [0, 90, 180, 270]) {
      rotSelect.append(el('option', { value: String(r), text: `${r}°` }));
    }
    rotSelect.value = String(inst.rotation || 0);
    on(rotSelect, 'change', () => {
      const target = Number(rotSelect.value);
      this.canvas?.rotateSelection(target - (inst.rotation || 0));
    });

    const sideSelect = el('select', { class: 'pbs-select' });
    sideSelect.append(
      el('option', { value: 'front', text: 'Component side (front)' }),
      el('option', { value: 'solder', text: 'Solder side (back)' }),
    );
    sideSelect.value = inst.side;
    on(sideSelect, 'change', () => {
      const v = sideSelect.value;
      this.patch('Change side', (m) => { m.side = v; });
    });

    const colInput = numberInput(inst.col, 0, this.store.doc.workspace.cols - 1,
      (v) => this.patch('Move module', (m) => { m.col = v; }));
    const rowInput = numberInput(inst.row, 0, this.store.doc.workspace.rows - 1,
      (v) => this.patch('Move module', (m) => { m.row = v; }));

    this.selBox.append(
      el('div', { class: 'pbs-sel-head' }, [
        el('span', { class: 'pbs-sel-art' }, [modulePreview(def, { width: 56, height: 56 })]),
        el('div', {}, [
          el('div', { class: 'pbs-sel-name', text: def.name }),
          el('div', { class: 'pbs-sel-sub', text: def.subtitle || def.category }),
        ]),
      ]),
      field('Reference', labelInput),
      el('div', { class: 'pbs-field-row' }, [
        field('Rotation', rotSelect),
        field('Side', sideSelect),
      ]),
      el('div', { class: 'pbs-field-row' }, [
        field('Column', colInput),
        field('Row', rowInput),
      ]),
    );

    if (def.resize) {
      const span = inst.span ?? def.footprint[def.resize.axis];
      const spanInput = numberInput(span, def.resize.min, def.resize.max, (v) => {
        this.patch('Resize module', (m) => { m.span = v; });
      });
      this.selBox.append(field(
        `Span (${def.resize.axis === 'cols' ? 'holes across' : 'holes down'})`,
        spanInput,
      ));
    }

    this.selBox.append(el('p', {
      class: 'pbs-note',
      text: `Anchor ${holeName(inst.col, inst.row)} · occupies ${b.cols} × ${b.rows} holes`
        + ` · footprint ${fp.cols} × ${fp.rows}`,
    }));

    if (def.datasheet) {
      this.selBox.append(el('p', { class: 'pbs-note' }, [
        el('a', { href: def.datasheet, target: '_blank', rel: 'noopener noreferrer', text: 'Datasheet ↗' }),
      ]));
    }

    const pins = pinCells(def, inst).filter((p) => p.name);
    if (pins.length) {
      const table = el('div', { class: 'pbs-pin-table' });
      for (const p of pins) {
        table.append(
          el('span', { class: `pbs-pin-dot pbs-pin-${p.type || 'signal'}` }),
          el('span', { class: 'pbs-pin-name', text: p.name }),
          el('span', { class: 'pbs-pin-hole', text: holeName(p.col, p.row) }),
        );
      }
      this.selBox.append(
        el('details', { class: 'pbs-details' }, [
          el('summary', { text: `Pinout (${pins.length})` }),
          table,
        ]),
      );
    }

    this.selBox.append(this.deleteButton());
  }

  renderWireProps(wire) {
    this.selBox.append(heading('Wire'));

    const swatches = el('div', { class: 'pbs-swatches' });
    for (const c of WIRE_COLORS) {
      const b = el('button', {
        type: 'button',
        class: `pbs-swatch${wire.color.toLowerCase() === c.hex.toLowerCase() ? ' is-active' : ''}`,
        style: `--swatch:${c.hex}`,
        title: c.label,
        'aria-label': c.label,
      });
      on(b, 'click', () => this.patchWire('Change wire colour', (w) => { w.color = c.hex; }));
      swatches.append(b);
    }

    const custom = el('input', { type: 'color', class: 'pbs-color', value: normalizeHex(wire.color) });
    on(custom, 'change', () => this.patchWire('Change wire colour', (w) => { w.color = custom.value; }));

    const gaugeSelect = el('select', { class: 'pbs-select' });
    for (const g of WIRE_GAUGES) gaugeSelect.append(el('option', { value: g.id, text: g.label }));
    gaugeSelect.value = wire.gauge;
    on(gaugeSelect, 'change', () => {
      const v = gaugeSelect.value;
      this.patchWire('Change wire gauge', (w) => { w.gauge = v; });
    });

    const sideSelect = el('select', { class: 'pbs-select' });
    sideSelect.append(
      el('option', { value: 'front', text: 'Component side (front)' }),
      el('option', { value: 'solder', text: 'Solder side (back)' }),
    );
    sideSelect.value = wire.side;
    on(sideSelect, 'change', () => {
      const v = sideSelect.value;
      this.patchWire('Change side', (w) => { w.side = v; });
    });

    const path = wire.points.map(([c, r]) => holeName(c, r)).join(' → ');

    this.selBox.append(
      field('Colour', el('div', { class: 'pbs-color-row' }, [swatches, custom])),
      el('div', { class: 'pbs-field-row' }, [
        field('Gauge', gaugeSelect),
        field('Side', sideSelect),
      ]),
      el('p', { class: 'pbs-note', text: `${wire.points.length} points · ${length(wire)} holes long` }),
      el('p', { class: 'pbs-path', text: path }),
      this.deleteButton(),
    );
  }

  deleteButton() {
    const b = el('button', { type: 'button', class: 'pbs-btn pbs-btn-danger', text: 'Delete (Del)' });
    on(b, 'click', () => this.canvas?.deleteSelection());
    return b;
  }

  patch(label, fn) {
    const sel = this.store.ui.selection;
    if (!sel || sel.kind !== 'module') return;
    this.store.commit(label, (doc) => {
      const m = doc.modules.find((x) => x.uid === sel.uid);
      if (!m) return false;
      fn(m);
    });
  }

  patchWire(label, fn) {
    const sel = this.store.ui.selection;
    if (!sel || sel.kind !== 'wire') return;
    this.store.commit(label, (doc) => {
      const w = doc.wires.find((x) => x.uid === sel.uid);
      if (!w) return false;
      fn(w);
    });
  }
}

// -- small builders ----------------------------------------------------------

function heading(text) {
  return el('h2', { class: 'pbs-panel-heading', text });
}

function field(label, control) {
  return el('label', { class: 'pbs-field' }, [
    el('span', { class: 'pbs-field-label', text: label }),
    control,
  ]);
}

function toggle(label, checked, onChange) {
  const input = el('input', { type: 'checkbox', class: 'pbs-checkbox' });
  input.checked = !!checked;
  on(input, 'change', () => onChange(input.checked));
  return el('label', { class: 'pbs-toggle' }, [input, el('span', { text: label })]);
}

/**
 * Labelled range input with a live percentage readout. `onInput` fires
 * continuously while dragging, so it must be cheap.
 */
function slider(label, value, onInput, { min, max, step }) {
  const pct = (v) => `${Math.round(v * 100)}%`;
  const readout = el('span', { class: 'pbs-field-value', text: pct(value) });
  const input = el('input', {
    class: 'pbs-range', type: 'range',
    min: String(min), max: String(max), step: String(step), value: String(value),
    'aria-label': label,
  });
  on(input, 'input', () => {
    const v = Number(input.value);
    readout.textContent = pct(v);
    onInput(v);
  });
  return el('label', { class: 'pbs-field' }, [
    el('span', { class: 'pbs-field-label pbs-field-label-row' }, [
      el('span', { text: label }),
      readout,
    ]),
    input,
  ]);
}

function numberInput(value, min, max, onCommit) {
  const input = el('input', {
    class: 'pbs-input pbs-input-num', type: 'number',
    min: String(min), max: String(max), step: '1', value: String(value),
  });
  const commit = () => {
    const v = Number.parseInt(input.value, 10);
    if (!Number.isFinite(v)) { input.value = String(value); return; }
    const clamped = Math.min(max, Math.max(min, v));
    input.value = String(clamped);
    if (clamped !== value) onCommit(clamped);
  };
  on(input, 'change', commit);
  on(input, 'keydown', (e) => { if (e.key === 'Enter') { e.preventDefault(); commit(); } });
  return input;
}

function clampDim(v) {
  const n = Math.round(Number(v));
  if (!Number.isFinite(n)) return MIN_DIM;
  return Math.min(MAX_DIM, Math.max(MIN_DIM, n));
}

function clampWorkspace(v) {
  const n = Math.round(Number(v));
  if (!Number.isFinite(n)) return MIN_WORKSPACE;
  return Math.min(MAX_WORKSPACE, Math.max(MIN_WORKSPACE, n));
}

function boardFill(colorId) {
  return (BOARD_COLORS.find((c) => c.id === colorId) || BOARD_COLORS[0]).fill;
}

function mm(holes, pitch) {
  return ((holes - 1) * pitch).toFixed(1);
}

function length(wire) {
  let total = 0;
  for (let i = 1; i < wire.points.length; i++) {
    total += Math.hypot(
      wire.points[i][0] - wire.points[i - 1][0],
      wire.points[i][1] - wire.points[i - 1][1],
    );
  }
  return total.toFixed(1);
}

function normalizeHex(hex) {
  if (/^#[0-9a-f]{6}$/i.test(hex)) return hex;
  if (/^#[0-9a-f]{3}$/i.test(hex)) {
    return `#${hex.slice(1).split('').map((c) => c + c).join('')}`;
  }
  return '#e02b25';
}
