"""Optional, explicit MusicBrainz recording lookup for typed search terms.

No local catalog, file paths, track IDs or media are sent. This module never
writes playlists. Network I/O happens only when lookup_recordings is called.
"""
from __future__ import annotations

import json
import re
import threading
import time
from urllib.parse import urlencode
from urllib.request import Request, build_opener, HTTPRedirectHandler

API = 'https://musicbrainz.org/ws/2/recording/'
MAX_REPLY = 256_000
MAX_RESULTS = 10
_LOCK = threading.Lock()
_LAST_CALL = 0.0


class _NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, request, fp, code, msg, headers, newurl):
        return None


class MusicBrainzError(ValueError):
    pass


def _term(value, label):
    if not isinstance(value, str):
        raise MusicBrainzError(f'{label} must be text.')
    if any(ord(c) < 32 for c in value):
        raise MusicBrainzError(f'Enter a {label.lower()} without control characters.')
    value = ' '.join(value.strip().split())
    if not value or len(value) > 120:
        raise MusicBrainzError(f'Enter a {label.lower()} of 1–120 printable characters.')
    # Escape Lucene syntax so user input stays a literal field query.
    special = set('+-!(){}[]^"~*?:\\/')
    return ''.join('\\' + c if c in special else c for c in value)


def build_query(artist, title):
    """Search only explicitly typed artist and title, not the loaded library."""
    return f'artist:"{_term(artist, "Artist")}" AND recording:"{_term(title, "Title")}"'


def _artist_name(record):
    credits = record.get('artist-credit') or []
    if not isinstance(credits, list):
        return ''
    parts = []
    for credit in credits:
        if isinstance(credit, dict):
            name = credit.get('name') or (credit.get('artist') or {}).get('name')
            if isinstance(name, str):
                parts.append(name)
            join = credit.get('joinphrase')
            if isinstance(join, str):
                parts.append(join)
        elif isinstance(credit, str):
            parts.append(credit)
    return ''.join(parts).strip()[:250]


def parse_response(raw):
    """Bound and normalize untrusted JSON; no HTML, URL, or filesystem use."""
    if isinstance(raw, bytes):
        if len(raw) > MAX_REPLY:
            raise MusicBrainzError('MusicBrainz response exceeded the 256 KB limit.')
        try:
            raw = raw.decode('utf-8')
        except UnicodeError as exc:
            raise MusicBrainzError('MusicBrainz returned invalid UTF-8.') from exc
    if not isinstance(raw, str) or len(raw) > MAX_REPLY:
        raise MusicBrainzError('Invalid or oversized MusicBrainz response.')
    try:
        payload = json.loads(raw)
    except (ValueError, TypeError) as exc:
        raise MusicBrainzError('MusicBrainz returned invalid JSON.') from exc
    if not isinstance(payload, dict) or not isinstance(payload.get('recordings'), list):
        raise MusicBrainzError('MusicBrainz returned an unexpected result structure.')
    rows = []
    for record in payload['recordings'][:MAX_RESULTS]:
        if not isinstance(record, dict):
            continue
        rid, title = record.get('id'), record.get('title')
        if not isinstance(rid, str) or not isinstance(title, str):
            continue
        if len(rid) != 36 or not all(c in '0123456789abcdef-' for c in rid.lower()):
            continue
        releases = record.get('releases') or []
        albums = []
        if isinstance(releases, list):
            for release in releases[:12]:
                if isinstance(release, dict) and isinstance(release.get('title'), str):
                    album = release['title'][:200]
                    if album not in albums:
                        albums.append(album)
        rows.append({'mbid': rid, 'artist': _artist_name(record), 'title': title[:250],
                     'albums': albums[:3], 'score': record.get('score') if isinstance(record.get('score'), int) else None})
    return rows


def _contact(value):
    if not isinstance(value, str):
        raise MusicBrainzError('MusicBrainz requires a contact URL or email in User-Agent.')
    value = value.strip()
    if len(value) > 200 or any(ord(c) < 33 or ord(c) > 126 for c in value):
        raise MusicBrainzError('Enter a contact URL or email without spaces/control characters.')
    if not (re.fullmatch(r'https://[A-Za-z0-9.-]+(?:/[A-Za-z0-9_./~%-]*)?', value)
            or re.fullmatch(r'[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}', value)):
        raise MusicBrainzError('Enter an HTTPS contact URL or email address for MusicBrainz.')
    return value


def lookup_recordings(artist, title, contact, *, opener=None):
    global _LAST_CALL
    query = build_query(artist, title)
    contact = _contact(contact)  # External service requires a reachable maintainer contact.
    url = API + '?' + urlencode({'query': query, 'fmt': 'json', 'limit': str(MAX_RESULTS)})
    request = Request(url, headers={'User-Agent': f'KyoceraPlaylistDesk/0.15 ({contact})',
                                    'Accept': 'application/json'})
    if opener is None:
        opener = build_opener(_NoRedirect()).open  # No forwarding typed terms to redirects.
    try:
        with _LOCK:  # Service policy: no more than one request per second per client.
            delay = 1.1 - (time.monotonic() - _LAST_CALL)
            if delay > 0:
                time.sleep(delay)
            _LAST_CALL = time.monotonic()
            with opener(request, timeout=8) as response:
                raw = response.read(MAX_REPLY + 1)
    except (OSError, TimeoutError) as exc:
        raise MusicBrainzError(f'Optional MusicBrainz request failed: {exc}') from exc
    return parse_response(raw)
