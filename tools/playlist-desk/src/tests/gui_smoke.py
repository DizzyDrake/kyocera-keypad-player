"""Run under Xvfb or a local display: python tests/gui_smoke.py."""
import hashlib
import json
import tempfile
from pathlib import Path
from unittest.mock import patch

from integrated_app import IntegratedApp

root = Path(__file__).resolve().parents[1]
phone_path = root / 'sample' / 'fictional_phone_snapshot.json'
phone_hash = hashlib.sha256(phone_path.read_bytes()).hexdigest()
errors = []
with tempfile.TemporaryDirectory() as td:
    td = Path(td)
    ui = IntegratedApp()
    ui.withdraw()
    try:
        assert ui.phone_snapshot is None
        with patch('integrated_app.filedialog.askopenfilename', return_value=str(phone_path)), patch('integrated_app.messagebox.showerror', side_effect=lambda *x: errors.append(x)):
            ui.attach_phone()
        assert not errors, errors
        assert ui.phone_snapshot['revision'] == 7
        assert len(ui.data['tracks']) == 3
        ui.selector.set('My order')
        ui.refresh_playlist()
        ui.plist.selection_set(0)
        ui.shift(1)
        expected = list(ui.current_pl()['track_ids'])
        assert expected[0].endswith('/20'), expected
        plan_path = td / 'plan.json'
        with patch('integrated_app.filedialog.asksaveasfilename', return_value=str(plan_path)), patch('integrated_app.messagebox.showerror', side_effect=lambda *x: errors.append(x)):
            ui.save_plan()
        assert not errors, errors
        plan = json.loads(plan_path.read_text())
        assert plan['operations'][0]['action'] == 'UPDATE'
        assert plan['proposed_playlists'][0]['track_keys'] == expected
        preview_path = td / 'simulated.json'
        with patch('integrated_app.filedialog.asksaveasfilename', return_value=str(preview_path)), patch('integrated_app.messagebox.showerror', side_effect=lambda *x: errors.append(x)):
            ui.save_preview()
        preview = json.loads(preview_path.read_text())
        assert preview['playlists'][0]['track_keys'] == expected
        assert preview['bookmarks'] == ui.phone_snapshot['bookmarks']
        assert preview['revision'] == 8
        before = plan_path.read_bytes()
        with patch('integrated_app.filedialog.asksaveasfilename', return_value=str(plan_path)), patch('integrated_app.messagebox.showerror', side_effect=lambda *x: errors.append(x)):
            ui.save_plan()
        assert len(errors) == 1 and 'already exists' in str(errors[0]), errors
        assert plan_path.read_bytes() == before
        errors.clear()
        editor_path = td / 'edited_pc.json'
        with patch('app.filedialog.asksaveasfilename', return_value=str(editor_path)), patch('app.messagebox.showerror', side_effect=lambda *x: errors.append(x)):
            ui.save_file()
        assert editor_path.exists() and not errors
        with patch('app.filedialog.askopenfilename', return_value=str(editor_path)), patch('app.messagebox.showerror', side_effect=lambda *x: errors.append(x)):
            ui.open_file()
        assert ui.phone_snapshot is None
        with patch('integrated_app.filedialog.askopenfilename', return_value=str(phone_path)), patch('integrated_app.messagebox.showerror', side_effect=lambda *x: errors.append(x)):
            ui.attach_phone()
        assert ui.phone_snapshot is not None
        assert ui.current_pl()['track_ids'] == expected
        assert 'playlists are retained' in ui.status.get()
        assert not errors
        assert hashlib.sha256(phone_path.read_bytes()).hexdigest() == phone_hash
        print('GUI_SMOKE_PASS: single window, snapshot import, reorder, plan, simulate, no-clobber, save/reopen/reattach')
    finally:
        ui.destroy()
