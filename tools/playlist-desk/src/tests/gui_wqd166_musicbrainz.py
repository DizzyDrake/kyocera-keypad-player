"""Synthetic Tk test: opt-in MusicBrainz, no automatic playlist mutation."""
import json,time
from pathlib import Path
from unittest.mock import patch
from integrated_app import IntegratedApp
from proposal_ui import ProposalDialog
from bridge import phone_to_pc
from musicbrainz_lookup import MusicBrainzError

fixture=Path(__file__).resolve().parents[1]/'sample'/'fictional_phone_snapshot.json'
app=IntegratedApp();app.withdraw()
app.data=phone_to_pc(json.loads(fixture.read_text()))
app.update_selector('My order');app.refresh_library();app.refresh_playlist()
d=ProposalDialog(app);d.withdraw()
assert d.tabs.tab(3,'text')=='MusicBrainz (optional)'
assert d._mb_queue is None and not d.mb_results
before=json.dumps(app.data,sort_keys=True)
called=[]
# Synthetic candidate matching an existing local record.
t=app.data['tracks'][0]
record={'mbid':'b16d9e84-a1c4-4d85-8f08-8f760ea94614','artist':t['artist'],'title':t['title'],'albums':[t.get('album','')],'score':100}
d.mb_artist.set(t['artist']);d.mb_title.set(t['title']);d.mb_contact.set('https://example.org/contact')
with patch('proposal_ui.lookup_recordings',side_effect=lambda artist,title,contact: called.append((artist,title,contact)) or [record]):
    d.preview_musicbrainz()
    for _ in range(60):
        app.update()
        if d._mb_queue is None: break
        time.sleep(.03)
assert called==[(t['artist'],t['title'],'https://example.org/contact')],called
assert len(d.mb_results)==1
assert d.mb_button.instate(['!disabled'])
d.mb_list.selection_set(0)
d.compare_musicbrainz()
assert len(d.rows)==1 and d.rows[0]['entry']['source'].startswith('MusicBrainz recording')
assert json.dumps(app.data,sort_keys=True)==before, 'preview must never modify playlists'
# Error path stays opt-in and preserves metadata.
d.mb_artist.set('Artist');d.mb_title.set('Unknown')
with patch('proposal_ui.lookup_recordings',side_effect=MusicBrainzError('synthetic network error')):
    with patch('proposal_ui.messagebox.showerror') as error:
        d.preview_musicbrainz()
        for _ in range(60):
            app.update()
            if d._mb_queue is None: break
            time.sleep(.03)
        assert error.call_count==1
assert json.dumps(app.data,sort_keys=True)==before
d.destroy();app.destroy()
print('GUI_WQD166: PASS explicit request, local ID preview, no mutation, error fallback')
