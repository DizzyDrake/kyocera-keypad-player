"""Linux Tk/Xvfb GUI: stage POSIX audio paths, save/reopen JSON, no media access."""
import hashlib
import json
import tempfile
from pathlib import Path
from unittest.mock import patch
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from integrated_app import IntegratedApp

source = Path(__file__).resolve().parents[1] / 'sample' / 'fictional_phone_snapshot.json'
original_hash = hashlib.sha256(source.read_bytes()).hexdigest()
ui = IntegratedApp()
ui.withdraw()
try:
    with patch('integrated_app.filedialog.askopenfilename', return_value=str(source)):
        ui.attach_phone()
    ui.selector.set('My order')
    ui.refresh_playlist()
    before = len(ui.data['tracks'])
    fake_files = ('/home/example/Música/First.mp3', '/home/example/Música/Second.flac')
    with patch('integrated_app.filedialog.askopenfilenames', return_value=fake_files):
        ui.add_pc_audio_files()
    assert len(ui.data['tracks']) == before + 2
    assert len([t for t in ui.data['tracks'] if t.get('pc_status')]) == 2
    assert '2 local PC file(s) staged' in ui.status.get(), ui.status.get()
    with tempfile.TemporaryDirectory() as td:
        output = Path(td) / 'linux_saved_playlist.json'
        with patch('app.filedialog.asksaveasfilename', return_value=str(output)):
            ui.save_file()
        saved = json.loads(output.read_text(encoding='utf-8'))
        pending = [t for t in saved['tracks'] if t.get('pc_status')]
        assert [t['pc_local_file'] for t in pending] == list(fake_files)
        with patch('app.filedialog.askopenfilename', return_value=str(output)):
            ui.open_file()
        assert len([t for t in ui.data['tracks'] if t.get('pc_status')]) == 2
    assert hashlib.sha256(source.read_bytes()).hexdigest() == original_hash
    print('GUI_LINUX_PORT_PASS: Linux paths staged, offline save/reopen, fictional source untouched')
finally:
    ui.destroy()
