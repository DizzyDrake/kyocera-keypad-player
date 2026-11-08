#!/usr/bin/env python3
"""Source checks only: parsing, warning, and mutation sequencing still need a real APK test."""
from pathlib import Path
r=Path(__file__).resolve().parent.parent
source=(r/'app/src/main/java/org/roarin/kyocerakeypad/KeypadPlayerActivity.java').read_text()
core=(r/'app/src/main/java/org/roarin/kyocerakeypad/core/PhonePlaylistImport.java').read_text()
checks={
 'correct schema retained': 'PhonePlaylistImport.SCHEMA.equals(jsonText(payload,"schema"))' in source,
 'optional snapshot id': 'payload.has("expected_snapshot_id")' in source,
 'mismatched id is information': 'Snapshot ID differs; stale import explicitly allowed.' in source,
 'no old snapshot refusal': 'if(!expected.equals(current))' not in source,
 'preview before stop': source.index('PhonePlaylistImport.prepare(state,specs)')<source.index('if(!playback.stopPlayer())',source.index('PhonePlaylistImport.prepare(state,specs)')),
 'missing refs counted': 'prepared.missingReferences' in source,
 'positive confirmation required': '.setPositiveButton("Replace playlists"' in source,
 'explicit data loss warning': 'Unmatched entries will be lost from the ' in source,
 'uses prepared valid subset': 'PhonePlaylistImport.apply(next,prepared.playlists)' in source,
 'transactional mutation retained': 'commitMutation("Import PC playlists"' in source,
 'tracks still keyed by identity': 'if(target.tracks.containsKey(key))' in core,
 'duplicate ids and names still rejected': 'Duplicate playlist ID/name' in core,
 'duplicate track identities still rejected': 'Invalid/duplicate track identity' in core,
 'no phone file deletion': 'target.playlists.clear()' in core and 'target.tracks.clear()' not in core,
 'files remain bounded': 'PhonePlaylistImport.MAX_BYTES' in source,
}
for label,yes in checks.items():
 print(('PASS' if yes else 'FAIL')+' '+label)
assert all(checks.values()),'Source checks failed'
print(f'{len(checks)}/{len(checks)} source checks PASS')
