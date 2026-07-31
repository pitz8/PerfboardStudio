/**
 * SVG renderer for the workspace.
 *
 * Layering
 * --------
 * Everything is drawn in "unit" space (1 unit = one hole pitch) and framed with
 * the SVG viewBox, so zooming scales strokes and text along with the geometry.
 *
 *   #geom    geometry; carries the horizontal mirror when the solder side is
 *            being viewed, so wire routing under the board is physically right.
 *   #labels  text, never mirrored — mirrored text is unreadable. Positions are
 *            computed in JS and written in display coordinates.
 *
 * The board layer is cached because it is the most expensive to build and only
 * depends on where the boards are, how big they are and what colour they are.
 */

import { svg, clear } from '../util/dom.js';
import {
  BOARD_MARGIN, RULER_GUTTER, boardColor, colLabel, deskColor, rowLabel,
  workspaceExtent,
} from '../core/board.js';
import {
  boundsOf, moduleTransform, normalizeRotation, pinCells, resolveInstance,
  rotatePoint,
} from '../core/geometry.js';
import {
  bodyShape, collectText, fallbackShape, padElements, shapeElement,
} from './shapes.js';
import { WIRE_GAUGES } from '../core/store.js';

const GHOST_OPACITY = 0.3;
const MIN_MODULE_OPACITY = 0.1;

export class Renderer {
  /**
   * @param {SVGSVGElement} root
   * @param {import('../core/store.js').Store} store
   * @param {import('../core/catalog.js').Catalog} catalog
   */
  constructor(root, store, catalog) {
    this.svg = root;
    this.store = store;
    this.catalog = catalog;

    this.defs = svg('defs');
    this.geom = svg('g', { id: 'pbs-geom' });
    this.labels = svg('g', { id: 'pbs-labels' });

    this.deskLayer = svg('g', { class: 'layer-desk' });
    this.boardLayer = svg('g', { class: 'layer-board' });
    this.ghostLayer = svg('g', { class: 'layer-ghost' });
    this.wireLayer = svg('g', { class: 'layer-wires' });
    this.moduleLayer = svg('g', { class: 'layer-modules' });
    this.overlayLayer = svg('g', { class: 'layer-overlay' });

    this.rulerLayer = svg('g', { class: 'layer-ruler' });
    this.textLayer = svg('g', { class: 'layer-text' });

    this.geom.append(
      this.deskLayer, this.boardLayer, this.ghostLayer, this.wireLayer,
      this.moduleLayer, this.overlayLayer,
    );
    this.labels.append(this.rulerLayer, this.textLayer);
    this.svg.append(this.defs, this.geom, this.labels);

    this._deskCacheKey = null;
    this._boardCacheKey = null;
  }

  get mirrored() { return this.store.ui.side === 'solder'; }

  /**
   * How solid a placed module's artwork should be. Turning this down lets wires
   * routed underneath show through; pads, designators and pin names are left
   * alone so the part stays identifiable however faint its body is.
   */
  get moduleOpacity() {
    const v = this.store.ui.moduleOpacity;
    if (!Number.isFinite(v)) return 1;
    return Math.min(1, Math.max(MIN_MODULE_OPACITY, v));
  }

  /** Mirror a continuous x coordinate for display when on the solder side. */
  dx(x) {
    return this.mirrored ? this.store.doc.workspace.cols - 1 - x : x;
  }

  // -- coordinate conversion -------------------------------------------------

  /** Client (mouse) point -> display unit coordinates. */
  clientToUnit(clientX, clientY) {
    const ctm = this.svg.getScreenCTM();
    if (!ctm) return { x: 0, y: 0 };
    const p = new DOMPoint(clientX, clientY).matrixTransform(ctm.inverse());
    return { x: p.x, y: p.y };
  }

  /** Client point -> continuous grid coordinates (un-mirrored). */
  clientToGrid(clientX, clientY) {
    const u = this.clientToUnit(clientX, clientY);
    return { x: this.dx(u.x), y: u.y };
  }

