"""Synthetic comma-joined library filter contract; no user data or phone needed."""
import unittest
from app import matches_library_query

TRACKS = [
    {'title': 'Blue Jazz Live', 'artist': 'A', 'album': 'Concert', 'genre': 'Jazz', 'path': 'a.mp3'},
    {'title': 'Blue Jazz Studio', 'artist': 'B', 'album': 'Record', 'genre': 'Jazz', 'path': 'b.mp3'},
    {'title': 'Soft Blues Studio', 'artist': 'C', 'album': 'Record', 'genre': 'Blues', 'path': 'c.mp3'},
    {'title': 'Blue Jazz Remix', 'artist': 'D', 'album': 'Record', 'genre': 'Jazz', 'path': 'd.mp3'},
    {'title': 'Blues Live Remix', 'artist': 'E', 'album': 'Concert', 'genre': 'Blues', 'path': 'e.mp3'},
    {'title': 'Christmas Carol', 'artist': 'F', 'album': 'Holiday', 'genre': 'Folk', 'path': 'f.mp3'},
]

class CommaFilterTests(unittest.TestCase):
    def ids(self, query):
        return [i for i, track in enumerate(TRACKS) if matches_library_query(track, query)]

    def test_plain_phrase_unchanged(self):
        self.assertEqual(self.ids('blue jazz'), [0, 1, 3])
    def test_legacy_multi_not_unchanged(self):
        self.assertEqual(self.ids('jazz NOT live NOT remix'), [1])
    def test_positive_or(self):
        self.assertEqual(self.ids('jazz, blues'), [0, 1, 2, 3, 4])
    def test_two_not_terms_are_both_applied(self):
        self.assertEqual(self.ids('NOT live, NOT remix'), [1, 2, 5])
    def test_mixed_or_and_global_exclusions(self):
        self.assertEqual(self.ids('jazz, blues, NOT live, NOT remix'), [1, 2])
    def test_mixed_legacy_and_comma(self):
        self.assertEqual(self.ids('jazz NOT live, blues, NOT remix'), [1, 2])
    def test_case_insensitive(self):
        self.assertEqual(self.ids('JAZZ, bLuEs, nOt LiVe'), [1, 2, 3])
    def test_whole_word_not_operator_only(self):
        self.assertEqual(self.ids('jazz, NOTebook'), [0, 1, 3])
    def test_trailing_comma_during_typing(self):
        self.assertEqual(self.ids('jazz,'), [0, 1, 3])
    def test_empty_slots_during_typing(self):
        self.assertEqual(self.ids('jazz, , blues,'), [0, 1, 2, 3, 4])
    def test_bare_not_does_not_broaden(self):
        self.assertEqual(self.ids('jazz, NOT'), [])
    def test_incomplete_legacy_operator_does_not_broaden(self):
        self.assertEqual(self.ids('jazz NOT'), [])
    def test_only_exclusions_match_anything_else(self):
        self.assertEqual(self.ids('NOT christmas, NOT live'), [1, 2, 3])
    def test_empty_query(self):
        self.assertEqual(self.ids(''), list(range(len(TRACKS))))

if __name__ == '__main__':
    unittest.main()
