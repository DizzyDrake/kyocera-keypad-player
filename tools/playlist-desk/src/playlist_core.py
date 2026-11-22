"""Offline, metadata-only Kyocera playlist model. No ADB, audio I/O, or phone writes."""
import json
import os
import tempfile
import re
from pathlib import Path, PurePosixPath

SCHEMA = 'kyocera-playlists-v0.1'
MAX_BYTES = 8_000_000

class PlaylistError(ValueError):
    pass

def safe_relative(value):
    if not isinstance(value, str) or not value or '\x00' in value or '\\' in value:
        raise PlaylistError('path must be nonempty POSIX-relative text without backslashes')
    if value.startswith('/') or re.match(r'^[a-zA-Z]:', value) or any(x in ('.', '..', '') for x in value.split('/')):
        raise PlaylistError('absolute, drive or traversal path forbidden: '+repr(value))
    return value

def validate(data):
    if not isinstance(data, dict) or data.get('schema') != SCHEMA:
        raise PlaylistError('unrecognized metadata schema')
    tracks = data.get('tracks')
    lists = data.get('playlists')
    if not isinstance(tracks, list) or not isinstance(lists, list):
        raise PlaylistError('tracks and playlists must be arrays')
    if len(tracks)>50000 or len(lists)>1000:
        raise PlaylistError('dataset exceeds v0.1 limits')
    ids=set(); paths=set()
    for t in tracks:
        if not isinstance(t,dict) or not isinstance(t.get('id'),str) or not t['id'].strip() or len(t['id'])>200:
            raise PlaylistError('track must have short nonempty text id')
        if t['id'] in ids: raise PlaylistError('duplicate track id: '+t['id'])
        ids.add(t['id']); p=safe_relative(t.get('path'))
        if p.casefold() in paths: raise PlaylistError('duplicate media path (case-insensitive): '+p)
        paths.add(p.casefold())
        for key in ('title','artist','album','genre'):
            if key in t and (not isinstance(t[key],str) or len(t[key])>2000):
                raise PlaylistError('invalid '+key)
        if 'duration_ms' in t and (type(t['duration_ms']) is not int or not 0<=t['duration_ms']<=10**10):
            raise PlaylistError('invalid duration_ms')
    names=set()
    for pl in lists:
        if not isinstance(pl,dict) or not isinstance(pl.get('name'),str) or not pl['name'].strip() or len(pl['name'])>200:
            raise PlaylistError('playlist name required')
        if pl['name'].casefold() in names: raise PlaylistError('duplicate playlist name')
        names.add(pl['name'].casefold())
        if not isinstance(pl.get('track_ids'),list) or len(pl['track_ids'])>50000:
            raise PlaylistError('playlist track_ids must be array')
        for tid in pl['track_ids']:
            if not isinstance(tid,str) or tid not in ids:
                raise PlaylistError('playlist refers to missing track id: '+repr(tid))
    return data

def load(path):
    p=Path(path)
    if p.stat().st_size>MAX_BYTES: raise PlaylistError('metadata exceeds size limit')
    with p.open('r',encoding='utf-8-sig') as f:
        return validate(json.load(f))

def ordered_paths(data, playlist_name):
    validate(data)
    pl=next((p for p in data['playlists'] if p['name']==playlist_name),None)
    if pl is None: raise PlaylistError('playlist not found')
    lookup={t['id']:t for t in data['tracks']}
    return [lookup[i]['path'] for i in pl['track_ids']]

def m3u8(data, playlist_name):
    # M3U8 is a transfer aid, not a guarantee any stock Kyocera player honors order.
    paths=ordered_paths(data,playlist_name)
    if any('\n' in p or '\r' in p or p.startswith('#') for p in paths):
        raise PlaylistError('newline or # in path cannot be exported unambiguously as M3U8')
    return '#EXTM3U\n'+'\n'.join(paths)+'\n'

def encode(data):
    validate(data)
    return (json.dumps(data,ensure_ascii=False,indent=2)+'\n').encode('utf-8')

def move(pl, index, direction):
    ids=pl['track_ids']; dest=index+direction
    if not (0<=index<len(ids) and 0<=dest<len(ids)):
        return False
    ids[index],ids[dest]=ids[dest],ids[index]
    return True

def remove(pl,index):
    if not 0<=index<len(pl['track_ids']): raise PlaylistError('invalid index')
    return pl['track_ids'].pop(index)

def add(pl,tid,tracks):
    if tid not in {t['id'] for t in tracks}: raise PlaylistError('unknown track')
    pl['track_ids'].append(tid)

def validate_output(path):
    # Explicit F: guard applies even to preview/save path selection; never access F:.
    s=str(path)
    if s.replace('/', '\\').startswith(('\\\\?\\', '\\\\.\\')):
        raise PlaylistError('Windows device/extended paths are not supported')
    if re.match(r'^[Ff]:',s) or re.match(r'^[/\\]mnt[/\\][Ff]([/\\]|$)',s):
        raise PlaylistError('F: is protected and must not be selected')
    return Path(path)


def create_playlist(data, name):
    validate(data)
    if not isinstance(name, str) or not name.strip() or len(name) > 200:
        raise PlaylistError('playlist name must be nonempty and at most 200 characters')
    if len(data['playlists']) >= 1000:
        raise PlaylistError('playlist limit reached')
    if any(p['name'].casefold() == name.casefold() for p in data['playlists']):
        raise PlaylistError('playlist name already exists')
    result = {'name': name, 'track_ids': []}
    data['playlists'].append(result)
    return result


def rename_playlist(data, old_name, new_name):
    validate(data)
    pl = next((p for p in data['playlists'] if p['name'] == old_name), None)
    if pl is None:
        raise PlaylistError('playlist not found')
    if not isinstance(new_name, str) or not new_name.strip() or len(new_name) > 200:
        raise PlaylistError('playlist name must be nonempty and at most 200 characters')
    if any(p is not pl and p['name'].casefold() == new_name.casefold() for p in data['playlists']):
        raise PlaylistError('playlist name already exists')
    pl['name'] = new_name
    return pl


def delete_playlist(data, name):
    validate(data)
    for i, pl in enumerate(data['playlists']):
        if pl['name'] == name:
            return data['playlists'].pop(i)
    raise PlaylistError('playlist not found')


def atomic_write(path, payload, replace_existing=False):
    """Same-directory temporary write, fsync, then atomic commit.

    For a NEW output, os.link is a no-clobber commit on ordinary NTFS/POSIX
    filesystems. If hard links are unsupported, fail without partial output.
    For a confirmed replacement, os.replace commits after the payload is ready.
    Parent junctions/reparse points cannot be proven safe without device access.
    """
    p = validate_output(path)
    if not isinstance(payload, bytes):
        raise PlaylistError('output must be bytes')
    tmp = None
    try:
        with tempfile.NamedTemporaryFile(mode='wb', dir=p.parent, prefix='.playlistdesk_',
                                         suffix='.tmp', delete=False) as f:
            tmp = Path(f.name)
            f.write(payload)
            f.flush()
            os.fsync(f.fileno())
        if replace_existing:
            os.replace(tmp, p)
        else:
            os.link(tmp, p)
        return p
    finally:
        if tmp is not None:
            tmp.unlink(missing_ok=True)
