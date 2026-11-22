"""Restore existing Saved As editor JSON using exact new phone track paths."""
import copy
import json
import unittest
from pathlib import Path
from bridge import phone_to_pc, BridgeError, phone_import_payload
from integration_core import reattach_saved_playlists

class ExistingPlaylistRecoveryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.phone=json.loads((Path(__file__).resolve().parent.parent/'sample/dev8_fictional_phone_export.json').read_text())

    def test_previously_saved_playlist_order_can_be_restored(self):
        previous=phone_to_pc(self.phone)
        prev_playlists=previous['playlists']
        prev_playlists[0]['track_ids'].reverse()
        prev_playlists.append({'name':'My already saved tracks','track_ids':previous['playlists'][0]['track_ids'][:], 'audiobook':False})
        next_phone=copy.deepcopy(self.phone)
        next_phone['snapshot_id']='appstate-updated-in-another-session'
        original=copy.deepcopy(previous)
        result=reattach_saved_playlists(next_phone,previous)
        self.assertEqual(result['playlists'][0]['track_ids'],prev_playlists[0]['track_ids'])
        self.assertEqual(result['playlists'][-1]['name'],'My already saved tracks')
        self.assertEqual(result['bridge']['snapshot_id'],next_phone['snapshot_id'])
        self.assertEqual(previous,original)
        self.assertEqual(phone_import_payload(next_phone,result)['expected_snapshot_id'],next_phone['snapshot_id'])

    def test_old_track_ids_map_by_exact_path_to_new_keys(self):
        previous=phone_to_pc(self.phone)
        updated=copy.deepcopy(self.phone)
        updated['snapshot_id']='appstate-updated-second'
        mapping={t['key']:'new-'+t['key'] for t in updated['tracks']}
        for track in updated['tracks']:
            track['key']=mapping[track['key']]
        for pl in updated['playlists']:
            pl['track_keys']=[mapping[k] for k in pl['track_keys']]
        for typ in ['music','book']:
            if updated.get(typ,{}).get('track_key'):
                updated[typ]['track_key']=mapping[updated[typ]['track_key']]
        for mark in updated['bookmarks']:
            mark['track_key']=mapping[mark['track_key']]
        result=reattach_saved_playlists(updated,previous)
        self.assertEqual(result['playlists'][0]['track_ids'],[mapping[k] for k in previous['playlists'][0]['track_ids']])

    def test_missing_track_rejected_not_silently_dropped(self):
        old=phone_to_pc(self.phone)
        changed=copy.deepcopy(self.phone)
        track=changed['tracks'].pop()
        for pl in changed['playlists']:
            pl['track_keys']=[key for key in pl['track_keys'] if key!=track['key']]
        for mode in ('music','book'):
            if changed[mode].get('track_key')==track['key']:
                changed[mode]={'playlist_id':'','track_key':'','position_ms':0}
        changed['bookmarks']=[m for m in changed['bookmarks'] if m['track_key']!=track['key']]
        # If a saved playlist needs the missing track, recovery refuses it.
        old['playlists'][0]['track_ids'].append(track['key'])
        with self.assertRaises(BridgeError): reattach_saved_playlists(changed,old)

    def test_pc_only_staged_track_rejected(self):
        old=phone_to_pc(self.phone)
        old['tracks'].append({'id':'pc-local-abc','path':'pc-pending/abc/test.mp3','pc_status':'pending-local-not-on-phone'})
        old['playlists'][0]['track_ids'].append('pc-local-abc')
        with self.assertRaises(BridgeError): reattach_saved_playlists(self.phone,old)

if __name__=='__main__':unittest.main()
