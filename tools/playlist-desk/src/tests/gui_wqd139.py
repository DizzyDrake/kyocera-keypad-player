"""Synthetic Xvfb/Tk checks for v0.8 owner-requested mouse UX. No owner data."""
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
import hashlib
import tkinter as tk
from integrated_app import IntegratedApp

fixture=Path(__file__).resolve().parents[1]/'sample'/'fictional_phone_snapshot.json'
source_hash=hashlib.sha256(fixture.read_bytes()).hexdigest()
ui=IntegratedApp()
try:
    ui.update()
    with patch('integrated_app.filedialog.askopenfilename',return_value=str(fixture)):
        ui.attach_phone()
    # The owner gets two buttons in the same playlist control row, no type dialog.
    buttons=[w for w in ui.playlist_actions.pack_slaves() if isinstance(w,tk.ttk.Button)]
    labels=[b.cget('text') for b in buttons]
    assert labels[:2]==['New Music','New Audiobook'],labels
    with patch('integrated_app.simpledialog.askstring',return_value='Story sample'),patch('integrated_app.messagebox.askyesnocancel',side_effect=AssertionError('type dialog must not appear')):
        buttons[1].invoke()
    assert ui.current_pl()['audiobook'] is True
    with patch('integrated_app.simpledialog.askstring',return_value='Music sample'),patch('integrated_app.messagebox.askyesnocancel',side_effect=AssertionError('type dialog must not appear')):
        buttons[0].invoke()
    assert ui.current_pl()['audiobook'] is False
    # Add enough *fictional* rows to make vertical scrolling observable.
    template=ui.data['tracks'][0].copy()
    for i in range(100):
        track=template.copy()
        track['id']=f'WQD139-fixture-{i}'
        track['title']=f'Synthetic Track {i:03d}'
        track['path']=f'Music/Synthetic/VeryLongFictionalPathForHorizontalScroll{i:03d}.mp3'
        ui.data['tracks'].append(track)
    ui.current_pl()['track_ids']=[t['id'] for t in ui.data['tracks']]
    ui.refresh_library();ui.refresh_playlist();ui.update()
    assert ui.library.size()>50 and ui.plist.size()>50
    for pane in (ui.library,ui.plist):
        pane.selection_clear(0,'end');pane.selection_set(2);pane.selection_anchor(2)
        before=pane.curselection()
        y_before=pane.yview()[0]
        pane.event_generate('<MouseWheel>',delta=-120,x=20,y=20)
        ui.update()
        assert pane.curselection()==before,('wheel changed selection',pane.curselection())
        assert pane.yview()[0]>y_before,('wheel failed to scroll',pane.yview())
        pane.event_generate('<Button-4>',x=20,y=20)
        ui.update()
        assert pane.curselection()==before,('button-4 changed selection',pane.curselection())
        # A held pointer leaving the listbox must not activate Tk's autoscan.
        pane.event_generate('<B1-Leave>',x=-20,y=20)
        ui.update()
        assert pane.curselection()==before,('B1-Leave changed selection',pane.curselection())
    # Draw a thin insertion cue on playlist, without altering playlist rows.
    x=ui.plist.winfo_rootx()+20
    bbox=ui.plist.bbox(2)
    y=ui.plist.winfo_rooty()+bbox[1]+3
    event=SimpleNamespace(x_root=x,y_root=y)
    count=ui.plist.size()
    ui._update_drop_indicator(event,'library');ui.update()
    assert ui._drop_marker.winfo_manager()=='place', 'no visible insertion line'
    assert ui.plist.size()==count, 'preview must not alter list'
    marker_y=int(ui._drop_marker.place_info()['y'])
    ui._update_drop_indicator(SimpleNamespace(x_root=x,y_root=y+20),'library');ui.update()
    assert int(ui._drop_marker.place_info()['y'])!=marker_y, 'marker must track boundary'
    ui._hide_drop_indicator();ui.update()
    assert not ui._drop_marker.winfo_manager(), 'marker remains after drag'
    # An unsupported library->library drag restores its previous x offset.
    ui.library.xview_moveto(0.2);ui.update()
    start_x=ui.library.xview()[0]
    a=ui.library.bbox(2);b=ui.library.bbox(3)
    assert a and b
    press=SimpleNamespace(state=0,y=a[1]+3,x_root=ui.library.winfo_rootx()+10,y_root=ui.library.winfo_rooty()+a[1]+3)
    ui._pane_press(press,'library')
    ui.library.xview_moveto(0.4)
    release=SimpleNamespace(x_root=press.x_root+12,y_root=ui.library.winfo_rooty()+b[1]+3)
    ui._pane_release(release,'library')
    assert abs(ui.library.xview()[0]-start_x)<0.02,(ui.library.xview(),start_x)
    assert ui._drop_marker.winfo_manager()=='', 'release must hide marker'
    # End-to-end library -> playlist drag while the insertion marker is present.
    ui._create_typed_playlist('Drag target', audiobook=False)
    ui.update_selector('Drag target');ui.refresh_playlist();ui.update()
    a=ui.library.bbox(3)
    source=SimpleNamespace(state=0,y=a[1]+3,
                           x_root=ui.library.winfo_rootx()+20,
                           y_root=ui.library.winfo_rooty()+a[1]+3)
    ui._pane_press(source,'library')
    tx=ui.plist.winfo_rootx()+20;ty=ui.plist.winfo_rooty()+8
    target_event=SimpleNamespace(x_root=tx,y_root=ty)
    ui._pane_motion(target_event,'library');ui.update()
    assert ui._drop_marker.winfo_manager()=='place'
    ui._pane_release(target_event,'library');ui.update()
    assert ui.current_pl()['track_ids']==[ui.filtered[3]],ui.current_pl()['track_ids']
    assert ui._drop_marker.winfo_manager()=='', 'marker remains after cross-pane drop'
    # Owner's actual player colors are reflected in Tk style and listboxes.
    assert ui.library.cget('selectbackground').lower()=='#d6a6ad'
    assert ui.plist.cget('foreground').lower()=='#252022'
    assert ui.tk.call('ttk::style','configure','Header.TFrame','-background').lower()=='#713e46'
    assert hashlib.sha256(fixture.read_bytes()).hexdigest()==source_hash
    print('GUI_WQD139_PASS: typed buttons, scroll-selection isolation, B1-Leave, insertion cue, xview restore, source-grounded palette')
finally:
    ui.destroy()
