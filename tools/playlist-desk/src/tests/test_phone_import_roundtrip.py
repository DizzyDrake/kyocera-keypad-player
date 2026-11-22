"""Fictional first-import test; no user files, phone, or ADB."""
import copy
import json
import unittest
from pathlib import Path
from bridge import phone_to_pc, phone_import_payload, BridgeError, IMPORT_SCHEMA

class PhoneImportRoundtripTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.phone=json.loads((Path(__file__).resolve().parent.parent/'sample/dev8_fictional_phone_export.json').read_text())

    def test_reordered_playlists_and_snapshot(self):
        pc=phone_to_pc(self.phone)
        pc['playlists'][0]['track_ids'].reverse()
        result=phone_import_payload(self.phone,pc)
        self.assertEqual(result['schema'],IMPORT_SCHEMA)
        self.assertEqual(result['expected_snapshot_id'],self.phone['snapshot_id'])
        self.assertEqual(result['playlists'][0]['track_keys'],pc['playlists'][0]['track_ids'])
        self.assertNotIn('tracks',result)
        self.assertNotIn('music',result)

    def test_first_import_allows_remove_current_track(self):
        pc=phone_to_pc(self.phone)
        pc['playlists'][0]['track_ids'].remove(self.phone['music']['track_key'])
        result=phone_import_payload(self.phone,pc)
        self.assertNotIn(self.phone['music']['track_key'],result['playlists'][0]['track_keys'])

    def test_legacy_plan_still_blocks_progress_change(self):
        from bridge import plan
        pc=phone_to_pc(self.phone)
        pc['playlists'][0]['track_ids'].remove(self.phone['music']['track_key'])
        with self.assertRaises(BridgeError): plan(self.phone,pc)

    def test_mismatched_snapshot_rejected(self):
        pc=phone_to_pc(self.phone)
        pc['bridge']['snapshot_id']='appstate-wrong'
        with self.assertRaises(BridgeError): phone_import_payload(self.phone,pc)

    def test_new_pc_only_track_rejected(self):
        pc=phone_to_pc(self.phone)
        pc['tracks'].append({'id':'pc_only','path':'Extra/not-on-phone.mp3'})
        with self.assertRaises(BridgeError): phone_import_payload(self.phone,pc)

    def test_original_not_modified(self):
        before=copy.deepcopy(self.phone)
        pc=phone_to_pc(self.phone)
        phone_import_payload(self.phone,pc)
        self.assertEqual(before,self.phone)

if __name__=='__main__': unittest.main()
