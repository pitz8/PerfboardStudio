/**
 * Image export.
 *
 * Both exporters work off a clone of the live SVG: whatever is on screen — side,
 * ghosting, labels — is what gets exported, minus the transient overlays.
 */

import { boardExtent } from '../core/board.js';
import { downloadText } from '../util/dom.js';

const XMLNS = 'http://www.w3.org/2000/svg';

/** Clone the board SVG, framed to the board and stripped of editing overlays. */
function snapshot(renderer, { background = '#11141a', padding = 0.5 } = {}) {
  const clone = renderer.svg.cloneNode(true);
  clone.setAttribute('xmlns', XMLNS);

  for (const sel of ['.layer-overlay', '.pbs-hit', '.pbs-selection']) {
    for (const n of [...clone.querySelectorAll(sel)]) n.remove();
  }

  const e = boardExtent(renderer.store.doc.board);
  const x = e.x - padding;
  const y = e.y - padding;
  const w = e.w + 2 * padding;
  const h = e.h + 2 * padding;
  clone.setAttribute('viewBox', `${x} ${y} ${w} ${h}`);
  clone.setAttribute('width', String(Math.round(w * 24)));
  clone.setAttribute('height', String(Math.round(h * 24)));
  clone.removeAttribute('style');
  clone.removeAttribute('class');

  if (background) {
    const bg = document.createElementNS(XMLNS, 'rect');
    bg.setAttribute('x', String(x));
    bg.setAttribute('y', String(y));
    bg.setAttribute('width', String(w));
    bg.setAttribute('height', String(h));
    bg.setAttribute('fill', background);
    clone.insertBefore(bg, clone.firstChild);
  }

  // Inline the font so the exported file does not depend on the page CSS.
  const style = document.createElementNS(XMLNS, 'style');
  style.textContent = 'text{font-family:ui-sans-serif,system-ui,"Segoe UI",Roboto,'
    + 'Helvetica,Arial,sans-serif}';
  clone.insertBefore(style, clone.firstChild);

  return { clone, width: w, height: h };
}

export function exportSvg(renderer, filename) {
  const { clone } = snapshot(renderer);
  const text = new XMLSerializer().serializeToString(clone);
  downloadText(filename, `<?xml version="1.0" encoding="UTF-8"?>\n${text}\n`, 'image/svg+xml');
}

export async function exportPng(renderer, filename, { scale = 3 } = {}) {
  const { clone, width, height } = snapshot(renderer);
  const text = new XMLSerializer().serializeToString(clone);
  const url = URL.createObjectURL(new Blob([text], { type: 'image/svg+xml;charset=utf-8' }));

  try {
    const img = await loadImage(url);
    const canvas = document.createElement('canvas');
    canvas.width = Math.max(1, Math.round(width * 24 * scale / 3));
    canvas.height = Math.max(1, Math.round(height * 24 * scale / 3));
    const ctx = canvas.getContext('2d');
    ctx.drawImage(img, 0, 0, canvas.width, canvas.height);

    const blob = await new Promise((res) => canvas.toBlob(res, 'image/png'));
    if (!blob) throw new Error('Canvas could not produce a PNG');
    const dl = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = dl;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    a.remove();
    setTimeout(() => URL.revokeObjectURL(dl), 1000);
  } finally {
    URL.revokeObjectURL(url);
  }
}

function loadImage(src) {
  return new Promise((resolve, reject) => {
    const img = new Image();
    img.onload = () => resolve(img);
    img.onerror = () => reject(new Error('Could not rasterise the SVG'));
    img.src = src;
  });
}

/**
 * A plain-text bill of materials, grouped by module definition.
 */
export function buildBom(doc, catalog) {
  const groups = new Map();
  for (const m of doc.modules) {
    const def = catalog.get(m.moduleId);
    const key = m.moduleId;
    if (!groups.has(key)) {
      groups.set(key, {
        name: def?.name || m.moduleId,
        subtitle: def?.subtitle || '',
        category: def?.category || 'unknown',
        refs: [],
      });
    }
    groups.get(key).refs.push(m.label || '—');
  }

  const rows = [...groups.entries()]
    .map(([id, g]) => ({ id, ...g, qty: g.refs.length }))
    .sort((a, b) => a.category.localeCompare(b.category) || a.name.localeCompare(b.name));

  const lines = [
    `# Bill of materials — ${doc.name}`,
    `# Board: ${doc.board.cols} × ${doc.board.rows} holes`,
    `# Generated ${new Date().toISOString()}`,
    '',
    'Qty\tRefs\tPart\tDescription\tCategory\tModule id',
  ];
  for (const r of rows) {
    lines.push([r.qty, r.refs.join(' '), r.name, r.subtitle, r.category, r.id].join('\t'));
  }
  const wires = doc.wires.length;
  if (wires) {
    lines.push('', `# ${wires} wire(s): `
      + `${doc.wires.filter((w) => w.side === 'front').length} front, `
      + `${doc.wires.filter((w) => w.side === 'solder').length} solder side`);
  }
  return `${lines.join('\n')}\n`;
}
