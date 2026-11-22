"""Independent synthetic regression tests; no phone or owner files."""
import copy
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from playlist_core import (PlaylistError, atomic_write, create_playlist,
                           delete_playlist, encode, m3u8, rename_playlist, validate)

FIXTURE = {
    'schema': 'kyocera-playlists-v0.1',
    'tracks': [
        {'id': 'c', 'path': 'music/c.mp3', 'title': 'C'},
        {'id': 'a', 'path': 'music/a.mp3', 'title': 'A'},
        {'id': 'b', 'path': 'music/b.mp3', 'title': 'B'},
    ],
    'playlists': [{'name': 'Unsorted', 'track_ids': ['c', 'a', 'b']}],
}

class PlaylistCRUDTests(unittest.TestCase):
    def setUp(self): self.data = copy.deepcopy(FIXTURE)
    def test_create_empty(self):
        pl = create_playlist(self.data, 'New')
        self.assertEqual(pl['track_ids'], [])
        self.assertEqual(len(self.data['playlists']), 2)
    def test_create_rejects_duplicate_casefold(self):
        with self.assertRaises(PlaylistError): create_playlist(self.data, 'unsorted')
    def test_create_rejects_blank(self):
        with self.assertRaises(PlaylistError): create_playlist(self.data, '  ')
    def test_create_rejects_nontext(self):
        with self.assertRaises(PlaylistError): create_playlist(self.data, 123)
    def test_create_limit(self):
        self.data['playlists']=[{'name':f'p{i}','track_ids':[]} for i in range(1000)]
        with self.assertRaises(PlaylistError): create_playlist(self.data, 'overflow')
    def test_rename_preserves_order(self):
        rename_playlist(self.data,'Unsorted','Favorites')
        self.assertEqual(m3u8(self.data,'Favorites').splitlines()[1:],
                         ['music/c.mp3','music/a.mp3','music/b.mp3'])
    def test_rename_rejects_collision(self):
        create_playlist(self.data,'Other')
        with self.assertRaises(PlaylistError): rename_playlist(self.data,'Other','UNSORTED')
    def test_rename_allows_case_change_same_playlist(self):
        rename_playlist(self.data,'Unsorted','UNSORTED')
        self.assertEqual(self.data['playlists'][0]['name'],'UNSORTED')
    def test_delete_does_not_delete_tracks(self):
        tracks=copy.deepcopy(self.data['tracks'])
        delete_playlist(self.data,'Unsorted')
        self.assertEqual(self.data['tracks'],tracks)
        self.assertEqual(self.data['playlists'],[])
    def test_delete_unknown(self):
        with self.assertRaises(PlaylistError): delete_playlist(self.data,'absent')
    def test_json_roundtrip_new_playlist(self):
        pl=create_playlist(self.data,'Favorites')
        pl['track_ids']=['b','a','c']
        loaded=json.loads(encode(self.data))
        validate(loaded)
        self.assertEqual(loaded['playlists'][-1]['track_ids'],['b','a','c'])

class AtomicOutputTests(unittest.TestCase):
    def test_new_output_and_cleanup(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'new.json';atomic_write(p,b'hello')
            self.assertEqual(p.read_bytes(),b'hello')
            self.assertEqual(sorted(x.name for x in Path(d).iterdir()),['new.json'])
    def test_no_clobber(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'existing.json';p.write_bytes(b'old')
            with self.assertRaises(FileExistsError):atomic_write(p,b'new')
            self.assertEqual(p.read_bytes(),b'old')
            self.assertEqual(len(list(Path(d).iterdir())),1)
    def test_explicit_replace(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'existing.json';p.write_bytes(b'old')
            atomic_write(p,b'new',True)
            self.assertEqual(p.read_bytes(),b'new')
    def test_link_failure_leaves_no_partial_output(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'new.json'
            with patch('playlist_core.os.link',side_effect=OSError('unsupported')):
                with self.assertRaises(OSError):atomic_write(p,b'new')
            self.assertEqual(list(Path(d).iterdir()),[])
    def test_replace_failure_preserves_existing(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'old.json';p.write_bytes(b'old')
            with patch('playlist_core.os.replace',side_effect=OSError('disk issue')):
                with self.assertRaises(OSError):atomic_write(p,b'new',True)
            self.assertEqual(p.read_bytes(),b'old')
            self.assertEqual(len(list(Path(d).iterdir())),1)
    def test_device_namespace_refused(self):
        with self.assertRaises(PlaylistError):atomic_write(r"\\?\F:\hidden.json",b"never")
    def test_protected_f_refused_without_creating_temp(self):
        with self.assertRaises(PlaylistError):atomic_write('F:\\do-not-touch.json',b'never')
