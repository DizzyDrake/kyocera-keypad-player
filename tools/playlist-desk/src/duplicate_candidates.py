"""Read-only duplicate-song *candidate* groups for Playlist Desk metadata.

No files are read, deleted, moved, or renamed. Matching metadata is not proof
of identical audio, and an album version/live recording may share a title.
"""
import re
import unicodedata
from collections import defaultdict


def _norm(value):
    if not isinstance(value, str):
        return ''
    value = unicodedata.normalize('NFKC', value).casefold()
    return ' '.join(re.findall(r'\w+', value, flags=re.UNICODE))


def candidate_groups(tracks, tolerance_ms=2000):
    """Return stable, conservative candidate pairs, not automatic deletions.

    Require nonempty title and artist, and both numeric durations within the
    requested tolerance. Pairwise results avoid nontransitive duration chains.
    Distinct track IDs and paths remain intact.
    """
    if type(tolerance_ms) is not int or tolerance_ms < 0:
        raise ValueError('tolerance_ms must be a nonnegative integer')
    buckets = defaultdict(list)
    for track in tracks:
        if not isinstance(track, dict):
            continue
        title, artist = _norm(track.get('title')), _norm(track.get('artist'))
        duration = track.get('duration_ms')
        if not title or not artist or type(duration) is not int or duration < 0:
            continue
        buckets[(title, artist)].append(track)
    pairs = []
    for key, group in buckets.items():
        ordered = sorted(group, key=lambda t:(t['duration_ms'],str(t.get('id',''))))
        for i, first in enumerate(ordered):
            for second in ordered[i+1:]:
                if second['duration_ms'] - first['duration_ms'] > tolerance_ms:
                    break
                if first.get('id') == second.get('id') or first.get('path') == second.get('path'):
                    continue
                pairs.append({'track_ids':(first.get('id'),second.get('id')),
                              'paths':(first.get('path'),second.get('path')),
                              'title_key':key[0], 'artist_key':key[1],
                              'duration_difference_ms':second['duration_ms']-first['duration_ms'],
                              'review_required':True})
    return sorted(pairs,key=lambda p:(p['artist_key'],p['title_key'],str(p['track_ids'])))


def iter_candidate_pairs(tracks, tolerance_ms=2000):
    """Yield candidate pairs without constructing the quadratic result list.

    Used for bounded GUI pages. Order is deterministic by normalized
    artist/title, then duration and ID; it need not match candidate_groups.
    """
    if type(tolerance_ms) is not int or tolerance_ms < 0:
        raise ValueError('tolerance_ms must be a nonnegative integer')
    buckets = defaultdict(list)
    for track in tracks:
        if not isinstance(track, dict):
            continue
        title, artist = _norm(track.get('title')), _norm(track.get('artist'))
        duration = track.get('duration_ms')
        if title and artist and type(duration) is int and duration >= 0:
            buckets[(artist, title)].append(track)
    for artist, title in sorted(buckets):
        ordered = sorted(buckets[(artist, title)],
                         key=lambda t: (t['duration_ms'], str(t.get('id', ''))))
        for i, first in enumerate(ordered):
            for second in ordered[i + 1:]:
                difference = second['duration_ms'] - first['duration_ms']
                if difference > tolerance_ms:
                    break
                if first.get('id') == second.get('id') or first.get('path') == second.get('path'):
                    continue
                yield {'track_ids': (first.get('id'), second.get('id')),
                       'paths': (first.get('path'), second.get('path')),
                       'title_key': title, 'artist_key': artist,
                       'duration_difference_ms': difference, 'review_required': True}
