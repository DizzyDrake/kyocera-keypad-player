"""Linux Tk synthetic GUI regression for PC file reuse and last-reference pruning."""
from pathlib import Path
from unittest.mock import patch
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from integrated_app import IntegratedApp
from pc_file_add import any_pending_files

ui = IntegratedApp()
try:
    ui.update()
    with patch('integrated_app.filedialog.askopenfilename', return_value=str(Path(__file__).resolve().parents[1] / 'sample' / 'fictional_phone_snapshot.json')):
        ui.attach_phone()
    ui._create_typed_playlist('A', False)
    ui._create_typed_playlist('B', True)
    ui.update_selector('A')
    with patch('integrated_app.filedialog.askopenfilenames', return_value=('C:\\Fictional\\shared.mp3',)):
        ui.add_pc_audio_files()
    tid = ui.current_pl()['track_ids'][0]
    inventory = len(ui.data['tracks'])
    ui.update_selector('B')
    with patch('integrated_app.filedialog.askopenfilenames', return_value=('c:\\fictional\\SHARED.MP3',)):
        ui.add_pc_audio_files()
    assert ui.current_pl()['track_ids'] == [tid]
    assert len(ui.data['tracks']) == inventory
    assert '1 local PC file(s) staged' in ui.status.get(), ui.status.get()
    # Repeated selection within B must not duplicate its entry.
    with patch('integrated_app.filedialog.askopenfilenames', return_value=('C:\\Fictional\\shared.mp3',)):
        ui.add_pc_audio_files()
    assert ui.current_pl()['track_ids'] == [tid]
    assert '1 duplicate(s) skipped' in ui.status.get()
    # Removing A's reference must preserve the B reference and global track.
    ui.update_selector('A')
    ui.plist.selection_clear(0, 'end'); ui.plist.selection_set(0)
    ui.remove_selected()
    assert any_pending_files(ui.data)
    assert len(ui.data['tracks']) == inventory
    ui.update_selector('B')
    assert ui.current_pl()['track_ids'] == [tid]
    ui.plist.selection_clear(0, 'end'); ui.plist.selection_set(0)
    ui.remove_selected()
    assert not any_pending_files(ui.data)
    assert len(ui.data['tracks']) == inventory - 1
    print('GUI_WQB458_PASS: two playlists share one PC-only track ID; duplicate same list skipped; first removal preserves; last removal prunes')
finally:
    ui.destroy()
