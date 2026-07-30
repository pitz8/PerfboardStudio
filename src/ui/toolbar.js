/**
 * Top bar: file actions, undo/redo, side flip, tools, wire colour, zoom.
 */

import { el, on } from '../util/dom.js';
import { WIRE_COLORS, WIRE_GAUGES } from '../core/store.js';

export class Toolbar {
  constructor(root, store, { actions, onStatus } = {}) {
    this.root = root;
    this.store = store;
    this.actions = actions;
    this.onStatus = onStatus || (() => {});
    this.nodes = {};
    this.build();
    this.sync();
  }

  build() {
    const a = this.actions;

    this.nodes.undo = iconButton('↶', 'Undo (Ctrl+Z)', () => a.undo());
    this.nodes.redo = iconButton('↷', 'Redo (Ctrl+Shift+Z)', () => a.redo());

    this.nodes.front = tabButton('Front', 'Component side — Tab to flip', () => a.setSide('front'));
    this.nodes.solder = tabButton('Solder', 'Solder side (mirrored) — Tab to flip', () => a.setSide('solder'));

    this.nodes.select = tabButton('▣ Select', 'Select and move (V)', () => a.setTool('select'));
    this.nodes.wire = tabButton('⌇ Wire', 'Draw wires (W)', () => a.setTool('wire'));
    this.nodes.erase = tabButton('⌫ Erase', 'Click to delete (E)', () => a.setTool('erase'));

    this.nodes.swatches = el('div', { class: 'pbs-swatches pbs-swatches-inline' });
    for (const c of WIRE_COLORS) {
      const b = el('button', {
        type: 'button', class: 'pbs-swatch', style: `--swatch:${c.hex}`,
        title: `${c.label} wire`, 'aria-label': `${c.label} wire`,
        dataset: { hex: c.hex },
      });
      on(b, 'click', () => a.setWireColor(c.hex));
      this.nodes.swatches.append(b);
    }
    this.nodes.customColor = el('input', {
      type: 'color', class: 'pbs-color', value: WIRE_COLORS[0].hex,
      title: 'Custom wire colour',
    });
    on(this.nodes.customColor, 'change', () => a.setWireColor(this.nodes.customColor.value));

    this.nodes.gauge = el('select', { class: 'pbs-select pbs-select-sm', title: 'Wire gauge' });
    for (const g of WIRE_GAUGES) {
      this.nodes.gauge.append(el('option', { value: g.id, text: g.label }));
    }
    on(this.nodes.gauge, 'change', () => a.setWireGauge(this.nodes.gauge.value));

    const fileMenu = this.menu('File', [
      ['New design', 'Ctrl+N', () => a.newDesign()],
      ['Open…', 'Ctrl+O', () => a.open()],
      ['Save as JSON', 'Ctrl+S', () => a.save()],
      null,
      ['Export SVG', '', () => a.exportSvg()],
      ['Export PNG', '', () => a.exportPng()],
      ['Export bill of materials', '', () => a.exportBom()],
    ]);

    const helpBtn = iconButton('?', 'Keyboard shortcuts (F1)', () => a.showHelp());

    this.nodes.title = el('span', { class: 'pbs-doc-name' });
    this.nodes.dirty = el('span', { class: 'pbs-dirty', title: 'Unsaved changes' });

    this.root.append(
      el('div', { class: 'pbs-brand' }, [
        el('span', { class: 'pbs-logo', text: '▦' }),
        el('span', { class: 'pbs-brand-name', text: 'Perfboard Studio' }),
      ]),
      fileMenu,
      group([this.nodes.undo, this.nodes.redo]),
      el('div', { class: 'pbs-doc' }, [this.nodes.title, this.nodes.dirty]),
      el('div', { class: 'pbs-spacer' }),
      group([this.nodes.select, this.nodes.wire, this.nodes.erase], 'Tool'),
      el('div', { class: 'pbs-wire-controls' }, [
        this.nodes.swatches, this.nodes.customColor, this.nodes.gauge,
      ]),
      group([this.nodes.front, this.nodes.solder], 'Side'),
      group([
        iconButton('⊕', 'Zoom in (+)', () => a.zoom(1.25)),
        iconButton('⊖', 'Zoom out (−)', () => a.zoom(0.8)),
        iconButton('⤢', 'Fit board (0)', () => a.fit()),
      ]),
      helpBtn,
    );
  }

  menu(label, items) {
    const list = el('div', { class: 'pbs-menu-list', role: 'menu' });
    for (const item of items) {
      if (!item) { list.append(el('hr', { class: 'pbs-menu-sep' })); continue; }
      const [text, hint, fn] = item;
      const b = el('button', { type: 'button', class: 'pbs-menu-item', role: 'menuitem' }, [
        el('span', { text }),
        hint ? el('kbd', { text: hint }) : null,
      ]);
      on(b, 'click', () => { details.open = false; fn(); });
      list.append(b);
    }
    const details = el('details', { class: 'pbs-menu' }, [
      el('summary', { class: 'pbs-menu-summary', text: label }),
      list,
    ]);
    on(document, 'click', (e) => {
      if (details.open && !details.contains(e.target)) details.open = false;
    });
    return details;
  }

  sync() {
    const { ui, doc } = this.store;
    this.nodes.undo.disabled = !this.store.canUndo;
    this.nodes.redo.disabled = !this.store.canRedo;
    this.nodes.undo.title = this.store.canUndo ? `Undo ${this.store.undoLabel} (Ctrl+Z)` : 'Nothing to undo';
    this.nodes.redo.title = this.store.canRedo ? `Redo ${this.store.redoLabel} (Ctrl+Shift+Z)` : 'Nothing to redo';

    this.nodes.front.classList.toggle('is-active', ui.side === 'front');
    this.nodes.solder.classList.toggle('is-active', ui.side === 'solder');
    this.root.classList.toggle('is-solder', ui.side === 'solder');

    for (const t of ['select', 'wire', 'erase']) {
      this.nodes[t].classList.toggle('is-active', ui.tool === t);
    }

    for (const b of this.nodes.swatches.children) {
      b.classList.toggle('is-active', b.dataset.hex.toLowerCase() === ui.wireColor.toLowerCase());
    }
    if (/^#[0-9a-f]{6}$/i.test(ui.wireColor)) this.nodes.customColor.value = ui.wireColor;
    this.nodes.gauge.value = ui.wireGauge;

    this.nodes.title.textContent = doc.name;
    this.nodes.dirty.textContent = ui.dirty ? '●' : '';
  }
}

function group(children, label) {
  return el('div', { class: 'pbs-group', ...(label ? { 'aria-label': label } : {}) }, children);
}

function iconButton(glyph, title, onClick) {
  const b = el('button', { type: 'button', class: 'pbs-icon-btn', title, 'aria-label': title, text: glyph });
  on(b, 'click', onClick);
  return b;
}

function tabButton(text, title, onClick) {
  const b = el('button', { type: 'button', class: 'pbs-tab-btn', title, text });
  on(b, 'click', onClick);
  return b;
}
