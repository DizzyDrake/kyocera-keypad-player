import copy
import json
import tempfile
import unittest
from pathlib import Path
from bridge import (BridgeError, PHONE_SCHEMA, phone_to_pc, plan, simulate,
                    validate_phone, digest, load_json, main)

SAMPLE=Path(__file__).resolve().parents[1]/'sample'/'fictional_phone_snapshot.json'

def fixture(): return json.loads(SAMPLE.read_text(encoding='utf-8'))

class BridgeTests(unittest.TestCase):
    def setUp(self):
        self.phone=fixture()
        self.pc=phone_to_pc(self.phone)
    def test_sample_valid(self): validate_phone(self.phone)
    def test_export_schema(self): self.assertEqual(self.pc['schema'],'kyocera-playlists-v0.1')
    def test_ids_exact(self): self.assertEqual(self.pc['tracks'][0]['id'],self.phone['tracks'][0]['key'])
    def test_export_accepted_by_actual_wq140_validator(self):
        from playlist_core import validate
        self.assertIs(validate(self.pc),self.pc)
    def test_phone_key_201_chars_rejected_before_export(self):
        key='K'*201
        old=self.phone['tracks'][0]['key']
        self.phone['tracks'][0]['key']=key
        for p in self.phone['playlists']:
            p['track_keys']=[key if x==old else x for x in p['track_keys']]
        for context in ('music','book'):
            if self.phone.get(context,{}).get('track_key')==old:
                self.phone[context]['track_key']=key
        for b in self.phone.get('bookmarks',[]):
            if b.get('track_key')==old:b['track_key']=key
        self.assertRaises(BridgeError,phone_to_pc,self.phone)
    def test_phone_key_200_chars_remains_supported(self):
        key='K'*200
        old=self.phone['tracks'][0]['key']
        self.phone['tracks'][0]['key']=key
        for p in self.phone['playlists']:
            p['track_keys']=[key if x==old else x for x in p['track_keys']]
        for context in ('music','book'):
            if self.phone.get(context,{}).get('track_key')==old:
                self.phone[context]['track_key']=key
        for b in self.phone.get('bookmarks',[]):
            if b.get('track_key')==old:b['track_key']=key
        from playlist_core import validate
        self.assertEqual(validate(phone_to_pc(self.phone))['tracks'][0]['id'],key)
    def test_no_path_guess(self):
        self.pc['playlists'][0]['track_ids']=['wrong'];self.assertRaises(BridgeError,plan,self.phone,self.pc)
    def test_reorder(self):
        self.pc['playlists'][0]['track_ids'].reverse()
        p=plan(self.phone,self.pc);s=simulate(self.phone,p)
        self.assertEqual(s['playlists'][0]['track_keys'],self.pc['playlists'][0]['track_ids'])
        self.assertEqual(s['revision'],8)
    def test_removing_active_track_refused(self):
        self.pc['playlists'][0]['track_ids'].pop(0)
        self.assertRaises(BridgeError,plan,self.phone,self.pc)
    def test_removing_nonactive_track_allowed(self):
        self.pc['playlists'][0]['track_ids'].pop(1)
        self.assertEqual(len(simulate(self.phone,plan(self.phone,self.pc))['playlists'][0]['track_keys']),1)
    def test_bookmarks_unchanged(self):
        self.pc['playlists'][0]['track_ids'].reverse()
        s=simulate(self.phone,plan(self.phone,self.pc))
        self.assertEqual(s['bookmarks'],self.phone['bookmarks']);self.assertEqual(s['book'],self.phone['book'])
    def test_phone_source_not_mutated(self):
        before=copy.deepcopy(self.phone);pc=phone_to_pc(self.phone);simulate(self.phone,plan(self.phone,pc))
        self.assertEqual(self.phone,before)
    def test_wq140_rename_function_retains_identity(self):
        from playlist_core import rename_playlist, encode
        rename_playlist(self.pc,'My order','Renamed with WQ140')
        saved=json.loads(encode(self.pc).decode('utf-8'))
        self.assertEqual(saved['playlists'][0]['phone_id'],'phone-music-01')
        self.assertEqual(simulate(self.phone,plan(self.phone,saved))['playlists'][0]['name'],'Renamed with WQ140')
    def test_rename_preserves_id(self):
        self.pc['playlists'][0]['name']='My renamed order'
        s=simulate(self.phone,plan(self.phone,self.pc))
        self.assertEqual(s['playlists'][0]['id'],'phone-music-01')
    def test_create(self):
        self.pc['playlists'].append({'name':'New playlist','track_ids':[self.pc['tracks'][1]['id']]})
        s=simulate(self.phone,plan(self.phone,self.pc));self.assertEqual(len(s['playlists']),3)
        self.assertTrue(s['playlists'][2]['id'].startswith('pc-'))
    def test_deleted_in_pc_preserved(self):
        self.pc['playlists'].pop(0)
        p=plan(self.phone,self.pc)
        self.assertTrue(any(x['action']=='PRESERVE_UNMENTIONED' for x in p['operations']))
        self.assertEqual(len(simulate(self.phone,p)['playlists']),2)
    def test_stale_revision(self):
        self.phone['revision']+=1;self.assertRaises(BridgeError,plan,self.phone,self.pc)
    def test_changed_track_metadata(self):
        self.pc['tracks'][0]['path']='Music/wrong.mp3';self.assertRaises(BridgeError,plan,self.phone,self.pc)
    def test_changed_snapshot(self):
        self.phone['tracks'][0]['title']='New title';self.assertRaises(BridgeError,plan,self.phone,self.pc)
    def test_missing_phone_id(self):
        self.pc['playlists'][0]['phone_id']='unknown';self.assertRaises(BridgeError,plan,self.phone,self.pc)
    def test_duplicate_pc_phone_id(self):
        self.pc['playlists'].append({'name':'Another','track_ids':[],'phone_id':'phone-music-01','audiobook':False})
        self.assertRaises(BridgeError,plan,self.phone,self.pc)
    def test_duplicate_android_entry(self):
        self.pc['playlists'][0]['track_ids'].append(self.pc['playlists'][0]['track_ids'][0])
        self.assertRaises(BridgeError,plan,self.phone,self.pc)
    def test_changed_kind(self):
        self.pc['playlists'][0]['audiobook']=True;self.assertRaises(BridgeError,plan,self.phone,self.pc)
    def test_duplicate_phone_key(self):
        self.phone['tracks'].append(copy.deepcopy(self.phone['tracks'][0]));self.assertRaises(BridgeError,validate_phone,self.phone)
    def test_duplicate_phone_path(self):
        self.phone['tracks'][1]['path']='music/beta.mp3';self.assertRaises(BridgeError,validate_phone,self.phone)
    def test_invalid_path(self):
        for path in ['../a','F:/audio','C:/music','Music/../secret','Music\\foo','/absolute']:
            self.phone['tracks'][0]['path']=path
            with self.subTest(path=path): self.assertRaises(BridgeError,validate_phone,self.phone)
    def test_missing_phone_track(self):
        self.phone['playlists'][0]['track_keys']=['no-such-key'];self.assertRaises(BridgeError,validate_phone,self.phone)
    def test_modified_plan_rejected(self):
        p=plan(self.phone,self.pc);p['proposed_playlists'][0]['name']='injected'
        self.assertRaises(BridgeError,simulate,self.phone,p)
    def test_modified_plan_edited_pc_rejected(self):
        p=plan(self.phone,self.pc);p['edited_pc']['playlists'][0]['name']='injected'
        self.assertRaises(BridgeError,simulate,self.phone,p)
    def test_bad_progress_track_refused(self):
        self.phone['music']['track_key']='unknown'
        self.assertRaises(BridgeError,validate_phone,self.phone)
    def test_bad_bookmark_refused(self):
        self.phone['bookmarks'][0]['track_key']='unknown'
        self.assertRaises(BridgeError,validate_phone,self.phone)
    def test_changed_phone_rejected_on_simulate(self):
        p=plan(self.phone,self.pc);self.phone['revision']=8
        self.assertRaises(BridgeError,simulate,self.phone,p)
    def test_name_collision_with_preserved(self):
        self.pc['playlists'].pop(0)
        self.pc['playlists'].append({'name':'My order','track_ids':[]})
        self.assertRaises(BridgeError,plan,self.phone,self.pc)
    def test_no_clobber_cli(self):
        with tempfile.TemporaryDirectory() as d:
            out=Path(d)/'out.json';out.write_text('sentinel')
            self.assertEqual(main(['export',str(SAMPLE),'--out',str(out)]),2)
            self.assertEqual(out.read_text(),'sentinel')
    def test_cli_export_plan_simulate(self):
        with tempfile.TemporaryDirectory() as d:
            d=Path(d);pc=d/'pc.json';p=d/'plan.json';out=d/'result.json'
            self.assertEqual(main(['export',str(SAMPLE),'--out',str(pc)]),0)
            self.assertEqual(main(['plan',str(SAMPLE),'--pc',str(pc),'--out',str(p)]),0)
            self.assertEqual(main(['simulate',str(SAMPLE),'--plan',str(p),'--out',str(out)]),0)
            self.assertEqual(json.loads(out.read_text())['revision'],8)
    def test_direct_protected_input_refused(self):
        from playlist_core import PlaylistError
        for path in ("F:/music.json", "f:\\music.json"):
            with self.subTest(path=path): self.assertRaises(PlaylistError,load_json,path)
    def test_input_size_limit(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'large.json';p.write_bytes(b' '*(8_000_001))
            self.assertRaises(BridgeError,load_json,p)
    def test_no_media_reads(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'Music';p.mkdir();f=p/'Beta.mp3';f.write_bytes(b'fictional bytes')
            before=f.read_bytes();simulate(self.phone,plan(self.phone,self.pc))
            self.assertEqual(f.read_bytes(),before)

if __name__=='__main__': unittest.main()
