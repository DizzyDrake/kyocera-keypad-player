"""Offline, synthetic-only metadata interchange experiment. NOT an Android importer or ADB tool.

@bridge WHAT: Phone snapshot -> WQ140 PC editor JSON -> guarded proposed phone playlist plan.
@bridge WHY: Never infer track identity from a name/path or modify audio to sync playlists.
@bridge HOW: Exact keys, snapshot digest, revision and explicit playlist IDs; reject conflicts.
@bridge LIMIT: Invented phone-export schema; no real Android exporter or importer exists.
"""
import argparse
import copy
import hashlib
import json
from pathlib import Path
from playlist_core import validate as validate_pc, safe_relative, atomic_write, validate_output, PlaylistError

PHONE_SCHEMA='kyocera-phone-snapshot-v0.1-PROVISIONAL'
BRIDGE_SCHEMA='kyocera-bridge-v0.1-PROVISIONAL'
PLAN_SCHEMA='kyocera-bridge-plan-v0.1-PROVISIONAL'
MAX_BYTES=8_000_000

class BridgeError(ValueError): pass

def digest(value):
    return hashlib.sha256(json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode('utf-8')).hexdigest()

def _short(s, label, max_len=200):
    if not isinstance(s,str) or not s.strip() or len(s)>max_len or any(ord(c)<32 for c in s):
        raise BridgeError('invalid '+label)
    return s

def _int(n,label,limit=10**15):
    if type(n) is not int or not 0<=n<=limit: raise BridgeError('invalid '+label)
    return n

def validate_phone(data):
    if not isinstance(data,dict) or data.get('schema')!=PHONE_SCHEMA: raise BridgeError('unknown phone snapshot schema')
    _short(data.get('snapshot_id'),'snapshot_id')
    _int(data.get('revision'),'revision',10**9)
    tracks=data.get('tracks'); lists=data.get('playlists')
    if not isinstance(tracks,list) or len(tracks)>50000 or not isinstance(lists,list) or len(lists)>1000:
        raise BridgeError('invalid tracks/playlists arrays')
    keys=set(); paths=set(); ids=set(); names=set()
    for t in tracks:
        if not isinstance(t,dict): raise BridgeError('invalid track')
        # WQ140 PC editor caps track IDs at 200 characters. Fail at the phone
        # snapshot boundary instead of exporting a file its editor cannot open.
        k=_short(t.get('key'),'track key',200)
        if k in keys: raise BridgeError('duplicate track key')
        keys.add(k)
        try: path=safe_relative(t.get('path'))
        except PlaylistError as e: raise BridgeError(str(e)) from e
        if path.casefold() in paths: raise BridgeError('duplicate path; identity ambiguous')
        paths.add(path.casefold())
        for name in ('title','artist','album','genre'):
            if name in t and (not isinstance(t[name],str) or len(t[name])>2000): raise BridgeError('invalid '+name)
        if 'duration_ms' in t: _int(t['duration_ms'],'duration_ms',10**10)
        if 'size_bytes' in t: _int(t['size_bytes'],'size_bytes')
    for p in lists:
        if not isinstance(p,dict): raise BridgeError('invalid playlist')
        pid=_short(p.get('id'),'playlist id')
        name=_short(p.get('name'),'playlist name')
        if pid in ids or name.casefold() in names: raise BridgeError('duplicate playlist id/name')
        ids.add(pid); names.add(name.casefold())
        if type(p.get('audiobook')) is not bool: raise BridgeError('audiobook must be boolean')
        entries=p.get('track_keys')
        if not isinstance(entries,list) or len(entries)>50000 or len(entries)!=len(set(map(str,entries))):
            raise BridgeError('duplicate or invalid playlist entries')
        if any(not isinstance(x,str) or x not in keys for x in entries):
            raise BridgeError('missing track key in phone playlist')
    for label in ('music','book'):
        ctx=data.get(label,{})
        if not isinstance(ctx,dict): raise BridgeError('invalid '+label+' progress')
        pid=ctx.get('playlist_id',''); key=ctx.get('track_key','')
        if not isinstance(pid,str) or not isinstance(key,str): raise BridgeError('invalid '+label+' progress identifiers')
        if pid and pid not in ids: raise BridgeError('unknown '+label+' playlist')
        if key and key not in keys: raise BridgeError('unknown '+label+' track')
        if key and pid and key not in next(p['track_keys'] for p in lists if p['id']==pid):
            raise BridgeError('current '+label+' track not in selected playlist')
        if 'position_ms' in ctx: _int(ctx['position_ms'],label+' position',10**15)
    marks=data.get('bookmarks',[])
    if not isinstance(marks,list) or len(marks)>10000: raise BridgeError('invalid bookmarks')
    for mark in marks:
        if not isinstance(mark,dict) or mark.get('track_key') not in keys: raise BridgeError('invalid bookmark track')
        _short(mark.get('name'),'bookmark name',1000)
        _int(mark.get('position_ms'),'bookmark position',10**15)
    return data

