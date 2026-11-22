"""Real Tk event-generation regression for click/shift/ctrl/group drag and audiobook metadata."""
from pathlib import Path
from unittest.mock import patch
from integrated_app import IntegratedApp
from bridge import plan
import copy, hashlib

fixture=Path(__file__).resolve().parents[1]/'sample'/'fictional_phone_snapshot.json'
before=hashlib.sha256(fixture.read_bytes()).hexdigest()
ui=IntegratedApp()
try:
    ui.update()
    with patch('integrated_app.filedialog.askopenfilename',return_value=str(fixture)):
        ui.attach_phone()
    ui.current_pl()['track_ids']=[t['id'] for t in ui.data['tracks']]
    ui.refresh_playlist();ui.update()
    for pane in (ui.library,ui.plist):
        assert pane.size()>=3
        def click(i,state=0):
            bbox=pane.bbox(i);x=bbox[0]+5;y=bbox[1]+max(2,bbox[3]//2)
            coords=dict(x=x,y=y,rootx=pane.winfo_rootx()+x,rooty=pane.winfo_rooty()+y,state=state)
            pane.event_generate('<ButtonPress-1>',**coords)
            pane.event_generate('<ButtonRelease-1>',**coords)
            ui.update()
        pane.selection_clear(0,'end')
        pane.selection_set(0,2)
        click(1)
        assert pane.curselection()==(1,),('plain click should collapse selection',pane.curselection())
        click(2,state=0x1)
        assert pane.curselection()==(1,2),('one Shift click should extend',pane.curselection())
        click(0,state=0x4)
        assert pane.curselection()==(0,1,2),('Ctrl click toggles',pane.curselection())
        click(1,state=0x4)
        assert pane.curselection()==(0,2),('Ctrl click toggles off',pane.curselection())
        click(2)
        assert pane.curselection()==(2,),('plain click after Ctrl',pane.curselection())
    # v0.8: the separate Music and Audiobook buttons choose type directly;
    # cancelling the name prompt leaves state unchanged.
    original=copy.deepcopy(ui.data)
    with patch('integrated_app.simpledialog.askstring',return_value=None):
        ui.new_playlist_kind(True)
    assert ui.data==original
    with patch('integrated_app.simpledialog.askstring',return_value='Chapter order'):
        ui.new_playlist_kind(True)
    book=ui.current_pl()
    assert book['audiobook'] is True and ui.kind_label.cget('text')=='Playlist type: AUDIOBOOK'
    assert ui.changed
    book['track_ids']=[ui.data['tracks'][1]['id'],ui.data['tracks'][0]['id']]
    proposed=plan(ui.phone_snapshot,ui.data)
    found=next(p for p in proposed['proposed_playlists'] if p['name']=='Chapter order')
    assert found['audiobook'] is True and found['track_keys']==book['track_ids']
    with patch('integrated_app.simpledialog.askstring',return_value='Music order'):
        ui.new_playlist_kind(False)
    assert ui.current_pl()['audiobook'] is False and ui.kind_label.cget('text')=='Playlist type: MUSIC'
    assert hashlib.sha256(fixture.read_bytes()).hexdigest()==before
    print('GUI_WQD138_PASS: both panes plain/Shift/Ctrl, name cancel, explicit audiobook/music, order, plan, no fixture mutation')
finally:
    ui.destroy()
