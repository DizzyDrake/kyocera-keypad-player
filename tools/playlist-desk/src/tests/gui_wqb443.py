"""Disposable Xvfb smoke: UI previews, real IDs, explicit Apply, undo, no file writes."""
import tkinter as tk
from tkinter import filedialog, messagebox
import tempfile
from pathlib import Path
from integrated_app import IntegratedApp
from proposal_ui import ProposalDialog
from playlist_match import resolved_ids
from bridge import phone_to_pc
import json

sample=Path(__file__).resolve().parents[1]/'sample'/'fictional_phone_snapshot.json'
phone=json.loads(sample.read_text())
app=IntegratedApp();app.withdraw();app.data=phone_to_pc(phone);app.update_selector('My order')
app.refresh_library();app.refresh_playlist()
assert len(app.data['playlists'][0]['track_ids'])==2
app._create_typed_playlist('Imported',audiobook=False)
app.update_selector('Imported')
d=ProposalDialog(app);d.withdraw()
d.artist.set('Imaginary Group');d.album.set('Example');d.preview_artist()
assert len(d.rows)==2 and all(x['chosen_id'] for x in d.rows)
assert resolved_ids(d.rows)[0]==[x['id'] for x in app.data['tracks'][:2]]
# simulate user confirmation, not file writes
original=messagebox.askyesno
messagebox.askyesno=lambda *a,**kw: True
try: d.apply()
finally: messagebox.askyesno=original
assert app.current_pl()['track_ids']==[x['id'] for x in app.data['tracks'][:2]]
assert app.changed
app.undo_last()
assert app.current_pl()['track_ids']==[]
# New dialog with ambiguous pasted list requires manual resolution.
d2=ProposalDialog(app);d2.withdraw();d2.tabs.select(1)
with tempfile.TemporaryDirectory() as tmp:
    fixture=Path(tmp)/'external.csv'
    fixture.write_text('artist,title,album\nImaginary Group,Beta,Example\n', encoding='utf-8')
    original_dialog=filedialog.askopenfilename
    filedialog.askopenfilename=lambda **kw: str(fixture)
    try: d2.load_pasted_file()
    finally: filedialog.askopenfilename=original_dialog
    assert 'Imaginary Group,Beta,Example' in d2.pasted.get('1.0','end')

d2.pasted.delete('1.0','end')
d2.pasted.insert('1.0','Imaginary Group - Beta\nMissing Artist - Lost Song')
d2.preview_pasted()
assert d2.rows[0]['status']=='MATCH' and d2.rows[1]['status']=='MISSING'
d2.destroy();app.destroy()
print('GUI_WQB443: PASS preview/append/undo/ambiguous-safe/missing-safe')
