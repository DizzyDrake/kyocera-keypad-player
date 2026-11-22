"""Synthetic metadata-only regression for WQC013 integrated GUI; no audio/device access."""
import copy
from integrated_app import IntegratedApp

tracks=[
 {'id':'t1','title':'Blue Sky','artist':'Jazz Trio','album':'A','path':'blue.mp3'},
 {'id':'t2','title':'Red Road','artist':'Blues Band','album':'B','path':'red.mp3'},
 {'id':'t3','title':'Live Set','artist':'Jazz Trio','album':'C','path':'live.mp3'},
 {'id':'t4','title':'Classical Waltz','artist':'Quartet','album':'D','path':'classical.mp3'}]
data={'tracks':tracks,'playlists':[{'name':'One','track_ids':['t1']},{'name':'Two','track_ids':['t2']},{'name':'Three','track_ids':['t4']}]}
app=IntegratedApp()
try:
 app.data=copy.deepcopy(data);app.update_selector('One');app.refresh_library()
 assert app.playlist_position.get()=='1 / 3'
 app.query.set('jazz, blues, NOT live')
 assert app.filtered==['t1','t2'],app.filtered
 assert app.library.size()==2
 app.query.set('jazz NOT live NOT blue')
 assert app.filtered==[],app.filtered
 app.query.set('classical, NOT live')
 assert app.filtered==['t4'],app.filtered
 app.query.set('')
 app.selector.focus_set();app.update();app.selector.event_generate('<Alt-Right>');app.update()
 assert app.selector.get()=='Two' and app.playlist_position.get()=='2 / 3'
 assert app.plist.size()==1
 app.next_playlist_button.invoke();app.update()
 assert app.selector.get()=='Three' and app.playlist_position.get()=='3 / 3'
 app.previous_playlist_button.invoke();app.update()
 assert app.selector.get()=='Two'
 assert app.data==data and app.changed is False
 print('PASS: actual IntegratedApp comma OR/NOT filtering, no-comma NOT, Alt+Right, next/previous controls, 3 playlists, unchanged catalog')
finally:
 app.destroy()
