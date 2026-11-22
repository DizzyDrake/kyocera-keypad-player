"""Real Tk bind-dispatch smoke: multi-selection survives a drag gesture."""
from pathlib import Path
from unittest.mock import patch
from integrated_app import IntegratedApp
ui=IntegratedApp()
try:
 ui.update()
 with patch('integrated_app.filedialog.askopenfilename',return_value=str(Path(__file__).resolve().parents[1]/'sample'/'fictional_phone_snapshot.json')):
  ui.attach_phone()
 ui.current_pl()['track_ids']=[]
 ui.refresh_playlist();ui.update()
 ui.library.selection_set(0,1)
 b=ui.library.bbox(0)
 x=b[0]+5;y=b[1]+3
 # Generate real Tk events on source listbox with release root coordinates over destination.
 ui.library.event_generate('<ButtonPress-1>',x=x,y=y,rootx=ui.library.winfo_rootx()+x,rooty=ui.library.winfo_rooty()+y)
 ui.update()
 assert ui.library.curselection()==(0,1),ui.library.curselection()
 ui.library.event_generate('<B1-Motion>',x=ui.library.winfo_width()+25,y=y,rootx=ui.plist.winfo_rootx()+10,rooty=ui.plist.winfo_rooty()+10)
 ui.library.event_generate('<ButtonRelease-1>',x=ui.library.winfo_width()+25,y=y,rootx=ui.plist.winfo_rootx()+10,rooty=ui.plist.winfo_rooty()+10)
 ui.update()
 assert len(ui.current_pl()['track_ids'])==2,ui.current_pl()
 print('GUI_EVENT_GENERATE_PASS: Tk binding dispatch retained two selected rows and cross-pane drop added both')
finally: ui.destroy()
