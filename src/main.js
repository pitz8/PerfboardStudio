/**
 * Perfboard Studio — application entry point.
 *
 * Wiring order: load the catalog, build the store, mount the renderer and
 * panels, then subscribe everything to the store and do the first render.
 */

import { clear, downloadText, el, on, pickTextFile, qs } from './util/dom.js';
import { Catalog } from './core/catalog.js';
import { Store } from './core/store.js';
import { Renderer } from './render/renderer.js';
import { CanvasController } from './ui/canvas.js';
import { Palette } from './ui/palette.js';
import { Inspector } from './ui/inspector.js';
import { Toolbar } from './ui/toolbar.js';
import { installShortcuts, shortcutTable } from './ui/shortcuts.js';
import { deserialize, filenameFor, toJSON } from './io/project.js';
import { buildBom, exportPng, exportSvg } from './io/export.js';
import { makeInstance } from './core/store.js';
import { clampBoardToArea, clampToArea } from './core/geometry.js';

const AUTOSAVE_KEY = 'pbs.autosave';

/**
 * State changes that fire continuously while the pointer is down. The board
 * still redraws for these; the inspector does not, because rebuilding its
 * inputs mid-gesture would drop the control being dragged.
 */
const LIVE_REASONS = new Set(['hover', 'drag', 'opacity']);

async function boot() {
  const loading = qs('#loading');
  const catalog = new Catalog();

  try {
    await catalog.load();
  } catch (err) {
    loading.innerHTML = '';
    loading.append(
      el('div', { class: 'pbs-fatal' }, [
        el('h1', { text: 'Could not load the module catalog' }),
        el('p', { text: String(err.message || err) }),
        el('p', {
          class: 'pbs-note',
          text: 'The app must be served over HTTP — opening index.html directly from '
            + 'the filesystem blocks the module fetches. Run "npm run dev" (or '
            + '"python -m http.server 5173") and reload.',
        }),
      ]),
    );
    return;
  }

  if (!catalog.byId.size) {
    loading.textContent = 'The catalog loaded but contains no usable modules.';
    return;
  }

  const store = new Store();
  const app = new App(store, catalog);
  loading.remove();
  app.mount();
}

class App {
  constructor(store, catalog) {
    this.store = store;
    this.catalog = catalog;
    this.dialog = null;
  }

  mount() {
    qs('#app').hidden = false;

    const svgRoot = qs('#board');
    this.renderer = new Renderer(svgRoot, this.store, this.catalog);

    this.status = new StatusBar(qs('#status'), this.store, this.catalog);

    this.canvas = new CanvasController(this.renderer, this.store, this.catalog, {
      onStatus: (msg, kind) => this.status.say(msg, kind),
    });

    this.actions = this.buildActions();

    this.toolbar = new Toolbar(qs('#toolbar'), this.store, {
      actions: this.actions,
      onStatus: (m, k) => this.status.say(m, k),
    });
    this.palette = new Palette(qs('#palette'), this.store, this.catalog, {
      onStatus: (m, k) => this.status.say(m, k),
    });
    this.inspector = new Inspector(qs('#inspector'), this.store, this.catalog, {
      canvas: this.canvas,
      onStatus: (m, k) => this.status.say(m, k),
    });

    installShortcuts(this.store, {
      canvas: this.canvas,
      actions: this.actions,
      palette: this.palette,
    });

    this.store.subscribe((s, reason) => this.onStateChange(s, reason));

    if (this.catalog.errors.length) {
      this.status.say(
        `${this.catalog.errors.length} module file(s) failed to load — see the console.`,
        'warn',
      );
      console.warn('Catalog problems:', this.catalog.errors);
    }

    this.renderAll();
    this.installUnloadGuard();

    // ?design=<path> opens a design straight from the server, which is how the
    // shipped examples are linked; ?side=solder lands on the solder view. Both
    // win over the autosave prompt.
    const params = new URLSearchParams(location.search);
    if (params.get('side') === 'solder') this.store.setUI({ side: 'solder' }, { silent: true });

    const wanted = params.get('design');
    if (wanted) {
      this.openUrl(wanted);
    } else {
      this.restoreAutosave();
      this.renderAll();
      this.status.say(`${this.catalog.byId.size} parts loaded. Pick one from the left to start.`);
    }
  }