  /** Client point -> nearest workspace hole, or null if outside the workspace. */
  clientToHole(clientX, clientY, tolerance = 0.55) {
    const g = this.clientToGrid(clientX, clientY);
    const col = Math.round(g.x);
    const row = Math.round(g.y);
    const ws = this.store.doc.workspace;
    if (col < 0 || row < 0 || col >= ws.cols || row >= ws.rows) return null;
    if (Math.hypot(g.x - col, g.y - row) > tolerance) return null;
    return { col, row };
  }

  // -- viewport -------------------------------------------------------------

  applyView() {
    const v = this.store.ui.view;
    if (!v) return;
    this.svg.setAttribute('viewBox', `${v.x} ${v.y} ${v.w} ${v.h}`);
  }

  /** Frame the whole workspace, preserving the element's aspect ratio. */
  fitView() {
    const e = workspaceExtent(this.store.doc.workspace);
    const rect = this.svg.getBoundingClientRect();
    const aspect = rect.width > 0 && rect.height > 0 ? rect.width / rect.height : 1;
    let w = e.w;
    let h = e.h;
    if (w / h > aspect) h = w / aspect;
    else w = h * aspect;
    const view = {
      x: e.x - (w - e.w) / 2,
      y: e.y - (h - e.h) / 2,
      w,
      h,
    };
    this.store.setUI({ view }, { silent: true });
    this.applyView();
  }

  /** Zoom by `factor` about a client point. */
  zoomAt(clientX, clientY, factor) {
    const v = this.store.ui.view;
    if (!v) return;
    const before = this.clientToUnit(clientX, clientY);
    const w = Math.min(4000, Math.max(4, v.w / factor));
    const scale = w / v.w;
    const h = v.h * scale;
    const view = {
      x: before.x - (before.x - v.x) * scale,
      y: before.y - (before.y - v.y) * scale,
      w,
      h,
    };
    this.store.setUI({ view }, { silent: true });
    this.applyView();
  }

  panBy(dxUnits, dyUnits) {
    const v = this.store.ui.view;
    if (!v) return;
    this.store.setUI({ view: { ...v, x: v.x - dxUnits, y: v.y - dyUnits } }, { silent: true });
    this.applyView();
  }

  // -- main entry -----------------------------------------------------------

  render() {
    if (!this.store.ui.view) this.fitView();
    else this.applyView();

    this.geom.setAttribute(
      'transform',
      this.mirrored ? `translate(${this.store.doc.workspace.cols - 1} 0) scale(-1 1)` : '',
    );

    this.renderDesk();
    this.renderBoards();
    this.renderRulers();
    this.renderContent();
  }

  // -- workspace ------------------------------------------------------------

  /**
   * The bare desk: a faint dot at every workspace hole. Parts placed off a board
   * still snap to this grid, so it needs to be visible enough to aim at without
   * competing with the boards drawn on top of it.
   */
  renderDesk() {
    const ws = this.store.doc.workspace;
    const key = `${ws.cols}x${ws.rows}:${ws.colorId}`;
    if (key === this._deskCacheKey) return;
    this._deskCacheKey = key;

    const col = deskColor(ws.colorId);
    clear(this.deskLayer);
    this.deskLayer.append(
      svg('rect', {
        class: 'pbs-desk',
        x: -BOARD_MARGIN, y: -BOARD_MARGIN,
        width: ws.cols - 1 + 2 * BOARD_MARGIN, height: ws.rows - 1 + 2 * BOARD_MARGIN,
        rx: 0.4, fill: col.fill, stroke: col.edge, 'stroke-width': 0.08,
      }),
      svg('path', { d: holePath(ws.cols, ws.rows, 0.09), fill: col.dot }),
    );
  }

  // -- boards ---------------------------------------------------------------

  renderBoards() {
    const boards = this.store.doc.boards.map((b) => this.effectiveBoard(b));
    const key = boards.map((b) => `${b.uid}@${b.col},${b.row}:${b.cols}x${b.rows}:${b.colorId}`)
      .join('|');
    if (key === this._boardCacheKey) return;
    this._boardCacheKey = key;

    clear(this.boardLayer);
    for (const b of boards) this.boardLayer.append(this.buildBoard(b));
  }

