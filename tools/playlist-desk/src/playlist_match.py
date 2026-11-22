"""Offline, deterministic track-ID matching for user-provided playlist text.

No network, local audio reads, automatic phone writes, model calls or guessed IDs.
All matching decisions refer exclusively to supplied, validated metadata rows.
"""
import csv
import io
import re
import unicodedata
from pathlib import PurePosixPath

MAX_TEXT = 100_000
MAX_ENTRIES = 1000

class MatchError(ValueError):
    pass


def norm(value):
    if not isinstance(value, str):
        return ''
    return ' '.join(unicodedata.normalize('NFKC', value).casefold().split())


def _entry(artist='', title='', album='', source=''):
    return {'artist': artist.strip(), 'title': title.strip(), 'album': album.strip(), 'source': source}


def parse_pasted(text):
    """CSV header artist,title[,album] OR lines 'Artist - Title' or 'Artist | Title | Album'.

    Explicitly rejects unstructured URLs; never fetches outside websites.
    """
    if not isinstance(text, str) or len(text) > MAX_TEXT:
        raise MatchError('Pasted list must be text under 100,000 characters.')
    raw = [line.strip() for line in text.lstrip('\ufeff').splitlines() if line.strip()]
    if not raw:
        raise MatchError('Paste a list with at least one track.')
    if len(raw) > MAX_ENTRIES + 1:
        raise MatchError('At most 1,000 entries can be previewed at once.')
    if any(line.lower().startswith(('http://', 'https://')) for line in raw):
        raise MatchError('Website URLs are not fetched. Paste its track list or a CSV export instead.')
    first = raw[0]
    # CSV with named columns, optional album, arbitrary column order.
    try:
        header = next(csv.reader([first]))
    except csv.Error as exc:
        raise MatchError('Malformed CSV header.') from exc
    fields = [norm(x).strip() for x in header]
    if 'title' in fields and 'artist' in fields:
        try:
            reader = csv.DictReader(io.StringIO('\n'.join(raw)), strict=True)
            if reader.fieldnames is None:
                raise MatchError('CSV header missing.')
            mapping = {norm(x): x for x in reader.fieldnames if x is not None}
            entries = []
            for row in reader:
                if None in row:
                    raise MatchError('CSV row has extra columns.')
                e = _entry(row.get(mapping['artist']) or '', row.get(mapping['title']) or '',
                           row.get(mapping['album']) or '' if 'album' in mapping else '', 'CSV')
                if not e['title'] or not e['artist']:
                    raise MatchError('CSV rows require both artist and title.')
                entries.append(e)
        except csv.Error as exc:
            raise MatchError('Malformed CSV rows.') from exc
    else:
        entries = []
        for number, line in enumerate(raw, 1):
            if line.startswith('#'):
                continue  # user comments, not an M3U importer
            if '|' in line:
                fields = [x.strip() for x in line.split('|')]
                if len(fields) not in (2, 3):
                    raise MatchError(f'Line {number}: use Artist | Title | optional Album.')
                artist, title = fields[:2]
                album = fields[2] if len(fields) == 3 else ''
            elif any(sep in line for sep in (' - ', ' — ', ' – ')):
                sep = next(sep for sep in (' - ', ' — ', ' – ') if sep in line)
                artist, title = line.split(sep, 1)
                album = ''
            else:
                raise MatchError(f'Line {number}: expected Artist - Title, Artist | Title | Album, or CSV.')
            if not artist.strip() or not title.strip():
                raise MatchError(f'Line {number}: artist and title cannot be empty.')
            entries.append(_entry(artist, title, album, f'line {number}'))
    if not entries or len(entries) > MAX_ENTRIES:
        raise MatchError('No usable tracks, or more than 1,000 entries.')
    return entries


def match_entries(entries, tracks):
    """Preserve requested order; never auto-choose duplicate title/artist editions."""
    rows = []
    for e in entries:
        if not isinstance(e, dict):
            raise MatchError('Invalid entry.')
        title, artist, album = (norm(e.get(k)) for k in ('title', 'artist', 'album'))
        if not title or not artist:
            raise MatchError('Artist and title are required for every entry.')
        matches = [t for t in tracks if norm(t.get('title')) == title and
                   norm(t.get('artist')) == artist and
                   (not album or norm(t.get('album')) == album)]
        rows.append({'entry': dict(e), 'candidate_ids': [t['id'] for t in matches],
                     'chosen_id': matches[0]['id'] if len(matches) == 1 else None,
                     'status': 'MATCH' if len(matches) == 1 else 'MISSING' if not matches else 'AMBIGUOUS'})
    return rows


def filter_artist_album(tracks, artist='', album=''):
    """Exact artist/album metadata filters, preserving snapshot order."""
    a, b = norm(artist), norm(album)
    if not a and not b:
        raise MatchError('Enter an artist or album to preview matching tracks.')
    return [t for t in tracks if (not a or norm(t.get('artist')) == a) and
            (not b or norm(t.get('album')) == b)]


def resolved_ids(rows, existing=()):
    """Return unique, real chosen IDs in input order; duplicates flagged explicitly."""
    seen = set(existing)
    chosen, duplicate_rows, unresolved_rows = [], [], []
    for i, row in enumerate(rows, 1):
        tid = row.get('chosen_id')
        if not tid or tid not in row.get('candidate_ids', []):
            unresolved_rows.append(i)
        elif tid in seen:
            duplicate_rows.append(i)
        else:
            seen.add(tid)
            chosen.append(tid)
    return chosen, duplicate_rows, unresolved_rows


