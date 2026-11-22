"""Synthetic Xvfb UI test: opt-in, no silent model requests, preview and stale guard."""
import json
import time
from pathlib import Path
from unittest.mock import patch
from integrated_app import IntegratedApp
from proposal_ui import ProposalDialog
from bridge import phone_to_pc
from tkinter import messagebox

fixture=Path(__file__).resolve().parents[1]/'sample'/'fictional_phone_snapshot.json'
app=IntegratedApp();app.withdraw()
app.data=phone_to_pc(json.loads(fixture.read_text()))
app.update_selector('My order');app.refresh_library();app.refresh_playlist()
d=ProposalDialog(app);d.withdraw()
assert d._gemma_queue is None and not d.rows
assert d.tabs.tab(2,'text')=='Optional local Gemma'
d.gemma_request.insert('1.0','choose Imaginary Group Example')
called=[]
def fake(request,pairs,model):
    called.append((request,len(pairs),model))
    return ([1],0)
with patch('proposal_ui.request_local_model',side_effect=fake):
    d.preview_gemma()
    for _ in range(60):
        app.update()
        if d._gemma_queue is None: break
        time.sleep(.03)
assert len(called)==1,called
assert len(d.rows)==2 and all(r['chosen_id'] for r in d.rows)
assert d.gemma_button.instate(['!disabled'])
assert '2 actual local tracks' in d.summary.get()
# Stale data must invalidate an in-flight suggestion rather than attach to new metadata.
d.gemma_request.delete('1.0','end');d.gemma_request.insert('1.0','author')
with patch('proposal_ui.request_local_model',side_effect=lambda *a: ([2],0)):
    d.preview_gemma()
    app.data['tracks'][0]['artist']='Changed during response'
    for _ in range(60):
        app.update()
        if d._gemma_queue is None: break
        time.sleep(.03)
assert 'changed while' in d.summary.get(),d.summary.get()
d.destroy();app.destroy()
print('GUI_WQB445: PASS opt-in-only / model preview / real IDs / stale metadata rejection')
