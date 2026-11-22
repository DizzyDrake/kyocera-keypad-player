"""Cross-project source contract, synthetic phone snapshot; no ADB or personal catalog."""
from pathlib import Path
import json, re, sys, unittest
ROOT=Path(__file__).resolve().parents[3]
DESK=ROOT/'tools'/'playlist-desk'/'src'
ANDROID=ROOT/'app'/'src'/'main'/'java'/'org'/'roarin'/'kyocerakeypad'
sys.path.insert(0,str(DESK))
from bridge import PHONE_SCHEMA, IMPORT_SCHEMA, IMPORT_FILENAME, phone_to_pc, phone_import_payload, BridgeError
from playlist_core import validate as validate_pc

class CompanionContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.phone=json.loads((DESK/'sample'/'dev8_fictional_phone_export.json').read_text(encoding='utf-8'))
        cls.import_java=(ANDROID/'core'/'PhonePlaylistImport.java').read_text(encoding='utf-8')
        cls.export_java=(ANDROID/'core'/'PhoneSnapshotExport.java').read_text(encoding='utf-8')
        cls.activity=(ANDROID/'KeypadPlayerActivity.java').read_text(encoding='utf-8')

    def test_real_export_schema_matches_pc_reader(self):
        self.assertEqual(self.phone['schema'],PHONE_SCHEMA)
        self.assertIn('SCHEMA = "'+PHONE_SCHEMA+'"',self.export_java)
        validate_pc(phone_to_pc(self.phone))

    def test_real_import_schema_and_filename_match(self):
        self.assertIn('SCHEMA = "'+IMPORT_SCHEMA+'"',self.import_java)
        self.assertIn('FILENAME = "'+IMPORT_FILENAME+'"',self.import_java)
        self.assertIn('PhonePlaylistImport.FILENAME',self.activity)

    def test_reorder_and_import_keep_ids_and_order(self):
        pc=phone_to_pc(self.phone)
        pc['playlists'][0]['track_ids'].reverse()
        payload=phone_import_payload(self.phone,pc)
        self.assertEqual(payload['schema'],IMPORT_SCHEMA)
        self.assertEqual(payload['expected_snapshot_id'],self.phone['snapshot_id'])
        self.assertEqual(payload['playlists'][0]['track_keys'],pc['playlists'][0]['track_ids'])
        self.assertNotIn('tracks',payload)
        self.assertNotIn('audio',payload)
        self.assertLessEqual(len(json.dumps(payload).encode('utf-8')),8_000_000)

    def test_reject_desktop_track_with_no_phone_identity(self):
        pc=phone_to_pc(self.phone)
        pc['tracks'].append({'id':'personal-test-only','path':'fictional/unavailable.mp3'})
        with self.assertRaises(BridgeError):phone_import_payload(self.phone,pc)

    def test_android_stale_import_preflight_and_confirmation(self):
        self.assertIn('PhonePlaylistImport.prepare(',self.activity)
        self.assertIn('PhonePlaylistImport.apply(',self.activity)
        self.assertIn('setPositiveButton("Replace playlists"',self.activity)
        self.assertIn('stale import explicitly allowed',self.activity)
        self.assertIn('getExternalFilesDir("transfer")',self.activity)

    def test_desktop_import_entrypoint(self):
        gui=(DESK/'integrated_app.py').read_text(encoding='utf-8')
        self.assertIn('Create phone import JSON',gui)
        self.assertIn('phone_import_payload(',gui)

if __name__=='__main__': unittest.main()
