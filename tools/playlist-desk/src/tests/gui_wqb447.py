"""Synthetic Tk regression for stale M3U hint and explicit format choice."""
import json, tempfile
from pathlib import Path
from tkinter import filedialog, messagebox
from bridge import phone_to_pc
from integrated_app import IntegratedApp
from proposal_ui import ProposalDialog

root=Path(__file__).resolve().parents[1]
app=IntegratedApp(); app.withdraw()
app.data=phone_to_pc(json.loads((root/'sample/fictional_phone_snapshot.json').read_text()))
app._create_typed_playlist('Format test',audiobook=False)
app.update_selector('Format test'); app.refresh_library(); app.refresh_playlist()
d=ProposalDialog(app); d.withdraw()
with tempfile.TemporaryDirectory() as tmp:
    f=Path(tmp)/'sample.m3u8'; f.write_text('Music/Álpha.mp3\n',encoding='utf-8')
    orig=filedialog.askopenfilename; filedialog.askopenfilename=lambda **kw:str(f)
    try:d.load_pasted_file()
    finally:filedialog.askopenfilename=orig
    assert d.list_format.get()=='Auto detect'
    d.preview_pasted(); assert d.mode=='m3u' and d.rows[0]['status']=='MATCH'
    # Replacing imported M3U text with a CSV is no longer forced to M3U.
    d.pasted.delete('1.0','end'); d.pasted.insert('1.0','artist,title\nImaginary Group,Beta')
    d.preview_pasted(); assert d.mode=='pasted' and d.rows[0]['status']=='MATCH'
    # Explicit override is visible and wins even for headerless edited M3U.
    d.pasted.delete('1.0','end'); d.pasted.insert('1.0','Music/Álpha.mp3')
    d.list_format.set('M3U/M3U8')
    d.preview_pasted(); assert d.mode=='m3u' and d.rows[0]['status']=='MATCH'
    d.list_format.set('Artist/title or CSV')
    d.pasted.delete('1.0','end'); d.pasted.insert('1.0','Imaginary Group - Beta')
    d.preview_pasted(); assert d.mode=='pasted' and d.rows[0]['status']=='MATCH'
    # Re-importing a CSV resets any prior manual M3U override to Auto.
    csv=Path(tmp)/'sample.csv'; csv.write_text('artist,title\nImaginary Group,Beta',encoding='utf-8')
    filedialog.askopenfilename=lambda **kw:str(csv)
    try:d.load_pasted_file()
    finally:filedialog.askopenfilename=orig
    assert d.list_format.get()=='Auto detect'
    d.preview_pasted(); assert d.mode=='pasted' and d.rows[0]['status']=='MATCH'
d.destroy(); app.destroy()
print('GUI_WQB447: PASS M3U file, edited CSV, manual mode override and reimport')
