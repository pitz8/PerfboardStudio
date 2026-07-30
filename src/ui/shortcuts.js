/**
 * Global keyboard shortcuts.
 *
 * Keys are ignored while the user is typing in a form control, except for
 * Escape, which always means "get me out of here".
 */

import { el, on } from '../util/dom.js';

export const SHORTCUTS = [
  ['V', 'Select / move tool'],
  ['W', 'Wire tool'],
  ['E', 'Erase tool'],
  ['Tab', 'Flip between front and solder side'],
  ['R / Shift+R', 'Rotate selection (or the part being placed)'],
  ['F', 'Send selection to the other side'],
  ['Arrows', 'Nudge the selected module by one hole'],
  ['Del / Backspace', 'Delete selection'],
  ['Enter', 'Finish the wire being drawn'],
  ['Esc', 'Cancel placement or wire, clear selection'],
  ['Ctrl+Z / Ctrl+Shift+Z', 'Undo / redo'],
  ['Ctrl+S', 'Save design as JSON'],
  ['Ctrl+O', 'Open a design'],
  ['Ctrl+N', 'New design'],
  ['Ctrl+D', 'Duplicate the selected module'],
  ['Ctrl+F', 'Focus the parts search'],
  ['+ / −', 'Zoom in / out'],
  ['0', 'Fit the board in view'],
  ['Space + drag', 'Pan (middle mouse also works)'],
  ['L / P / G', 'Toggle labels / pin names / other-side ghost'],
  ['F1 or ?', 'This help'],
];

export function installShortcuts(store, { canvas, actions, palette }) {
  on(window, 'keydown', (e) => {
    const typing = isTyping(e.target);

    if (e.key === 'Escape') {
      if (actions.closeDialog()) return;
      if (store.ui.wireDraft) { canvas.cancelWire(); return; }
      if (store.ui.placing) { store.setUI({ placing: null }); actions.syncPalette(); return; }
      if (store.ui.selection) { store.setUI({ selection: null }); return; }
      if (typing) e.target.blur();
      return;
    }

    if (typing) return;

    const ctrl = e.ctrlKey || e.metaKey;

    if (ctrl) {
      switch (e.key.toLowerCase()) {
        case 'z': e.preventDefault(); if (e.shiftKey) actions.redo(); else actions.undo(); return;
        case 'y': e.preventDefault(); actions.redo(); return;
        case 's': e.preventDefault(); actions.save(); return;
        case 'o': e.preventDefault(); actions.open(); return;
        case 'n': e.preventDefault(); actions.newDesign(); return;
        case 'd': e.preventDefault(); actions.duplicate(); return;
        case 'f': e.preventDefault(); palette.focusSearch(); return;
        default: return;
      }
    }

    switch (e.key) {
      case 'v': case 'V': actions.setTool('select'); break;
      case 'w': case 'W': actions.setTool('wire'); break;
      case 'e': case 'E': actions.setTool('erase'); break;
      case 'r': canvas.rotateSelection(90); break;
      case 'R': canvas.rotateSelection(-90); break;
      case 'f': case 'F': canvas.flipSelectionSide(); break;
      case 'Tab':
        e.preventDefault();
        actions.setSide(store.ui.side === 'front' ? 'solder' : 'front');
        break;
      case 'Delete': case 'Backspace':
        e.preventDefault();
        if (!canvas.backspaceWire()) canvas.deleteSelection();
        break;
      case 'Enter': canvas.finishWire(); break;
      case 'ArrowLeft': e.preventDefault(); canvas.nudgeSelection(-1, 0); break;
      case 'ArrowRight': e.preventDefault(); canvas.nudgeSelection(1, 0); break;
      case 'ArrowUp': e.preventDefault(); canvas.nudgeSelection(0, -1); break;
      case 'ArrowDown': e.preventDefault(); canvas.nudgeSelection(0, 1); break;
      case '+': case '=': actions.zoom(1.25); break;
      case '-': case '_': actions.zoom(0.8); break;
      case '0': actions.fit(); break;
      case 'l': case 'L': store.setUI({ showLabels: !store.ui.showLabels }); break;
      case 'p': case 'P': store.setUI({ showPinNames: !store.ui.showPinNames }); break;
      case 'g': case 'G': store.setUI({ showGhost: !store.ui.showGhost }); break;
      case 'F1': case '?': e.preventDefault(); actions.showHelp(); break;
      default: break;
    }
  });
}

function isTyping(target) {
  if (!(target instanceof HTMLElement)) return false;
  const tag = target.tagName;
  return tag === 'INPUT' || tag === 'TEXTAREA' || tag === 'SELECT' || target.isContentEditable;
}

/** Build the shortcut reference table shown in the help dialog. */
export function shortcutTable() {
  const grid = el('div', { class: 'pbs-shortcut-grid' });
  for (const [keys, desc] of SHORTCUTS) {
    grid.append(
      el('kbd', { class: 'pbs-kbd', text: keys }),
      el('span', { text: desc }),
    );
  }
  return grid;
}