  buildBoard(board) {
    const col = boardColor(board.colorId);
    const g = svg('g', {
      class: 'pbs-board',
      'data-uid': board.uid,
      transform: `translate(${board.col} ${board.row})`,
    });
    g.append(
      svg('rect', {
        x: -BOARD_MARGIN, y: -BOARD_MARGIN,
        width: board.cols - 1 + 2 * BOARD_MARGIN, height: board.rows - 1 + 2 * BOARD_MARGIN,
        rx: 0.5, fill: col.fill, stroke: col.edge, 'stroke-width': 0.12,
      }),
      svg('path', { d: holePath(board.cols, board.rows, 0.34), fill: col.pad, opacity: 0.9 }),
      svg('path', { d: holePath(board.cols, board.rows, 0.13), fill: '#0d1014', opacity: 0.85 }),
    );
    return g;
  }

  renderRulers() {
    clear(this.rulerLayer);
    if (!this.store.ui.showRulers) return;
    const ws = this.store.doc.workspace;
    const off = BOARD_MARGIN + RULER_GUTTER * 0.45;

    for (let c = 0; c < ws.cols; c++) {
      const major = (c + 1) % 5 === 0 || c === 0;
      this.rulerLayer.append(this.text({
        x: this.dx(c), y: -off, text: colLabel(c), size: 0.5,
        color: major ? '#c0caf5' : '#6b7280', weight: major ? 700 : 500,
      }));
    }
    for (let r = 0; r < ws.rows; r++) {
      const major = (r + 1) % 5 === 0 || r === 0;
      this.rulerLayer.append(this.text({
        x: this.dx(-off), y: r, text: rowLabel(r), size: 0.5,
        color: major ? '#c0caf5' : '#6b7280', weight: major ? 700 : 500,
      }));
    }
  }

  // -- content --------------------------------------------------------------

  renderContent() {
    const { doc, ui } = this.store;
    clear(this.ghostLayer);
    clear(this.wireLayer);
    clear(this.moduleLayer);
    clear(this.overlayLayer);
    clear(this.textLayer);

    const near = (item) => item.side === ui.side;
    const modules = doc.modules.map((m) => this.effectiveModule(m));

    if (ui.showGhost) {
      for (const w of doc.wires) if (!near(w)) this.ghostLayer.append(this.buildWire(w, true));
      for (const m of modules) {
        if (near(m)) continue;
        const g = this.buildModule(m, { ghost: true });
        if (g) this.ghostLayer.append(g);
      }
    }

    const fade = this.moduleOpacity;
    for (const w of doc.wires) if (near(w)) this.wireLayer.append(this.buildWire(w, false));
    for (const m of modules) {
      if (!near(m)) continue;
      const g = this.buildModule(m, { ghost: false, fade });
      if (g) this.moduleLayer.append(g);
    }

    this.renderSelection();
    this.renderWireDraft();
    this.renderPlacementPreview();
    this.renderHover();
  }

  // -- modules --------------------------------------------------------------

  /**
   * A module as it should currently appear: an in-flight drag moves it without
   * touching the document, so nothing lands in the undo stack until pointer-up.
   */
  effectiveModule(m) {
    const d = this.store.ui.drag;
    if (d && d.kind === 'module' && d.uid === m.uid) return { ...m, col: d.col, row: d.row };
    return m;
  }

  /** Same, for a board being dragged around the workspace. */
  effectiveBoard(b) {
    const d = this.store.ui.drag;
    if (d && d.kind === 'board' && d.uid === b.uid) return { ...b, col: d.col, row: d.row };
    return b;
  }

