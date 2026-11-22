"""Bounded integration assertions for WQB434's single-window offline candidate."""
import copy
import json
import unittest
from pathlib import Path

from bridge import BridgeError, load_json
from integration_core import attach_candidate, create_plan, create_preview
from playlist_core import move

ROOT = Path(__file__).resolve().parents[1]


class IntegrationTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.phone = load_json(ROOT / 'sample' / 'fictional_phone_snapshot.json')

    def test_fresh_phone_to_editor(self):
        pc, retained = attach_candidate(self.phone)
        self.assertFalse(retained)
        self.assertEqual(pc['schema'], 'kyocera-playlists-v0.1')
        self.assertEqual(pc['playlists'][0]['track_ids'], self.phone['playlists'][0]['track_keys'])

    def test_same_snapshot_retains_edited_order(self):
        pc, _ = attach_candidate(self.phone)
        move(pc['playlists'][0], 0, 1)
        same, retained = attach_candidate(self.phone, pc)
        self.assertTrue(retained)
        self.assertEqual(same['playlists'][0]['track_ids'], pc['playlists'][0]['track_ids'])
        self.assertIsNot(same, pc)

    def test_different_revision_does_not_retain_edits(self):
        pc, _ = attach_candidate(self.phone)
        move(pc['playlists'][0], 0, 1)
        updated = copy.deepcopy(self.phone)
        updated['revision'] += 1
        fresh, retained = attach_candidate(updated, pc)
        self.assertFalse(retained)
        self.assertEqual(fresh['playlists'][0]['track_ids'], self.phone['playlists'][0]['track_keys'])

    def test_plan_and_preview_keep_order_and_bookmarks(self):
        pc, _ = attach_candidate(self.phone)
        move(pc['playlists'][0], 0, 1)
        plan = create_plan(self.phone, pc)
        preview = create_preview(self.phone, pc)
        self.assertEqual(plan['operations'][0]['action'], 'UPDATE')
        self.assertEqual(preview['playlists'][0]['track_keys'], pc['playlists'][0]['track_ids'])
        self.assertEqual(preview['bookmarks'], self.phone['bookmarks'])
        self.assertEqual(preview['music'], self.phone['music'])
        self.assertEqual(preview['book'], self.phone['book'])
        self.assertEqual(preview['revision'], self.phone['revision'] + 1)
        self.assertEqual(self.phone['revision'], 7)

    def test_missing_active_track_is_refused(self):
        pc, _ = attach_candidate(self.phone)
        pc['playlists'][0]['track_ids'].remove(self.phone['music']['track_key'])
        with self.assertRaises(BridgeError):
            create_preview(self.phone, pc)

    def test_dev8_source_fixture_uses_same_provisional_bridge_contract(self):
        # Source-only DEV8 fixture, NOT the owner's actual exported JSON.
        dev8 = load_json(ROOT / 'sample' / 'dev8_fictional_phone_export.json')
        pc, retained = attach_candidate(dev8)
        self.assertFalse(retained)
        self.assertEqual(pc['playlists'][0]['name'], 'Owner order')
        self.assertEqual(create_preview(dev8, pc)['revision'], 1)

    def test_invalid_phone_schema_refused(self):
        altered = copy.deepcopy(self.phone)
        altered['schema'] = 'owner-export-unverified'
        with self.assertRaises(BridgeError):
            attach_candidate(altered)

    def test_no_file_write_in_memory_functions(self):
        before = json.dumps(self.phone, sort_keys=True)
        pc, _ = attach_candidate(self.phone)
        create_plan(self.phone, pc)
        create_preview(self.phone, pc)
        self.assertEqual(json.dumps(self.phone, sort_keys=True), before)


if __name__ == '__main__':
    unittest.main()
