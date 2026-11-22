"""Disposable Xvfb GUI smoke for two-pane multi-selection, DnD and undo."""
import copy
import hashlib
import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from integrated_app import IntegratedApp

source=Path(__file__).resolve().parents[1]/'sample'/'fictional_phone_snapshot.json'
hash_before=hashlib.sha256(source.read_bytes()).hexdigest()
ui=IntegratedApp()
try:
    ui.update()
    with patch('integrated_app.filedialog.askopenfilename',return_value=str(source)):
        ui.attach_phone()
    ui.selector.set('My order');ui.refresh_playlist();ui.update()
    assert ui.library.cget('selectmode')=='extended'
    assert ui.plist.cget('selectmode')=='extended'
    assert ui.library.size()>=3
    assert ui.plist.size()==2
    old=copy.deepcopy(ui.data)
    ui.current_pl()['track_ids'] = []  # disposable in-memory blank playlist for multi-add
    ui.refresh_playlist();ui.update()
    empty=copy.deepcopy(ui.data)
    # Select two rows on library and drag them onto playlist, adding both.
    ui.library.selection_set(0,1)
    b0=ui.library.bbox(0)
    x0=ui.library.winfo_rootx()+b0[0]+5;y0=ui.library.winfo_rooty()+b0[1]+3
    x1=ui.plist.winfo_rootx()+5;y1=ui.plist.winfo_rooty()+5
    ui._pane_press(SimpleNamespace(x_root=x0,y_root=y0,y=b0[1]+3,state=0),'library')
    ui._pane_release(SimpleNamespace(x_root=x1,y_root=y1),'library')
    assert ui.current_pl()['track_ids'][:2]==[ui.filtered[0],ui.filtered[1]],ui.current_pl()
    assert len(ui.current_pl()['track_ids'])==2
    ui.undo_last()
    assert ui.data==empty
    ui.data=copy.deepcopy(old);ui.refresh_playlist();ui._undo.clear();ui.update()
    # Select two playlist occurrences, reorder to end as a group.
    ui.plist.selection_set(0,1)
    p0=ui.plist.bbox(0);p1=ui.plist.bbox(1)
    x=ui.plist.winfo_rootx()+p0[0]+5
    y0=ui.plist.winfo_rooty()+p0[1]+3
    y1=ui.plist.winfo_rooty()+p1[1]+p1[3]-2
    ui._pane_press(SimpleNamespace(x_root=x,y_root=y0,y=p0[1]+3,state=0),'playlist')
    ui._pane_release(SimpleNamespace(x_root=x,y_root=y1),'playlist')
    assert ui.data==old  # entire 2-track group cannot reorder itself
    # Add third track then remove two playlist references via drag to library.
    ui.library.selection_clear(0,'end');ui.library.selection_set(2)
    ui.add_selected();ui.update()
    before_remove=copy.deepcopy(ui.data)
    ui.plist.selection_clear(0,'end');ui.plist.selection_set(0,1)
    p0=ui.plist.bbox(0);l0=ui.library.bbox(0)
    x0=ui.plist.winfo_rootx()+p0[0]+5;y0=ui.plist.winfo_rooty()+p0[1]+3
    x1=ui.library.winfo_rootx()+l0[0]+5;y1=ui.library.winfo_rooty()+l0[1]+3
    ui._pane_press(SimpleNamespace(x_root=x0,y_root=y0,y=p0[1]+3,state=0),'playlist')
    ui._pane_release(SimpleNamespace(x_root=x1,y_root=y1),'playlist')
    assert len(ui.current_pl()['track_ids'])==1,ui.current_pl()
    assert len(ui.data['tracks'])==3 # no deletion of actual library tracks
    ui.undo_last()
    assert ui.data==before_remove
    # Ctrl+A should select all in each pane.
    ui._select_all(None,ui.library);assert len(ui.library.curselection())==3
    ui._select_all(None,ui.plist);assert len(ui.plist.curselection())==3
    assert hashlib.sha256(source.read_bytes()).hexdigest()==hash_before
    print('GUI_WQB442_PASS: both extended-select, library->playlist multi-add, playlist->library multi-remove, undo, no source mutation')
finally:
    ui.destroy()
