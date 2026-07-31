/**
 * Pointer and wheel interaction on the workspace.
 *
 * Drags are kept out of the document until pointer-up so a single move produces
 * exactly one undo entry.
 */

import { on } from '../util/dom.js';
import { boardAt, boardCovers, holeName, inBounds, localHoleName } from '../core/board.js';
import {
  boundsOf, clampBoardToArea, clampToArea, distToPolyline, normalizeRotation,
} from '../core/geometry.js';
import { makeInstance, makeWire } from '../core/store.js';

const WIRE_PICK_RADIUS = 0.35;

export class CanvasController {
  constructor(renderer, store, catalog, { onStatus } = {}) {
    this.r = renderer;
    this.store = store;
    this.catalog = catalog;
    this.onStatus = onStatus || (() => {});

    this.pan = null;
    this.drag = null;
    this.spaceDown = false;
    this.frame = null;

    const svgEl = renderer.svg;
    on(svgEl, 'pointerdown', (e) => this.onPointerDown(e));
    on(svgEl, 'pointermove', (e) => this.onPointerMove(e));
    on(window, 'pointerup', (e) => this.onPointerUp(e));
    on(svgEl, 'pointerleave', () => this.setHover(null));
    on(svgEl, 'wheel', (e) => this.onWheel(e), { passive: false });
    on(svgEl, 'dblclick', (e) => this.onDoubleClick(e));
    on(svgEl, 'contextmenu', (e) => this.onContextMenu(e));
    on(window, 'keydown', (e) => { if (e.code === 'Space') this.spaceDown = true; });
    on(window, 'keyup', (e) => { if (e.code === 'Space') this.spaceDown = false; });
    on(window, 'resize', () => this.onResize());
  }

  onResize() {
    // Keep the framing sane when the window changes shape.
    const v = this.store.ui.view;
    if (!v) return;
    const rect = this.r.svg.getBoundingClientRect();
    if (!rect.width || !rect.height) return;
    const aspect = rect.width / rect.height;
    const cx = v.x + v.w / 2;
    const cy = v.y + v.h / 2;
    const h = v.w / aspect;
    this.store.setUI({ view: { x: cx - v.w / 2, y: cy - h / 2, w: v.w, h } }, { silent: true });
    this.r.applyView();
  }

  // -- helpers ---------------------------------------------------------------

  setHover(hole) {
    const cur = this.store.ui.hover;
    const same = (!cur && !hole) || (cur && hole && cur.col === hole.col && cur.row === hole.row);
    if (same) return;
    this.store.setUI({ hover: hole }, { reason: 'hover' });
  }

  /** The topmost interactive item under the event target, if any. */
  pickFromTarget(e) {
    const node = e.target instanceof Element ? e.target.closest('[data-uid]') : null;
    if (!node) return null;
    const uid = node.dataset.uid;
    if (uid === '__preview') return null;
    if (node.classList.contains('is-ghost')) return null;
    if (node.classList.contains('pbs-module')) return { kind: 'module', uid };
    if (node.classList.contains('pbs-wire')) return { kind: 'wire', uid };
    if (node.classList.contains('pbs-board')) return { kind: 'board', uid };
    return null;
  }

  /**
   * Fallback geometric pick, used when the DOM target is the bare desk.
   * Boards come last: they are the substrate, so anything sitting on one wins.
   */
  pickAt(gridX, gridY) {
    const { doc, ui } = this.store;
    for (let i = doc.modules.length - 1; i >= 0; i--) {
      const m = doc.modules[i];
      if (m.side !== ui.side) continue;
      const def = this.catalog.get(m.moduleId);
      const b = def ? boundsOf(def, m) : { col: m.col, row: m.row, cols: 1, rows: 1 };
      if (gridX >= b.col - 0.5 && gridX <= b.col + b.cols - 0.5
        && gridY >= b.row - 0.5 && gridY <= b.row + b.rows - 0.5) {
        return { kind: 'module', uid: m.uid };
      }
    }
    for (let i = doc.wires.length - 1; i >= 0; i--) {
      const w = doc.wires[i];
      if (w.side !== ui.side) continue;
      if (distToPolyline(gridX, gridY, w.points) <= WIRE_PICK_RADIUS) {
        return { kind: 'wire', uid: w.uid };
      }
    }
    const board = boardAt(doc.boards, Math.round(gridX), Math.round(gridY));
    if (board) return { kind: 'board', uid: board.uid };
    return null;
  }

