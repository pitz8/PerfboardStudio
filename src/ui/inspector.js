/**
 * Right-hand panel: board setup, view options, and properties of whatever is
 * selected.
 */

import { clear, el, on } from '../util/dom.js';
import {
  BOARD_COLORS, BOARD_PRESETS, MAX_DIM, MIN_DIM, holeName, presetFor,
} from '../core/board.js';
import { WIRE_COLORS, WIRE_GAUGES } from '../core/store.js';
import { boundsOf, footprintOf, pinCells } from '../core/geometry.js';
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

  // -- board -----------------------------------------------------------------

  renderBoard() {
    const { board } = this.store.doc;
    clear(this.boardBox);

    const preset = el('select', { class: 'pbs-select' });
    preset.append(el('option', { value: '', text: 'Custom size…' }));
    for (const p of BOARD_PRESETS) {
      preset.append(el('option', {
        value: p.id,
        text: `${p.label} — ${p.cols} × ${p.rows}`,
      }));
    }
    preset.value = presetFor(board.cols, board.rows)?.id ?? '';
    on(preset, 'change', () => {
      const p = BOARD_PRESETS.find((x) => x.id === preset.value);
      if (p) this.resizeBoard(p.cols, p.rows);
    });

    const colsInput = numberInput(board.cols, MIN_DIM, MAX_DIM, (v) => this.resizeBoard(v, board.rows));
    const rowsInput = numberInput(board.rows, MIN_DIM, MAX_DIM, (v) => this.resizeBoard(board.cols, v));

    const colorSelect = el('select', { class: 'pbs-select' });
    for (const c of BOARD_COLORS) {
      colorSelect.append(el('option', { value: c.id, text: c.label }));
    }
    colorSelect.value = board.colorId;
    on(colorSelect, 'change', () => {
      this.store.commit('Change board colour', (doc) => { doc.board.colorId = colorSelect.value; });
    });

    const nameInput = el('input', {
      class: 'pbs-input', type: 'text', value: this.store.doc.name,
      'aria-label': 'Design name', maxlength: '80',
    });
    on(nameInput, 'change', () => {
      const v = nameInput.value.trim() || 'Untitled design';
      this.store.commit('Rename design', (doc) => { doc.name = v; });
    });

    this.boardBox.append(
      heading('Board'),
      field('Design name', nameInput),
      field('Size preset', preset),
      el('div', { class: 'pbs-field-row' }, [
        field('Columns (A…)', colsInput),
        field('Rows (1…)', rowsInput),
      ]),
      field('Material', colorSelect),
      el('p', {
        class: 'pbs-note',
        text: `${board.cols * board.rows} holes · ${board.pitchMm} mm pitch · `
          + `${mm(board.cols, board.pitchMm)} × ${mm(board.rows, board.pitchMm)} mm grid`,
      }),
    );
  }

  resizeBoard(cols, rows) {
    const c = clampDim(cols);
    const r = clampDim(rows);
    const { board } = this.store.doc;
    if (c === board.cols && r === board.rows) return;

    // Warn before shrinking away someone's work rather than silently dropping it.
    const lost = this.itemsOutside(c, r);
    if (lost.modules || lost.wires) {
      const parts = [];
      if (lost.modules) parts.push(`${lost.modules} module(s)`);
      if (lost.wires) parts.push(`${lost.wires} wire(s)`);
      const ok = window.confirm(
        `Shrinking to ${c} × ${r} holes leaves ${parts.join(' and ')} off the board.\n\n`
        + 'They will be removed. Continue?',
      );
      if (!ok) { this.renderBoard(); return; }
    }

    this.store.commit('Resize board', (doc) => {
      doc.board.cols = c;
      doc.board.rows = r;
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
    for (const inst of this.store.doc.modules) {
      const def = this.catalog.get(inst.moduleId);
      const b = def ? boundsOf(def, inst) : { col: inst.col, row: inst.row, cols: 1, rows: 1 };
      if (b.col + b.cols > cols || b.row + b.rows > rows) m++;
    }
    for (const wire of this.store.doc.wires) {
      if (wire.points.some(([x, y]) => x >= cols || y >= rows)) w++;
    }
    return { modules: m, wires: w };
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
    );
  }

  // -- selection -------------------------------------------------------------

  renderSelection() {
    clear(this.selBox);
    const sel = this.store.selected;
    if (!sel) {
      this.selBox.append(
        heading('Selection'),
        el('p', { class: 'pbs-empty', text: 'Nothing selected. Click a module or wire on the board.' }),
      );
      return;
    }
    if (sel.kind === 'module') this.renderModuleProps(sel.item);
    else this.renderWireProps(sel.item);
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

    const colInput = numberInput(inst.col, 0, this.store.doc.board.cols - 1,
      (v) => this.patch('Move module', (m) => { m.col = v; }));
    const rowInput = numberInput(inst.row, 0, this.store.doc.board.rows - 1,
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