  // -- state plumbing --------------------------------------------------------

  onStateChange(store, reason) {
    this.renderer.render();
    this.toolbar.sync();
    this.palette.syncActive();

    // The inspector rebuilds its inputs, so avoid doing it mid-drag, on every
    // mouse move, or while its own slider is being dragged — that would steal
    // focus and thrash the DOM.
    if (!LIVE_REASONS.has(reason)) this.inspector.render();
    this.status.sync();

    if (reason === 'doc' || reason === 'load') this.scheduleAutosave();
  }

  renderAll() {
    this.renderer.render();
    this.toolbar.sync();
    this.inspector.render();
    this.palette.syncActive();
    this.status.sync();
  }

  buildActions() {
    const store = this.store;
    return {
      undo: () => { if (!store.undo()) this.status.say('Nothing to undo'); },
      redo: () => { if (!store.redo()) this.status.say('Nothing to redo'); },

      setTool: (tool) => {
        store.setUI({ tool, placing: null });
        if (tool !== 'wire') this.canvas.cancelWire();
        this.status.say(TOOL_HINTS[tool] || '');
      },

      setSide: (side) => {
        if (store.ui.side === side) return;
        this.canvas.cancelWire();
        store.setUI({ side, placing: null });
        this.status.say(side === 'solder'
          ? 'Solder side — view is mirrored, so wiring under the board reads correctly'
          : 'Component side');
      },

      setWireColor: (hex) => {
        store.setUI({ wireColor: hex });
        const draft = store.ui.wireDraft;
        if (draft) store.setUI({ wireDraft: { ...draft, color: hex } });
        const sel = store.selected;
        if (sel?.kind === 'wire') {
          store.commit('Change wire colour', (doc) => {
            const w = doc.wires.find((x) => x.uid === sel.item.uid);
            if (!w) return false;
            w.color = hex;
          });
        }
      },

      setWireGauge: (gauge) => {
        store.setUI({ wireGauge: gauge });
        const draft = store.ui.wireDraft;
        if (draft) store.setUI({ wireDraft: { ...draft, gauge } });
      },

      zoom: (factor) => {
        const r = this.renderer.svg.getBoundingClientRect();
        this.renderer.zoomAt(r.left + r.width / 2, r.top + r.height / 2, factor);
      },
      fit: () => { this.renderer.fitView(); },

      duplicate: () => this.duplicateSelection(),

      newDesign: () => {
        if (!this.confirmDiscard('Start a new design?')) return;
        this.store.reset();
        this.status.say('New design');
      },
      open: () => this.openFile(),
      save: () => this.saveFile(),
      exportSvg: () => {
        exportSvg(this.renderer, filenameFor(store.doc).replace(/\.pbs\.json$/, '.svg'));
        this.status.say('Exported SVG');
      },
      exportPng: async () => {
        try {
          await exportPng(this.renderer, filenameFor(store.doc).replace(/\.pbs\.json$/, '.png'));
          this.status.say('Exported PNG');
        } catch (err) {
          this.status.say(`PNG export failed: ${err.message}`, 'warn');
        }
      },
      exportBom: () => {
        const name = filenameFor(store.doc).replace(/\.pbs\.json$/, '-bom.tsv');
        downloadText(name, buildBom(store.doc, this.catalog), 'text/tab-separated-values');
        this.status.say('Exported bill of materials');
      },

      showHelp: () => this.showHelp(),
      closeDialog: () => this.closeDialog(),
      syncPalette: () => this.palette.syncActive(),
    };
  }

