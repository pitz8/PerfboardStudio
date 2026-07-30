/**
 * Module catalog loader.
 *
 * There are two ways in, tried in order:
 *
 *  1. `modules/catalog.json` — every definition inlined by
 *     tools/generate_catalog.py. One request, which is what makes a
 *     several-hundred-part catalog boot quickly.
 *  2. `modules/index.json` plus one fetch per module file. Slower, but it means
 *     the app still runs straight from a checkout where the bundle was deleted,
 *     and editing a single JSON file is live with no build step.
 *
 * Failures are collected rather than thrown so one bad file cannot take the
 * whole app down.
 */

const CATALOG_ROOT = 'modules';

export class Catalog {
  constructor() {
    /** @type {Map<string, object>} */
    this.byId = new Map();
    /** @type {Array<{id:string,name:string,color:string}>} */
    this.categories = [];
    /** @type {Array<{file:string, error:string}>} */
    this.errors = [];
    this.pitchMm = 2.54;
  }

  get all() { return [...this.byId.values()]; }

  get(id) { return this.byId.get(id) || null; }

  categoryName(id) {
    return this.categories.find((c) => c.id === id)?.name || id;
  }

  categoryColor(id) {
    return this.categories.find((c) => c.id === id)?.color || '#8d949c';
  }

  /** Modules for a category, in catalog order. */
  inCategory(id) {
    return this.all.filter((m) => m.category === id);
  }

  /**
   * Free-text search over name, subtitle, id and tags.
   * Multiple terms must all match (AND).
   */
  search(query) {
    const terms = String(query || '').toLowerCase().split(/\s+/).filter(Boolean);
    if (!terms.length) return this.all;
    return this.all.filter((m) => {
      const haystack = m._search;
      return terms.every((t) => haystack.includes(t));
    });
  }

  /**
   * Register a definition that is not in the catalog files — used when opening
   * a saved design that embeds modules we do not know about.
   */
  register(def, { source = 'embedded' } = {}) {
    const norm = normalizeDef(def, source);
    if (!norm) return null;
    if (!this.byId.has(norm.id)) this.byId.set(norm.id, norm);
    if (!this.categories.some((c) => c.id === norm.category)) {
      this.categories.push({ id: norm.category, name: norm.category, color: '#8d949c' });
    }
    return this.byId.get(norm.id);
  }

  async load() {
    const bundle = await fetchJson(`${CATALOG_ROOT}/catalog.json`).catch(() => null);
    const results = bundle && bundle.definitions
      ? this.readBundle(bundle)
      : await this.readIndividually();

    for (const r of results) {
      if (r.error) { this.errors.push({ file: r.rel, error: r.error }); continue; }
      const norm = normalizeDef(r.def, r.rel);
      if (!norm) {
        this.errors.push({ file: r.rel, error: 'missing id, name, category or footprint' });
        continue;
      }
      if (this.byId.has(norm.id)) {
        this.errors.push({ file: r.rel, error: `duplicate id "${norm.id}"` });
        continue;
      }
      this.byId.set(norm.id, norm);
    }

    // Drop categories that ended up with nothing in them, and surface any
    // module whose category was never declared.
    const present = new Set(this.all.map((m) => m.category));
    for (const cat of present) {
      if (!this.categories.some((c) => c.id === cat)) {
        this.categories.push({ id: cat, name: cat, color: '#8d949c' });
      }
    }
    this.categories = this.categories.filter((c) => present.has(c.id));

    return this;
  }

  /** Unpack the one-request bundle. `source` stays the original file path. */
  readBundle(bundle) {
    this.categories = (bundle.categories || []).map((c) => ({ ...c }));
    this.pitchMm = bundle.pitchMm || 2.54;
    return Object.entries(bundle.definitions).map(([rel, def]) => ({ rel, def }));
  }

  /** Fallback: read index.json and fetch every module file in parallel. */
  async readIndividually() {
    const index = await fetchJson(`${CATALOG_ROOT}/index.json`);
    this.categories = (index.categories || []).map((c) => ({ ...c }));
    this.pitchMm = index.pitchMm || 2.54;

    return Promise.all((index.modules || []).map(async (rel) => {
      try {
        return { rel, def: await fetchJson(`${CATALOG_ROOT}/${rel}`) };
      } catch (err) {
        return { rel, error: err.message || String(err) };
      }
    }));
  }
}

async function fetchJson(url) {
  const res = await fetch(url, { cache: 'no-cache' });
  if (!res.ok) throw new Error(`HTTP ${res.status} for ${url}`);
  return res.json();
}

/**
 * Validate the required fields and precompute a search haystack. Returns null
 * if the definition is unusable.
 */
export function normalizeDef(raw, source) {
  if (!raw || typeof raw !== 'object') return null;
  const { id, name, category, footprint } = raw;
  if (!id || !name || !category) return null;
  if (!footprint || !Number.isFinite(footprint.cols) || !Number.isFinite(footprint.rows)) return null;
  if (footprint.cols < 1 || footprint.rows < 1) return null;

  const def = { ...raw };
  delete def.$schema;
  def.pins = Array.isArray(raw.pins) ? raw.pins.filter(validPin) : [];
  def.shapes = Array.isArray(raw.shapes) ? raw.shapes : [];
  def.tags = Array.isArray(raw.tags) ? raw.tags.map(String) : [];
  def.designator = raw.designator || 'U';
  def._source = source;
  def._search = [id, name, raw.subtitle || '', category, ...def.tags]
    .join(' ').toLowerCase();

  if (def.resize) {
    const { axis, min, max } = def.resize;
    if ((axis !== 'cols' && axis !== 'rows') || !Number.isFinite(min) || !Number.isFinite(max)) {
      delete def.resize;
    } else {
      def.resize = { axis, min: Math.max(1, min), max: Math.max(min, max) };
    }
  }
  return def;
}

function validPin(p) {
  return p && Number.isFinite(p.col) && Number.isFinite(p.row) && p.col >= 0 && p.row >= 0;
}