  // -- pointer ---------------------------------------------------------------

  onPointerDown(e) {
    if (e.button === 1 || (e.button === 0 && this.spaceDown)) {
      this.pan = { x: e.clientX, y: e.clientY };
      this.r.svg.setPointerCapture?.(e.pointerId);
      this.r.svg.classList.add('is-panning');
      e.preventDefault();
      return;
    }
    if (e.button !== 0) return;

    const { ui } = this.store;
    const g = this.r.clientToGrid(e.clientX, e.clientY);
    const hole = this.r.clientToHole(e.clientX, e.clientY, 0.9);

    if (ui.placing) {
      if (hole) this.placeModule(hole);
      return;
    }

    if (ui.tool === 'wire') {
      if (hole) this.extendWire(hole);
      return;
    }

    if (ui.tool === 'erase') {
      const pick = this.pickFromTarget(e) || this.pickAt(g.x, g.y);
      if (pick) this.deleteItem(pick);
      return;
    }

    // select tool
    const pick = this.pickFromTarget(e) || this.pickAt(g.x, g.y);
    if (!pick) {
      this.store.setUI({ selection: null });
      return;
    }
    this.store.setUI({ selection: pick });

    // Modules and boards both drag; wires do not (they are edited point-wise).
    const item = pick.kind === 'module' ? this.store.moduleByUid(pick.uid)
      : pick.kind === 'board' ? this.store.boardByUid(pick.uid)
        : null;
    if (item) {
      this.drag = {
        kind: pick.kind,
        uid: item.uid,
        offCol: item.col - g.x,
        offRow: item.row - g.y,
        origCol: item.col,
        origRow: item.row,
        moved: false,
      };
      this.r.svg.setPointerCapture?.(e.pointerId);
    }
  }

  onPointerMove(e) {
    if (this.pan) {
      const v = this.store.ui.view;
      const rect = this.r.svg.getBoundingClientRect();
      const scale = v.w / rect.width;
      const dx = (e.clientX - this.pan.x) * scale;
      const dy = (e.clientY - this.pan.y) * scale;
      this.pan = { x: e.clientX, y: e.clientY };
      // Panning in display space; the mirror does not affect the viewBox.
      this.store.setUI({ view: { ...v, x: v.x - dx, y: v.y - dy } }, { silent: true });
      this.r.applyView();
      return;
    }

    const hole = this.r.clientToHole(e.clientX, e.clientY, 0.9);
    this.reportStatus(hole);

    if (this.drag) {
      const g = this.r.clientToGrid(e.clientX, e.clientY);
      const at = this.dragTarget(g);
      if (!at) return;
      if (at.col !== this.drag.col || at.row !== this.drag.row) {
        this.drag.col = at.col;
        this.drag.row = at.row;
        this.drag.moved = at.col !== this.drag.origCol || at.row !== this.drag.origRow;
        this.store.setUI({ drag: { ...this.drag } }, { reason: 'drag' });
      }
      return;
    }

    this.setHover(hole);
  }

  /** Where the dragged item wants to land, clamped inside the workspace. */
  dragTarget(g) {
    const { workspace } = this.store.doc;
    const want = {
      col: Math.round(g.x + this.drag.offCol),
      row: Math.round(g.y + this.drag.offRow),
    };
    if (this.drag.kind === 'board') {
      const b = this.store.boardByUid(this.drag.uid);
      return b ? clampBoardToArea(workspace, { ...b, ...want }) : null;
    }
    const m = this.store.moduleByUid(this.drag.uid);
    if (!m) return null;
    const def = this.catalog.get(m.moduleId);
    return def ? clampToArea(workspace, def, { ...m, ...want }) : want;
  }

