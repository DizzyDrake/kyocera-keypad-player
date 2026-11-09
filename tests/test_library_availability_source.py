#!/usr/bin/env python3
"""Static Android UI safety wiring checks; device behavior remains untested."""
from pathlib import Path
source=Path('app/src/main/java/org/roarin/kyocerakeypad/KeypadPlayerActivity.java').read_text()
checks={
 'settings cleanup': 'Review / clear unavailable audio references' in source,
 'settings rescan': 'Rescan local audio' in source,
 'cleanup dialog confirmation': '.setPositiveButton("Remove references"' in source,
 'transactional cleanup': 'next->LibraryAvailability.pruneInPlace(next,available)' in source and 'commitMutation("Clear unavailable audio references"' in source,
 'safe playback stop before cleanup': 'if(!stopPlayer()){\n                    message("Cleanup canceled:' in source,
 'cleanup rescan afterwards': 'scanLibrary();\n                    message("Removed stale saved references.' in source,
 'browser excludes unavailable': 'if(missing.contains(t.key) || conflicts.contains(t.key) || !mediaPaths.containsKey(t.key))continue;' in source,
 'snapshot projected': 'PhoneSnapshotExport.encode(preview.state,mediaPaths)' in source,
 'export no missing gate': 'if(recoveryMode || !mediaReady){\n            message("Export unavailable' in source,
 'import preflight projected': 'PhonePlaylistImport.prepare(view.state,specs)' in source,
 'stale imports no missing gate': 'Import blocked until the audio scan is ready' in source,
 'no title substitution': 'No title-based substitutions' in source,
 'path collision guard': 'available.removeAll(ambiguous)' in source,
 'audio preserved warning': 'it does not delete or rename any audio file' in source,
}
for name,ok in checks.items():
 print(('PASS ' if ok else 'FAIL ')+name)
assert all(checks.values()),'snapshot and cleanup wiring regression'
print(str(len(checks))+'/'+str(len(checks))+' safe source wiring checks PASS')
