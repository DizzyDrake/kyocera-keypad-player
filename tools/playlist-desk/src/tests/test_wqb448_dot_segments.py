"""Regression for safe M3U textual dot-segment matching; synthetic only."""
import unittest
from playlist_match import match_m3u, parse_m3u

TRACKS = [{'id': 'fictional-one', 'path': 'Music/Album/song.mp3',
           'artist': 'Imaginary Band', 'title': 'Song'}]

class DotSegments(unittest.TestCase):
    def test_internal_dot_segment_matches_same_local_path(self):
        row = match_m3u(parse_m3u('Music/./Album/song.mp3'), TRACKS)[0]
        self.assertEqual((row['status'], row['chosen_id']), ('MATCH', 'fictional-one'))
        self.assertEqual(row['match_basis'], 'exact local relative path')

    def test_backslash_dot_segment_matches_as_text(self):
        row = match_m3u(parse_m3u(r'Music\.\Album\song.mp3'), TRACKS)[0]
        self.assertEqual((row['status'], row['chosen_id']), ('MATCH', 'fictional-one'))

    def test_parent_traversal_remains_review_only(self):
        row = match_m3u(parse_m3u('Music/../Album/song.mp3'), TRACKS)[0]
        self.assertIsNone(row['chosen_id'])
        self.assertNotEqual(row['status'], 'MATCH')

    def test_absolute_path_remains_review_only(self):
        row = match_m3u(parse_m3u('/Music/./Album/song.mp3'), TRACKS)[0]
        self.assertIsNone(row['chosen_id'])

    def test_normal_path_unchanged(self):
        row = match_m3u(parse_m3u('Music/Album/song.mp3'), TRACKS)[0]
        self.assertEqual(row['chosen_id'], 'fictional-one')

if __name__ == '__main__':
    unittest.main()