  onPointerUp(e) {
    if (this.pan) {
      this.pan = null;
      this.r.svg.classList.remove('is-panning');
      this.r.svg.releasePointerCapture?.(e.pointerId);
      return;
    }
    if (!this.drag) return;
    const d = this.drag;
    this.drag = null;
    this.store.setUI({ drag: null }, { silent: true });
    if (!d.moved || !Number.isFinite(d.col)) {
      this.store.emit('ui');
      return;
    }
    const what = d.kind === 'board' ? 'board' : 'module';
    this.store.commit(`Move ${what}`, (doc) => {
      const list = d.kind === 'board' ? doc.boards : doc.modules;
      const item = list.find((x) => x.uid === d.uid);
      if (!item) return false;
      item.col = d.col;
      item.row = d.row;
    });
  }

  onDoubleClick(e) {
    if (this.store.ui.tool === 'wire') {
      e.preventDefault();
      this.finishWire();
    }
  }

  onContextMenu(e) {
    e.preventDefault();
    const { ui } = this.store;
    if (ui.wireDraft) { this.cancelWire(); return; }
    if (ui.placing) { this.store.setUI({ placing: null }); return; }
  }

  onWheel(e) {
    e.preventDefault();
    const factor = Math.exp(-e.deltaY * 0.0015);
    this.r.zoomAt(e.clientX, e.clientY, factor);
  }

  // -- actions ---------------------------------------------------------------

  placeModule(hole) {
    const { ui } = this.store;
    const def = this.catalog.get(ui.placing);
    if (!def) return;
    const inst = makeInstance(def, {
      col: hole.col,
      row: hole.row,
      rotation: normalizeRotation(ui.placingRotation),
      side: ui.side,
      label: this.store.nextDesignator(def),
    });
    const { workspace } = this.store.doc;
    const at = clampToArea(workspace, def, inst);
    inst.col = at.col;
    inst.row = at.row;

    const b = boundsOf(def, inst);
    if (b.cols > workspace.cols || b.rows > workspace.rows) {
      this.onStatus(`${def.name} is larger than the workspace`, 'warn');
      return;
    }

    this.store.commit(`Place ${def.name}`, (doc) => { doc.modules.push(inst); });
    this.store.setUI({ selection: { kind: 'module', uid: inst.uid } });
    this.onStatus(`Placed ${def.name} at ${this.describeHole(inst.col, inst.row)}`);
  }

  extendWire(hole) {
    const { ui } = this.store;
    const draft = ui.wireDraft;
    if (!draft) {
      this.store.setUI({
        wireDraft: { points: [[hole.col, hole.row]], color: ui.wireColor, gauge: ui.wireGauge },
      });
      this.onStatus(`Wire from ${this.describeHole(hole.col, hole.row)} — click to add bends, double-click or Enter to finish`);
      return;
    }
    const last = draft.points.at(-1);
    if (last[0] === hole.col && last[1] === hole.row) {
      this.finishWire();
      return;
    }
    const points = [...draft.points, [hole.col, hole.row]];
    this.store.setUI({ wireDraft: { ...draft, points } });
  }

  finishWire() {
    const draft = this.store.ui.wireDraft;
    if (!draft) return;
    if (draft.points.length < 2) { this.cancelWire(); return; }
    const wire = makeWire({
      points: draft.points,
      color: draft.color,
      gauge: draft.gauge,
      side: this.store.ui.side,
    });
    this.store.setUI({ wireDraft: null }, { silent: true });
    this.store.commit('Add wire', (doc) => { doc.wires.push(wire); });
    this.store.setUI({ selection: { kind: 'wire', uid: wire.uid } });
    const a = this.describeHole(wire.points[0][0], wire.points[0][1]);
    const b = this.describeHole(wire.points.at(-1)[0], wire.points.at(-1)[1]);
    this.onStatus(`Wire ${a} → ${b} on the ${wire.side} side`);
  }

  cancelWire() {
    if (!this.store.ui.wireDraft) return;
    this.store.setUI({ wireDraft: null });
    this.onStatus('Wire cancelled');
  }

  /** Remove the last point of the wire being drawn. */
  backspaceWire() {
    const draft = this.store.ui.wireDraft;
    if (!draft) return false;
    const points = draft.points.slice(0, -1);
    if (!points.length) { this.cancelWire(); return true; }
    this.store.setUI({ wireDraft: { ...draft, points } });
    return true;
  }

