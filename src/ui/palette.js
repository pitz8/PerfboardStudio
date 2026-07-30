/**
 * Module palette: search, category filter, and the list of placeable parts.
 *
 * The card list itself is rebuilt on every filter change — cheap, because a card
 * is three elements. What is not cheap is the little SVG preview on each card,
 * so those are drawn only once a card scrolls into view. The art box has a fixed
 * size in CSS, so filling it in late costs no layout shift.
 */

import { clear, el, on } from '../util/dom.js';
import { modulePreview } from '../render/preview.js';

const RECENT_KEY = 'pbs.recentModules';
const RECENT_MAX = 12;

export class Palette {
  constructor(root, store, catalog, { onStatus } = {}) {
    this.root = root;
    this.store = store;
    this.catalog = catalog;
    this.onStatus = onStatus || (() => {});
    this.query = '';
    this.category = 'all';
    this.recent = readRecent();

    /** Art boxes waiting to be filled in, keyed by their DOM node. */
    this.pendingArt = new WeakMap();
    this.artObserver = typeof IntersectionObserver === 'function'
      ? new IntersectionObserver((entries) => {
        for (const entry of entries) {
          if (entry.isIntersecting) this.drawArt(entry.target);
        }
      }, { rootMargin: '250px 0px' })
      : null;

    this.build();
    this.renderList();
  }

  build() {
    this.search = el('input', {
      type: 'search',
      class: 'pbs-search',
      placeholder: 'Search parts…',
      'aria-label': 'Search modules',
      autocomplete: 'off',
    });
    this.search.placeholder = `Search ${this.catalog.byId.size} parts…`;
    on(this.search, 'input', () => {
      this.query = this.search.value;
      this.renderList();
    });

    this.categorySelect = el('select', { class: 'pbs-select', 'aria-label': 'Filter by category' });
    this.categorySelect.append(el('option', { value: 'all', text: 'All categories' }));
    if (this.recent.length) {
      this.categorySelect.append(el('option', { value: '__recent', text: 'Recently used' }));
    }
    for (const c of this.catalog.categories) {
      this.categorySelect.append(el('option', {
        value: c.id,
        text: `${c.name} (${this.catalog.inCategory(c.id).length})`,
      }));
    }
    on(this.categorySelect, 'change', () => {
      this.category = this.categorySelect.value;
      this.renderList();
    });

    this.list = el('div', { class: 'pbs-palette-list', role: 'listbox' });
    this.count = el('div', { class: 'pbs-palette-count' });

    this.root.append(
      el('div', { class: 'pbs-palette-controls' }, [this.search, this.categorySelect]),
      this.count,
      this.list,
    );
  }

  filtered() {
    let items = this.query.trim()
      ? this.catalog.search(this.query)
      : this.catalog.all;

    if (this.category === '__recent') {
      const order = new Map(this.recent.map((id, i) => [id, i]));
      items = items.filter((m) => order.has(m.id))
        .sort((a, b) => order.get(a.id) - order.get(b.id));
    } else if (this.category !== 'all') {
      items = items.filter((m) => m.category === this.category);
    }
    return items;
  }

  renderList() {
    const items = this.filtered();
    // The old cards are about to be dropped; stop watching them.
    this.artObserver?.disconnect();
    this.pendingArt = new WeakMap();
    clear(this.list);
    this.count.textContent = items.length === this.catalog.byId.size
      ? `${items.length} parts`
      : `${items.length} of ${this.catalog.byId.size} parts`;

    if (!items.length) {
      this.list.append(el('p', { class: 'pbs-empty', text: 'No parts match that search.' }));
      return;
    }

    let lastCategory = null;
    const groupByCategory = this.category === 'all' && !this.query.trim();
    const frag = document.createDocumentFragment();

    for (const def of items) {
      if (groupByCategory && def.category !== lastCategory) {
        lastCategory = def.category;
        frag.append(el('div', {
          class: 'pbs-palette-group',
          text: this.catalog.categoryName(def.category),
          style: `--cat-color:${this.catalog.categoryColor(def.category)}`,
        }));
      }
      frag.append(this.card(def));
    }
    this.list.append(frag);
  }

  card(def) {
    const fp = def.footprint;
    const btn = el('button', {
      class: 'pbs-card',
      type: 'button',
      role: 'option',
      dataset: { moduleId: def.id },
      title: `${def.name}${def.subtitle ? ` — ${def.subtitle}` : ''}\n`
        + `${fp.cols} × ${fp.rows} holes · ${(def.pins || []).length} pins\nid: ${def.id}`,
    });
    const art = el('span', { class: 'pbs-card-art' });
    if (this.artObserver) {
      this.pendingArt.set(art, def);
      this.artObserver.observe(art);
    } else {
      art.append(modulePreview(def, { width: 52, height: 52 }));
    }

    btn.append(
      art,
      el('span', { class: 'pbs-card-body' }, [
        el('span', { class: 'pbs-card-name', text: def.name }),
        el('span', {
          class: 'pbs-card-meta',
          text: `${fp.cols}×${fp.rows}${(def.pins || []).length ? ` · ${def.pins.length}p` : ''}`
            + `${def.subtitle ? ` · ${def.subtitle}` : ''}`,
        }),
      ]),
    );
    on(btn, 'click', () => this.arm(def));
    return btn;
  }

  /** Fill in one card's preview, once. */
  drawArt(node) {
    const def = this.pendingArt.get(node);
    if (!def) return;
    this.pendingArt.delete(node);
    this.artObserver?.unobserve(node);
    node.append(modulePreview(def, { width: 52, height: 52 }));
  }

  arm(def) {
    const already = this.store.ui.placing === def.id;
    this.store.setUI({
      placing: already ? null : def.id,
      placingRotation: 0,
      tool: 'select',
      selection: null,
      wireDraft: null,
    });
    if (already) {
      this.onStatus('Placement cancelled');
    } else {
      this.pushRecent(def.id);
      this.onStatus(`Click a hole to place ${def.name} — R rotates, Esc cancels`);
    }
    this.syncActive();
  }

  /** Keep the armed card visually in sync with the store. */
  syncActive() {
    const armed = this.store.ui.placing;
    for (const node of this.list.querySelectorAll('.pbs-card')) {
      node.classList.toggle('is-armed', node.dataset.moduleId === armed);
    }
  }

  pushRecent(id) {
    this.recent = [id, ...this.recent.filter((x) => x !== id)].slice(0, RECENT_MAX);
    writeRecent(this.recent);
    if (![...this.categorySelect.options].some((o) => o.value === '__recent')) {
      this.categorySelect.insertBefore(
        el('option', { value: '__recent', text: 'Recently used' }),
        this.categorySelect.options[1] || null,
      );
    }
  }

  focusSearch() {
    this.search.focus();
    this.search.select();
  }
}

function readRecent() {
  try {
    const v = JSON.parse(localStorage.getItem(RECENT_KEY) || '[]');
    return Array.isArray(v) ? v.filter((x) => typeof x === 'string').slice(0, RECENT_MAX) : [];
  } catch {
    return [];
  }
}

function writeRecent(list) {
  try {
    localStorage.setItem(RECENT_KEY, JSON.stringify(list));
  } catch {
    /* storage disabled — recents simply do not persist */
  }
}
