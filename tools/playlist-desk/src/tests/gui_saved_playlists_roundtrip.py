"""Existing Playlist Desk Save As JSON survives refreshed phone snapshot and exports to phone.
Synthetic GUI test: no phone, USB, ADB, or personal media.
"""
import copy
import json
import tempfile
from pathlib import Path
from unittest.mock import patch

from integrated_app import IntegratedApp
from bridge import phone_to_pc, IMPORT_SCHEMA

fixture = Path(__file__).resolve().parents[1]/'sample/dev8_fictional_phone_export.json'
source_phone = json.loads(fixture.read_text())
editor = phone_to_pc(source_phone)
editor['playlists'][0]['track_ids'].reverse()
editor['playlists'].append({'name':'Already organized!', 'track_ids':editor['playlists'][0]['track_ids'][:], 'audiobook':False})
phone_after = copy.deepcopy(source_phone)
phone_after['snapshot_id'] = 'appstate-changed-since-original-save'
with tempfile.TemporaryDirectory() as tmp:
    tmp = Path(tmp)
    saved = tmp/'saved_playlists.json'
    phone = tmp/'refreshed_phone.json'
    output = tmp/'new_import.json'
    saved.write_text(json.dumps(editor))
    phone.write_text(json.dumps(phone_after))
    ui=IntegratedApp(); ui.withdraw()
    try:
        with patch('app.filedialog.askopenfilename',return_value=str(saved)):
            ui.open_file()
        assert ui.data['playlists'][0]['track_ids'] == editor['playlists'][0]['track_ids']
        with patch('integrated_app.filedialog.askopenfilename',return_value=str(phone)), \
             patch('integrated_app.messagebox.askyesno',return_value=True):
            ui.attach_phone()
        assert ui.data['playlists'][0]['track_ids'] == editor['playlists'][0]['track_ids']
        assert ui.data['playlists'][-1]['name'] == 'Already organized!'
        with patch('integrated_app.filedialog.asksaveasfilename',return_value=str(output)), \
             patch('integrated_app.messagebox.askyesno',return_value=True):
            ui.create_phone_import()
        result=json.loads(output.read_text())
        assert result['schema']==IMPORT_SCHEMA
        assert result['expected_snapshot_id']==phone_after['snapshot_id']
        assert result['playlists'][0]['track_keys']==editor['playlists'][0]['track_ids']
        assert result['playlists'][-1]['name']=='Already organized!'
        assert json.loads(saved.read_text())==editor
        print('GUI_SAVED_PLAYLISTS_PASS: saved editor JSON + refreshed phone snapshot -> matching phone import; originals preserved')
    finally:
        ui.destroy()