  duplicateSelection() {
    const sel = this.store.selected;
    if (!sel) { this.status.say('Nothing selected to duplicate'); return; }

    if (sel.kind === 'board') {
      const src = sel.item;
      const copy = {
        ...structuredClone(src),
        uid: `b${Date.now().toString(36).slice(-5)}${Math.random().toString(36).slice(2, 6)}`,
        label: this.store.nextBoardLabel(),
      };
      const at = clampBoardToArea(this.store.doc.workspace, {
        ...copy, col: src.col + 2, row: src.row + 2,
      });
      copy.col = at.col;
      copy.row = at.row;
      this.store.commit(`Duplicate ${src.label || 'board'}`, (doc) => { doc.boards.push(copy); });
      this.store.setUI({ selection: { kind: 'board', uid: copy.uid } });
      this.status.say('Duplicated');
      return;
    }

    if (sel.kind === 'module') {
      const def = this.catalog.get(sel.item.moduleId);
      if (!def) return;
      const copy = makeInstance(def, {
        col: sel.item.col + 1,
        row: sel.item.row + 1,
        rotation: sel.item.rotation,
        side: sel.item.side,
        span: sel.item.span,
        label: this.store.nextDesignator(def),
      });
      const at = clampToArea(this.store.doc.workspace, def, copy);
      copy.col = at.col;
      copy.row = at.row;
      this.store.commit(`Duplicate ${def.name}`, (doc) => { doc.modules.push(copy); });
      this.store.setUI({ selection: { kind: 'module', uid: copy.uid } });
    } else {
      const src = sel.item;
      const ws = this.store.doc.workspace;
      const dy = src.points.every(([, r]) => r + 1 < ws.rows) ? 1 : 0;
      const copy = {
        ...structuredClone(src),
        uid: `w${Date.now().toString(36).slice(-5)}${Math.random().toString(36).slice(2, 6)}`,
        points: src.points.map(([c, r]) => [c, r + dy]),
      };
      this.store.commit('Duplicate wire', (doc) => { doc.wires.push(copy); });
      this.store.setUI({ selection: { kind: 'wire', uid: copy.uid } });
    }
    this.status.say('Duplicated');
  }

  // -- files -----------------------------------------------------------------

  saveFile() {
    const json = toJSON(this.store.doc, this.catalog);
    downloadText(filenameFor(this.store.doc), json);
    this.store.setUI({ dirty: false });
    this.status.say(`Saved ${filenameFor(this.store.doc)}`);
  }

  async openFile() {
    const picked = await pickTextFile('.json,.pbs.json,application/json');
    if (!picked) return;
    if (!this.confirmDiscard(`Open ${picked.name}?`)) return;
    try {
      const { doc, warnings } = deserialize(picked.text, this.catalog);
      this.store.load(doc);
      // A design may have brought new definitions with it.
      this.palette.renderList();
      this.status.say(
        warnings.length
          ? `Opened ${picked.name} with ${warnings.length} warning(s)`
          : `Opened ${picked.name}`,
        warnings.length ? 'warn' : 'ok',
      );
      if (warnings.length) console.warn('Open warnings:', warnings);
    } catch (err) {
      this.status.say(`Could not open ${picked.name}: ${err.message}`, 'warn');
      window.alert(`Could not open ${picked.name}.\n\n${err.message}`);
    }
  }

  /**
   * Open a design served from the same origin. Only same-origin relative paths
   * are accepted, so a crafted link cannot make the app fetch somewhere else.
   */
  async openUrl(path) {
    if (/^[a-z][a-z0-9+.-]*:|^\/\//i.test(path)) {
      this.status.say('Only same-origin design paths can be opened from a link', 'warn');
      return;
    }
    try {
      const res = await fetch(path, { cache: 'no-cache' });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const { doc, warnings } = deserialize(await res.text(), this.catalog);
      this.store.load(doc);
      this.palette.renderList();
      this.status.say(
        warnings.length ? `Opened ${path} with ${warnings.length} warning(s)` : `Opened ${path}`,
        warnings.length ? 'warn' : 'ok',
      );
      if (warnings.length) console.warn('Open warnings:', warnings);
    } catch (err) {
      this.status.say(`Could not open ${path}: ${err.message}`, 'warn');
    }
  }

  confirmDiscard(question) {
    if (!this.store.ui.dirty) return true;
    return window.confirm(`${question}\n\nThe current design has unsaved changes.`);
  }

  installUnloadGuard() {
    on(window, 'beforeunload', (e) => {
      if (!this.store.ui.dirty) return;
      e.preventDefault();
      e.returnValue = '';
    });
  }

  // -- autosave --------------------------------------------------------------

  scheduleAutosave() {
    clearTimeout(this._autosaveTimer);
    this._autosaveTimer = setTimeout(() => {
      try {
        localStorage.setItem(AUTOSAVE_KEY, toJSON(this.store.doc, this.catalog));
      } catch {
        /* quota or private mode — autosave is a convenience, not a guarantee */
      }
    }, 800);
  }

