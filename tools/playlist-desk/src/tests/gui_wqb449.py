"""Fictional Tk regression: held Shift-motion must not expand selected rows.

Xvfb/Tk 8.6 only; does not prove owner Windows 10 behavior.
"""
from pathlib import Path
from unittest.mock import patch
import hashlib
import tkinter as tk
from integrated_app import IntegratedApp

fixture = Path(__file__).resolve().parents[1] / 'sample' / 'fictional_phone_snapshot.json'
original_hash = hashlib.sha256(fixture.read_bytes()).hexdigest()
for pane_name in ('library', 'playlist'):
    ui = IntegratedApp()
    try:
        ui.update()
        with patch('integrated_app.filedialog.askopenfilename', return_value=str(fixture)):
            ui.attach_phone()
        template = ui.data['tracks'][0]
        for i in range(65):
            row = template.copy()
            row['id'] = f'WQB449-synthetic-{i}'
            row['title'] = f'Synthetic {i:03d}'
            ui.data['tracks'].append(row)
        ui.current_pl()['track_ids'] = [t['id'] for t in ui.data['tracks']]
        ui.refresh_library()
        ui.refresh_playlist()
        ui.update()
        w = ui.library if pane_name == 'library' else ui.plist
        assert w.size() > 50
        w.yview_moveto(0)
        w.selection_clear(0, tk.END)
        w.selection_set(1)
        w.selection_anchor(1)
        w.activate(1)
        ui.update()
        y4 = w.bbox(4)[1] + 3
        y9 = w.bbox(9)[1] + 3
        w.event_generate('<ButtonPress-1>', x=20, y=y4, state=0x0001)
        ui.update()
        expected = tuple(range(1, 5))
        assert w.curselection() == expected, ('Shift-click failed', pane_name, w.curselection())
        w.event_generate('<B1-Motion>', x=20, y=y9, state=0x0101)
        ui.update()
        assert w.curselection() == expected, ('modifier motion changed selection', pane_name, w.curselection())
        old_y = w.yview()[0]
        w.event_generate('<MouseWheel>', x=20, y=y9, state=0x0101, delta=-120)
        ui.update()
        assert w.yview()[0] > old_y, ('wheel did not scroll', pane_name, w.yview())
        assert w.curselection() == expected, ('wheel changed selection', pane_name, w.curselection())
        w.event_generate('<B1-Motion>', x=20, y=y9, state=0x0101)
        ui.update()
        assert w.curselection() == expected, ('motion after wheel changed selection', pane_name, w.curselection())
        w.event_generate('<ButtonRelease-1>', x=20, y=y9, state=0x0001)
        ui.update()
        assert w.curselection() == expected
    finally:
        ui.destroy()
assert hashlib.sha256(fixture.read_bytes()).hexdigest() == original_hash
print('GUI_WQB449_PASS: both panes preserve Shift-click range across B1 motion and wheel')
