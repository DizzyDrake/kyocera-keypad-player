"""Offline PC-only playlist entries for explicit multi-file chooser selections.

These are *not* phone tracks. No file is opened/copied, no metadata is read,
no ADB action is performed. The phone bridge intentionally rejects changed
track inventories until an actual owner-approved import/mapping exists.
"""
import copy
import ntpath
import posixpath
import re
import uuid
from pathlib import Path
from playlist_core import PlaylistError, validate

AUDIO_EXTS = {'.mp3', '.m4a', '.aac', '.ogg', '.opus', '.flac', '.wav', '.wma', '.mp4', '.m4b'}


def validate_pc_audio_path(value):
    """Validate chooser text without opening the selected media.

    Windows drive paths retain the legacy v0.16 semantics, even when a saved
    plan is opened on Linux. Native POSIX paths are accepted for Linux staging.
    Protected F: and its conventional /mnt/f mount are rejected as text.
    """
    if not isinstance(value, str) or not value or '\x00' in value or any(c in value for c in '\r\n'):
        raise PlaylistError('invalid selected audio filename')
    if value.startswith('/'):
        if (value.startswith('//') or '\\' in value or
                re.match(r'^/mnt/[Ff](?:/|$)', value)):
            raise PlaylistError('network, protected or ambiguous POSIX path is not allowed')
        ext = posixpath.splitext(value)[1].lower()
        if ext not in AUDIO_EXTS:
            raise PlaylistError('unsupported audio file extension: ' + ext)
        return value
    normalized = value.replace('/', '\\')
    if (normalized.startswith('\\\\') or normalized.startswith('\\\\?\\') or
            normalized.startswith('\\\\.\\') or re.match(r'^[Ff]:', normalized)):
        raise PlaylistError('protected F: / network / device path is not allowed')
    if not re.match(r'^[A-Za-z]:\\', normalized) or re.match(r'^[Ff]:', normalized):
        raise PlaylistError('select an absolute local Windows or Linux audio path (not F:)')
    ext = ntpath.splitext(normalized)[1].lower()
    if ext not in AUDIO_EXTS:
        raise PlaylistError('unsupported audio file extension: ' + ext)
    return normalized


def _path_key(path):
    """Windows paths are case-insensitive; Linux paths are case-sensitive."""
    return path if path.startswith('/') else path.casefold()


def _path_basename(path):
    return posixpath.basename(path) if path.startswith('/') else ntpath.basename(path)


def append_pc_files(data, playlist_name, selections):
    """Return (new_data, playlist_references_added, already_in_playlist); original unchanged.

    Existing PC-only tracks are reused across playlists by ID. This prevents
    duplicate inventory entries and permits the same file in multiple lists.

    Never call stat/open on selections. The native file chooser is the only
    source of selected paths; file existence is not independently verified.
    """
    validate(data)
    if not isinstance(selections, (list, tuple)):
        raise PlaylistError('file chooser selection must be a list or tuple')
    if len(selections) > 1000:
        raise PlaylistError('select at most 1000 files at a time')
    candidate = copy.deepcopy(data)
    pl = next((p for p in candidate['playlists'] if p['name'] == playlist_name), None)
    if pl is None:
        raise PlaylistError('select a playlist before adding files')
    # A staged PC file is one editor inventory record that may be referenced by
    # multiple playlists. Duplicate suppression applies *within* a playlist,
    # not globally across the editor. No file is opened or inspected here.
    existing = {_path_key(t['pc_local_file']): t['id'] for t in candidate['tracks']
                if t.get('pc_status') == 'pending-local-not-on-phone'
                and isinstance(t.get('pc_local_file'), str)}
    count = skipped = 0
    for original in selections:
        p = validate_pc_audio_path(original)
        key = _path_key(p)
        if key in existing:
            tid = existing[key]
            if tid in pl['track_ids']:
                skipped += 1
                continue
            if len(pl['track_ids']) >= 50000:
                raise PlaylistError('playlist capacity reached')
            pl['track_ids'].append(tid)
            count += 1
            continue
        if len(candidate['tracks']) >= 50000 or len(pl['track_ids']) >= 50000:
            raise PlaylistError('track/playlist capacity reached')
        basename = _path_basename(p)
        if basename in ('', '.', '..'):
            raise PlaylistError('invalid audio basename')
        title = ntpath.splitext(basename)[0] if not p.startswith('/') else posixpath.splitext(basename)[0]
        if not title or len(title) > 2000:
            raise PlaylistError('audio title too long or empty')
        track_id = 'pc-local-' + uuid.uuid4().hex
        # Stable synthetic *editor-only* path; never claim this is a phone path.
        relative = 'pc-pending/' + track_id + '/' + basename
        track = {'id': track_id, 'path': relative, 'title': title,
                 'pc_local_file': p, 'pc_status': 'pending-local-not-on-phone'}
        candidate['tracks'].append(track)
        pl['track_ids'].append(track_id)
        existing[key] = track_id
        count += 1
    validate(candidate)
    return candidate, count, skipped


def playlist_has_pending_files(data, playlist_name):
    if data is None:
        return False
    pl = next((p for p in data['playlists'] if p['name'] == playlist_name), None)
    if pl is None:
        return False
    pending = {t['id'] for t in data['tracks'] if t.get('pc_status') == 'pending-local-not-on-phone'}
    return any(tid in pending for tid in pl['track_ids'])


def any_pending_files(data):
    return bool(data and any(t.get('pc_status') == 'pending-local-not-on-phone' for t in data['tracks']))


def move_track_to(pl, start, dest):
    """Move a playlist entry to the drop index, preserving all other order."""
    ids = pl['track_ids']
    if type(start) is not int or type(dest) is not int or not (0 <= start < len(ids) and 0 <= dest < len(ids)):
        return False
    if start == dest:
        return False
    item = ids.pop(start)
    ids.insert(dest, item)
    return True