  restoreAutosave() {
    let raw;
    try {
      raw = localStorage.getItem(AUTOSAVE_KEY);
    } catch {
      return;
    }
    if (!raw) return;
    let parsed;
    try {
      parsed = deserialize(raw, this.catalog);
    } catch {
      return;
    }
    if (!parsed.doc.modules.length && !parsed.doc.wires.length) return;

    const n = parsed.doc.modules.length;
    const w = parsed.doc.wires.length;
    const ok = window.confirm(
      `Restore your last session?\n\n"${parsed.doc.name}" — ${n} module(s), ${w} wire(s).\n\n`
      + 'Cancel starts from an empty board.',
    );
    if (ok) {
      this.store.load(parsed.doc, { markClean: false });
    } else {
      try { localStorage.removeItem(AUTOSAVE_KEY); } catch { /* ignore */ }
    }
  }

  // -- dialog ----------------------------------------------------------------

  showHelp() {
    this.openDialog('Keyboard & mouse', [
      shortcutTable(),
      el('h3', { class: 'pbs-dialog-h3', text: 'Adding your own parts' }),
      el('p', {
        class: 'pbs-note',
        html: 'Drop a JSON file into <code>modules/&lt;category&gt;/</code>, add its path to '
          + '<code>modules/index.json</code>, and reload — there is no build step. '
          + 'The format is documented in <code>docs/MODULE_FORMAT.md</code>.',
      }),
    ]);
  }

  openDialog(title, content) {
    this.closeDialog();
    const body = el('div', { class: 'pbs-dialog-body' }, content);
    const close = el('button', { type: 'button', class: 'pbs-dialog-close', text: '✕', 'aria-label': 'Close' });
    const panel = el('div', { class: 'pbs-dialog', role: 'dialog', 'aria-modal': 'true' }, [
      el('div', { class: 'pbs-dialog-head' }, [el('h2', { text: title }), close]),
      body,
    ]);
    const backdrop = el('div', { class: 'pbs-backdrop' }, [panel]);
    on(close, 'click', () => this.closeDialog());
    on(backdrop, 'click', (e) => { if (e.target === backdrop) this.closeDialog(); });
    document.body.append(backdrop);
    this.dialog = backdrop;
    close.focus();
  }

  closeDialog() {
    if (!this.dialog) return false;
    this.dialog.remove();
    this.dialog = null;
    return true;
  }
}

const TOOL_HINTS = {
  select: 'Select tool — click to select, drag to move, R rotates',
  wire: 'Wire tool — click holes to route, double-click or Enter to finish',
  erase: 'Erase tool — click a module or wire to delete it',
};

class StatusBar {
  constructor(root, store, catalog) {
    this.root = root;
    this.store = store;
    this.catalog = catalog;
    this.message = el('span', { class: 'pbs-status-msg' });
    this.coords = el('span', { class: 'pbs-status-coords' });
    this.counts = el('span', { class: 'pbs-status-counts' });
    this.root.append(this.message, el('span', { class: 'pbs-spacer' }), this.coords, this.counts);
  }

  say(text, kind = 'ok') {
    if (kind === 'coords') { this.coords.textContent = text; return; }
    this.message.textContent = text;
    this.message.className = `pbs-status-msg${kind === 'warn' ? ' is-warn' : ''}`;
  }

  sync() {
    const { doc, ui } = this.store;
    const front = doc.modules.filter((m) => m.side === 'front').length;
    const solder = doc.modules.length - front;
    clear(this.counts);
    this.counts.append(
      el('span', { text: `${doc.workspace.cols}×${doc.workspace.rows}` }),
      el('span', { text: `${doc.boards.length} board${doc.boards.length === 1 ? '' : 's'}` }),
      el('span', { text: `${doc.modules.length} modules (${front}F/${solder}S)` }),
      el('span', { text: `${doc.wires.length} wires` }),
      el('span', { class: ui.side === 'solder' ? 'is-solder' : '', text: ui.side === 'solder' ? 'SOLDER SIDE' : 'FRONT' }),
    );
  }
}

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', boot, { once: true });
} else {
  boot();
}
