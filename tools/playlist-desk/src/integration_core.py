"""Combine existing WQ140 editor and WQ146 bridge without changing their contracts.

WHAT: Produce editor JSON, proposed plan and simulated result in memory.
WHY: One UI can retain exact phone-snapshot provenance while editing manual order.
IF CHANGED: Recheck bridge.plan/simulate, playlist_core.validate and GUI attach rules.
"""
import copy
from bridge import phone_to_pc, plan, simulate, BridgeError
from playlist_core import validate as validate_pc, PlaylistError


def attach_candidate(phone, existing_pc=None):
    """Return (editor_data, retained_edits) for the same exact snapshot.

    Do not preserve an editor's edits if its bridge identity/track inventory
    differs. The GUI asks before discarding such edits.
    """
    fresh = phone_to_pc(phone)
    if (isinstance(existing_pc, dict)
            and existing_pc.get('bridge') == fresh['bridge']
            and existing_pc.get('tracks') == fresh['tracks']):
        return copy.deepcopy(existing_pc), True
    return fresh, False


def create_plan(phone, pc):
    return plan(phone, pc)


def create_preview(phone, pc):
    return simulate(phone, create_plan(phone, pc))


def reattach_saved_playlists(phone, saved_pc):
    """Recover an existing editor JSON against a new phone snapshot by exact paths.

    This is an explicit opt-in alternative to the strict snapshot-identity match;
    it changes the IN-MEMORY editor data only. No file transfer or phone change.
    Never guess based on song title, artist, filename, or fuzzy similarity.
    """
    try:
        validate_pc(saved_pc)
    except PlaylistError as exc:
        raise BridgeError(str(exc)) from exc
    fresh=phone_to_pc(phone)
    by_path={t['path'].casefold():t['id'] for t in fresh['tracks']}
    old_tracks={t['id']:t for t in saved_pc['tracks']}
    phone_by_id={p['phone_id']:p for p in fresh['playlists'] if p.get('phone_id')}
    phone_by_name={p['name'].casefold():p for p in fresh['playlists']}
    recovered=[]
    for old in saved_pc['playlists']:
        entries=[]
        for old_id in old['track_ids']:
            original=old_tracks[old_id]
            if original.get('pc_status') == 'pending-local-not-on-phone':
                raise BridgeError('Saved playlist '+repr(old['name'])+
                    ' includes a PC-only audio file that is not yet on the phone: '+original['path'])
            path=original['path'].casefold()
            if path not in by_path:
                raise BridgeError('Saved playlist '+repr(old['name'])+
                    ' refers to a track not in the new phone snapshot: '+original['path'])
            entries.append(by_path[path])
        if len(entries)!=len(set(entries)):
            raise BridgeError('Saved playlist '+repr(old['name'])+' has duplicate track references')
        matched=None
        old_phone_id=old.get('phone_id')
        if isinstance(old_phone_id,str):
            matched=phone_by_id.get(old_phone_id)
        if matched is None:
            matched=phone_by_name.get(old['name'].casefold())
        audiobook=old.get('audiobook',matched.get('audiobook',False) if matched else False)
        if type(audiobook) is not bool:
            raise BridgeError('Unknown audiobook classification in '+repr(old['name']))
        if matched and audiobook!=matched['audiobook']:
            raise BridgeError('Music/audiobook classification changed in '+repr(old['name']))
        out={'name':old['name'],'track_ids':entries,'audiobook':audiobook}
        if matched:
            out['phone_id']=matched['phone_id']
        recovered.append(out)
    # Keep existing phone playlists that are not represented in the saved editor.
    used_ids={p.get('phone_id') for p in recovered}
    used_names={p['name'].casefold() for p in recovered}
    for phone_pl in fresh['playlists']:
        if phone_pl.get('phone_id') not in used_ids and phone_pl['name'].casefold() not in used_names:
            recovered.append(phone_pl)
    fresh['playlists']=recovered
    validate_pc(fresh)
    # Source snapshot identity is now current. The caller still asks the user
    # to confirm the reattachment; saved_pc and phone are never mutated.
    return fresh