# WQB446: external M3U/M3U8 is a *text track-list*, not a request to open media.
# Do not dereference media paths or URLs, even if an EXTINF line is present.
def looks_like_m3u(text):
    if not isinstance(text, str):
        return False
    return any(line.lstrip().upper().startswith(('#EXTM3U', '#EXTINF:'))
               for line in text.lstrip('\ufeff').splitlines())


# WQB447: the imported file extension is a hint, not a persistent mode.
# A paste/edit invalidates that hint; explicit user choice always wins.
def choose_list_format(text, selection='Auto detect', unchanged_import_hint=None):
    if selection == 'M3U/M3U8':
        return 'm3u'
    if selection == 'Artist/title or CSV':
        return 'pasted'
    if selection != 'Auto detect':
        raise MatchError('Choose a supported list format.')
    if looks_like_m3u(text) or unchanged_import_hint == 'm3u':
        return 'm3u'
    return 'pasted'


def parse_m3u(text):
    """Read bounded M3U/M3U8 text preserving line order and inert source paths.

    An EXTINF artist/title is a *hint*, not a trusted ID. Relative path matches
    are checked against the already loaded phone metadata; media is never opened.
    """
    if not isinstance(text, str) or len(text) > MAX_TEXT:
        raise MatchError('M3U text must be under 100,000 characters.')
    entries, hint = [], None
    for line_no, original in enumerate(text.lstrip('\ufeff').splitlines(), 1):
        line = original.strip()
        if not line:
            continue
        if line.upper().startswith('#EXTINF:'):
            hint = ('', '')
            if ',' in line:
                label = line.split(',', 1)[1].strip()
                for separator in (' - ', ' — ', ' – '):
                    if separator in label:
                        artist, title = label.split(separator, 1)
                        if artist.strip() and title.strip():
                            hint = (artist.strip(), title.strip())
                        break
            continue
        if line.startswith('#'):
            continue
        if '\x00' in line:
            raise MatchError(f'M3U line {line_no}: NUL in source path.')
        artist, title = hint or ('', '')
        entries.append({'artist': artist, 'title': title, 'album': '',
                        'source': f'M3U line {line_no}', 'path': line})
        hint = None
        if len(entries) > MAX_ENTRIES:
            raise MatchError('At most 1,000 M3U entries can be previewed.')
    if not entries:
        raise MatchError('No M3U media entries found.')
    return entries


def _path_key(path):
    """Normalize harmless dot segments for TEXT comparison, never filesystem I/O.

    The caller checks whether an M3U source is relative and traversal-free
    before using this key for an automatic exact-path match. Keep '..' intact
    here so this comparison helper never silently collapses traversal.
    """
    path = path.strip().replace('\\', '/')
    parts = [part for part in path.split('/') if part != '.']
    return unicodedata.normalize('NFKC', '/'.join(parts)).casefold()


def _is_relative_source(path):
    p = path.replace('\\', '/')
    return (not p.startswith('/') and not re.match(r'^[a-zA-Z]:', p)
            and not re.match(r'^[a-zA-Z][a-zA-Z0-9+.-]*://', p)
            and all(part not in ('..', '') for part in p.split('/')))


def match_m3u(entries, tracks):
    """Resolve exact local paths first, then EXTINF; filename alone needs review.

    Every candidate ID comes from supplied metadata. Duplicate matches remain
    ambiguous; no path/URL is opened, fetched or interpreted as a local file.
    """
    rows = []
    for e in entries:
        if not isinstance(e, dict) or not isinstance(e.get('path'), str):
            raise MatchError('Invalid M3U entry.')
        path = e['path']
        exact = ([t for t in tracks if _path_key(t.get('path', '')) == _path_key(path)]
                 if _is_relative_source(path) else [])
        if exact:
            matches = exact
            # An external EXTINF tag can disagree with the exact local path.
            # Preserve the candidate but require a deliberate owner choice.
            mismatch = bool(norm(e.get('artist')) and norm(e.get('title')) and
                            any(norm(t.get('artist')) != norm(e['artist']) or
                                norm(t.get('title')) != norm(e['title']) for t in matches))
            basis = ('exact path conflicts with EXTINF; manual review required' if mismatch
                     else 'exact local relative path')
            auto = len(matches) == 1 and not mismatch
        elif norm(e.get('artist')) and norm(e.get('title')):
            basis = 'EXTINF artist/title (not a track ID)'
            matches = [t for t in tracks if norm(t.get('artist')) == norm(e['artist'])
                       and norm(t.get('title')) == norm(e['title'])]
            auto = len(matches) == 1
        else:
            basis = 'filename only; manual review required'
            # Never infer local files from remote URLs. Filenames are only a
            # candidate hint, not sufficient to authorize a match.
            is_url = bool(re.match(r'^[a-zA-Z][a-zA-Z0-9+.-]*://', path))
            filename = PurePosixPath(path.replace('\\', '/')).name
            matches = ([t for t in tracks
                        if norm(PurePosixPath(t.get('path', '')).name) == norm(filename)]
                       if filename and not is_url else [])
            auto = False
        status = ('MATCH' if auto else 'MISSING' if not matches
                  else 'REVIEW' if len(matches) == 1 else 'AMBIGUOUS')
        rows.append({'entry': dict(e), 'candidate_ids': [t['id'] for t in matches],
                     'chosen_id': matches[0]['id'] if auto else None,
                     'status': status, 'match_basis': basis})
    return rows
