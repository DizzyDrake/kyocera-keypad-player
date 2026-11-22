"""Real-Tk offline comma-search smoke test; fictional metadata only."""
import json
from pathlib import Path
from bridge import phone_to_pc
from integrated_app import IntegratedApp

fixture = Path(__file__).resolve().parents[1] / 'sample' / 'fictional_phone_snapshot.json'
app = IntegratedApp()
app.withdraw()
try:
    app.data = phone_to_pc(json.loads(fixture.read_text(encoding='utf-8')))
    variants = [
        ('Blue Jazz Live', 'Jazz'),
        ('Blue Jazz Studio', 'Jazz'),
        ('Soft Blues Studio', 'Blues'),
    ]
    for track, (name, genre) in zip(app.data['tracks'], variants):
        track['title'] = name
        track['genre'] = genre
    app.update_selector('My order')
    original_playlists = [(p['name'], tuple(p['track_ids'])) for p in app.data['playlists']]
    app.refresh_library()
    expected = [track['id'] for track in app.data['tracks']]
    app.query.set('jazz, blues')
    app.update()
    assert app.filtered == expected, ('OR', app.filtered, expected)
    assert app.library.size() == 3
    app.query.set('jazz, blues, NOT live')
    app.update()
    assert app.filtered == expected[1:], ('OR plus NOT', app.filtered)
    assert app.library.size() == 2
    app.query.set('NOT live, NOT blues')
    app.update()
    assert app.filtered == [expected[1]], ('multiple NOT', app.filtered)
    assert app.library.size() == 1
    app.query.set('jazz NOT live')
    app.update()
    assert app.filtered == [expected[1]], ('legacy query', app.filtered)
    assert [(p['name'], tuple(p['track_ids'])) for p in app.data['playlists']] == original_playlists
    assert not app.changed, 'filter must not create unsaved playlist edits'
    print('GUI_COMMA_FILTER: PASS 4 filter paths, playlist unchanged')
finally:
    app.destroy()