  deleteItem(pick) {
    if (pick.kind === 'module') {
      const m = this.store.moduleByUid(pick.uid);
      const def = m && this.catalog.get(m.moduleId);
      this.store.commit(`Delete ${def?.name || 'module'}`, (doc) => {
        const i = doc.modules.findIndex((x) => x.uid === pick.uid);
        if (i < 0) return false;
        doc.modules.splice(i, 1);
      });
    } else if (pick.kind === 'board') {
      // Deleting a board leaves whatever sat on it in place: the parts and
      // wiring are still real, they have just lost their substrate.
      const b = this.store.boardByUid(pick.uid);
      this.store.commit(`Delete ${b?.label || 'board'}`, (doc) => {
        const i = doc.boards.findIndex((x) => x.uid === pick.uid);
        if (i < 0) return false;
        doc.boards.splice(i, 1);
      });
    } else {
      this.store.commit('Delete wire', (doc) => {
        const i = doc.wires.findIndex((x) => x.uid === pick.uid);
        if (i < 0) return false;
        doc.wires.splice(i, 1);
      });
    }
    this.store.setUI({ selection: null }, { silent: true });
  }

  deleteSelection() {
    const sel = this.store.ui.selection;
    if (!sel) return false;
    this.deleteItem(sel);
    return true;
  }

  rotateSelection(delta = 90) {
    const { ui } = this.store;
    if (ui.placing) {
      this.store.setUI({ placingRotation: normalizeRotation(ui.placingRotation + delta) });
      return true;
    }
    const sel = ui.selection;
    if (!sel || sel.kind !== 'module') return false;
    return this.store.commit('Rotate module', (doc) => {
      const m = doc.modules.find((x) => x.uid === sel.uid);
      if (!m) return false;
      const def = this.catalog.get(m.moduleId);
      m.rotation = normalizeRotation(m.rotation + delta);
      if (def) {
        const at = clampToArea(doc.workspace, def, m);
        m.col = at.col;
        m.row = at.row;
      }
    });
  }

  /** Move the selected module or board by whole holes (arrow keys). */
  nudgeSelection(dCol, dRow) {
    const sel = this.store.ui.selection;
    if (!sel || sel.kind === 'wire') return false;
    const what = sel.kind === 'board' ? 'board' : 'module';
    return this.store.commit(`Move ${what}`, (doc) => {
      const list = sel.kind === 'board' ? doc.boards : doc.modules;
      const item = list.find((x) => x.uid === sel.uid);
      if (!item) return false;
      const want = { ...item, col: item.col + dCol, row: item.row + dRow };
      let at;
      if (sel.kind === 'board') {
        at = clampBoardToArea(doc.workspace, want);
      } else {
        const def = this.catalog.get(item.moduleId);
        at = def ? clampToArea(doc.workspace, def, want) : want;
      }
      if (at.col === item.col && at.row === item.row) return false;
      item.col = at.col;
      item.row = at.row;
    });
  }

  /** Send the selected item to the other side. Boards have no side. */
  flipSelectionSide() {
    const sel = this.store.ui.selection;
    if (!sel || sel.kind === 'board') return false;
    return this.store.commit('Change side', (doc) => {
      const list = sel.kind === 'module' ? doc.modules : doc.wires;
      const item = list.find((x) => x.uid === sel.uid);
      if (!item) return false;
      item.side = item.side === 'front' ? 'solder' : 'front';
    });
  }

  /**
   * Workspace hole name, plus the board-local one when the hole is on a board —
   * "AB14 · Board 1 C6". Layouts are addressed globally now, but people read
   * their own board in its own numbering.
   */
  describeHole(col, row) {
    const global = holeName(col, row);
    const board = boardAt(this.store.doc.boards, col, row);
    if (!board) return global;
    const local = localHoleName(board, col, row);
    return `${global} · ${board.label || 'board'} ${local}`;
  }

  reportStatus(hole) {
    if (!hole) { this.onStatus('', 'coords'); return; }
    const { doc } = this.store;
    if (!inBounds(doc.workspace, hole.col, hole.row)) { this.onStatus('', 'coords'); return; }
    this.onStatus(this.describeHole(hole.col, hole.row), 'coords');
  }
}
