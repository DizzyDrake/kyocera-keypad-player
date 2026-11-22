"""Linux path portability tests; no actual media or device files accessed."""
import copy
import unittest
from unittest.mock import patch
from pc_file_add import append_pc_files, validate_pc_audio_path
from playlist_core import PlaylistError, validate


def fixture():
    return {'schema': 'kyocera-playlists-v0.1', 'tracks': [],
            'playlists': [{'name': 'Music A', 'track_ids': []},
                          {'name': 'Music B', 'track_ids': []}]}


class LinuxPortTests(unittest.TestCase):
    def test_absolute_posix_paths_are_accepted_as_text(self):
        for suffix in ('.mp3', '.flac', '.ogg', '.m4b', '.opus'):
            path = '/home/aurora/Música/Álpha' + suffix
            self.assertEqual(validate_pc_audio_path(path), path)

    def test_unsafe_or_unsupported_paths_rejected(self):
        for path in ('relative.mp3', '~/Music/song.mp3', '/home/user/file.txt',
                     '//server/share/song.mp3', '/mnt/f/song.mp3', '/mnt/F/song.mp3',
                     '/home/user/bad\\name.mp3', '/home/user/new\nline.mp3',
                     '/home/user/zero\x00.mp3', 'F:\\Media\\song.mp3'):
            with self.subTest(path=repr(path)), self.assertRaises(PlaylistError):
                validate_pc_audio_path(path)

    def test_posix_case_sensitive_reuse_and_cross_playlist(self):
        data = fixture()
        one, count, skipped = append_pc_files(data, 'Music A', [
            '/home/user/Music/Song.mp3', '/home/user/Music/song.mp3'])
        self.assertEqual((count, skipped), (2, 0))
        self.assertEqual(len(one['tracks']), 2)
        two, count, skipped = append_pc_files(one, 'Music B', [
            '/home/user/Music/Song.mp3', '/home/user/Music/song.mp3'])
        self.assertEqual((count, skipped), (2, 0))
        self.assertEqual(len(two['tracks']), 2)
        self.assertEqual(two['playlists'][0]['track_ids'], two['playlists'][1]['track_ids'])
        three, count, skipped = append_pc_files(two, 'Music B', ['/home/user/Music/Song.mp3'])
        self.assertEqual((count, skipped), (0, 1))
        self.assertEqual(three, two)
        self.assertEqual(data, fixture())
        validate(two)

    def test_linux_path_keeps_basename_and_pending_flag(self):
        data, count, _ = append_pc_files(fixture(), 'Music A', ['/home/user/Albums/Älpha - First.FLAC'])
        self.assertEqual(count, 1)
        track = data['tracks'][0]
        self.assertEqual(track['title'], 'Älpha - First')
        self.assertEqual(track['pc_local_file'], '/home/user/Albums/Älpha - First.FLAC')
        self.assertEqual(track['pc_status'], 'pending-local-not-on-phone')
        self.assertTrue(track['path'].startswith('pc-pending/'))

    def test_mixed_platform_paths_are_distinct(self):
        one, _, _ = append_pc_files(fixture(), 'Music A', ['C:\\Music\\Song.mp3'])
        two, _, _ = append_pc_files(one, 'Music B', ['/home/user/Music/Song.mp3'])
        self.assertEqual(len(two['tracks']), 2)

    def test_no_media_file_access(self):
        with patch('builtins.open', side_effect=AssertionError('opened audio')), \
             patch('pathlib.Path.stat', side_effect=AssertionError('stat audio')):
            data, count, skipped = append_pc_files(fixture(), 'Music A', ['/home/user/Music/First.mp3'])
        self.assertEqual((count, skipped), (1, 0))
        self.assertEqual(len(data['tracks']), 1)

    def test_atomic_rejection_and_unchanged_input(self):
        data = fixture()
        snapshot = copy.deepcopy(data)
        with self.assertRaises(PlaylistError):
            append_pc_files(data, 'Music A', ['/home/user/Music/ok.mp3', '/mnt/f/forbidden.mp3'])
        self.assertEqual(data, snapshot)


if __name__ == '__main__':
    unittest.main()
