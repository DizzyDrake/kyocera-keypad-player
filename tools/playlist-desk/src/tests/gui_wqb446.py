"""Linux/Xvfb GUI smoke using fictional metadata and inert M3U text."""
import json
import tempfile
from pathlib import Path
from tkinter import filedialog, messagebox
from bridge import phone_to_pc
from integrated_app import IntegratedApp
from proposal_ui import ProposalDialog

root=Path(__file__).resolve().parents[1]
app=IntegratedApp();app.withdraw()
app.data=phone_to_pc(json.loads((root/'sample/fictional_phone_snapshot.json').read_text()))
app._create_typed_playlist('Imported M3U',audiobook=False)
app.update_selector('Imported M3U');app.refresh_library();app.refresh_playlist()
d=ProposalDialog(app);d.withdraw()
with tempfile.TemporaryDirectory() as tmp:
    f=Path(tmp)/'external.m3u8'
    f.write_text('#EXTM3U\nMusic/Álpha.mp3\n#EXTINF:-1,Imaginary Group - Beta\nhttps://example.invalid/remote.mp3\nMissing.mp3\n',encoding='utf-8')
    orig=filedialog.askopenfilename
    filedialog.askopenfilename=lambda **kw: str(f)
    try:d.load_pasted_file()
    finally:filedialog.askopenfilename=orig
    assert d.pasted_format_hint=='m3u'
    d.preview_pasted()
    assert [r['status'] for r in d.rows]==['MATCH','MATCH','MISSING']
    assert len(d.preview.get(0,'end'))==3
    assert 'Music/Álpha.mp3' in d.preview.get(0)
    ask=messagebox.askyesno
    messagebox.askyesno=lambda *a,**kw:True
    try:d.apply()
    finally:messagebox.askyesno=ask
    assert len(app.current_pl()['track_ids'])==2
    app.undo_last();assert not app.current_pl()['track_ids']
    d2=ProposalDialog(app);d2.withdraw()
    d2.pasted.insert('1.0','#EXTM3U\nMusic/Beta.mp3')
    d2.preview_pasted();assert d2.rows[0]['status']=='MATCH'
    d2.destroy()
app.destroy()
print('GUI_WQB446: PASS local M3U8 import, preview, inert URL, missing, Apply and Undo')
