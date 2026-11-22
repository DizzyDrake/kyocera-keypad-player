import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from app import App
app=App();app.withdraw()
app.data={'playlists':[{'name':'Alpha','track_ids':[]},{'name':'Beta','track_ids':[]},{'name':'Gamma','track_ids':[]}],'tracks':[]}
app.update_selector('Alpha')
assert app.playlist_position.get()=='1 / 3'
assert not app.changed
app.step_playlist(-1)
assert app.selector.get()=='Gamma' and app.playlist_position.get()=='3 / 3'
app.step_playlist(1)
assert app.selector.get()=='Alpha' and not app.changed
app.data={'playlists':[],'tracks':[]};app.update_selector()
assert app.playlist_position.get()=='0 / 0'
assert str(app.next_playlist_button['state'])=='disabled'
app.destroy();print('WQA321 GUI PASS')
