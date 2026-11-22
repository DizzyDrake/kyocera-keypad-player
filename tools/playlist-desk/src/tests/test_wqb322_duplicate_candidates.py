import unittest
from duplicate_candidates import candidate_groups

class DuplicateCandidatesTests(unittest.TestCase):
    def test_flags_separate_files_same_song_metadata(self):
        tracks=[dict(id='a',path='one.mp3',title='  HELLO! ',artist='Björk',duration_ms=200000),dict(id='b',path='two.flac',title='hello',artist='Björk',duration_ms=200500)]
        out=candidate_groups(tracks)
        self.assertEqual(len(out),1)
        self.assertTrue(out[0]['review_required'])
    def test_different_artist_or_duration_not_flagged(self):
        t=[dict(id='a',path='a',title='Song',artist='A',duration_ms=100000),dict(id='b',path='b',title='Song',artist='B',duration_ms=100000),dict(id='c',path='c',title='Song',artist='A',duration_ms=105000)]
        self.assertEqual(candidate_groups(t),[])
    def test_missing_metadata_not_inferred(self):
        self.assertEqual(candidate_groups([dict(id='a',path='a',title='Song'),dict(id='b',path='b',title='Song')]),[])
    def test_no_mutation(self):
        t=[dict(id='a',path='a',title='X',artist='Y',duration_ms=1000),dict(id='b',path='b',title='X',artist='Y',duration_ms=1000)]
        before=repr(t);candidate_groups(t);self.assertEqual(repr(t),before)
    def test_invalid_tolerance(self):
        with self.assertRaises(ValueError):candidate_groups([], -1)
        with self.assertRaises(ValueError):candidate_groups([], True)
    def test_pairwise_not_transitive(self):
        t=[dict(id=str(i),path=str(i),title='X',artist='Y',duration_ms=i*1500) for i in range(3)]
        self.assertEqual(len(candidate_groups(t)),2)

if __name__=='__main__':unittest.main()