  /**
   * Build one placed module. Geometry goes in the (possibly mirrored) group;
   * its text is pushed to the unmirrored label layer at absolute coordinates.
   */
  buildModule(inst, { ghost, fade = 1 }) {
    const def = this.catalog.get(inst.moduleId);
    if (!def) return this.buildMissingModule(inst, ghost);

    const { cols, rows, scaleX, scaleY } = resolveInstance(def, inst);
    const fp = { cols, rows };

    const g = svg('g', {
      class: `pbs-module${ghost ? ' is-ghost' : ''}`,
      'data-uid': inst.uid,
      transform: moduleTransform(inst, cols, rows),
      opacity: ghost ? GHOST_OPACITY : null,
    });

    // The artwork lives in its own group so `fade` can be a single group opacity
    // — overlapping shapes then blend once instead of stacking up. Artwork is
    // authored for the unresized footprint, so stretch it to match.
    const art = svg('g', {
      class: 'pbs-module-art',
      transform: (scaleX !== 1 || scaleY !== 1) ? `scale(${scaleX} ${scaleY})` : null,
      opacity: fade < 1 ? fade : null,
    });

    const base = def.body ? bodyShape(def, def.footprint) : fallbackShape(def, def.footprint);
    if (base) art.append(shapeElement(base));
    for (const s of def.shapes || []) {
      const e = shapeElement(s);
      if (e) art.append(e);
    }
    g.append(art);

    // Pads sit on the resolved (already stretched) pin holes, unscaled. They stay
    // fully opaque: they are what tells you which holes the part actually uses.
    for (const p of resolveInstance(def, inst).pins) {
      for (const e of padElements(p)) g.append(e);
    }

    // A transparent hit area so thin parts are still easy to grab.
    g.append(svg('rect', {
      class: 'pbs-hit',
      x: -0.5, y: -0.5, width: cols - 1 + 1, height: rows - 1 + 1,
      fill: 'transparent', 'pointer-events': ghost ? 'none' : 'all',
    }));

    if (!ghost) this.emitModuleText(def, inst, fp, scaleX, scaleY, fade);
    return g;
  }

  /** Placeholder for a design that references a module we do not have. */
  buildMissingModule(inst, ghost) {
    const g = svg('g', {
      class: `pbs-module is-missing${ghost ? ' is-ghost' : ''}`,
      'data-uid': inst.uid,
      transform: `translate(${inst.col} ${inst.row})`,
      opacity: ghost ? GHOST_OPACITY : null,
    });
    g.append(svg('rect', {
      x: -0.4, y: -0.4, width: 1.8, height: 1.8, rx: 0.14,
      fill: '#3a1f26', stroke: '#f7768e', 'stroke-width': 0.08,
      'stroke-dasharray': '0.25 0.2',
    }));
    if (!ghost) {
      this.textLayer.append(this.text({
        x: this.dx(inst.col + 0.5), y: inst.row + 0.5, text: '?', size: 0.9,
        color: '#f7768e', weight: 700,
      }));
    }
    return g;
  }

  emitModuleText(def, inst, fp, scaleX, scaleY, fade = 1) {
    const { ui } = this.store;
    const rot = normalizeRotation(inst.rotation);
    const flip = this.mirrored ? -1 : 1;

    if (ui.showLabels) {
      // Silkscreen is part of the artwork, so it fades with it. The designator
      // below is ours, not the part's, and stays readable.
      const silk = (o) => (o == null ? (fade < 1 ? fade : null) : o * fade);
      for (const t of collectText(def, def.footprint)) {
        const local = rotatePoint(t.x * scaleX, t.y * scaleY, fp.cols, fp.rows, rot);
        this.textLayer.append(this.text({
          x: this.dx(local.x + inst.col),
          y: local.y + inst.row,
          text: t.text,
          size: t.size,
          color: t.color,
          anchor: t.anchor,
          weight: t.weight,
          rotate: flip * (rot + t.rotate),
          opacity: silk(t.opacity),
        }));
      }
      if (inst.label) {
        const b = boundsOf(def, inst);
        this.textLayer.append(this.text({
          x: this.dx(b.col + (b.cols - 1) / 2),
          y: b.row - 0.62,
          text: inst.label,
          size: 0.46,
          color: '#ffd479',
          weight: 700,
          className: 'pbs-designator',
          halo: true,
        }));
      }
    }

    if (ui.showPinNames) {
      for (const p of pinCells(def, inst)) {
        if (!p.name) continue;
        this.textLayer.append(this.text({
          x: this.dx(p.col), y: p.row - 0.42, text: p.name, size: 0.26,
          color: PIN_TEXT[p.type] || '#c0caf5', weight: 600,
          className: 'pbs-pinname',
          halo: true,
        }));
      }
    }
  }

  // -- wires ----------------------------------------------------------------

