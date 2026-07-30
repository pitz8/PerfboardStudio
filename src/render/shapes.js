/**
 * Turns the declarative `shapes` array of a module definition into SVG.
 *
 * Text is handled separately from geometry: geometry lives inside a group that
 * may be mirrored (solder-side view), but mirrored text is unreadable, so text
 * is collected here and re-emitted by the renderer into an unmirrored layer at
 * absolute coordinates.
 */

import { svg } from '../util/dom.js';

const num = (v, fallback = 0) => (Number.isFinite(v) ? v : fallback);

/**
 * Build the SVG element for one non-text shape.
 * Returns null for text shapes and unknown types.
 */
export function shapeElement(s) {
  if (!s || typeof s !== 'object') return null;
  const paint = {
    fill: s.fill || 'none',
    stroke: s.stroke || null,
    'stroke-width': s.stroke ? num(s.strokeWidth, 0.035) : null,
    'stroke-linecap': s.linecap || null,
    'stroke-linejoin': s.stroke ? 'round' : null,
    opacity: Number.isFinite(s.opacity) ? s.opacity : null,
  };

  switch (s.type) {
    case 'rect':
      return svg('rect', {
        x: num(s.x), y: num(s.y), width: num(s.w), height: num(s.h),
        rx: Number.isFinite(s.rx) ? s.rx : null,
        ry: Number.isFinite(s.ry) ? s.ry : null,
        ...paint,
      });
    case 'circle':
      return svg('circle', { cx: num(s.cx), cy: num(s.cy), r: num(s.r), ...paint });
    case 'ellipse':
      return svg('ellipse', {
        cx: num(s.cx), cy: num(s.cy), rx: num(s.rx), ry: num(s.ry), ...paint,
      });
    case 'line':
      return svg('line', {
        x1: num(s.x1), y1: num(s.y1), x2: num(s.x2), y2: num(s.y2),
        ...paint,
        fill: 'none',
        stroke: s.stroke || '#000',
        'stroke-width': num(s.strokeWidth, 0.1),
      });
    case 'polygon':
      if (!Array.isArray(s.points)) return null;
      return svg('polygon', {
        points: s.points.map((p) => `${num(p[0])},${num(p[1])}`).join(' '),
        ...paint,
      });
    case 'path':
      if (typeof s.d !== 'string') return null;
      return svg('path', { d: s.d, ...paint });
    default:
      return null;
  }
}

/**
 * Collect the text a definition wants drawn, in module-local coordinates.
 * `label` is emitted last so it sits on top, matching the documented order.
 */
export function collectText(def, footprint) {
  const out = [];
  for (const s of def.shapes || []) {
    if (s.type !== 'text' || typeof s.text !== 'string') continue;
    out.push({
      x: num(s.x), y: num(s.y),
      text: s.text,
      size: num(s.size, 0.32),
      color: s.color || '#e6edf3',
      anchor: s.anchor || 'middle',
      rotate: num(s.rotate, 0),
      weight: s.weight ?? 600,
      opacity: Number.isFinite(s.opacity) ? s.opacity : null,
    });
  }
  const l = def.label;
  if (l && typeof l.text === 'string' && l.text !== '') {
    out.push({
      x: Number.isFinite(l.x) ? l.x : (footprint.cols - 1) / 2,
      y: Number.isFinite(l.y) ? l.y : (footprint.rows - 1) / 2,
      text: l.text,
      size: num(l.size, 0.4),
      color: l.color || '#e6edf3',
      anchor: l.anchor || 'middle',
      rotate: num(l.rotate, 0),
      weight: l.weight ?? 600,
      opacity: null,
    });
  }
  return out;
}

/** The optional `body` shorthand, as a rect shape. */
export function bodyShape(def, footprint) {
  const b = def.body;
  if (!b) return null;
  const w = Number.isFinite(b.w) ? b.w : footprint.cols - 1;
  const h = Number.isFinite(b.h) ? b.h : footprint.rows - 1;
  return {
    type: 'rect',
    x: num(b.x), y: num(b.y), w, h,
    rx: Number.isFinite(b.rx) ? b.rx : 0.12,
    fill: b.fill || '#2a3038',
    stroke: b.stroke || null,
    strokeWidth: num(b.strokeWidth, 0.04),
    opacity: Number.isFinite(b.opacity) ? b.opacity : null,
  };
}

/**
 * When a definition has no artwork at all, draw a plain plate over the
 * footprint so the module is still visible and grabbable.
 */
export function fallbackShape(def, footprint) {
  if (def.body || (def.shapes && def.shapes.length)) return null;
  return {
    type: 'rect',
    x: -0.4, y: -0.4,
    w: footprint.cols - 1 + 0.8,
    h: footprint.rows - 1 + 0.8,
    rx: 0.14,
    fill: '#2a3038',
    stroke: '#4a525c',
    strokeWidth: 0.04,
  };
}

const PAD_TINT = {
  power: '#e0703a',
  gnd: '#7f878f',
  analog: '#3aa8a8',
  nc: '#4a525c',
};

/** Copper pad + drill hole for one pin, in module-local coordinates. */
export function padElements(p) {
  const tint = PAD_TINT[p.type] || '#c4763a';
  return [
    svg('circle', { cx: p.col, cy: p.row, r: 0.3, fill: '#c4763a', opacity: 0.95 }),
    svg('circle', {
      cx: p.col, cy: p.row, r: 0.28, fill: 'none', stroke: tint, 'stroke-width': 0.07,
    }),
    svg('circle', { cx: p.col, cy: p.row, r: 0.1, fill: '#14181d' }),
  ];
}
