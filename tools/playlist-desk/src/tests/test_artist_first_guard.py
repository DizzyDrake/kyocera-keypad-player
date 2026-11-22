"""Regressions from owner Gemma4 artist query returning 80 unrelated pairs and 461 tracks.

Fictional input only; no Ollama connection or owner media/library used.
"""
import json
import unittest
from unittest.mock import patch

from gemma_local import (
    MatchError, MAX_MODEL_SELECTED_PAIRS, checked_model_rows, catalog_pairs,
    plan_artist_first, request_local_model, rows_from_indices,
)


class Reply:
    def __init__(self, payload):
        self.payload = payload
    def __enter__(self):
        return self
    def __exit__(self, *args):
        return None
    def read(self, n):
        return self.payload[:n]


class TestArtistFirst(unittest.TestCase):
    def setUp(self):
        self.tracks = [
            {'id': 'h1', 'artist': 'Jimi Hendrix', 'album': 'First Light', 'title': 'A'},
            {'id': 'h2', 'artist': 'Jimi Hendrix', 'album': 'First Light', 'title': 'B'},
            {'id': 'h3', 'artist': 'Jimi Hendrix', 'album': 'Live at Dawn', 'title': 'C'},
            {'id': 'c1', 'artist': 'Charming Disaster', 'album': 'Super Natural History', 'title': 'D'},
            {'id': 't1', 'artist': 'Jimi Hendrix Tribute Band', 'album': 'Fake', 'title': 'E'},
            {'id': 'e1', 'artist': 'Eric Clapton', 'album': 'Live at Dawn', 'title': 'F'},
        ]
        self.pairs = catalog_pairs(self.tracks)

    def test_exact_artist_bypasses_model_and_never_picks_tribute(self):
        for text in ('Jimi Hendrix', 'jimi hendrix?', 'find Jimi Hendrix',
                     'songs by Jimi Hendrix', 'find all songs by Jimi Hendrix',
                     'Jimi Hendrix tracks', 'jimi hendrix please'):
            with self.subTest(text=text):
                pairs, local, _ = plan_artist_first(text, self.pairs)
                self.assertTrue(local)
                self.assertEqual([p['artist'] for p in pairs], ['Jimi Hendrix', 'Jimi Hendrix'])
                rows = rows_from_indices(self.tracks, pairs, list(range(1, len(pairs)+1)))
                self.assertEqual({r['chosen_id'] for r in rows}, {'h1', 'h2', 'h3'})

    def test_full_credit_exactness_no_implicit_article_alias(self):
        pairs = catalog_pairs([{'artist': 'The Jimi Hendrix', 'album': 'One'}])
        subset, local, _ = plan_artist_first('The Jimi Hendrix', pairs)
        self.assertTrue(local)
        self.assertEqual(len(subset), 1)
        # Bare artist names do not implicitly match a distinct credit.
        subset, local, _ = plan_artist_first('Jimi Hendrix', pairs)
        self.assertFalse(local)
        with self.assertRaisesRegex(MatchError, 'No exact local artist'):
            plan_artist_first('songs by Jimi Hendrix', pairs)
        subset, local, _ = plan_artist_first('Jimi', self.pairs)
        self.assertFalse(local)

    def test_explicit_unknown_artist_refuses_model(self):
        with self.assertRaisesRegex(MatchError, 'No exact local artist'):
            plan_artist_first('songs by Nobody Exists', self.pairs)

    def test_artist_anchored_prompt_uses_fewer_pairs(self):
        pairs, direct, scope = plan_artist_first('Compare Jimi Hendrix and Eric Clapton albums', self.pairs)
        self.assertFalse(direct)
        self.assertIn('artist-narrowed', scope)
        self.assertEqual({p['artist'] for p in pairs}, {'Jimi Hendrix', 'Eric Clapton'})

    def test_negated_album_does_not_narrow_catalog_to_excluded_album(self):
        subset, direct, _ = plan_artist_first('all albums except Super Natural History', self.pairs)
        self.assertFalse(direct)
        self.assertEqual(len(subset), len(self.pairs))

    def test_album_anchored_prompt_uses_fewer_pairs(self):
        pairs, direct, scope = plan_artist_first('Maybe the Super Natural History album', self.pairs)
        self.assertFalse(direct)
        self.assertIn('album-narrowed', scope)
        self.assertEqual([(p['artist'], p['album']) for p in pairs], [('Charming Disaster','Super Natural History')])

    def test_similarity_prompt_does_not_collapse_to_reference_artist(self):
        pairs, direct, _ = plan_artist_first('Artists similar to Jimi Hendrix', self.pairs)
        self.assertFalse(direct)
        self.assertEqual(len(pairs), len(self.pairs))

    def test_80_selection_failure_is_caught_before_expansion(self):
        tracks = []
        for i in range(1, 101):
            for n in range(6):
                tracks.append({'id':f'{i}/{n}', 'artist':f'Artist {i}',
                               'album':f'Album {i}', 'title':f'Track {n}'})
        pairs = catalog_pairs(tracks)
        with self.assertRaisesRegex(MatchError, '80 artist/album pairs'):
            checked_model_rows(tracks,pairs,list(range(1,81)))
        # Original behavior: 80 chosen pairs would mean 480 tracks.
        self.assertEqual(len(rows_from_indices(tracks,pairs,list(range(1,81)))),480)

    def test_small_pair_count_but_huge_tracks_is_rejected(self):
        tracks = [{'id':f'long-{n}', 'artist':'Artist X', 'album':'Long Album', 'title':str(n)}
                  for n in range(121)]
        pairs = catalog_pairs(tracks)
        with self.assertRaisesRegex(MatchError, '121 tracks'):
            checked_model_rows(tracks,pairs,[1])

    def test_reasonable_model_response_passes(self):
        rows = checked_model_rows(self.tracks,self.pairs,[3])
        self.assertEqual([r['chosen_id'] for r in rows], ['c1'])
        self.assertEqual(checked_model_rows(self.tracks,self.pairs,[]),[])

    def test_schema_and_no_thinking_set_on_actual_request(self):
        def opener(req,timeout):
            self.assertEqual(req.full_url,'http://127.0.0.1:11434/api/generate')
            body=json.loads(req.data)
            self.assertIs(body['think'],False)
            self.assertEqual(body['model'],'gemma4:12b')
            self.assertEqual(body['format']['type'],'object')
            self.assertEqual(body['format']['required'],['indices'])
            self.assertEqual(body['format']['properties']['indices']['maxItems'],100)
            self.assertEqual(body['format']['properties']['indices']['items']['maximum'],len(self.pairs))
            self.assertNotIn('h1',body['prompt'])
            self.assertNotIn('Track',body['prompt'])
            return Reply(json.dumps({'response':'{"indices":[1]}'}).encode())
        self.assertEqual(request_local_model('Something imaginative',self.pairs,'gemma4:12b',opener=opener),([1],0))

    def test_raw_logging_opt_in(self):
        def opener(req,timeout):
            return Reply(json.dumps({'response':'{"indices":[]}'}).encode())
        with patch.dict('os.environ', {'PLAYLIST_DESK_DEBUG_GEMMA':'0'}):
            with patch('builtins.print') as printer:
                request_local_model('Any',self.pairs,'gemma4:12b',opener=opener)
                printer.assert_not_called()
        with patch.dict('os.environ', {'PLAYLIST_DESK_DEBUG_GEMMA':'1'}):
            with patch('builtins.print') as printer:
                request_local_model('Any',self.pairs,'gemma4:12b',opener=opener)
                self.assertGreaterEqual(printer.call_count,3)

if __name__=='__main__':
    unittest.main()
