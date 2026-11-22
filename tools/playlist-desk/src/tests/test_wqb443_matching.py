import unittest
from playlist_match import MatchError, norm, parse_pasted, match_entries, filter_artist_album, resolved_ids

TRACKS = [
    {'id':'k10','title':'Blue Sky','artist':'Test Artist','album':'First'},
    {'id':'k20','title':'Blue Sky','artist':'Test Artist','album':'Live'},
    {'id':'k30','title':'Next','artist':'Test Artist','album':'First'},
    {'id':'k40','title':'Chapter 1','artist':'Book Author','album':'Book'},
]

class TestMatcher(unittest.TestCase):
    def test_csv_header_arbitrary_order(self):
        entries=parse_pasted('title,album,artist\nBlue Sky,Live,Test Artist\nNext,First,Test Artist')
        self.assertEqual([e['title'] for e in entries],['Blue Sky','Next'])
        self.assertEqual(match_entries(entries,TRACKS)[0]['chosen_id'],'k20')
    def test_em_dash(self):
        self.assertEqual(parse_pasted("Test Artist — Next")[0]["title"],"Next")
    def test_pipe_album_and_line(self):
        entries=parse_pasted('Test Artist | Blue Sky | First\nTest Artist - Next')
        self.assertEqual([r['chosen_id'] for r in match_entries(entries,TRACKS)],['k10','k30'])
    def test_ambiguous_without_album(self):
        rows=match_entries(parse_pasted('Test Artist - Blue Sky'),TRACKS)
        self.assertEqual(rows[0]['status'],'AMBIGUOUS')
        self.assertIsNone(rows[0]['chosen_id'])
        self.assertEqual(rows[0]['candidate_ids'],['k10','k20'])
    def test_missing_never_fabricates(self):
        rows=match_entries(parse_pasted('Test Artist - Not Here'),TRACKS)
        self.assertEqual(rows[0]['status'],'MISSING')
        self.assertEqual(rows[0]['candidate_ids'],[])
    def test_order_and_duplicates(self):
        rows=match_entries(parse_pasted('Test Artist | Next | First\nTest Artist | Blue Sky | Live\nTest Artist | Next | First'),TRACKS)
        self.assertEqual(resolved_ids(rows),(['k30','k20'],[3],[]))
    def test_existing_playlist_not_readded(self):
        rows=match_entries(parse_pasted('Test Artist | Next | First\nTest Artist | Blue Sky | Live'),TRACKS)
        self.assertEqual(resolved_ids(rows,existing=['k20']),(['k30'],[2],[]))
    def test_ambiguous_manual_choice_must_be_real_candidate(self):
        rows=match_entries(parse_pasted('Test Artist - Blue Sky'),TRACKS)
        rows[0]['chosen_id']='invented'
        self.assertEqual(resolved_ids(rows),([],[],[1]))
        rows[0]['chosen_id']='k20'
        self.assertEqual(resolved_ids(rows),(['k20'],[],[]))
    def test_artist_album_order(self):
        self.assertEqual([t['id'] for t in filter_artist_album(TRACKS,'test artist','First')],['k10','k30'])
        self.assertEqual([t['id'] for t in filter_artist_album(TRACKS,album='Live')],['k20'])
    def test_unicode_and_case(self):
        self.assertEqual(norm('  ÁRTIST  '),norm('  A\u0301rtist'))
        self.assertEqual(norm('ＡＢＣ'),'abc')
    def test_url_rejected_no_fetch(self):
        with self.assertRaises(MatchError): parse_pasted('https://example.org/list')
    def test_unstructured_rejected(self):
        with self.assertRaises(MatchError): parse_pasted('Some Track Without Artist')
    def test_limits(self):
        with self.assertRaises(MatchError): parse_pasted('x'*100001)
        with self.assertRaises(MatchError): parse_pasted('Artist - Title\n'*1001)
    def test_csv_bad_fields(self):
        with self.assertRaises(MatchError): parse_pasted('artist,title\nA,B,C')
    def test_invalid_rows(self):
        with self.assertRaises(MatchError): match_entries([{'title':'Only'}],TRACKS)
    def test_requires_filter(self):
        with self.assertRaises(MatchError): filter_artist_album(TRACKS)

if __name__=='__main__': unittest.main()
