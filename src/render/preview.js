/**
 * Small standalone renderings of a module definition, for the palette and the
 * inspector. Previews are never mirrored, so text can be drawn inline.
 */

import { svg } from '../util/dom.js';
import { bodyShape, collectText, fallbackShape, padElements, shapeElement } from './shapes.js';

/**
 * @param {object} def module definition
 * @param {{width?:number,height?:number,padding?:number,showText?:boolean}} opts
 * @returns {SVGSVGElement}
 */
export function modulePreview(def, opts = {}) {
  const {
    width = 64, height = 64, padding = 0.6, showText = true, autoRotate = true,
  } = opts;
  const fp = def.footprint;

  const root = svg('svg', {
    class: 'pbs-preview',
    width,
    height,
    viewBox: '0 0 1 1',
    'aria-hidden': 'true',
    focusable: 'false',
  });

  const g = svg('g');
  const base = def.body ? bodyShape(def, fp) : fallbackShape(def, fp);
  if (base) g.append(shapeElement(base));
  for (const s of def.shapes || []) {
    const e = shapeElement(s);
    if (e) g.append(e);
  }
  for (const p of def.pins || []) {
    for (const e of padElements(p)) g.append(e);
  }
  if (showText) {
    for (const t of collectText(def, fp)) {
      const node = svg('text', {
        'font-size': t.size,
        fill: t.color,
        'text-anchor': t.anchor,
        'font-weight': t.weight,
        'dominant-baseline': 'central',
        transform: t.rotate
          ? `translate(${t.x} ${t.y}) rotate(${t.rotate})`
          : `translate(${t.x} ${t.y})`,
      });
      node.textContent = t.text;
      g.append(node);
    }
  }
  root.append(g);

  // Frame the artwork rather than the nominal footprint, so parts whose body
  // overhangs their holes (TO-220, buzzers, pots) are not clipped.
  const box = artworkBounds(def, padding);

  // Tall parts (dev boards, DIP-28s, headers) would letterbox down to an
  // unreadable sliver in a landscape thumbnail, so lay them on their side. The
  // thumbnail is decoration, not a placement preview, so the turn costs nothing.
  const landscapeSlot = width >= height;
  if (autoRotate && landscapeSlot && box.h > box.w * 1.5) {
    g.setAttribute('transform', 'rotate(90)');
    // rotate(90) maps (x,y) -> (-y,x), so the framed box turns with it.
    root.setAttribute('viewBox', `${-(box.y + box.h)} ${box.x} ${box.h} ${box.w}`);
  } else {
    root.setAttribute('viewBox', `${box.x} ${box.y} ${box.w} ${box.h}`);
  }
  root.setAttribute('preserveAspectRatio', 'xMidYMid meet');
  return root;
}

/**
 * Conservative bounding box over the declared artwork, in hole units.
 * Only shape types with cheap analytic extents are considered; `path` shapes
 * fall back to the footprint, which the padding then covers.
 */
export function artworkBounds(def, padding = 0.6) {
  const fp = def.footprint;
  let minX = 0;
  let minY = 0;
  let maxX = fp.cols - 1;
  let maxY = fp.rows - 1;

  const grow = (x1, y1, x2, y2) => {
    if (![x1, y1, x2, y2].every(Number.isFinite)) return;
    minX = Math.min(minX, x1, x2);
    minY = Math.min(minY, y1, y2);
    maxX = Math.max(maxX, x1, x2);
    maxY = Math.max(maxY, y1, y2);
  };

  const b = def.body;
  if (b) {
    const w = Number.isFinite(b.w) ? b.w : fp.cols - 1;
    const h = Number.isFinite(b.h) ? b.h : fp.rows - 1;
    grow(b.x || 0, b.y || 0, (b.x || 0) + w, (b.y || 0) + h);
  }

  for (const s of def.shapes || []) {
    switch (s.type) {
      case 'rect':
        grow(s.x, s.y, s.x + s.w, s.y + s.h);
        break;
      case 'circle':
        grow(s.cx - s.r, s.cy - s.r, s.cx + s.r, s.cy + s.r);
        break;
      case 'ellipse':
        grow(s.cx - s.rx, s.cy - s.ry, s.cx + s.rx, s.cy + s.ry);
        break;
      case 'line':
        grow(s.x1, s.y1, s.x2, s.y2);
        break;
      case 'polygon':
        for (const p of s.points || []) grow(p[0], p[1], p[0], p[1]);
        break;
      default:
        break;
    }
  }

  return {
    x: minX - padding,
    y: minY - padding,
    w: (maxX - minX) + 2 * padding,
    h: (maxY - minY) + 2 * padding,
  };
}
