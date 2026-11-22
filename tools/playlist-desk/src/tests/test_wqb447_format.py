import unittest
from playlist_match import MatchError, choose_list_format

class FormatSelectionTests(unittest.TestCase):
    def test_auto_detect_header(self):
        self.assertEqual(choose_list_format('#EXTM3U\nSong.mp3'), 'm3u')
    def test_auto_detect_pasted_csv_over_stale_import(self):
        self.assertEqual(choose_list_format('artist,title\nA,B', 'Auto detect'), 'pasted')
    def test_unchanged_headerless_file_hint(self):
        self.assertEqual(choose_list_format('Music/Song.mp3', 'Auto detect', 'm3u'), 'm3u')
    def test_explicit_m3u_for_edited_path_only(self):
        self.assertEqual(choose_list_format('Music/Edited.mp3', 'M3U/M3U8'), 'm3u')
    def test_explicit_csv_over_m3u_header(self):
        self.assertEqual(choose_list_format('#EXTM3U\nA - B', 'Artist/title or CSV', 'm3u'), 'pasted')
    def test_unknown_mode_rejected(self):
        with self.assertRaises(MatchError): choose_list_format('A - B', 'Unknown')

if __name__=='__main__': unittest.main()
