"""Synthetic Tk test of new manual phone import file. No USB/ADB/phone/media writes."""
import hashlib
import json
import tempfile
from pathlib import Path
from unittest.mock import patch

from integrated_app import IntegratedApp
from bridge import IMPORT_FILENAME, IMPORT_SCHEMA

fixture=Path(__file__).resolve().parents[1]/'sample/fictional_phone_snapshot.json'
fixture_hash=hashlib.sha256(fixture.read_bytes()).hexdigest()
ui=IntegratedApp(); ui.withdraw()
try:
    with patch('integrated_app.filedialog.askopenfilename',return_value=str(fixture)):
        ui.attach_phone()
    assert ui.phone_snapshot is not None
    ui.data['playlists'][0]['track_ids'].reverse()
    with tempfile.TemporaryDirectory() as tmp:
        file=Path(tmp)/IMPORT_FILENAME
        errs=[]
        with patch('integrated_app.messagebox.askyesno',return_value=True), \
             patch('integrated_app.filedialog.asksaveasfilename',return_value=str(file)), \
             patch('integrated_app.messagebox.showerror',side_effect=lambda *e: errs.append(e)):
            ui.create_phone_import()
        assert not errs,errs
        payload=json.loads(file.read_text())
        assert payload['schema']==IMPORT_SCHEMA
        assert payload['expected_snapshot_id']==ui.phone_snapshot['snapshot_id']
        assert payload['playlists'][0]['track_keys']==ui.data['playlists'][0]['track_ids']
        assert not any(k in payload for k in ('music','book','tracks','bookmarks'))
        assert 'Use ADB' in ui.status.get()
        old=file.read_bytes()
        with patch('integrated_app.messagebox.askyesno',return_value=True), \
             patch('integrated_app.filedialog.asksaveasfilename',return_value=str(file)), \
             patch('integrated_app.messagebox.showerror',side_effect=lambda *e: errs.append(e)):
            ui.create_phone_import()
        assert errs and 'already exists' in str(errs[-1]),errs
        assert file.read_bytes()==old
    assert hashlib.sha256(fixture.read_bytes()).hexdigest()==fixture_hash
    print('GUI_PC_PHONE_IMPORT_PASS: import JSON, exact ID, manual ADB, no clobber, fixture unchanged')
finally:
    ui.destroy()
