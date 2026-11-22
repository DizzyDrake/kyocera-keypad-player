"""Synthetic M3U/M3U8 reconstruction; never accesses referenced media or URLs."""
import unittest
from playlist_match import (parse_m3u, match_m3u, looks_like_m3u,
                            resolved_ids, MatchError)

TRACKS = [
    {'id':'one','path':'Music/First.mp3','artist':'Fictional Band','title':'First','album':'Studio'},
    {'id':'two','path':'Music/Second.mp3','artist':'Fictional Band','title':'Second','album':'Studio'},
    {'id':'three','path':'Live/First.mp3','artist':'Fictional Band','title':'First','album':'Live'},
    {'id':'four','path':'Books/Chapter01.mp3','artist':'Imaginary Author','title':'Chapter One','album':'Book'},
    {'id':'five','path':'Other/Second.mp3','artist':'Another Group','title':'Second','album':'Other'},
]

class TestM3U(unittest.TestCase):
    def test_generated_m3u8_paths_and_order(self):
        text='#EXTM3U\nMusic/Second.mp3\nMusic/First.mp3\n'
        entries=parse_m3u(text)
        self.assertEqual([e['path'] for e in entries],['Music/Second.mp3','Music/First.mp3'])
        rows=match_m3u(entries,TRACKS)
        self.assertEqual(resolved_ids(rows),(['two','one'],[],[]))
        self.assertTrue(all(r['match_basis']=='exact local relative path' for r in rows))
    def test_extinf_remote_url_is_inert(self):
        entries=parse_m3u('#EXTM3U\n#EXTINF:-1,Fictional Band - Second\nhttps://example.invalid/not-a-file.mp3\n')
        self.assertEqual(entries[0]['path'],'https://example.invalid/not-a-file.mp3')
        rows=match_m3u(entries,TRACKS)
        self.assertEqual(rows[0]['status'],'MATCH')
        self.assertEqual(rows[0]['chosen_id'],'two')
        self.assertIn('EXTINF',rows[0]['match_basis'])
    def test_extinf_conflicts_with_exact_path_requires_review(self):
        text='#EXTM3U\n#EXTINF:-1,Wrong Artist - Wrong Title\nMusic/First.mp3'
        rows=match_m3u(parse_m3u(text),TRACKS)
        self.assertEqual(rows[0]['status'],'REVIEW')
        self.assertEqual(rows[0]['candidate_ids'],['one'])
        self.assertIsNone(rows[0]['chosen_id'])
        self.assertIn('conflicts',rows[0]['match_basis'])
    def test_extinf_duplicate_ambiguous(self):
        rows=match_m3u(parse_m3u('#EXTINF:-1,Fictional Band - First\nC:\\Unknown\\First.mp3'),TRACKS)
        self.assertEqual(rows[0]['status'],'AMBIGUOUS')
        self.assertEqual(rows[0]['candidate_ids'],['one','three'])
        self.assertIsNone(rows[0]['chosen_id'])
    def test_filename_unique_needs_manual_choice(self):
        rows=match_m3u(parse_m3u('C:\\External\\Chapter01.mp3'),TRACKS)
        self.assertEqual(rows[0]['status'],'REVIEW')
        self.assertEqual(rows[0]['candidate_ids'],['four'])
        self.assertEqual(resolved_ids(rows),([],[],[1]))
        rows[0]['chosen_id']='four'
        self.assertEqual(resolved_ids(rows),(['four'],[],[]))
    def test_filename_collision_not_guessed(self):
        rows=match_m3u(parse_m3u('Second.mp3'),TRACKS)
        self.assertEqual(rows[0]['status'],'AMBIGUOUS')
        self.assertEqual(rows[0]['candidate_ids'],['two','five'])
    def test_remote_url_without_metadata_never_filename_matches(self):
        rows=match_m3u(parse_m3u('https://example.invalid/First.mp3'),TRACKS)
        self.assertEqual(rows[0]['status'],'MISSING')
    def test_missing_never_fabricates(self):
        rows=match_m3u(parse_m3u('#EXTM3U\nMissing.mp3'),TRACKS)
        self.assertEqual(rows[0]['candidate_ids'],[])
        self.assertEqual(rows[0]['status'],'MISSING')
    def test_windows_backslash_path_is_review_not_auto(self):
        rows=match_m3u(parse_m3u('Music\\First.mp3'),TRACKS)
        self.assertEqual(rows[0]['status'],'MATCH')
        self.assertEqual(rows[0]['chosen_id'],'one')
    def test_relative_dot_prefix_is_exact(self):
        rows=match_m3u(parse_m3u('./Music/First.mp3'),TRACKS)
        self.assertEqual(rows[0]['chosen_id'],'one')
    def test_traversal_cannot_exact_match(self):
        rows=match_m3u(parse_m3u('../Music/First.mp3'),TRACKS)
        self.assertEqual(rows[0]['status'],'AMBIGUOUS')
        self.assertIsNone(rows[0]['chosen_id'])
    def test_bom_comments_and_metadata_pairing(self):
        text='\ufeff#EXTM3U\n#PLAYLIST: Fictional\n#EXTINF:123,Imaginary Author - Chapter One\nBooks/Chapter01.mp3\n#EXTINF:-1,Not A Real - Ghost\nGhost.mp3'
        entries=parse_m3u(text)
        self.assertEqual(len(entries),2)
        self.assertEqual(entries[0]['artist'],'Imaginary Author')
        self.assertEqual(entries[1]['title'],'Ghost')
        self.assertEqual(match_m3u(entries,TRACKS)[1]['status'],'MISSING')
    def test_format_recognition(self):
        self.assertTrue(looks_like_m3u('\ufeff#EXTM3U\nMusic/First.mp3'))
        self.assertTrue(looks_like_m3u('#EXTINF:-1,Artist - Song\nX.mp3'))
        self.assertFalse(looks_like_m3u('artist,title\nX,Y'))
    def test_limits_and_invalid(self):
        with self.assertRaises(MatchError):parse_m3u('a'*100001)
        with self.assertRaises(MatchError):parse_m3u('#EXTM3U\n')
        with self.assertRaises(MatchError):parse_m3u('a.mp3\n'*1001)
        with self.assertRaises(MatchError):parse_m3u('file\x00.mp3')
        with self.assertRaises(MatchError):match_m3u([{'path':1}],TRACKS)
    def test_duplicate_preserved_for_review_and_skipped_on_apply(self):
        rows=match_m3u(parse_m3u('Music/First.mp3\nMusic/First.mp3'),TRACKS)
        self.assertEqual(len(rows),2)
        self.assertEqual(resolved_ids(rows),(['one'],[2],[]))

if __name__=='__main__':unittest.main()