  buildWire(wire, ghost) {
    const width = (WIRE_GAUGES.find((g) => g.id === wire.gauge) || WIRE_GAUGES[1]).width;
    const pts = wire.points.map(([c, r]) => `${c},${r}`).join(' ');
    const g = svg('g', {
      class: `pbs-wire${ghost ? ' is-ghost' : ''}`,
      'data-uid': wire.uid,
      opacity: ghost ? GHOST_OPACITY : null,
    });
    // A wide transparent stroke underneath makes thin wires clickable.
    g.append(svg('polyline', {
      points: pts, fill: 'none', stroke: 'transparent',
      'stroke-width': Math.max(width * 3, 0.5), 'stroke-linecap': 'round',
      'pointer-events': ghost ? 'none' : 'stroke', class: 'pbs-hit',
    }));
    g.append(svg('polyline', {
      points: pts, fill: 'none', stroke: '#000', opacity: 0.35,
      'stroke-width': width * 1.35, 'stroke-linecap': 'round',
      'stroke-linejoin': 'round', 'pointer-events': 'none',
    }));
    g.append(svg('polyline', {
      points: pts, fill: 'none', stroke: wire.color,
      'stroke-width': width, 'stroke-linecap': 'round', 'stroke-linejoin': 'round',
      'pointer-events': 'none',
    }));
    for (const [c, r] of [wire.points[0], wire.points.at(-1)]) {
      g.append(svg('circle', {
        cx: c, cy: r, r: width * 0.85, fill: '#cfd6de', stroke: '#8d949c',
        'stroke-width': 0.04, 'pointer-events': 'none',
      }));
    }
    return g;
  }

  renderWireDraft() {
    const draft = this.store.ui.wireDraft;
    if (!draft || !draft.points.length) return;
    const width = (WIRE_GAUGES.find((g) => g.id === draft.gauge) || WIRE_GAUGES[1]).width;
    const pts = [...draft.points];
    const hover = this.store.ui.hover;
    if (hover) pts.push([hover.col, hover.row]);

    this.overlayLayer.append(svg('polyline', {
      points: pts.map(([c, r]) => `${c},${r}`).join(' '),
      fill: 'none', stroke: draft.color, 'stroke-width': width,
      'stroke-linecap': 'round', 'stroke-linejoin': 'round',
      'stroke-dasharray': '0.4 0.25', opacity: 0.9, 'pointer-events': 'none',
    }));
    for (const [c, r] of draft.points) {
      this.overlayLayer.append(svg('circle', {
        cx: c, cy: r, r: width * 0.9, fill: draft.color, opacity: 0.9,
        'pointer-events': 'none',
      }));
    }
  }

  // -- overlays -------------------------------------------------------------

  /**
   * Draw an overlay outline so it reads on any backdrop.
   *
   * Overlays land on whatever is underneath — a graphite desk, a white one, a tan
   * board — so no single stroke colour stays legible. A darker, wider copy
   * underneath gives the tinted stroke its own contrast wherever it ends up.
   */
  outline(tag, attrs) {
    const width = Number(attrs['stroke-width']) || 0.1;
    this.overlayLayer.append(
      svg(tag, {
        ...attrs, stroke: '#0b0e12', 'stroke-width': width * 2.4, opacity: 0.5,
      }),
      svg(tag, attrs),
    );
  }

  renderSelection() {
    const sel = this.store.selected;
    if (!sel) return;
    if (sel.kind === 'board') {
      const b = this.effectiveBoard(sel.item);
      this.outline('rect', {
        class: 'pbs-selection',
        x: b.col - BOARD_MARGIN - 0.15, y: b.row - BOARD_MARGIN - 0.15,
        width: b.cols - 1 + 2 * BOARD_MARGIN + 0.3,
        height: b.rows - 1 + 2 * BOARD_MARGIN + 0.3,
        rx: 0.5, fill: 'none', stroke: '#7dcfff', 'stroke-width': 0.12,
        'stroke-dasharray': '0.6 0.4', 'pointer-events': 'none',
      });
      return;
    }
    if (sel.kind === 'module') {
      const inst = this.effectiveModule(sel.item);
      const def = this.catalog.get(inst.moduleId);
      const b = def
        ? boundsOf(def, inst)
        : { col: inst.col, row: inst.row, cols: 1, rows: 1 };
      this.outline('rect', {
        class: 'pbs-selection',
        x: b.col - 0.55, y: b.row - 0.55,
        width: b.cols - 1 + 1.1, height: b.rows - 1 + 1.1,
        rx: 0.2, fill: 'none', stroke: '#7dcfff', 'stroke-width': 0.1,
        'stroke-dasharray': '0.45 0.3', 'pointer-events': 'none',
      });
    } else {
      const w = sel.item;
      this.overlayLayer.append(svg('polyline', {
        class: 'pbs-selection',
        points: w.points.map(([c, r]) => `${c},${r}`).join(' '),
        fill: 'none', stroke: '#7dcfff', 'stroke-width': 0.42, opacity: 0.45,
        'stroke-linecap': 'round', 'stroke-linejoin': 'round',
        'pointer-events': 'none',
      }));
    }
  }