def phone_to_pc(phone):
    validate_phone(phone)
    pc = {
        'schema':'kyocera-playlists-v0.1',
        'tracks':[{'id':t['key'],'path':t['path'],**{k:t[k] for k in ('title','artist','album','genre','duration_ms') if k in t}} for t in phone['tracks']],
        'playlists':[{'name':p['name'],'track_ids':p['track_keys'][:], 'phone_id':p['id'],'audiobook':p['audiobook']} for p in phone['playlists']],
        'bridge':{'schema':BRIDGE_SCHEMA,'snapshot_id':phone['snapshot_id'],'revision':phone['revision'],
                  'phone_sha256':digest(phone), 'track_sha256':digest(phone['tracks'])}}
    # Keep the provisional bridge export compatible with the *actual* WQ140
    # editor contract. A valid phone snapshot must not yield unusable PC JSON.
    try: validate_pc(pc)
    except PlaylistError as e: raise BridgeError('phone snapshot cannot be opened in PC editor: '+str(e)) from e
    return pc

def plan(phone,pc,allow_reset_progress=False):
    validate_phone(phone)
    try: validate_pc(pc)
    except PlaylistError as e: raise BridgeError(str(e)) from e
    meta=pc.get('bridge')
    if not isinstance(meta,dict) or meta.get('schema')!=BRIDGE_SCHEMA or meta.get('snapshot_id')!=phone['snapshot_id'] or meta.get('revision')!=phone['revision'] or meta.get('phone_sha256')!=digest(phone) or meta.get('track_sha256')!=digest(phone['tracks']):
        raise BridgeError('stale or altered bridge metadata / phone snapshot; re-export before planning')
    expected=phone_to_pc(phone)
    if pc['tracks']!=expected['tracks']:
        raise BridgeError('track metadata changed; editing metadata is not supported, re-export')
    by_id={p['id']:p for p in phone['playlists']}
    proposed=[]; seen_ids=set(); operations=[]
    for p in pc['playlists']:
        # PC editor preserves unknown playlist fields through reorder and rename.
        pid=p.get('phone_id')
        if pid is None:
            pid='pc-'+hashlib.sha256((phone['snapshot_id']+'\0'+p['name']).encode()).hexdigest()[:24]
            if pid in by_id: raise BridgeError('generated ID collision')
            kind=p.get('audiobook',False)
            if type(kind) is not bool: raise BridgeError('invalid audiobook flag')
            action='CREATE'
        else:
            if not isinstance(pid,str) or pid not in by_id: raise BridgeError('unknown playlist ID; no name-based remapping')
            if type(p.get('audiobook')) is not bool or p['audiobook']!=by_id[pid]['audiobook']:
                raise BridgeError('playlist audiobook kind changed')
            kind=p['audiobook']
            action='UPDATE' if (p['name']!=by_id[pid]['name'] or p['track_ids']!=by_id[pid]['track_keys']) else 'UNCHANGED'
        if pid in seen_ids: raise BridgeError('duplicate playlist ID in PC file')
        seen_ids.add(pid)
        if len(p['track_ids'])!=len(set(p['track_ids'])): raise BridgeError('Android player cannot preserve duplicate entries')
        proposed.append({'id':pid,'name':p['name'],'audiobook':kind,'track_keys':p['track_ids'][:]})
        operations.append({'action':action,'id':pid,'name':p['name'],'count':len(p['track_ids'])})
    # Absence from PC editor means KEEP, never implicit deletion.
    for p in phone['playlists']:
        if p['id'] not in seen_ids:
            proposed.append(copy.deepcopy(p))
            operations.append({'action':'PRESERVE_UNMENTIONED','id':p['id'],'name':p['name'],'count':len(p['track_keys'])})
    # Legacy offline plan refuses removing active listening context. The first phone
    # import may explicitly reset positions, per Aurora's Nov 5 owner decision.
    proposed_by_id={p['id']:p for p in proposed}
    for label in ('music','book'):
        ctx=phone.get(label,{})
        if not isinstance(ctx,dict): raise BridgeError('invalid '+label+' progress')
        pid=ctx.get('playlist_id',''); key=ctx.get('track_key','')
        if (not allow_reset_progress) and pid and key and (pid not in proposed_by_id or key not in proposed_by_id[pid]['track_keys']):
            raise BridgeError('edited playlist would remove current '+label+' listening track; no silent reset')
    names=[p['name'].casefold() for p in proposed]
    if len(names)!=len(set(names)): raise BridgeError('proposed playlist names collide with preserved phone playlists')
    return {'schema':PLAN_SCHEMA,'snapshot_id':phone['snapshot_id'],'expected_revision':phone['revision'],
            'expected_phone_sha256':digest(phone),'proposed_playlists':proposed,'operations':operations,'edited_pc':copy.deepcopy(pc),
            'note':'OFFLINE SIMULATION ONLY. NOT AN ANDROID IMPORT COMMAND.'}

