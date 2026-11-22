"""Real Tk under virtual Linux display; only fictional snapshot and mocked model."""
import json
import time
from pathlib import Path
from unittest.mock import patch

from integrated_app import IntegratedApp
from proposal_ui import ProposalDialog
from bridge import phone_to_pc

fixture = Path(__file__).resolve().parents[1] / 'sample' / 'fictional_phone_snapshot.json'
app = IntegratedApp(); app.withdraw()
app.data = phone_to_pc(json.loads(fixture.read_text(encoding='utf-8')))
app.update_selector('My order'); app.refresh_library(); app.refresh_playlist()
d = ProposalDialog(app); d.withdraw()
try:
    assert d.model_name.get() == 'gemma4:12b', d.model_name.get()
    d.gemma_request.insert('1.0', 'Imaginary Group')
    with patch('proposal_ui.request_local_model', side_effect=AssertionError('Ollama should NOT be contacted')):
        d.preview_gemma()
    assert [r['chosen_id'] for r in d.rows] == [t['id'] for t in app.data['tracks'][:2]]
    assert 'Ollama was not contacted' in d.summary.get(), d.summary.get()
    d.gemma_request.delete('1.0','end')
    d.gemma_request.insert('1.0', 'find songs by Not In Library')
    with patch('proposal_ui.messagebox.showerror') as error, patch('proposal_ui.request_local_model', side_effect=AssertionError('no HTTP for explicit missing artist')):
        d.preview_gemma()
    assert error.called
    assert not d.rows, 'failed new preview must clear previous match'
    assert d.snapshot_signature is None

    d.gemma_request.delete('1.0','end')
    d.gemma_request.insert('1.0', 'Choose something imaginative')
    with patch('proposal_ui.request_local_model', return_value=([1],0)) as model:
        d.preview_gemma()
        for _ in range(80):
            app.update()
            if d._gemma_queue is None: break
            time.sleep(.02)
    assert model.call_count == 1
    assert d.rows and 'Gemma suggested' in d.summary.get(),d.summary.get()
    assert d._gemma_queue is None
    print('GUI_ARTIST_FIRST: PASS local-only direct / missing reject & clear / ambiguous opt-in model')
finally:
    d.destroy(); app.destroy()