  renderPlacementPreview() {
    const { ui } = this.store;
    if (!ui.placing || !ui.hover) return;
    const def = this.catalog.get(ui.placing);
    if (!def) return;
    const inst = {
      uid: '__preview',
      moduleId: def.id,
      col: ui.hover.col,
      row: ui.hover.row,
      rotation: ui.placingRotation,
      side: ui.side,
      span: def.resize ? def.footprint[def.resize.axis] : undefined,
    };
    const g = this.buildModule(inst, { ghost: false });
    if (!g) return;
    g.setAttribute('opacity', '0.65');
    g.setAttribute('pointer-events', 'none');
    this.overlayLayer.append(g);

    const b = boundsOf(def, inst);
    const ws = this.store.doc.workspace;
    const fits = b.col + b.cols <= ws.cols && b.row + b.rows <= ws.rows;
    this.outline('rect', {
      x: b.col - 0.5, y: b.row - 0.5,
      width: b.cols - 1 + 1, height: b.rows - 1 + 1,
      rx: 0.2, fill: 'none', stroke: fits ? '#73daca' : '#f7768e',
      'stroke-width': 0.1, 'stroke-dasharray': '0.4 0.25', 'pointer-events': 'none',
    });
  }

  renderHover() {
    const { ui } = this.store;
    if (!ui.hover || ui.placing) return;
    if (ui.tool !== 'wire' && ui.tool !== 'erase') return;
    this.outline('circle', {
      cx: ui.hover.col, cy: ui.hover.row, r: 0.44,
      fill: 'none', stroke: ui.tool === 'erase' ? '#f7768e' : '#73daca',
      'stroke-width': 0.1, 'pointer-events': 'none',
    });
  }

  // -- text helper ----------------------------------------------------------

  /**
   * A single text node in display coordinates.
   *
   * `halo` draws a dark outline behind the glyphs (`paint-order` puts the stroke
   * under the fill, so the letterforms keep their weight). Our own overlays —
   * designators, pin names — can land on a module, a board or bare workspace of
   * any colour, and a fixed fill alone cannot stay readable across all three.
   */
  text({
    x, y, text, size, color, anchor = 'middle', weight = 600, rotate = 0,
    opacity, className, halo = false,
  }) {
    const node = svg('text', {
      x: 0, y: 0,
      'font-size': size,
      fill: color,
      'text-anchor': anchor,
      'font-weight': weight,
      'dominant-baseline': 'central',
      transform: rotate
        ? `translate(${x} ${y}) rotate(${rotate})`
        : `translate(${x} ${y})`,
      'pointer-events': 'none',
      opacity: opacity ?? null,
      class: className || null,
      stroke: halo ? '#0b0e12' : null,
      'stroke-width': halo ? size * 0.28 : null,
      'stroke-opacity': halo ? 0.7 : null,
      'stroke-linejoin': halo ? 'round' : null,
      'paint-order': halo ? 'stroke fill' : null,
    });
    node.textContent = text;
    return node;
  }
}

/** One path containing a filled circle of radius `r` at every hole of a grid. */
function holePath(cols, rows, r) {
  const parts = [];
  for (let row = 0; row < rows; row++) {
    for (let c = 0; c < cols; c++) {
      parts.push(`M${c - r} ${row}a${r} ${r} 0 1 0 ${2 * r} 0a${r} ${r} 0 1 0 ${-2 * r} 0`);
    }
  }
  return parts.join('');
}

const PIN_TEXT = {
  power: '#ff9e64',
  gnd: '#a9b1d6',
  analog: '#73daca',
  io: '#7dcfff',
  nc: '#6b7280',
};