IMPORT_SCHEMA='kyocera-playlist-import-v0.1'
IMPORT_FILENAME='pc_playlist_import_v1.json'

def phone_import_payload(phone, edited_pc):
    """Build the minimal manually transferred playlist-only import payload.

    Uses the existing exact-snapshot/track-identity bridge validation. Unlike the
    legacy offline plan, this explicitly permits clearing music/book progress on
    the phone. The Android app still requires a matching local snapshot ID.
    """
    proposed = plan(phone, edited_pc, allow_reset_progress=True)
    result = {
        'schema': IMPORT_SCHEMA,
        'expected_snapshot_id': proposed['snapshot_id'],
        'playlists': proposed['proposed_playlists'],
    }
    raw = (json.dumps(result, ensure_ascii=False, indent=2)+'\n').encode('utf-8')
    if len(raw)>MAX_BYTES:
        raise BridgeError('phone import exceeds 8 MB limit')
    return result

def simulate(phone,proposal):
    validate_phone(phone)
    if not isinstance(proposal,dict) or proposal.get('schema')!=PLAN_SCHEMA or proposal.get('snapshot_id')!=phone['snapshot_id'] or proposal.get('expected_revision')!=phone['revision'] or proposal.get('expected_phone_sha256')!=digest(phone):
        raise BridgeError('stale or modified phone snapshot; reject simulation')
    if plan(phone,proposal.get('edited_pc'))!=proposal:
        raise BridgeError('plan contents modified; recompute from PC editor JSON')
    candidate=copy.deepcopy(phone)
    candidate['playlists']=copy.deepcopy(proposal.get('proposed_playlists'))
    candidate['revision']+=1
    validate_phone(candidate)
    return candidate

def load_json(path):
    p=validate_output(path)
    if p.stat().st_size>MAX_BYTES: raise BridgeError('file exceeds 8 MB')
    with p.open('r',encoding='utf-8-sig') as f:
        try: return json.load(f)
        except (ValueError,UnicodeError) as e: raise BridgeError('invalid JSON: '+str(e)) from e

def main(argv=None):
    parser=argparse.ArgumentParser(description='Fictional offline Kyocera playlist metadata contract; NO ADB')
    parser.add_argument('action',choices=['export','plan','simulate'])
    parser.add_argument('phone',help='provisional phone snapshot JSON (synthetic only)')
    parser.add_argument('--pc',help='WQ140-edited metadata JSON (for plan)')
    parser.add_argument('--plan',dest='plan_path',help='proposed plan JSON (for simulate)')
    parser.add_argument('--out',required=True,help='new output JSON path, never overwrite')
    args=parser.parse_args(argv)
    try:
        phone=load_json(args.phone)
        if args.action=='export': result=phone_to_pc(phone)
        elif args.action=='plan':
            if not args.pc: parser.error('--pc is required for plan')
            result=plan(phone,load_json(args.pc))
        else:
            if not args.plan_path: parser.error('--plan is required for simulate')
            result=simulate(phone,load_json(args.plan_path))
        # No overwrite, and output path checks inherited from WQ140.
        atomic_write(args.out,(json.dumps(result,ensure_ascii=False,indent=2)+'\n').encode('utf-8'))
        print('Wrote new offline '+args.action+' JSON: '+str(args.out))
        if args.action=='plan':
            for x in result['operations']: print(x['action']+': '+x['name'])
        return 0
    except (BridgeError,PlaylistError,OSError,TypeError,ValueError) as e:
        print('REFUSED: '+str(e))
        return 2

if __name__=='__main__': raise SystemExit(main())
