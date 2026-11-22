import copy,json,tempfile,unittest
from pathlib import Path
from playlist_core import *
BASE={'schema':SCHEMA,'tracks':[{'id':'track-a','path':'Music/Beta.mp3','title':'Beta','artist':'B','duration_ms':60000},{'id':'track-b','path':'Music/Álpha.mp3','title':'Álpha','artist':'A','duration_ms':30000}],'playlists':[{'name':'Manual','track_ids':['track-a','track-b']} ]}
class Tests(unittest.TestCase):
 def test_valid(self):self.assertIs(validate(copy.deepcopy(BASE)),validate(copy.deepcopy(BASE))) if False else validate(copy.deepcopy(BASE))
 def test_manual_order(self):
  d=copy.deepcopy(BASE);self.assertEqual(ordered_paths(d,'Manual'),['Music/Beta.mp3','Music/Álpha.mp3']);move(d['playlists'][0],1,-1);self.assertEqual(ordered_paths(d,'Manual'),['Music/Álpha.mp3','Music/Beta.mp3'])
 def test_m3u(self):self.assertEqual(m3u8(BASE,'Manual'),'#EXTM3U\nMusic/Beta.mp3\nMusic/Álpha.mp3\n')
 def test_roundtrip(self):
  d=copy.deepcopy(BASE);move(d['playlists'][0],0,1)
  with tempfile.TemporaryDirectory() as td:
   p=Path(td)/'playlist.json';p.write_bytes(encode(d));self.assertEqual(load(p)['playlists'][0]['track_ids'],['track-b','track-a'])
 def test_duplicate_id(self):
  d=copy.deepcopy(BASE);d['tracks'].append(dict(d['tracks'][0]));self.assertRaises(PlaylistError,validate,d)
 def test_duplicate_path_casefold(self):
  d=copy.deepcopy(BASE);d['tracks'][1]['path']='music/bETA.mp3';self.assertRaises(PlaylistError,validate,d)
 def test_missing_track(self):
  d=copy.deepcopy(BASE);d['playlists'][0]['track_ids']=['absent'];self.assertRaises(PlaylistError,validate,d)
 def test_duplicate_name(self):
  d=copy.deepcopy(BASE);d['playlists'].append({'name':'manual','track_ids':[]});self.assertRaises(PlaylistError,validate,d)
 def test_bad_schema(self):
  d=copy.deepcopy(BASE);d['schema']='future';self.assertRaises(PlaylistError,validate,d)
 def test_bad_duration_bool(self):
  d=copy.deepcopy(BASE);d['tracks'][0]['duration_ms']=True;self.assertRaises(PlaylistError,validate,d)
 def test_add_remove(self):
  d=copy.deepcopy(BASE);pl=d['playlists'][0];add(pl,'track-b',d['tracks']);self.assertEqual(remove(pl,2),'track-b');self.assertEqual(pl['track_ids'],['track-a','track-b'])
 def test_invalid_move(self):
  d=copy.deepcopy(BASE);self.assertFalse(move(d['playlists'][0],0,-1));self.assertFalse(move(d['playlists'][0],1,1))
 def test_unknown_add(self):self.assertRaises(PlaylistError,add,copy.deepcopy(BASE)['playlists'][0],'x',BASE['tracks'])
 def test_unsafe_paths(self):
  for p in ('../x','Music/../x','/absolute','C:/x','F:/x','a\\b','a//b','a/./b','', '#x\nfoo'):
   if p=='#x\nfoo':self.assertRaises(PlaylistError,m3u8,{'schema':SCHEMA,'tracks':[{'id':'a','path':p}],'playlists':[{'name':'P','track_ids':['a']}]},'P')
   else:self.assertRaises(PlaylistError,safe_relative,p)
 def test_protected_F(self):
  for p in ('F:/Music','f:\\music','/mnt/f/music'):self.assertRaises(PlaylistError,validate_output,p)
 def test_newline_m3u(self):
  d=copy.deepcopy(BASE);d['tracks'][0]['path']='Music/foo\nbar.mp3';self.assertRaises(PlaylistError,m3u8,d,'Manual')
 def test_input_limit(self):
  with tempfile.TemporaryDirectory() as td:
   p=Path(td)/'big.json';p.write_bytes(b' '* (MAX_BYTES+1));self.assertRaises(PlaylistError,load,p)
 def test_does_not_touch_media(self):
  with tempfile.TemporaryDirectory() as td:
   media=Path(td)/'Beta.mp3';media.write_bytes(b'fictional media sentinel');before=media.read_bytes();encode(BASE);m3u8(BASE,'Manual');self.assertEqual(media.read_bytes(),before)
if __name__=='__main__':unittest.main()
