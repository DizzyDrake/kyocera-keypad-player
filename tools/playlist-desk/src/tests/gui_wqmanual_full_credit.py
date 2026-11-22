"""Real Tk Xvfb synthetic regression. No Ollama, owner library, or phone used."""
import json
import time
from pathlib import Path
from unittest.mock import patch
from bridge import phone_to_pc
from integrated_app import IntegratedApp
from proposal_ui import ProposalDialog

fixture=Path(__file__).resolve().parents[1]/'sample'/'fictional_phone_snapshot.json'
app=IntegratedApp(); app.withdraw()
app.data=phone_to_pc(json.loads(fixture.read_text(encoding='utf-8')))
for i, name in enumerate(('The','The The','The Beatles')):
    app.data['tracks'][i]['artist']=name
app.update_selector('My order'); app.refresh_library(); app.refresh_playlist()
initial={p['name']:tuple(p['track_ids']) for p in app.data['playlists']}
d=ProposalDialog(app); d.withdraw()

def query(text, *, no_model=True):
    d.gemma_request.delete('1.0','end'); d.gemma_request.insert('1.0',text)
    if no_model:
        with patch('proposal_ui.request_local_model', side_effect=AssertionError('unexpected Ollama call')):
            d.preview_gemma()
    else:
        d.preview_gemma()

def ids():
    return [r['chosen_id'] for r in d.rows]

def pump():
    for _ in range(90):
        app.update()
        if d._gemma_queue is None: return
        time.sleep(.02)
    raise AssertionError('model preview worker did not complete')

try:
    with patch('proposal_ui.messagebox.showerror') as error:
        query('songs by The')
        assert ids()==[app.data['tracks'][0]['id']],ids()
        assert not error.called
        query('songs by The The')
        assert ids()==[app.data['tracks'][1]['id']],ids()
        query('songs by Beatles')
        assert error.called,'explicit unmatched artist must raise a user-facing error'
        assert not d.rows and d.snapshot_signature is None,'stale preview remains'
        error.reset_mock()
        query('songs by The Beatles')
        assert ids()==[app.data['tracks'][2]['id']],ids()
        assert not error.called

    with patch('proposal_ui.request_local_model',return_value=([1],0)) as model:
        query('something energetic',no_model=False)
        pump()
        assert model.call_count==1
        assert len(d.rows)==1 and 'Gemma suggested' in d.summary.get()

    # Inject fictional distinct artist credits; verify 21-pair model response is
    # rejected in the actual UI, with stale previous proposal removed.
    for i in range(21):
        app.data['tracks'].append({'id':f'fictional-extra-{i}','artist':f'Fictional Artist {i}',
                                   'album':f'Fictional Album {i}','title':f'Fictional Track {i}',
                                   'path':f'Music/Fictional-{i}.mp3'})
    with patch('proposal_ui.messagebox.showerror') as error, patch('proposal_ui.request_local_model',return_value=(list(range(1,22)),0)) as model:
        query('something different',no_model=False)
        pump()
        assert model.call_count==1
        assert error.called,'oversized model proposal must give a visible error'
        assert not d.rows and d.snapshot_signature is None
        assert 'too broad' in d.summary.get()
    assert {p['name']:tuple(p['track_ids']) for p in app.data['playlists']}==initial
    print('GUI_WQMANUAL_FULL_CREDIT: PASS 7 cases; all playlist orders unchanged')
finally:
    d.destroy(); app.destroy()
