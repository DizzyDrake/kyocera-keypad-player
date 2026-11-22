"""Xvfb disposable GUI smoke: drag, multi-file add, save, bridge safety."""
import hashlib
import json
import tempfile
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from integrated_app import IntegratedApp

root=Path(__file__).resolve().parents[1]
source=root/'sample'/'fictional_phone_snapshot.json'
before=hashlib.sha256(source.read_bytes()).hexdigest()
errors=[]
ui=IntegratedApp()
try:
    ui.update()
    with patch('integrated_app.filedialog.askopenfilename',return_value=str(source)):
        ui.attach_phone()
    ui.selector.set('My order');ui.refresh_playlist();ui.update()
    ids_before=ui.current_pl()['track_ids'][:]
    assert len(ids_before)>=2
    a=ui.plist.bbox(0);b=ui.plist.bbox(1)
    assert a and b,(a,b)
    ui.plist.selection_set(0)
    x=ui.plist.winfo_rootx()+a[0]+3
    y0=ui.plist.winfo_rooty()+a[1]+3
    y1=ui.plist.winfo_rooty()+b[1]+b[3]-2
    ui._pane_press(SimpleNamespace(x_root=x,y_root=y0,y=a[1]+3,state=0), 'playlist')
    ui._pane_motion(SimpleNamespace(x_root=x,y_root=y1), 'playlist')
    ui._pane_release(SimpleNamespace(x_root=x,y_root=y1), 'playlist')
    assert ui.current_pl()['track_ids']==[ids_before[1],ids_before[0]],ui.current_pl()['track_ids']
    assert ui.changed
    with patch('integrated_app.filedialog.askopenfilenames',return_value=('C:\\Music\\one.mp3','D:\\Audio\\two.flac')):
        ui.add_pc_audio_files()
    assert len(ui.current_pl()['track_ids'])==4
    assert len([t for t in ui.data['tracks'] if t.get('pc_status')])==2
    assert 'PC ONLY' in ui.plist.get(2)
    assert '2 local PC file' in ui.status.get()
    with patch('integrated_app.messagebox.showerror',side_effect=lambda *a:errors.append(a)):
        ui.save_plan()
        ui.save_preview()
        ui.export_m3u8()
    assert len(errors)==3,errors
    assert all('PC' in str(e) or 'pending' in str(e) for e in errors),errors
    with tempfile.TemporaryDirectory() as td:
        out=Path(td)/'edited.json'
        with patch('app.filedialog.asksaveasfilename',return_value=str(out)):
            ui.save_file()
        data=json.loads(out.read_text())
        assert data['playlists'][0]['track_ids']==ui.current_pl()['track_ids']
        assert len([t for t in data['tracks'] if t.get('pc_local_file')])==2
    # Confirm protected-drive rejection without accessing any file.
    with patch('integrated_app.filedialog.askopenfilenames',return_value=('F:\\DO_NOT_TOUCH\\song.mp3',)),patch('integrated_app.messagebox.showerror',side_effect=lambda *a:errors.append(a)):
        snapshot=json.dumps(ui.data,sort_keys=True)
        ui.add_pc_audio_files()
        assert json.dumps(ui.data,sort_keys=True)==snapshot
    assert len(errors)==4
    # Removing both pending rows should restore the original phone track inventory.
    for _ in range(2):
        ui.plist.selection_clear(0,'end')
        ui.plist.selection_set(2)
        ui.remove_selected()
    assert len(ui.data['tracks'])==3
    assert len(ui.current_pl()['track_ids'])==2
    with tempfile.TemporaryDirectory() as td:
        target=Path(td)/'after_remove_plan.json'
        with patch('integrated_app.filedialog.asksaveasfilename',return_value=str(target)):
            ui.save_plan()
        assert target.exists(), 'bridge plan should work again after pending tracks removed'
    assert hashlib.sha256(source.read_bytes()).hexdigest()==before
    print('GUI_WQD137_PASS: mouse reorder, multi-file stage, save order, 3 bridge/export refusals, F: rejected')
finally:
    ui.destroy()
